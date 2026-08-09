import logging
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import settings

logger = logging.getLogger("app.database")

db_url = settings.database_url
engine = None

# Attempt to connect to MySQL. Fall back to local SQLite if it fails.
try:
    # Use a short timeout of 3 seconds so we don't hang startup if host is unreachable
    engine = create_engine(db_url, connect_args={"connect_timeout": 3})
    # Force a test connection to verify auth credentials
    with engine.connect() as conn:
        logger.info("Database: Successfully connected to MySQL database.")
except Exception as e:
    fallback_dir = settings.upload_dir
    os.makedirs(fallback_dir, exist_ok=True)
    fallback_path = os.path.join(fallback_dir, "ai_data_analyst.db")
    db_url = f"sqlite:///{fallback_path}"
    
    logger.warning(
        f"Database: Failed to connect to MySQL database ({str(e)}).\n"
        f"Database: Falling back to local SQLite database at: {db_url}"
    )
    # SQLite requires check_same_thread=False for multi-threaded applications like FastAPI
    engine = create_engine(db_url, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """
    FastAPI dependency yielding a scoped database session.
    Automatically closes the session after request lifecycle.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
