from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Body, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.schemas.matching import (
    MatchWeightConfig,
    RankedMatchesResponse,
    MatchExecutionSummary,
    CandidateMatchResult
)
from app.services.matching_service import matching_service
from app.dependencies.auth import get_current_user

router = APIRouter(prefix="/jobs", tags=["Matching & Ranking"])


@router.post("/{job_id}/match", response_model=MatchExecutionSummary)
def run_job_matching(
    job_id: str,
    weights: MatchWeightConfig = Body(default_factory=MatchWeightConfig),
    candidate_ids: Optional[List[str]] = Body(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Execute transparent multi-factor matching engine for a job description.
    Scores candidates on Required Skills (40%), Preferred (20%), Experience (20%), Education (10%), and Semantics (10%).
    """
    return matching_service.execute_matching_for_job(
        db=db,
        job_id=job_id,
        candidate_ids=candidate_ids,
        weights=weights
    )


@router.get("/{job_id}/matches", response_model=RankedMatchesResponse)
def get_ranked_matches(
    job_id: str,
    sort_by: str = Query("score", pattern="^(score|experience)$", description="Sort by overall match score or total experience"),
    min_score: Optional[float] = Query(None, ge=0.0, le=100.0, description="Filter by minimum overall score percentage"),
    status: Optional[str] = Query(None, description="Filter by application pipeline status"),
    search: Optional[str] = Query(None, description="Search candidate name or email"),
    skill: Optional[str] = Query(None, description="Filter candidates possessing specific skill"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve ranked candidates for a specific job requisition with transparent factor breakdowns and explainability.
    """
    return matching_service.get_ranked_matches(
        db=db,
        job_id=job_id,
        sort_by=sort_by,
        min_score=min_score,
        status_filter=status,
        search=search,
        skill=skill
    )
