from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class CandidateSkillBase(BaseModel):
    skill: str = Field(..., min_length=1, max_length=100)
    years_experience: float = Field(default=1.0, ge=0.0, le=50.0)
    confidence_score: float = Field(default=1.0, ge=0.0, le=1.0)


class CandidateSkillCreate(CandidateSkillBase):
    pass


class CandidateSkillResponse(CandidateSkillBase):
    id: str
    candidate_id: str

    model_config = ConfigDict(from_attributes=True)


class CandidateBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=150)
    email: EmailStr
    phone: Optional[str] = Field(None, max_length=50)
    location: str = Field(default="Not specified", max_length=150)
    total_experience: float = Field(default=0.0, ge=0.0, le=50.0)
    education_level: str = Field(
        default="BACHELORS",
        pattern="^(BACHELORS|MASTERS|PHD|DIPLOMA|SELF_TAUGHT|OTHER)$"
    )
    education_details: Optional[str] = Field(None, max_length=255)
    summary: Optional[str] = None


class CandidateCreate(CandidateBase):
    skills: List[CandidateSkillCreate] = []
    resume_filename: Optional[str] = None
    resume_path: Optional[str] = None
    resume_raw_text: Optional[str] = None


class CandidateUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=150)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=50)
    location: Optional[str] = Field(None, max_length=150)
    total_experience: Optional[float] = Field(None, ge=0.0, le=50.0)
    education_level: Optional[str] = Field(
        None,
        pattern="^(BACHELORS|MASTERS|PHD|DIPLOMA|SELF_TAUGHT|OTHER)$"
    )
    education_details: Optional[str] = Field(None, max_length=255)
    summary: Optional[str] = None
    skills: Optional[List[CandidateSkillCreate]] = None


class CandidateResponse(CandidateBase):
    id: str
    resume_filename: Optional[str] = None
    resume_path: Optional[str] = None
    resume_raw_text: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    skills: List[CandidateSkillResponse] = []

    model_config = ConfigDict(from_attributes=True)


class CandidateUploadResponse(BaseModel):
    candidate: CandidateResponse
    extracted_text_preview: str
    message: str = "Resume successfully ingested and parsed"
