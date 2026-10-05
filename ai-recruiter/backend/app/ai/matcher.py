import json
from typing import Dict, List, Tuple, Any
from app.ai.normalizer import skill_normalizer
from app.ai.embeddings import calculate_text_semantic_similarity
from app.schemas.matching import MatchWeightConfig, ScoreExplanationSchema

EDUCATION_TIERS = {
    "PHD": 4,
    "MASTERS": 3,
    "BACHELORS": 2,
    "DIPLOMA": 1,
    "SELF_TAUGHT": 1,
    "OTHER": 0
}


class MatchingEngine:
    @staticmethod
    def _normalize_skill_set(skills: List[str]) -> set:
        """Normalize list of skill strings to a set of canonical names."""
        normalized = set()
        for s in skills:
            if s and s.strip():
                normalized.add(skill_normalizer.normalize(s.strip()))
        return normalized

    @classmethod
    def calculate_match(
        cls,
        candidate_skills: List[str],
        candidate_experience: float,
        candidate_education: str,
        candidate_text: str,
        job_required_skills: List[str],
        job_preferred_skills: List[str],
        job_min_experience: float,
        job_max_experience: float,
        job_text: str,
        weights: MatchWeightConfig = MatchWeightConfig()
    ) -> Dict[str, Any]:
        """
        Compute transparent, multi-factor match score with explainability breakdown.
        """
        # 1. Skill Normalization & Intersection
        cand_skills_norm = cls._normalize_skill_set(candidate_skills)
        job_req_norm = cls._normalize_skill_set(job_required_skills)
        job_pref_norm = cls._normalize_skill_set(job_preferred_skills)

        matched_req = sorted(list(cand_skills_norm.intersection(job_req_norm)))
        missing_req = sorted(list(job_req_norm.difference(cand_skills_norm)))

        matched_pref = sorted(list(cand_skills_norm.intersection(job_pref_norm)))
        missing_pref = sorted(list(job_pref_norm.difference(cand_skills_norm)))

        # Required Skills Score (0 - 100%)
        if len(job_req_norm) > 0:
            score_req = (len(matched_req) / len(job_req_norm)) * 100.0
        else:
            score_req = 100.0

        # Preferred Skills Score (0 - 100%)
        if len(job_pref_norm) > 0:
            score_pref = (len(matched_pref) / len(job_pref_norm)) * 100.0
        else:
            score_pref = 100.0

        # 2. Experience Match Score (0 - 100%)
        if job_min_experience <= 0.0 or candidate_experience >= job_min_experience:
            score_exp = 100.0
        else:
            score_exp = (candidate_experience / job_min_experience) * 100.0
        score_exp = max(0.0, min(100.0, score_exp))

        # 3. Education Match Score (0 - 100%)
        cand_edu_tier = EDUCATION_TIERS.get(candidate_education.upper(), 1)
        # Default target tier is Bachelors (Tier 2) unless specified
        target_edu_tier = 2

        if cand_edu_tier >= target_edu_tier:
            score_edu = 100.0
        elif cand_edu_tier == target_edu_tier - 1:
            score_edu = 75.0
        else:
            score_edu = 50.0

        # Experience equivalency rule: 5+ years guarantees minimum 85% education score
        if candidate_experience >= 5.0 and score_edu < 85.0:
            score_edu = 85.0

        # 4. Semantic Vector Similarity Score (0 - 100%)
        score_sem = calculate_text_semantic_similarity(candidate_text, job_text)

        # 5. Weighted Overall Composite Score
        raw_overall = (
            (weights.weight_required_skills * score_req) +
            (weights.weight_preferred_skills * score_pref) +
            (weights.weight_experience * score_exp) +
            (weights.weight_education * score_edu) +
            (weights.weight_semantic * score_sem)
        )
        overall_score = round(max(0.0, min(100.0, raw_overall)), 1)

        # 6. Natural Language Reason Generation
        reasons = []
        if len(missing_req) == 0:
            reasons.append(f"Candidate matches all {len(matched_req)} required skills.")
        else:
            reasons.append(f"Candidate matches {len(matched_req)} of {len(job_req_norm)} required skills (missing: {', '.join(missing_req)}).")

        if candidate_experience >= job_min_experience:
            reasons.append(f"Experience ({candidate_experience} yrs) meets or exceeds requirement ({job_min_experience} yrs min).")
        else:
            reasons.append(f"Experience ({candidate_experience} yrs) is below requirement ({job_min_experience} yrs min).")

        if len(missing_pref) > 0 and len(matched_pref) > 0:
            reasons.append(f"Matches preferred skill(s) {', '.join(matched_pref)}.")
        elif len(missing_pref) > 0:
            reasons.append(f"Preferred skill(s) {', '.join(missing_pref)} not listed.")

        if score_sem >= 80.0:
            reasons.append("High semantic alignment with role responsibilities.")

        nl_explanation = " ".join(reasons)

        explanation = ScoreExplanationSchema(
            matched_required_skills=matched_req,
            missing_required_skills=missing_req,
            matched_preferred_skills=matched_pref,
            missing_preferred_skills=missing_pref,
            experience_summary=f"{candidate_experience} yrs experience (Job requires {job_min_experience} - {job_max_experience} yrs)",
            education_summary=f"Holds {candidate_education.title()} tier qualification",
            natural_language_explanation=nl_explanation
        )

        return {
            "overall_score": overall_score,
            "required_skills_score": round(score_req, 1),
            "preferred_skills_score": round(score_pref, 1),
            "experience_score": round(score_exp, 1),
            "education_score": round(score_edu, 1),
            "semantic_score": round(score_sem, 1),
            "explanation": explanation
        }


matching_engine = MatchingEngine()
