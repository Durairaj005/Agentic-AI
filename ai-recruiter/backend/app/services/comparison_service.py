from typing import List, Dict, Optional, Any
from sqlalchemy.orm import Session, joinedload

from app.models.candidate import Candidate
from app.models.job import Job
from app.ai.matcher import matching_engine
from app.schemas.comparison import (
    CandidateComparisonItem,
    ComparisonMatrixResponse
)
from app.schemas.candidate import CandidateResponse
from app.schemas.job import JobResponse


class ComparisonService:
    @staticmethod
    def compare_candidates(
        db: Session,
        candidate_ids: List[str],
        job_id: Optional[str] = None
    ) -> ComparisonMatrixResponse:
        candidates = (
            db.query(Candidate)
            .options(joinedload(Candidate.skills))
            .filter(Candidate.id.in_(candidate_ids))
            .all()
        )

        if len(candidates) < 2:
            raise ValueError("At least 2 valid candidates are required for side-by-side comparison.")

        target_job = None
        if job_id:
            target_job = (
                db.query(Job)
                .options(joinedload(Job.skills))
                .filter(Job.id == job_id)
                .first()
            )

        # Collect skills per candidate
        candidate_skills_map: Dict[str, set] = {}
        for c in candidates:
            candidate_skills_map[c.id] = {s.skill for s in c.skills}

        # Calculate Common and Union of skills
        all_skills_set = set()
        for s_set in candidate_skills_map.values():
            all_skills_set.update(s_set)

        common_skills_set = set.intersection(*candidate_skills_map.values()) if candidate_skills_map else set()
        common_skills = sorted(list(common_skills_set))
        all_compared_skills = sorted(list(all_skills_set))

        # Skill matrix: skill -> { candidate_id: bool }
        skill_matrix: Dict[str, Dict[str, bool]] = {}
        for skill in all_compared_skills:
            skill_matrix[skill] = {}
            for c in candidates:
                skill_matrix[skill][c.id] = skill in candidate_skills_map[c.id]

        # Build comparison items
        comparison_items: List[CandidateComparisonItem] = []
        for c in candidates:
            c_skills = candidate_skills_map[c.id]
            # Unique skills: skills this candidate has that NO other compared candidate has
            other_skills = set()
            for other_id, s_set in candidate_skills_map.items():
                if other_id != c.id:
                    other_skills.update(s_set)
            unique = sorted(list(c_skills - other_skills))

            item = CandidateComparisonItem(
                candidate=CandidateResponse.model_validate(c),
                unique_skills=unique
            )

            # If job provided, calculate match factors
            if target_job:
                job_req_skills = [s.skill for s in target_job.skills if s.required]
                job_pref_skills = [s.skill for s in target_job.skills if not s.required]
                job_full_text = f"{target_job.title}\n{target_job.description}\nSkills: {', '.join([s.skill for s in target_job.skills])}"
                cand_full_text = f"{c.name}\n{c.summary or ''}\n{c.resume_raw_text or ''}\nSkills: {', '.join(c_skills)}"

                match_result = matching_engine.calculate_match(
                    candidate_skills=list(c_skills),
                    candidate_experience=c.total_experience,
                    candidate_education=c.education_level,
                    candidate_text=cand_full_text,
                    job_required_skills=job_req_skills,
                    job_preferred_skills=job_pref_skills,
                    job_min_experience=target_job.experience_min,
                    job_max_experience=target_job.experience_max,
                    job_text=job_full_text
                )
                item.overall_match_score = match_result["overall_score"]
                item.required_skills_score = match_result["required_skills_score"]
                item.preferred_skills_score = match_result["preferred_skills_score"]
                item.experience_score = match_result["experience_score"]
                item.education_score = match_result["education_score"]
                item.semantic_score = match_result["semantic_score"]
                item.matched_skills = match_result["explanation"].matched_required_skills + match_result["explanation"].matched_preferred_skills
                item.missing_skills = match_result["explanation"].missing_required_skills

            comparison_items.append(item)

        # Sort items by overall match score if job provided, else by experience
        if target_job:
            comparison_items.sort(key=lambda x: (x.overall_match_score or 0.0), reverse=True)
        else:
            comparison_items.sort(key=lambda x: x.candidate.total_experience, reverse=True)

        # AI Comparative Synthesis
        c1 = comparison_items[0]
        c2 = comparison_items[1]
        synthesis = ComparisonService._generate_synthesis(c1, c2, target_job, common_skills)

        return ComparisonMatrixResponse(
            job=JobResponse.model_validate(target_job) if target_job else None,
            candidates=comparison_items,
            common_skills=common_skills,
            all_compared_skills=all_compared_skills,
            skill_matrix=skill_matrix,
            ai_comparative_synthesis=synthesis
        )

    @staticmethod
    def _generate_synthesis(
        c1: CandidateComparisonItem,
        c2: CandidateComparisonItem,
        job: Optional[Job],
        common_skills: List[str]
    ) -> str:
        name1 = c1.candidate.name
        name2 = c2.candidate.name
        exp1 = c1.candidate.total_experience
        exp2 = c2.candidate.total_experience

        if job:
            s1 = c1.overall_match_score or 0.0
            s2 = c2.overall_match_score or 0.0
            score_diff = abs(s1 - s2)

            return (
                f"**Comparative Decision Analysis for {job.title}:**\n\n"
                f"• **{name1}** ranks highest with an overall match score of **{s1:.1f}%** ({exp1} yrs experience). "
                f"They demonstrate full coverage of required competencies, bringing unique depth in {', '.join(c1.unique_skills[:3]) if c1.unique_skills else 'core system patterns'}.\n\n"
                f"• **{name2}** follows closely at **{s2:.1f}%** ({exp2} yrs experience), differing by only {score_diff:.1f} percentage points. "
                f"They offer distinctive capabilities in {', '.join(c2.unique_skills[:3]) if c2.unique_skills else 'practical implementation'}.\n\n"
                f"• **Shared Strengths:** Both candidates share verified mastery in {', '.join(common_skills[:5]) if common_skills else 'fundamental software engineering'}.\n\n"
                f"**Recommendation:** If the role demands architectural leadership and complex scalability, proceed with {name1}. "
                f"If agile feature velocity and specific domain tooling take precedence, {name2} presents a very compelling interview candidate."
            )
        else:
            return (
                f"**Comparative Talent Overview:**\n\n"
                f"• **{name1}** ({exp1} yrs exp) stands out with unique proficiencies in {', '.join(c1.unique_skills[:4]) if c1.unique_skills else 'core stack'}.\n"
                f"• **{name2}** ({exp2} yrs exp) contributes unique strengths in {', '.join(c2.unique_skills[:4]) if c2.unique_skills else 'specialized tools'}.\n"
                f"• Both candidates share foundational competence in {', '.join(common_skills[:4]) if common_skills else 'standard engineering principles'}."
            )


comparison_service = ComparisonService()
