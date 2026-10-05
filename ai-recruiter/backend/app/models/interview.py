import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class Interview(Base):
    __tablename__ = "interviews"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    application_id = Column(String(36), ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True)
    interview_date = Column(DateTime, nullable=False)
    interview_type = Column(String(50), default="TECHNICAL", nullable=False)  # SCREENING, TECHNICAL, BEHAVIORAL, FINAL
    interviewer = Column(String(120), default="Recruiting Team", nullable=False)
    status = Column(String(30), default="SCHEDULED", nullable=False)  # SCHEDULED, COMPLETED, CANCELLED, NO_SHOW
    feedback = Column(Text, nullable=True)
    rating = Column(Integer, nullable=True)  # 1 - 5
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    application = relationship("Application", back_populates="interviews")
