import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Float, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base


class Application(Base):
    __tablename__ = "applications"
    __table_args__ = (
        UniqueConstraint("job_id", "candidate_id", name="uq_job_candidate"),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String(36), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    candidate_id = Column(String(36), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Detailed match scores (0.0 to 100.0)
    match_score = Column(Float, default=0.0, index=True, nullable=False)
    required_skills_score = Column(Float, default=0.0, nullable=False)
    preferred_skills_score = Column(Float, default=0.0, nullable=False)
    experience_score = Column(Float, default=0.0, nullable=False)
    education_score = Column(Float, default=0.0, nullable=False)
    semantic_score = Column(Float, default=0.0, nullable=False)
    
    # Explainability payload (JSON string with matched/missing skills, rationale, etc.)
    score_explanation = Column(Text, nullable=True)
    
    # Recruitment Pipeline Stage:
    # NEW | SCREENING | SHORTLISTED | CONTACTED | INTERVIEW | SELECTED | REJECTED | HIRED
    status = Column(String(30), default="NEW", index=True, nullable=False)
    recruiter_notes = Column(Text, nullable=True)
    
    applied_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    job = relationship("Job", back_populates="applications")
    candidate = relationship("Candidate", back_populates="applications")
    interviews = relationship("Interview", back_populates="application", cascade="all, delete-orphan")
