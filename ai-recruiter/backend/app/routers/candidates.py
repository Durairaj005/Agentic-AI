import os
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, UploadFile, File, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.candidate import Candidate
from app.schemas.candidate import (
    CandidateCreate,
    CandidateUpdate,
    CandidateResponse,
    CandidateUploadResponse,
)
from app.services.candidate_service import candidate_service
from app.dependencies.auth import get_current_user

router = APIRouter(prefix="/candidates", tags=["Candidates"])


@router.get("", response_model=List[CandidateResponse])
def list_candidates(
    search: Optional[str] = Query(None, description="Search by name, email, location, or summary"),
    min_experience: Optional[float] = Query(None, ge=0.0, description="Minimum years of experience"),
    max_experience: Optional[float] = Query(None, ge=0.0, description="Maximum years of experience"),
    education_level: Optional[str] = Query(None, description="Education tier"),
    skill: Optional[str] = Query(None, description="Filter by technical skill (e.g. Python, SQL)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List candidates with multi-factor filters and search."""
    return candidate_service.list_candidates(
        db,
        skip=skip,
        limit=limit,
        search=search,
        min_experience=min_experience,
        max_experience=max_experience,
        education_level=education_level,
        skill=skill
    )


@router.post("", response_model=CandidateResponse, status_code=status.HTTP_201_CREATED)
def create_candidate(
    candidate_in: CandidateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Manually register a candidate profile with skills."""
    return candidate_service.create_candidate(db, candidate_in)


@router.post("/upload-resume", response_model=CandidateUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_resume(
    file: UploadFile = File(..., description="Resume document (PDF, DOCX, TXT)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upload resume document, extract text using PyMuPDF / python-docx, and parse skills."""
    return await candidate_service.upload_and_parse(db, file)


@router.post("/seed", response_model=List[CandidateResponse])
def seed_candidates(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Seed 20 realistic candidate profiles for demonstration and testing."""
    return candidate_service.seed_default_candidates(db)


@router.get("/{candidate_id}", response_model=CandidateResponse)
def get_candidate(
    candidate_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve full candidate profile with skills and history."""
    return candidate_service.get_candidate(db, candidate_id)


@router.put("/{candidate_id}", response_model=CandidateResponse)
def update_candidate(
    candidate_id: str,
    candidate_in: CandidateUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update candidate details and technical skills."""
    return candidate_service.update_candidate(db, candidate_id, candidate_in)


@router.delete("/{candidate_id}")
def delete_candidate(
    candidate_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete candidate and associated skills."""
    return candidate_service.delete_candidate(db, candidate_id)


@router.get("/{candidate_id}/download-resume")
def download_resume(
    candidate_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Download original candidate resume file."""
    candidate = candidate_service.get_candidate(db, candidate_id)
    if not candidate.resume_path or not os.path.exists(candidate.resume_path):
        raise HTTPException(status_code=404, detail="No resume file stored for this candidate.")

    return FileResponse(
        path=candidate.resume_path,
        filename=candidate.resume_filename or "resume.pdf",
        media_type="application/octet-stream"
    )
