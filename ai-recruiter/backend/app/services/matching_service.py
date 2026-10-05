import json
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_
from fastapi import HTTPException, status
from app.models.job import Job, JobSkill
from app.models.candidate import Candidate, CandidateSkill
from app.models.application import Application
from app.ai.matcher import matching_engine
from app.schemas.matching import (
    MatchWeightConfig,
    ScoreExplanationSchema,
    CandidateMatchResult,
    RankedMatchesResponse,
    MatchExecutionSummary,
)
from app.schemas.candidate import CandidateResponse


class MatchingService:
    @classmethod
    def execute_matching_for_job(
        cls,
        db: Session,
        job_id: str,
        candidate_ids: Optional[List[str]] = None,
        weights: MatchWeightConfig = MatchWeightConfig()
    ) -> MatchExecutionSummary:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job requisition not found")

        # Extract job skills
        job_req_skills = [s.skill for s in job.skills if s.required]
        job_pref_skills = [s.skill for s in job.skills if not s.required]
        job_full_text = f"{job.title}\n{job.description}\nSkills: {', '.join([s.skill for s in job.skills])}"

        # Fetch candidates
        query = db.query(Candidate)
        if candidate_ids and len(candidate_ids) > 0:
            query = query.filter(Candidate.id.in_(candidate_ids))
        candidates = query.all()

        if not candidates:
            return MatchExecutionSummary(
                job_id=job_id,
                evaluated_count=0,
                created_applications_count=0,
                message="No candidates found in directory to evaluate."
            )

        evaluated_count = 0
        created_count = 0

        for cand in candidates:
            cand_skills = [s.skill for s in cand.skills]
            cand_full_text = f"{cand.name}\n{cand.summary or ''}\n{cand.resume_raw_text or ''}\nSkills: {', '.join(cand_skills)}"

            match_result = matching_engine.calculate_match(
                candidate_skills=cand_skills,
                candidate_experience=cand.total_experience,
                candidate_education=cand.education_level,
                candidate_text=cand_full_text,
                job_required_skills=job_req_skills,
                job_preferred_skills=job_pref_skills,
                job_min_experience=job.experience_min,
                job_max_experience=job.experience_max,
                job_text=job_full_text,
                weights=weights
            )

            # Upsert application
            app = db.query(Application).filter(
                Application.job_id == job.id,
                Application.candidate_id == cand.id
            ).first()

            explanation_json = match_result["explanation"].model_dump_json()

            if app:
                app.match_score = match_result["overall_score"]
                app.required_skills_score = match_result["required_skills_score"]
                app.preferred_skills_score = match_result["preferred_skills_score"]
                app.experience_score = match_result["experience_score"]
                app.education_score = match_result["education_score"]
                app.semantic_score = match_result["semantic_score"]
                app.score_explanation = explanation_json
            else:
                app = Application(
                    job_id=job.id,
                    candidate_id=cand.id,
                    match_score=match_result["overall_score"],
                    required_skills_score=match_result["required_skills_score"],
                    preferred_skills_score=match_result["preferred_skills_score"],
                    experience_score=match_result["experience_score"],
                    education_score=match_result["education_score"],
                    semantic_score=match_result["semantic_score"],
                    score_explanation=explanation_json,
                    status="SCREENING"
                )
                db.add(app)
                created_count += 1

            evaluated_count += 1

        db.commit()

        return MatchExecutionSummary(
            job_id=job_id,
            evaluated_count=evaluated_count,
            created_applications_count=created_count,
            message=f"Successfully evaluated {evaluated_count} candidates against requisition '{job.title}'."
        )

    @classmethod
    def get_ranked_matches(
        cls,
        db: Session,
        job_id: str,
        sort_by: str = "score",  # score, experience
        min_score: Optional[float] = None,
        status_filter: Optional[str] = None,
        search: Optional[str] = None,
        skill: Optional[str] = None,
        weights: MatchWeightConfig = MatchWeightConfig()
    ) -> RankedMatchesResponse:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job requisition not found")

        # Auto-run matching if no applications exist yet for this job
        app_count = db.query(Application).filter(Application.job_id == job.id).count()
        if app_count == 0:
            cls.execute_matching_for_job(db, job_id=job.id, weights=weights)

        query = db.query(Application).join(Candidate, Application.candidate_id == Candidate.id).filter(
            Application.job_id == job.id
        )

        if min_score is not None:
            query = query.filter(Application.match_score >= min_score)

        if status_filter and status_filter.upper() != "ALL":
            query = query.filter(Application.status == status_filter.upper())

        if search and search.strip():
            term = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    Candidate.name.ilike(term),
                    Candidate.email.ilike(term),
                    Candidate.location.ilike(term)
                )
            )

        if skill and skill.strip():
            skill_term = f"%{skill.strip()}%"
            query = query.join(Candidate.skills).filter(CandidateSkill.skill.ilike(skill_term))

        # Sorting
        if sort_by == "experience":
            query = query.order_by(Candidate.total_experience.desc(), Application.match_score.desc())
        else:
            query = query.order_by(Application.match_score.desc(), Candidate.total_experience.desc())

        applications = query.all()

        results = []
        for app in applications:
            cand = app.candidate
            try:
                explanation_data = json.loads(app.score_explanation) if app.score_explanation else {}
                explanation = ScoreExplanationSchema(**explanation_data)
            except Exception:
                explanation = ScoreExplanationSchema(natural_language_explanation="Score computed via matching engine.")

            cand_response = CandidateResponse.model_validate(cand)

            results.append(
                CandidateMatchResult(
                    candidate=cand_response,
                    application_id=app.id,
                    overall_score=app.match_score,
                    required_skills_score=app.required_skills_score,
                    preferred_skills_score=app.preferred_skills_score,
                    experience_score=app.experience_score,
                    education_score=app.education_score,
                    semantic_score=app.semantic_score,
                    status=app.status,
                    recruiter_notes=app.recruiter_notes,
                    explanation=explanation
                )
            )

        return RankedMatchesResponse(
            job_id=job.id,
            job_title=job.title,
            total_evaluated=len(results),
            matches=results,
            weight_config=weights
        )


matching_service = MatchingService()
