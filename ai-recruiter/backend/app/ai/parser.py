import re
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from pydantic import BaseModel, Field
from app.ai.normalizer import skill_normalizer


class ParsedProject(BaseModel):
    title: str
    description: Optional[str] = None
    technologies: List[str] = []


class ParsedExperience(BaseModel):
    title: Optional[str] = None
    company: Optional[str] = None
    duration: Optional[str] = None
    years: float = 0.0
    description: Optional[str] = None


class ParsedEducation(BaseModel):
    degree: str
    level: str  # BACHELORS, MASTERS, PHD, DIPLOMA, OTHER
    institution: Optional[str] = None
    year: Optional[str] = None


class ResumeParseResult(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None
    location: str = "Not specified"
    total_experience: float = 0.0
    education_level: str = "BACHELORS"
    education_details: str = "Bachelor's Degree"
    summary: str = ""
    skills: List[Dict[str, Any]] = []
    experiences: List[ParsedExperience] = []
    educations: List[ParsedEducation] = []
    certifications: List[str] = []
    projects: List[ParsedProject] = []


SECTION_PATTERNS = {
    "EXPERIENCE": r"(?:work\s+experience|professional\s+experience|employment\s+history|experience)",
    "EDUCATION": r"(?:education|academic\s+background|academics|qualifications)",
    "SKILLS": r"(?:technical\s+skills|skills\s*&\s*competencies|core\s+competencies|technologies|skills)",
    "PROJECTS": r"(?:projects|key\s+projects|personal\s+projects)",
    "CERTIFICATIONS": r"(?:certifications|licenses\s*&\s*certifications|certificates|credentials)"
}


class ResumeParser:
    @staticmethod
    def _extract_contact_info(text: str) -> Dict[str, Optional[str]]:
        # Email
        email_match = re.search(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", text)
        email = email_match.group(0).lower() if email_match else None

        # Phone
        phone_match = re.search(
            r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}",
            text
        )
        phone = phone_match.group(0) if phone_match else None

        # Heuristic Name Extraction
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        name = "Unknown Candidate"
        for l in lines[:5]:
            if "@" not in l and "http" not in l and not re.search(r"\d{3}", l):
                words = l.split()
                if 2 <= len(words) <= 4 and len(l) < 50:
                    name = l
                    break

        # Location heuristic
        location_match = re.search(
            r"\b([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?),\s*([A-Z]{2})\b",
            text
        )
        location = location_match.group(0) if location_match else "Remote / Flexible"

        return {"name": name, "email": email, "phone": phone, "location": location}

    @staticmethod
    def _segment_sections(text: str) -> Dict[str, str]:
        """Split resume into identified logical sections."""
        sections: Dict[str, str] = {}
        lines = text.split("\n")
        current_section = "HEADER"
        section_lines: Dict[str, List[str]] = {current_section: []}

        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue

            matched_section = None
            for sec_name, pattern in SECTION_PATTERNS.items():
                if re.match(r"^\s*" + pattern + r"\s*[:\-]?\s*$", stripped, re.IGNORECASE):
                    matched_section = sec_name
                    break

            if matched_section:
                current_section = matched_section
                if current_section not in section_lines:
                    section_lines[current_section] = []
            else:
                section_lines[current_section].append(stripped)

        for sec, lines_list in section_lines.items():
            sections[sec] = "\n".join(lines_list)

        return sections

    @classmethod
    def _extract_experience_years(cls, text: str) -> Tuple[float, List[ParsedExperience]]:
        """Calculate total experience years from date ranges or explicit statements."""
        # 1. Check stated experience (e.g. "5+ years of experience")
        exp_stated = re.search(r"(\d+(?:\.\d+)?)\+?\s*(?:years|yrs)\s*(?:of)?\s*(?:experience|exp)", text, re.IGNORECASE)
        stated_years = float(exp_stated.group(1)) if exp_stated else 0.0

        # 2. Date span analysis (e.g. 2018 - 2023, 2021 - Present)
        current_year = datetime.now().year
        year_ranges = re.findall(r"\b(20\d{2}|19\d{2})\s*(?:-|–|to)\s*(20\d{2}|present|current)\b", text, re.IGNORECASE)
        calculated_years = 0.0
        experiences = []

        for start_str, end_str in year_ranges:
            start_yr = int(start_yr) if (start_yr := start_str) else current_year
            end_yr = current_year if end_str.lower() in ["present", "current"] else int(end_str)
            span = max(0.5, float(end_yr - start_yr))
            calculated_years += span
            experiences.append(
                ParsedExperience(
                    duration=f"{start_str} - {end_str}",
                    years=span
                )
            )

        total = max(stated_years, calculated_years)
        return (total if total > 0 else 3.0), experiences

    @staticmethod
    def _extract_education(text: str) -> Tuple[str, str, List[ParsedEducation]]:
        lower = text.lower()
        level = "BACHELORS"
        details = "Bachelor of Science in Computer Science"
        educations = []

        if "ph.d" in lower or "phd" in lower or "doctor of philosophy" in lower:
            level = "PHD"
            details = "Doctor of Philosophy (Ph.D.)"
        elif "master" in lower or "m.s." in lower or "m.tech" in lower or "msc" in lower or "mba" in lower:
            level = "MASTERS"
            details = "Master of Science (M.S.)"
        elif "bachelor" in lower or "b.s." in lower or "b.tech" in lower or "bsc" in lower or "b.e." in lower:
            level = "BACHELORS"
            details = "Bachelor of Science / B.Tech"
        elif "diploma" in lower or "associate" in lower:
            level = "DIPLOMA"
            details = "Associate Degree / Technical Diploma"
        else:
            level = "SELF_TAUGHT"
            details = "Professional Experience & Technical Training"

        educations.append(ParsedEducation(degree=details, level=level))
        return level, details, educations

    @staticmethod
    def _extract_certifications(text: str) -> List[str]:
        known_certs = [
            "AWS Certified Solutions Architect", "AWS Certified Developer",
            "Certified Kubernetes Administrator (CKA)", "CKA", "CKAD",
            "Azure Solutions Architect", "GCP Professional Cloud Architect",
            "CISSP", "PMP", "Scrum Master", "CompTIA Security+", "Terraform Associate"
        ]
        found = []
        for cert in known_certs:
            if re.search(r"\b" + re.escape(cert) + r"\b", text, re.IGNORECASE):
                found.append(cert)
        return found

    @classmethod
    def parse_resume(cls, raw_text: str, filename: str = "resume.pdf") -> ResumeParseResult:
        contact = cls._extract_contact_info(raw_text)
        sections = cls._segment_sections(raw_text)

        total_exp, experiences = cls._extract_experience_years(raw_text)
        edu_level, edu_details, educations = cls._extract_education(raw_text)
        certifications = cls._extract_certifications(raw_text)

        # Normalize skills using SkillNormalizer
        skills_data = skill_normalizer.extract_from_text(raw_text)

        # Generate summary
        summary = ""
        if "SUMMARY" in sections:
            summary = sections["SUMMARY"][:400]
        else:
            summary = raw_text[:350].strip() + ("..." if len(raw_text) > 350 else "")

        return ResumeParseResult(
            name=contact["name"] if contact["name"] != "Unknown Candidate" else filename.split(".")[0].replace("_", " ").title(),
            email=contact["email"] or f"candidate_{abs(hash(raw_text)) % 100000}@smartrecruit.ai",
            phone=contact["phone"],
            location=contact["location"],
            total_experience=total_exp,
            education_level=edu_level,
            education_details=edu_details,
            summary=summary,
            skills=skills_data,
            experiences=experiences,
            educations=educations,
            certifications=certifications,
            projects=[]
        )


resume_parser = ResumeParser()
