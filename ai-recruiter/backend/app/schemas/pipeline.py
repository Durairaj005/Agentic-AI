from datetime import datetime
from typing import List, Optional, Any
from pydantic import BaseModel, Field, ConfigDict
from app.schemas.candidate import CandidateResponse
from app.schemas.job import JobResponse


class ApplicationUpdateStage(BaseModel):
    status: str = Field(..., description="NEW, SCREENING, SHORTLISTED, CONTACTED, INTERVIEW, SELECTED, REJECTED, HIRED")
    recruiter_notes: Optional[str] = None


class ApplicationResponse(BaseModel):
    id: str
    job_id: str
    candidate_id: str
    match_score: float
    required_skills_score: float
    preferred_skills_score: float
    experience_score: float
    education_score: float
    semantic_score: float
    score_explanation: Optional[str] = None
    status: str
    recruiter_notes: Optional[str] = None
    applied_at: datetime
    updated_at: datetime
    candidate: Optional[CandidateResponse] = None
    job: Optional[JobResponse] = None

    model_config = ConfigDict(from_attributes=True)


class NoteCreate(BaseModel):
    note: str = Field(..., min_length=1, max_length=5000)


class NoteResponse(BaseModel):
    id: str
    candidate_id: str
    recruiter_id: Optional[str] = None
    recruiter_name: Optional[str] = "Recruiting Team"
    note: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FollowupCreate(BaseModel):
    candidate_id: str
    followup_date: datetime
    method: str = Field(default="CALL", description="CALL, EMAIL, LINKEDIN, MEETING")
    notes: Optional[str] = None


class FollowupUpdate(BaseModel):
    followup_date: Optional[datetime] = None
    method: Optional[str] = None
    status: Optional[str] = Field(None, description="PENDING, COMPLETED, OVERDUE")
    notes: Optional[str] = None


class FollowupResponse(BaseModel):
    id: str
    candidate_id: str
    recruiter_id: Optional[str] = None
    candidate_name: Optional[str] = None
    candidate_email: Optional[str] = None
    followup_date: datetime
    method: str
    status: str
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InterviewCreate(BaseModel):
    application_id: str
    interview_date: datetime
    interview_type: str = Field(default="TECHNICAL", description="SCREENING, TECHNICAL, BEHAVIORAL, FINAL")
    interviewer: str = Field(default="Technical Hiring Team")
    feedback: Optional[str] = None
    rating: Optional[int] = Field(default=None, ge=1, le=5)


class InterviewUpdate(BaseModel):
    interview_date: Optional[datetime] = None
    interview_type: Optional[str] = None
    interviewer: Optional[str] = None
    status: Optional[str] = Field(None, description="SCHEDULED, COMPLETED, CANCELLED, NO_SHOW")
    feedback: Optional[str] = None
    rating: Optional[int] = Field(None, ge=1, le=5)


class InterviewResponse(BaseModel):
    id: str
    application_id: str
    candidate_id: Optional[str] = None
    candidate_name: Optional[str] = None
    job_title: Optional[str] = None
    company: Optional[str] = None
    interview_date: datetime
    interview_type: str
    interviewer: str
    status: str
    feedback: Optional[str] = None
    rating: Optional[int] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
