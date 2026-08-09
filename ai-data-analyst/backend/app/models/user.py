"""
models/user.py — SQLAlchemy User Model (Phase 10)
"""
import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from app.database.connection import Base


class User(Base):
    """Represents an authenticated user of the platform."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(64), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(
        DateTime,
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        nullable=False,
    )
