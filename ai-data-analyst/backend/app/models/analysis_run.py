import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database.connection import Base

class AnalysisRun(Base):
    """
    SQLAlchemy model representing an agentic analysis execution run.
    """
    __tablename__ = "analysis_runs"

    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False)
    query = Column(String(500), nullable=False)
    explanation = Column(Text, nullable=False)
    result = Column(String(500), nullable=True)     # Path to visual chart or output artifact
    errors_json = Column(Text, nullable=False)    # Serialized errors list JSON
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), nullable=False)

    dataset = relationship("Dataset", back_populates="analysis_runs")
