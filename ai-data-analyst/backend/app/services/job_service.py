import logging
import json
import datetime
from typing import Optional, Dict, Any
from app.services.cache_service import cache_service

logger = logging.getLogger("app.jobs")

class JobStatusService:
    """
    Tracks state of asynchronous analysis tasks.
    Uses Redis when available, falls back to a thread-safe in-memory cache if Redis is down.
    """
    def __init__(self):
        # Local in-memory fallback cache
        self.in_memory_jobs: Dict[str, Dict[str, Any]] = {}

    def _get_key(self, job_id: str) -> str:
        return f"job:{job_id}"

    def set_job_status(self, job_id: str, status: str, result: Optional[Any] = None, error: Optional[str] = None):
        """
        Record or update the execution status of a task.
        """
        job_data = {
            "job_id": job_id,
            "status": status,
            "result": json.dumps(result) if result else None,
            "error": error,
            "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }

        # 1. Attempt Redis Storage
        if cache_service.is_available():
            key = self._get_key(job_id)
            try:
                # Store all fields in Redis hash
                cache_service.redis_client.hset(key, mapping=job_data)
                # Set TTL of 2 hours
                cache_service.redis_client.expire(key, 7200)
                logger.info(f"Job Service: Saved job '{job_id}' status '{status}' to Redis.")
                return
            except Exception as e:
                logger.error(f"Job Service: Failed to write job to Redis: {str(e)}")

        # 2. Memory Fallback
        self.in_memory_jobs[job_id] = job_data
        logger.info(f"Job Service: Saved job '{job_id}' status '{status}' to Memory Fallback.")

    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve execution status of a task.
        """
        # 1. Attempt Redis Read
        if cache_service.is_available():
            key = self._get_key(job_id)
            try:
                data = cache_service.redis_client.hgetall(key)
                if data:
                    return {
                        "job_id": data.get("job_id"),
                        "status": data.get("status"),
                        "result": json.loads(data["result"]) if data.get("result") else None,
                        "error": data.get("error"),
                        "updated_at": data.get("updated_at")
                    }
            except Exception as e:
                logger.error(f"Job Service: Failed to read job from Redis: {str(e)}")

        # 2. Memory Fallback
        data = self.in_memory_jobs.get(job_id)
        if data:
            return {
                "job_id": data.get("job_id"),
                "status": data.get("status"),
                "result": json.loads(data["result"]) if data.get("result") else None,
                "error": data.get("error"),
                "updated_at": data.get("updated_at")
            }

        return None

# Singleton instance
job_service = JobStatusService()
