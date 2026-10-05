import re
from typing import Dict, List, Optional, Any, Tuple
from pydantic import BaseModel, Field
from app.ai.normalizer import skill_normalizer


class ClassifiedSkill(BaseModel):
    skill: str
    importance: str = "HIGH"  # HIGH, MEDIUM, LOW
    required: bool = True     # True = Required, False = Preferred
    category: str = "Technical"


class ParsedJobDescription(BaseModel):
    title: str
    company: str = "Company Confidential"
    location: str = "Remote"
    employment_type: str = "FULL_TIME"
    experience_min: float = 2.0
    experience_max: float = 6.0
    education: str = "Bachelor's degree in Computer Science or related field"
    description: str
    skills: List[ClassifiedSkill] = []
    responsibilities: List[str] = []
    keywords: List[str] = []


REQUIRED_SECTION_PATTERNS = [
    r"(?:required\s+skills|requirements|must\s+have|minimum\s+qualifications|what\s+you(?:'ll)?\s+need|core\s+requirements|qualifications)",
]

PREFERRED_SECTION_PATTERNS = [
    r"(?:preferred\s+skills|nice\s+to\s+have|preferred\s+qualifications|bonus\s+points|pluses|good\s+to\s+have|desired\s+skills)",
]


class JobDescriptionParser:
    @staticmethod
    def _extract_title(text: str) -> str:
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        common_roles = [
            "Software Engineer", "Backend Engineer", "Frontend Engineer", "Full Stack Engineer",
            "Python Developer", "Java Developer", "Data Engineer", "Data Analyst",
            "DevOps Engineer", "Cloud Architect", "Machine Learning Engineer", "Solutions Architect"
        ]
        for l in lines[:6]:
            for r in common_roles:
                if r.lower() in l.lower():
                    return l.strip("#* :-\t")
        if lines:
            first_line = lines[0].strip("#* :-\t")
            if len(first_line) < 80:
                return first_line
        return "Technical Specialist"

    @staticmethod
    def _extract_experience(text: str) -> Tuple[float, float]:
        # Pattern like "3-5 years" or "3 to 5 years"
        range_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:-|to)\s*(\d+(?:\.\d+)?)\s*(?:years|yrs)", text, re.IGNORECASE)
        if range_match:
            min_e = float(range_match.group(1))
            max_e = float(range_match.group(2))
            return min_e, max(max_e, min_e + 2.0)

        # Pattern like "3+ years"
        plus_match = re.search(r"(\d+(?:\.\d+)?)\+?\s*(?:years|yrs)", text, re.IGNORECASE)
        if plus_match:
            min_e = float(plus_match.group(1))
            return min_e, min_e + 4.0

        return 2.0, 6.0

    @staticmethod
    def _extract_location_and_type(text: str) -> Tuple[str, str]:
        lower = text.lower()
        location = "Remote"
        emp_type = "FULL_TIME"

        if "remote" in lower:
            location = "Remote"
        elif "hybrid" in lower:
            location = "Hybrid"

        if "contract" in lower:
            emp_type = "CONTRACT"
        elif "part-time" in lower or "part time" in lower:
            emp_type = "PART_TIME"

        return location, emp_type

    @classmethod
    def parse_jd(cls, raw_text: str) -> ParsedJobDescription:
        title = cls._extract_title(raw_text)
        exp_min, exp_max = cls._extract_experience(raw_text)
        location, emp_type = cls._extract_location_and_type(raw_text)

        # Segment raw text into Required vs Preferred blocks
        lower_text = raw_text.lower()
        required_text = ""
        preferred_text = ""

        # Find preferred section start
        preferred_start = -1
        for p in PREFERRED_SECTION_PATTERNS:
            m = re.search(p, lower_text)
            if m:
                preferred_start = m.start()
                break

        # Find required section start
        required_start = -1
        for p in REQUIRED_SECTION_PATTERNS:
            m = re.search(p, lower_text)
            if m:
                required_start = m.start()
                break

        if required_start != -1 and preferred_start != -1:
            if required_start < preferred_start:
                required_text = raw_text[required_start:preferred_start]
                preferred_text = raw_text[preferred_start:]
            else:
                preferred_text = raw_text[preferred_start:required_start]
                required_text = raw_text[required_start:]
        elif required_start != -1:
            required_text = raw_text[required_start:]
        elif preferred_start != -1:
            preferred_text = raw_text[preferred_start:]
        else:
            required_text = raw_text

        # Extract and classify skills
        req_skills = skill_normalizer.extract_from_text(required_text)
        pref_skills = skill_normalizer.extract_from_text(preferred_text)

        classified: Dict[str, ClassifiedSkill] = {}

        for s in req_skills:
            classified[s["skill"]] = ClassifiedSkill(
                skill=s["skill"],
                importance="HIGH",
                required=True,
                category=s["category"]
            )

        for s in pref_skills:
            if s["skill"] not in classified:
                classified[s["skill"]] = ClassifiedSkill(
                    skill=s["skill"],
                    importance="MEDIUM",
                    required=False,
                    category=s["category"]
                )

        # If very few skills were classified by headers, extract from full document
        if len(classified) < 3:
            all_skills = skill_normalizer.extract_from_text(raw_text)
            for idx, s in enumerate(all_skills):
                if s["skill"] not in classified:
                    classified[s["skill"]] = ClassifiedSkill(
                        skill=s["skill"],
                        importance="HIGH" if idx < 3 else "MEDIUM",
                        required=(idx < 4),
                        category=s["category"]
                    )

        return ParsedJobDescription(
            title=title,
            location=location,
            employment_type=emp_type,
            experience_min=exp_min,
            experience_max=exp_max,
            description=raw_text.strip(),
            skills=list(classified.values()),
            keywords=[s.skill for s in classified.values()]
        )


jd_parser = JobDescriptionParser()
