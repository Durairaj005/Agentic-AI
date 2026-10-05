import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class Job(Base):
    __tablename__ = "jobs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(200), index=True, nullable=False)
    company = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    location = Column(String(150), default="Remote", nullable=False)
    employment_type = Column(String(50), default="FULL_TIME", nullable=False)  # FULL_TIME, CONTRACT, PART_TIME, REMOTE
    experience_min = Column(Float, default=0.0, nullable=False)
    experience_max = Column(Float, default=10.0, nullable=False)
    status = Column(String(30), default="ACTIVE", index=True, nullable=False)  # ACTIVE, DRAFT, CLOSED
    created_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    creator = relationship("User", back_populates="jobs")
    skills = relationship("JobSkill", back_populates="job", cascade="all, delete-orphan")
    applications = relationship("Application", back_populates="job", cascade="all, delete-orphan")


class JobSkill(Base):
    __tablename__ = "job_skills"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String(36), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    skill = Column(String(100), nullable=False, index=True)
    importance = Column(String(20), default="HIGH", nullable=False)  # HIGH, MEDIUM, LOW
    required = Column(Boolean, default=True, nullable=False)  # True = Required, False = Preferred

    job = relationship("Job", back_populates="skills")
