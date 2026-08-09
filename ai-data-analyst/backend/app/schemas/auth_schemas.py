"""
schemas/auth_schemas.py — Pydantic schemas for auth requests/responses (Phase 10)
"""
from pydantic import BaseModel, EmailStr
from typing import Optional


class UserCreate(BaseModel):
    """Payload for POST /register."""
    username: str
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    """Payload for POST /login."""
    username: str
    password: str


class Token(BaseModel):
    """Response from successful /login."""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Decoded JWT payload container."""
    username: Optional[str] = None


class UserResponse(BaseModel):
    """Safe user information returned to the client (no password)."""
    id: int
    username: str
    email: str
    is_active: bool

    model_config = {"from_attributes": True}
