from typing import List
from fastapi import APIRouter, Depends, Query, Body
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.schemas.user import UserResponse
from app.services.auth_service import auth_service
from app.dependencies.auth import require_admin

router = APIRouter(prefix="/users", tags=["Users (Admin)"])


@router.get("", response_model=List[UserResponse])
def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """Admin-only: list all system users."""
    return auth_service.get_all(db, skip=skip, limit=limit)


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: str,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """Admin-only: fetch details of a specific user."""
    return auth_service.get_by_id(db, user_id)


@router.put("/{user_id}/role", response_model=UserResponse)
def change_user_role(
    user_id: str,
    role: str = Body(..., embed=True),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """Admin-only: update user role (RECRUITER <-> ADMIN)."""
    return auth_service.update_role(db, user_id=user_id, role=role)
