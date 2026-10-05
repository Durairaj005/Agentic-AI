from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.models.job import Job, JobSkill
from app.models.candidate import Candidate, CandidateSkill
from app.models.application import Application
from app.models.interview import Interview
from app.models.followup import Note, Followup
from app.schemas.analytics import (
    AnalyticsOverviewResponse,
    FunnelStageMetric,
    ScoreBucketMetric,
    SkillDemandSupplyMetric,
    EducationDistributionMetric,
    RecentActivityItem
)

ORDERED_STAGES = [
    "NEW",
    "SCREENING",
    "SHORTLISTED",
    "CONTACTED",
    "INTERVIEW",
    "SELECTED",
    "HIRED",
    "REJECTED"
]


class AnalyticsService:
    @staticmethod
    def get_overview_metrics(db: Session) -> AnalyticsOverviewResponse:
        total_jobs = db.query(Job).count()
        active_jobs = db.query(Job).filter(Job.status == "ACTIVE").count()
        total_candidates = db.query(Candidate).count()
        total_applications = db.query(Application).count()
        hired_count = db.query(Application).filter(Application.status == "HIRED").count()
        interviewing_count = db.query(Application).filter(Application.status == "INTERVIEW").count()

        # Average match score
        avg_score_raw = db.query(func.avg(Application.match_score)).scalar()
        average_match_score = round(float(avg_score_raw), 1) if avg_score_raw is not None else 0.0

        # Funnel stage breakdown
        stage_counts_raw = (
            db.query(Application.status, func.count(Application.id))
            .group_by(Application.status)
            .all()
        )
        stage_map = {stage: count for stage, count in stage_counts_raw}

        funnel: List[FunnelStageMetric] = []
        for stage in ORDERED_STAGES:
            cnt = stage_map.get(stage, 0)
            conv = round((cnt / total_applications * 100), 1) if total_applications > 0 else 0.0
            funnel.append(FunnelStageMetric(
                stage=stage,
                count=cnt,
                conversion_rate=conv
            ))

        # Score distribution buckets
        apps = db.query(Application.match_score).all()
        scores = [a[0] for a in apps]

        b_90_100 = sum(1 for s in scores if s >= 90.0)
        b_80_89 = sum(1 for s in scores if 80.0 <= s < 90.0)
        b_70_79 = sum(1 for s in scores if 70.0 <= s < 80.0)
        b_60_69 = sum(1 for s in scores if 60.0 <= s < 70.0)
        b_below_60 = sum(1 for s in scores if s < 60.0)

        score_distribution = [
            ScoreBucketMetric(bucket="90-100%", count=b_90_100, label="Exceptional Fit (90-100%)"),
            ScoreBucketMetric(bucket="80-89%", count=b_80_89, label="Strong Fit (80-89%)"),
            ScoreBucketMetric(bucket="70-79%", count=b_70_79, label="Moderate Fit (70-79%)"),
            ScoreBucketMetric(bucket="60-69%", count=b_60_69, label="Potential Fit (60-69%)"),
            ScoreBucketMetric(bucket="<60%", count=b_below_60, label="Low Fit (<60%)"),
        ]

        # Skills Demand vs Supply
        # Top 8 required skills across active jobs
        job_skills_query = (
            db.query(JobSkill.skill, func.count(JobSkill.id))
            .join(Job)
            .filter(Job.status == "ACTIVE")
            .group_by(JobSkill.skill)
            .order_by(desc(func.count(JobSkill.id)))
            .limit(8)
            .all()
        )

        skills_gap: List[SkillDemandSupplyMetric] = []
        for skill_name, job_demand in job_skills_query:
            # Count candidates with this canonical skill
            cand_supply = (
                db.query(CandidateSkill)
                .filter(CandidateSkill.skill.ilike(skill_name))
                .count()
            )
            skills_gap.append(SkillDemandSupplyMetric(
                skill=skill_name,
                job_demand_count=job_demand,
                talent_supply_count=cand_supply
            ))

        # Education Breakdown
        edu_query = (
            db.query(Candidate.education_level, func.count(Candidate.id))
            .group_by(Candidate.education_level)
            .all()
        )
        education_breakdown: List[EducationDistributionMetric] = []
        for edu_level, cnt in edu_query:
            pct = round((cnt / total_candidates * 100), 1) if total_candidates > 0 else 0.0
            education_breakdown.append(EducationDistributionMetric(
                level=edu_level or "OTHER",
                count=cnt,
                percentage=pct
            ))

        # Recent Activity (Interleaved recent notes, interviews, applications)
        recent_activity: List[RecentActivityItem] = []

        # Recent applications
        recent_apps = (
            db.query(Application)
            .order_by(Application.applied_at.desc())
            .limit(4)
            .all()
        )
        for app in recent_apps:
            cand_name = app.candidate.name if app.candidate else "Candidate"
            job_name = app.job.title if app.job else "Role"
            recent_activity.append(RecentActivityItem(
                id=app.id,
                type="APPLICATION",
                title=f"{cand_name} matched for {job_name}",
                description=f"AI match calculated at {app.match_score:.1f}% fit score ({app.status}).",
                timestamp=app.applied_at.isoformat()
            ))

        # Recent interviews
        recent_interviews = (
            db.query(Interview)
            .order_by(Interview.created_at.desc())
            .limit(3)
            .all()
        )
        for itw in recent_interviews:
            cand_name = itw.application.candidate.name if itw.application and itw.application.candidate else "Candidate"
            recent_activity.append(RecentActivityItem(
                id=itw.id,
                type="INTERVIEW",
                title=f"{itw.interview_type} Round: {cand_name}",
                description=f"Panel: {itw.interviewer} &bull; Status: {itw.status}",
                timestamp=itw.created_at.isoformat()
            ))

        # Recent notes
        recent_notes = (
            db.query(Note)
            .order_by(Note.created_at.desc())
            .limit(3)
            .all()
        )
        for n in recent_notes:
            cand_name = n.candidate.name if n.candidate else "Candidate"
            recruiter_name = n.recruiter.name if n.recruiter else "Recruiter"
            recent_activity.append(RecentActivityItem(
                id=n.id,
                type="NOTE",
                title=f"Note by {recruiter_name} on {cand_name}",
                description=n.note[:100] + ("..." if len(n.note) > 100 else ""),
                timestamp=n.created_at.isoformat()
            ))

        # Sort recent activities by timestamp descending and take 6
        recent_activity.sort(key=lambda x: x.timestamp, reverse=True)
        recent_activity = recent_activity[:6]

        return AnalyticsOverviewResponse(
            total_jobs=total_jobs,
            active_jobs=active_jobs,
            total_candidates=total_candidates,
            total_applications=total_applications,
            hired_count=hired_count,
            interviewing_count=interviewing_count,
            average_match_score=average_match_score,
            funnel=funnel,
            score_distribution=score_distribution,
            skills_gap=skills_gap,
            education_breakdown=education_breakdown,
            recent_activity=recent_activity
        )


analytics_service = AnalyticsService()
