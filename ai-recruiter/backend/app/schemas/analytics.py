from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class FunnelStageMetric(BaseModel):
    stage: str
    count: int
    conversion_rate: float  # Percentage of candidates that moved from initial stage


class ScoreBucketMetric(BaseModel):
    bucket: str
    count: int
    label: str


class SkillDemandSupplyMetric(BaseModel):
    skill: str
    job_demand_count: int
    talent_supply_count: int


class EducationDistributionMetric(BaseModel):
    level: str
    count: int
    percentage: float


class RecentActivityItem(BaseModel):
    id: str
    type: str  # 'APPLICATION', 'STAGE_CHANGE', 'INTERVIEW', 'NOTE'
    title: str
    description: str
    timestamp: str


class AnalyticsOverviewResponse(BaseModel):
    total_jobs: int
    active_jobs: int
    total_candidates: int
    total_applications: int
    hired_count: int
    interviewing_count: int
    average_match_score: float
    funnel: List[FunnelStageMetric]
    score_distribution: List[ScoreBucketMetric]
    skills_gap: List[SkillDemandSupplyMetric]
    education_breakdown: List[EducationDistributionMetric]
    recent_activity: List[RecentActivityItem]

    model_config = ConfigDict(from_attributes=True)
