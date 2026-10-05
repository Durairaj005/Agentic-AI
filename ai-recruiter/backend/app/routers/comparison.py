from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.services.comparison_service import comparison_service
from app.schemas.comparison import CompareCandidatesRequest, ComparisonMatrixResponse

router = APIRouter(prefix="/candidates", tags=["Candidate Comparison Matrix"])


@router.post("/compare", response_model=ComparisonMatrixResponse)
def compare_candidates(
    payload: CompareCandidatesRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Compare 2 to 4 candidates side-by-side with skill overlap, factor breakdowns, and AI verdict."""
    try:
        matrix = comparison_service.compare_candidates(
            db=db,
            candidate_ids=payload.candidate_ids,
            job_id=payload.job_id
        )
        return matrix
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
