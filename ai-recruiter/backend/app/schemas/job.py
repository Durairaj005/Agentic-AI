from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class JobSkillBase(BaseModel):
    skill: str = Field(..., min_length=1, max_length=100)
    importance: str = Field(default="HIGH", pattern="^(HIGH|MEDIUM|LOW)$")
    required: bool = Field(default=True)  # True = Required, False = Preferred


class JobSkillCreate(JobSkillBase):
    pass


class JobSkillResponse(JobSkillBase):
    id: str
    job_id: str

    model_config = ConfigDict(from_attributes=True)


class JobBase(BaseModel):
    title: str = Field(..., min_length=2, max_length=200)
    company: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=10)
    location: str = Field(default="Remote", max_length=150)
    employment_type: str = Field(default="FULL_TIME", pattern="^(FULL_TIME|PART_TIME|CONTRACT|REMOTE)$")
    experience_min: float = Field(default=0.0, ge=0.0, le=50.0)
    experience_max: float = Field(default=10.0, ge=0.0, le=50.0)
    status: str = Field(default="ACTIVE", pattern="^(ACTIVE|DRAFT|CLOSED)$")


class JobCreate(JobBase):
    skills: List[JobSkillCreate] = []


class JobUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=2, max_length=200)
    company: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, min_length=10)
    location: Optional[str] = Field(None, max_length=150)
    employment_type: Optional[str] = Field(None, pattern="^(FULL_TIME|PART_TIME|CONTRACT|REMOTE)$")
    experience_min: Optional[float] = Field(None, ge=0.0, le=50.0)
    experience_max: Optional[float] = Field(None, ge=0.0, le=50.0)
    status: Optional[str] = Field(None, pattern="^(ACTIVE|DRAFT|CLOSED)$")
    skills: Optional[List[JobSkillCreate]] = None


class JobResponse(JobBase):
    id: str
    created_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    skills: List[JobSkillResponse] = []
    applicant_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class JobListResponse(BaseModel):
    items: List[JobResponse]
    total: int
