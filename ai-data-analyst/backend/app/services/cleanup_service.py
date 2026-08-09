import asyncio
import datetime
import logging
import os
from pathlib import Path
from sqlalchemy.orm import Session
from app.database.connection import SessionLocal
from app.models.dataset import Dataset

logger = logging.getLogger("app.cleanup")

async def start_cleanup_worker(interval_seconds: int = 900, retention_hours: int = 4):
    """
    A persistent background loop that runs every `interval_seconds` (default: 15 minutes)
    and purges datasets (and files/charts) older than `retention_hours` (default: 4 hours).
    """
    logger.info("Database Cleanup Service: Background worker started.")
    while True:
        try:
            db = SessionLocal()
            try:
                cleanup_expired_datasets(db, retention_hours)
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Database Cleanup Service: Error during execution: {str(e)}")
        
        await asyncio.sleep(interval_seconds)

def cleanup_expired_datasets(db: Session, retention_hours: int = 4) -> int:
    """
    Finds and deletes datasets older than `retention_hours`.
    Deletes physical file assets and database rows.
    Returns the count of purged datasets.
    """
    cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=retention_hours)
    expired = db.query(Dataset).filter(Dataset.created_at < cutoff).all()
    
    if not expired:
        return 0
    
    logger.info(f"Database Cleanup Service: Found {len(expired)} expired datasets to purge.")
    
    purged_count = 0
    for ds in expired:
        try:
            # 1. Delete physical dataset file
            if os.path.exists(ds.filepath):
                try:
                    os.remove(ds.filepath)
                    logger.info(f"Database Cleanup Service: Deleted dataset file: {ds.filepath}")
                except Exception as e:
                    logger.error(f"Database Cleanup Service: Failed to delete file {ds.filepath}: {e}")
            
            # 2. Delete generated visual charts for all related analysis runs
            for run in ds.analysis_runs:
                if run.result and os.path.exists(run.result):
                    # Safety check: make sure we are deleting generated charts inside exports/charts or similar
                    result_path = Path(run.result)
                    if "exports" in result_path.parts or "charts" in result_path.parts:
                        try:
                            os.remove(run.result)
                            logger.info(f"Database Cleanup Service: Deleted chart file: {run.result}")
                        except Exception as e:
                            logger.error(f"Database Cleanup Service: Failed to delete chart {run.result}: {e}")
            
            # 2.5 Invalidate Redis cache keys associated with this dataset
            try:
                from app.services.cache_service import cache_service
                cache_service.invalidate_dataset_cache(ds.id)
            except Exception as cache_err:
                logger.error(f"Database Cleanup Service: Failed to invalidate cache: {cache_err}")

            # 3. Delete database record (cascading deletes analysis runs automatically)
            db.delete(ds)
            purged_count += 1
        except Exception as e:
            logger.error(f"Database Cleanup Service: Failed to purge dataset '{ds.filename}': {str(e)}")
            
    if purged_count > 0:
        db.commit()
        logger.info(f"Database Cleanup Service: Successfully purged {purged_count} datasets.")
        
    return purged_count
