from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.schemas.job import JobCreate, JobUpdate, JobResponse
from app.services.job_service import job_service
from app.dependencies.auth import get_current_user

router = APIRouter(prefix="/jobs", tags=["Jobs"])


@router.get("", response_model=List[JobResponse])
def list_jobs(
    status: Optional[str] = Query(None, description="Filter by status (ACTIVE, DRAFT, CLOSED, ALL)"),
    search: Optional[str] = Query(None, description="Search term for title, company, location, or description"),
    employment_type: Optional[str] = Query(None, description="Filter by employment type"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all job requisitions with optional status and text filters."""
    return job_service.list_jobs(
        db,
        skip=skip,
        limit=limit,
        status_filter=status,
        search=search,
        employment_type=employment_type
    )


@router.post("", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
def create_job(
    job_in: JobCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new job requisition with classified skills (required vs. preferred)."""
    return job_service.create_job(db, job_in=job_in, user_id=current_user.id)


@router.post("/seed", response_model=List[JobResponse])
def seed_jobs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Seed 5 realistic sample job requisitions (Python, Java, Data Engineer, Data Analyst, DevOps)."""
    return job_service.seed_default_jobs(db, user_id=current_user.id)


@router.get("/{job_id}", response_model=JobResponse)
def get_job(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get full details of a specific job requisition including skills and applicant count."""
    return job_service.get_job(db, job_id=job_id)


@router.put("/{job_id}", response_model=JobResponse)
def update_job(
    job_id: str,
    job_in: JobUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update job requisition details and classified technical skills."""
    return job_service.update_job(
        db,
        job_id=job_id,
        job_in=job_in,
        user_id=current_user.id,
        is_admin=(current_user.role == "ADMIN")
    )


@router.patch("/{job_id}/toggle-status", response_model=JobResponse)
def toggle_job_status(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Toggle a job's status between ACTIVE and CLOSED."""
    return job_service.toggle_status(
        db,
        job_id=job_id,
        user_id=current_user.id,
        is_admin=(current_user.role == "ADMIN")
    )


@router.delete("/{job_id}")
def delete_job(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a job requisition and its associated skills."""
    return job_service.delete_job(
        db,
        job_id=job_id,
        user_id=current_user.id,
        is_admin=(current_user.role == "ADMIN")
    )
