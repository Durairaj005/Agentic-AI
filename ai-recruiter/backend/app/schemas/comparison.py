from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field, ConfigDict
from app.schemas.candidate import CandidateResponse
from app.schemas.job import JobResponse


class CompareCandidatesRequest(BaseModel):
    candidate_ids: List[str] = Field(..., min_length=2, max_length=4)
    job_id: Optional[str] = None


class CandidateComparisonItem(BaseModel):
    candidate: CandidateResponse
    overall_match_score: Optional[float] = None
    required_skills_score: Optional[float] = None
    preferred_skills_score: Optional[float] = None
    experience_score: Optional[float] = None
    education_score: Optional[float] = None
    semantic_score: Optional[float] = None
    matched_skills: List[str] = []
    missing_skills: List[str] = []
    unique_skills: List[str] = []

    model_config = ConfigDict(from_attributes=True)


class ComparisonMatrixResponse(BaseModel):
    job: Optional[JobResponse] = None
    candidates: List[CandidateComparisonItem]
    common_skills: List[str]
    all_compared_skills: List[str]
    skill_matrix: Dict[str, Dict[str, bool]]  # skill -> { candidate_id: bool }
    ai_comparative_synthesis: str

    model_config = ConfigDict(from_attributes=True)
