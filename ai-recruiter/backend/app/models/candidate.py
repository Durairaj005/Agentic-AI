import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(150), index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    phone = Column(String(50), nullable=True)
    location = Column(String(150), default="Not specified", nullable=False)
    total_experience = Column(Float, default=0.0, nullable=False)
    education_level = Column(String(50), default="BACHELORS", nullable=False)  # BACHELORS, MASTERS, PHD, DIPLOMA, OTHER
    education_details = Column(String(255), nullable=True)
    resume_filename = Column(String(255), nullable=True)
    resume_path = Column(String(500), nullable=True)
    resume_raw_text = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    skills = relationship("CandidateSkill", back_populates="candidate", cascade="all, delete-orphan")
    applications = relationship("Application", back_populates="candidate", cascade="all, delete-orphan")
    notes = relationship("Note", back_populates="candidate", cascade="all, delete-orphan")
    followups = relationship("Followup", back_populates="candidate", cascade="all, delete-orphan")


class CandidateSkill(Base):
    __tablename__ = "candidate_skills"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    candidate_id = Column(String(36), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    skill = Column(String(100), nullable=False, index=True)
    years_experience = Column(Float, default=1.0, nullable=False)
    confidence_score = Column(Float, default=1.0, nullable=False)  # 0.0 - 1.0

    candidate = relationship("Candidate", back_populates="skills")
