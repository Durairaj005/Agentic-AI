from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict
from app.schemas.candidate import CandidateResponse


class MatchWeightConfig(BaseModel):
    weight_required_skills: float = Field(default=0.40, ge=0.0, le=1.0)
    weight_preferred_skills: float = Field(default=0.20, ge=0.0, le=1.0)
    weight_experience: float = Field(default=0.20, ge=0.0, le=1.0)
    weight_education: float = Field(default=0.10, ge=0.0, le=1.0)
    weight_semantic: float = Field(default=0.10, ge=0.0, le=1.0)


class ScoreExplanationSchema(BaseModel):
    matched_required_skills: List[str] = []
    missing_required_skills: List[str] = []
    matched_preferred_skills: List[str] = []
    missing_preferred_skills: List[str] = []
    experience_summary: str = ""
    education_summary: str = ""
    natural_language_explanation: str = ""


class CandidateMatchResult(BaseModel):
    candidate: CandidateResponse
    application_id: Optional[str] = None
    overall_score: float
    required_skills_score: float
    preferred_skills_score: float
    experience_score: float
    education_score: float
    semantic_score: float
    status: str = "NEW"
    recruiter_notes: Optional[str] = None
    explanation: ScoreExplanationSchema

    model_config = ConfigDict(from_attributes=True)


class RankedMatchesResponse(BaseModel):
    job_id: str
    job_title: str
    total_evaluated: int
    matches: List[CandidateMatchResult]
    weight_config: MatchWeightConfig


class MatchExecutionSummary(BaseModel):
    job_id: str
    evaluated_count: int
    created_applications_count: int
    message: str = "Candidate matching completed successfully."
