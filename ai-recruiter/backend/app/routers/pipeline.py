from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.services.pipeline_service import pipeline_service, VALID_STAGES
from app.schemas.pipeline import (
    ApplicationResponse,
    ApplicationUpdateStage,
    NoteCreate,
    NoteResponse,
    FollowupCreate,
    FollowupUpdate,
    FollowupResponse,
    InterviewCreate,
    InterviewUpdate,
    InterviewResponse,
)

router = APIRouter(tags=["Recruitment Pipeline & Activities"])


# --- Applications & Pipeline Stages ---

@router.get("/applications", response_model=List[ApplicationResponse])
def get_applications(
    job_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    min_score: Optional[float] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve applications filtered by job, pipeline stage, score, and search."""
    return pipeline_service.get_applications(
        db, job_id=job_id, status=status, search=search, min_score=min_score
    )


@router.get("/applications/{application_id}", response_model=ApplicationResponse)
def get_application_by_id(
    application_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get single application details."""
    app = pipeline_service.get_application_by_id(db, application_id)
    if not app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Application {application_id} not found",
        )
    return app


@router.put("/applications/{application_id}/stage", response_model=ApplicationResponse)
def update_application_stage(
    application_id: str,
    payload: ApplicationUpdateStage,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Transition candidate to a new recruitment pipeline stage."""
    try:
        updated = pipeline_service.update_application_stage(
            db=db,
            application_id=application_id,
            stage=payload.status,
            recruiter_notes=payload.recruiter_notes,
            user_id=current_user.id,
        )
        return updated
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# --- Candidate Recruiter Notes ---

@router.get("/candidates/{candidate_id}/notes", response_model=List[NoteResponse])
def get_candidate_notes(
    candidate_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Fetch timeline of recruiter notes for a candidate."""
    notes = pipeline_service.get_candidate_notes(db, candidate_id)
    result = []
    for n in notes:
        recruiter_name = n.recruiter.name if n.recruiter else "Recruiting Team"
        result.append(
            NoteResponse(
                id=n.id,
                candidate_id=n.candidate_id,
                recruiter_id=n.recruiter_id,
                recruiter_name=recruiter_name,
                note=n.note,
                created_at=n.created_at,
            )
        )
    return result


@router.post("/candidates/{candidate_id}/notes", response_model=NoteResponse)
def create_candidate_note(
    candidate_id: str,
    payload: NoteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add a new recruiter note for a candidate."""
    try:
        note = pipeline_service.create_candidate_note(
            db=db,
            candidate_id=candidate_id,
            note_text=payload.note,
            user_id=current_user.id,
        )
        return NoteResponse(
            id=note.id,
            candidate_id=note.candidate_id,
            recruiter_id=note.recruiter_id,
            recruiter_name=current_user.name,
            note=note.note,
            created_at=note.created_at,
        )
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# --- Follow-ups ---

@router.get("/followups", response_model=List[FollowupResponse])
def get_followups(
    candidate_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve list of candidate follow-up reminders."""
    items = pipeline_service.get_followups(db, candidate_id=candidate_id, status=status)
    result = []
    for f in items:
        cand_name = f.candidate.name if f.candidate else "Unknown Candidate"
        cand_email = f.candidate.email if f.candidate else None
        result.append(
            FollowupResponse(
                id=f.id,
                candidate_id=f.candidate_id,
                recruiter_id=f.recruiter_id,
                candidate_name=cand_name,
                candidate_email=cand_email,
                followup_date=f.followup_date,
                method=f.method,
                status=f.status,
                notes=f.notes,
                created_at=f.created_at,
                updated_at=f.updated_at,
            )
        )
    return result


@router.post("/followups", response_model=FollowupResponse)
def create_followup(
    payload: FollowupCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new candidate follow-up reminder."""
    try:
        f = pipeline_service.create_followup(db, payload, user_id=current_user.id)
        cand_name = f.candidate.name if f.candidate else "Unknown Candidate"
        cand_email = f.candidate.email if f.candidate else None
        return FollowupResponse(
            id=f.id,
            candidate_id=f.candidate_id,
            recruiter_id=f.recruiter_id,
            candidate_name=cand_name,
            candidate_email=cand_email,
            followup_date=f.followup_date,
            method=f.method,
            status=f.status,
            notes=f.notes,
            created_at=f.created_at,
            updated_at=f.updated_at,
        )
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch("/followups/{followup_id}", response_model=FollowupResponse)
def update_followup(
    followup_id: str,
    payload: FollowupUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update follow-up status (e.g., mark COMPLETED) or notes."""
    try:
        f = pipeline_service.update_followup(db, followup_id, payload)
        cand_name = f.candidate.name if f.candidate else "Unknown Candidate"
        cand_email = f.candidate.email if f.candidate else None
        return FollowupResponse(
            id=f.id,
            candidate_id=f.candidate_id,
            recruiter_id=f.recruiter_id,
            candidate_name=cand_name,
            candidate_email=cand_email,
            followup_date=f.followup_date,
            method=f.method,
            status=f.status,
            notes=f.notes,
            created_at=f.created_at,
            updated_at=f.updated_at,
        )
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/followups/{followup_id}")
def delete_followup(
    followup_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a follow-up reminder."""
    success = pipeline_service.delete_followup(db, followup_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Followup not found"
        )
    return {"message": "Followup deleted successfully"}


# --- Interviews ---

@router.get("/interviews", response_model=List[InterviewResponse])
def get_interviews(
    application_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Fetch scheduled and completed interviews."""
    interviews = pipeline_service.get_interviews(db, application_id=application_id, status=status)
    result = []
    for i in interviews:
        cand_id = i.application.candidate_id if i.application else None
        cand_name = i.application.candidate.name if i.application and i.application.candidate else "Candidate"
        job_title = i.application.job.title if i.application and i.application.job else "Role"
        company = i.application.job.company if i.application and i.application.job else ""
        result.append(
            InterviewResponse(
                id=i.id,
                application_id=i.application_id,
                candidate_id=cand_id,
                candidate_name=cand_name,
                job_title=job_title,
                company=company,
                interview_date=i.interview_date,
                interview_type=i.interview_type,
                interviewer=i.interviewer,
                status=i.status,
                feedback=i.feedback,
                rating=i.rating,
                created_at=i.created_at,
            )
        )
    return result


@router.post("/interviews", response_model=InterviewResponse)
def schedule_interview(
    payload: InterviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Schedule a technical, behavioral, or screening interview."""
    try:
        i = pipeline_service.schedule_interview(db, payload)
        cand_id = i.application.candidate_id if i.application else None
        cand_name = i.application.candidate.name if i.application and i.application.candidate else "Candidate"
        job_title = i.application.job.title if i.application and i.application.job else "Role"
        company = i.application.job.company if i.application and i.application.job else ""
        return InterviewResponse(
            id=i.id,
            application_id=i.application_id,
            candidate_id=cand_id,
            candidate_name=cand_name,
            job_title=job_title,
            company=company,
            interview_date=i.interview_date,
            interview_type=i.interview_type,
            interviewer=i.interviewer,
            status=i.status,
            feedback=i.feedback,
            rating=i.rating,
            created_at=i.created_at,
        )
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch("/interviews/{interview_id}", response_model=InterviewResponse)
def update_interview(
    interview_id: str,
    payload: InterviewUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update interview status, rating, or submit evaluation feedback."""
    try:
        i = pipeline_service.update_interview(db, interview_id, payload)
        cand_id = i.application.candidate_id if i.application else None
        cand_name = i.application.candidate.name if i.application and i.application.candidate else "Candidate"
        job_title = i.application.job.title if i.application and i.application.job else "Role"
        company = i.application.job.company if i.application and i.application.job else ""
        return InterviewResponse(
            id=i.id,
            application_id=i.application_id,
            candidate_id=cand_id,
            candidate_name=cand_name,
            job_title=job_title,
            company=company,
            interview_date=i.interview_date,
            interview_type=i.interview_type,
            interviewer=i.interviewer,
            status=i.status,
            feedback=i.feedback,
            rating=i.rating,
            created_at=i.created_at,
        )
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# --- Seeder endpoint ---

@router.post("/pipeline/seed")
def seed_pipeline(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Seed demonstration applications across all 8 pipeline stages with notes and interviews."""
    return pipeline_service.seed_pipeline_demo_data(db)
