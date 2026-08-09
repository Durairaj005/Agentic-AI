import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.orm import relationship
from app.database.connection import Base

class Dataset(Base):
    """
    SQLAlchemy model representing an uploaded dataset.
    """
    __tablename__ = "datasets"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), unique=True, index=True, nullable=False)
    filepath = Column(String(500), nullable=False)
    total_rows = Column(Integer, nullable=False)
    total_columns = Column(Integer, nullable=False)
    profile_json = Column(Text, nullable=False)  # Serialized dataset profile dict
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), nullable=False)

    # Cascades deletions to clear query history logs automatically when dataset is purged
    analysis_runs = relationship("AnalysisRun", back_populates="dataset", cascade="all, delete-orphan")
