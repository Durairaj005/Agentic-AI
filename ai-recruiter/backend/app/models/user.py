import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime
from sqlalchemy.orm import relationship
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(120), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(30), default="RECRUITER", nullable=False)  # RECRUITER, ADMIN
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    jobs = relationship("Job", back_populates="creator", cascade="all, delete-orphan")
    notes = relationship("Note", back_populates="recruiter", cascade="all, delete-orphan")
    followups = relationship("Followup", back_populates="recruiter", cascade="all, delete-orphan")
