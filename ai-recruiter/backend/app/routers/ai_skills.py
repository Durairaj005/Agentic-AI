from typing import List, Dict, Any
from fastapi import APIRouter, Depends, Body, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.candidate import Candidate, CandidateSkill
from app.ai.normalizer import skill_normalizer
from app.ai.jd_parser import jd_parser, ParsedJobDescription
from app.ai.parser import resume_parser, ResumeParseResult
from app.schemas.candidate import CandidateResponse
from app.dependencies.auth import get_current_user

router = APIRouter(prefix="/ai", tags=["AI & Skill Normalization"])


class NormalizeRequest(BaseModel):
    skills: List[str]


class NormalizeResponse(BaseModel):
    normalized: List[Dict[str, str]]


class ParseJDRequest(BaseModel):
    text: str


@router.post("/skills/normalize", response_model=NormalizeResponse)
def normalize_skills(
    payload: NormalizeRequest,
    current_user: User = Depends(get_current_user)
):
    """Normalize a list of technology aliases into standard canonical names."""
    results = []
    for s in payload.skills:
        canonical = skill_normalizer.normalize(s)
        results.append({
            "input": s,
            "canonical": canonical,
            "category": skill_normalizer.get_category(canonical)
        })
    return NormalizeResponse(normalized=results)


@router.get("/skills/taxonomy")
def get_skill_taxonomy(current_user: User = Depends(get_current_user)):
    """Retrieve full catalog of canonical skills grouped by domain categories."""
    return {
        "categories": skill_normalizer.canonical_to_category,
        "total_canonical_skills": len(skill_normalizer.canonical_skills),
        "total_aliases_indexed": len(skill_normalizer.alias_to_canonical)
    }


@router.post("/parse-jd", response_model=ParsedJobDescription)
def parse_job_description(
    payload: ParseJDRequest,
    current_user: User = Depends(get_current_user)
):
    """Parse raw job description text into structured title, experience band, and classified skills."""
    if not payload.text.strip():
        raise HTTPException(status_code=400, detail="Job description text cannot be empty.")
    return jd_parser.parse_jd(payload.text)


@router.post("/candidates/{candidate_id}/reparse", response_model=CandidateResponse)
def reparse_candidate_resume(
    candidate_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Re-run the advanced section parser and canonical normalizer over stored resume text."""
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    if not candidate.resume_raw_text:
        raise HTTPException(status_code=400, detail="Candidate does not have stored resume text to reparse.")

    parsed = resume_parser.parse_resume(
        raw_text=candidate.resume_raw_text,
        filename=candidate.resume_filename or "resume.txt"
    )

    candidate.total_experience = parsed.total_experience
    candidate.education_level = parsed.education_level
    candidate.education_details = parsed.education_details
    candidate.summary = parsed.summary

    # Update candidate skills with normalized results
    db.query(CandidateSkill).filter(CandidateSkill.candidate_id == candidate.id).delete()
    for s in parsed.skills:
        db.add(
            CandidateSkill(
                candidate_id=candidate.id,
                skill=s["skill"],
                years_experience=min(candidate.total_experience, 4.0),
                confidence_score=s.get("confidence", 0.95)
            )
        )

    db.commit()
    db.refresh(candidate)
    return candidate
