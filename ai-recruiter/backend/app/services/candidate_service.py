import os
import re
import uuid
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from fastapi import HTTPException, status, UploadFile
from app.models.candidate import Candidate, CandidateSkill
from app.schemas.candidate import (
    CandidateCreate,
    CandidateUpdate,
    CandidateResponse,
    CandidateUploadResponse,
    CandidateSkillCreate,
)
from app.utils.file_handler import process_and_store_resume

# Core technical skills dictionary for deterministic extraction
COMMON_TECH_SKILLS = [
    "Python", "FastAPI", "Django", "Flask", "Java", "Spring Boot", "Hibernate",
    "SQL", "PostgreSQL", "MySQL", "MongoDB", "Redis", "Kafka", "RabbitMQ",
    "Docker", "Kubernetes", "AWS", "Azure", "GCP", "Terraform", "CI/CD",
    "Git", "Linux", "React", "TypeScript", "JavaScript", "HTML", "CSS", "Node.js",
    "Apache Spark", "Airflow", "Snowflake", "Data Modeling", "ETL", "Hadoop",
    "Tableau", "Power BI", "Excel", "Data Visualization", "Pandas", "NumPy",
    "Machine Learning", "NLP", "Scikit-Learn", "PyTorch", "TensorFlow",
    "REST API", "GraphQL", "Microservices", "Prometheus", "Grafana", "Elasticsearch"
]


class CandidateService:
    @staticmethod
    def _extract_basic_info(raw_text: str, filename: str) -> dict:
        """Deterministic extractor for email, phone, name, experience, and skills."""
        # 1. Email extraction
        email_match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", raw_text)
        email = email_match.group(0).lower() if email_match else f"candidate_{uuid.uuid4().hex[:6]}@example.com"

        # 2. Phone extraction
        phone_match = re.search(r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}", raw_text)
        phone = phone_match.group(0) if phone_match else None

        # 3. Name extraction (heuristic: first non-empty line of resume or filename)
        lines = [line.strip() for line in raw_text.split("\n") if line.strip()]
        name = "Unknown Candidate"
        if lines:
            # Pick first clean title-like line with 2-4 words and no email/URL
            for l in lines[:5]:
                if "@" not in l and "http" not in l and 2 <= len(l.split()) <= 4 and len(l) < 50:
                    name = l
                    break
        if name == "Unknown Candidate":
            base_name, _ = os.path.splitext(filename)
            name = re.sub(r"[_\-]+", " ", base_name).title()

        # 4. Experience extraction
        exp_match = re.search(r"(\d+(?:\.\d+)?)\+?\s*(?:years|yrs)\s*(?:of)?\s*experience", raw_text, re.IGNORECASE)
        total_experience = float(exp_match.group(1)) if exp_match else 3.0

        # 5. Education tier detection
        edu_level = "BACHELORS"
        lower_text = raw_text.lower()
        if "ph.d" in lower_text or "phd" in lower_text or "doctor of philosophy" in lower_text:
            edu_level = "PHD"
        elif "master" in lower_text or "m.s." in lower_text or "m.tech" in lower_text or "msc" in lower_text:
            edu_level = "MASTERS"
        elif "bachelor" in lower_text or "b.s." in lower_text or "b.tech" in lower_text or "bsc" in lower_text:
            edu_level = "BACHELORS"
        elif "diploma" in lower_text or "associate" in lower_text:
            edu_level = "DIPLOMA"

        # 6. Extract matching skills
        extracted_skills = []
        for skill in COMMON_TECH_SKILLS:
            pattern = r"\b" + re.escape(skill) + r"\b"
            if re.search(pattern, raw_text, re.IGNORECASE):
                extracted_skills.append({
                    "skill": skill,
                    "years_experience": min(total_experience, 4.0),
                    "confidence_score": 0.90
                })

        return {
            "name": name,
            "email": email,
            "phone": phone,
            "location": "Remote / Flexible",
            "total_experience": total_experience,
            "education_level": edu_level,
            "education_details": f"{edu_level.title()} Degree",
            "summary": raw_text[:350].strip() + ("..." if len(raw_text) > 350 else ""),
            "skills": extracted_skills
        }

    @classmethod
    def list_candidates(
        cls,
        db: Session,
        skip: int = 0,
        limit: int = 50,
        search: Optional[str] = None,
        min_experience: Optional[float] = None,
        max_experience: Optional[float] = None,
        education_level: Optional[str] = None,
        skill: Optional[str] = None
    ) -> List[Candidate]:
        query = db.query(Candidate)

        if search:
            search_str = search.strip()
            has_boolean = bool(re.search(r"\b(AND|OR|NOT)\b", search_str))
            if has_boolean:
                and_parts = re.split(r"\bAND\b", search_str, flags=re.IGNORECASE)
                for part in and_parts:
                    part = part.strip()
                    if not part:
                        continue
                    if re.search(r"\bNOT\b", part, flags=re.IGNORECASE):
                        not_split = re.split(r"\bNOT\b", part, flags=re.IGNORECASE)
                        pos = not_split[0].strip().strip("\"'")
                        neg = not_split[1].strip().strip("\"'") if len(not_split) > 1 else ""
                        if pos:
                            query = query.filter(
                                or_(
                                    Candidate.name.ilike(f"%{pos}%"),
                                    Candidate.summary.ilike(f"%{pos}%"),
                                    Candidate.resume_raw_text.ilike(f"%{pos}%")
                                )
                            )
                        if neg:
                            query = query.filter(
                                ~or_(
                                    Candidate.name.ilike(f"%{neg}%"),
                                    Candidate.summary.ilike(f"%{neg}%"),
                                    Candidate.resume_raw_text.ilike(f"%{neg}%")
                                )
                            )
                    elif re.search(r"\bOR\b", part, flags=re.IGNORECASE):
                        or_parts = [p.strip().strip("\"'") for p in re.split(r"\bOR\b", part, flags=re.IGNORECASE) if p.strip()]
                        or_clauses = []
                        for op in or_parts:
                            or_clauses.extend([
                                Candidate.name.ilike(f"%{op}%"),
                                Candidate.summary.ilike(f"%{op}%"),
                                Candidate.resume_raw_text.ilike(f"%{op}%")
                            ])
                        if or_clauses:
                            query = query.filter(or_(*or_clauses))
                    else:
                        clean_term = part.strip("\"'")
                        query = query.filter(
                            or_(
                                Candidate.name.ilike(f"%{clean_term}%"),
                                Candidate.summary.ilike(f"%{clean_term}%"),
                                Candidate.resume_raw_text.ilike(f"%{clean_term}%")
                            )
                        )
            else:
                search_term = f"%{search.strip()}%"
                query = query.filter(
                    or_(
                        Candidate.name.ilike(search_term),
                        Candidate.email.ilike(search_term),
                        Candidate.location.ilike(search_term),
                        Candidate.summary.ilike(search_term),
                        Candidate.resume_raw_text.ilike(search_term)
                    )
                )

        if min_experience is not None:
            query = query.filter(Candidate.total_experience >= min_experience)

        if max_experience is not None:
            query = query.filter(Candidate.total_experience <= max_experience)

        if education_level and education_level.upper() != "ALL":
            query = query.filter(Candidate.education_level == education_level.upper())

        if skill and skill.strip():
            skill_term = f"%{skill.strip()}%"
            query = query.join(Candidate.skills).filter(CandidateSkill.skill.ilike(skill_term))

        query = query.order_by(Candidate.created_at.desc())
        return query.offset(skip).limit(limit).all()

    @classmethod
    def get_candidate(cls, db: Session, candidate_id: str) -> Candidate:
        candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
        if not candidate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Candidate with id {candidate_id} not found"
            )
        return candidate

    @classmethod
    def create_candidate(cls, db: Session, candidate_in: CandidateCreate) -> Candidate:
        # Check duplicate email
        existing = db.query(Candidate).filter(Candidate.email == candidate_in.email.lower().strip()).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A candidate with this email address already exists."
            )

        candidate = Candidate(
            name=candidate_in.name.strip(),
            email=candidate_in.email.lower().strip(),
            phone=candidate_in.phone,
            location=candidate_in.location,
            total_experience=candidate_in.total_experience,
            education_level=candidate_in.education_level,
            education_details=candidate_in.education_details,
            summary=candidate_in.summary,
            resume_filename=candidate_in.resume_filename,
            resume_path=candidate_in.resume_path,
            resume_raw_text=candidate_in.resume_raw_text
        )
        db.add(candidate)
        db.flush()

        for s in candidate_in.skills:
            skill_obj = CandidateSkill(
                candidate_id=candidate.id,
                skill=s.skill.strip(),
                years_experience=s.years_experience,
                confidence_score=s.confidence_score
            )
            db.add(skill_obj)

        db.commit()
        db.refresh(candidate)
        return candidate

    @classmethod
    def update_candidate(cls, db: Session, candidate_id: str, candidate_in: CandidateUpdate) -> Candidate:
        candidate = cls.get_candidate(db, candidate_id)

        update_data = candidate_in.model_dump(exclude_unset=True)
        skills_data = update_data.pop("skills", None)

        for key, value in update_data.items():
            if key == "email" and value:
                value = value.lower().strip()
            setattr(candidate, key, value)

        if skills_data is not None:
            db.query(CandidateSkill).filter(CandidateSkill.candidate_id == candidate.id).delete()
            for s in skills_data:
                db.add(
                    CandidateSkill(
                        candidate_id=candidate.id,
                        skill=s["skill"].strip(),
                        years_experience=s.get("years_experience", 1.0),
                        confidence_score=s.get("confidence_score", 1.0)
                    )
                )

        db.commit()
        db.refresh(candidate)
        return candidate

    @classmethod
    def delete_candidate(cls, db: Session, candidate_id: str) -> dict:
        candidate = cls.get_candidate(db, candidate_id)
        # Clean up file on disk if exists
        if candidate.resume_path and os.path.exists(candidate.resume_path):
            try:
                os.remove(candidate.resume_path)
            except Exception:
                pass

        db.delete(candidate)
        db.commit()
        return {"success": True, "message": f"Candidate {candidate_id} deleted successfully."}

    @classmethod
    async def upload_and_parse(cls, db: Session, file: UploadFile) -> CandidateUploadResponse:
        """Validate, store file on disk, extract text, and register candidate."""
        filename, file_path, raw_text = await process_and_store_resume(file)
        parsed = cls._extract_basic_info(raw_text, filename)

        # Check if candidate email already exists; if so, update their resume text and file
        candidate = db.query(Candidate).filter(Candidate.email == parsed["email"]).first()
        if candidate:
            candidate.name = parsed["name"]
            candidate.phone = parsed["phone"]
            candidate.total_experience = parsed["total_experience"]
            candidate.education_level = parsed["education_level"]
            candidate.education_details = parsed["education_details"]
            candidate.summary = parsed["summary"]
            candidate.resume_filename = filename
            candidate.resume_path = file_path
            candidate.resume_raw_text = raw_text

            # Update skills
            db.query(CandidateSkill).filter(CandidateSkill.candidate_id == candidate.id).delete()
            for s in parsed["skills"]:
                db.add(CandidateSkill(candidate_id=candidate.id, **s))
        else:
            candidate = Candidate(
                name=parsed["name"],
                email=parsed["email"],
                phone=parsed["phone"],
                location=parsed["location"],
                total_experience=parsed["total_experience"],
                education_level=parsed["education_level"],
                education_details=parsed["education_details"],
                summary=parsed["summary"],
                resume_filename=filename,
                resume_path=file_path,
                resume_raw_text=raw_text
            )
            db.add(candidate)
            db.flush()
            for s in parsed["skills"]:
                db.add(CandidateSkill(candidate_id=candidate.id, **s))

        db.commit()
        db.refresh(candidate)

        return CandidateUploadResponse(
            candidate=candidate,
            extracted_text_preview=raw_text[:500],
            message=f"Resume '{filename}' parsed. Identified {len(candidate.skills)} technical skills."
        )

    @classmethod
    def seed_default_candidates(cls, db: Session) -> List[Candidate]:
        """Seed 20 realistic synthetic candidate profiles across technical domains."""
        current_count = db.query(Candidate).count()
        if current_count >= 20:
            return db.query(Candidate).all()

        sample_candidates = [
            # Python Specialists
            {
                "name": "Marcus Vance",
                "email": "marcus.vance@techdev.io",
                "phone": "+1 415-555-0142",
                "location": "San Francisco, CA",
                "total_experience": 5.5,
                "education_level": "MASTERS",
                "education_details": "MS in Computer Science, Stanford",
                "summary": "Senior Python Backend Engineer specializing in high-throughput FastAPI and Django microservices with PostgreSQL and Redis caching.",
                "skills": ["Python", "FastAPI", "Django", "PostgreSQL", "Docker", "AWS", "Redis"]
            },
            {
                "name": "Priya Sharma",
                "email": "priya.sharma@cloudspecialist.net",
                "phone": "+1 206-555-0189",
                "location": "Seattle, WA",
                "total_experience": 4.0,
                "education_level": "BACHELORS",
                "education_details": "BS in Software Engineering, UW",
                "summary": "Full stack Python and React developer with robust background in REST APIs, Docker containerization, and AWS serverless deployment.",
                "skills": ["Python", "Django", "React", "TypeScript", "PostgreSQL", "Docker", "AWS"]
            },
            {
                "name": "Liam O'Connor",
                "email": "liam.oconnor@codeworks.org",
                "phone": "+1 512-555-0131",
                "location": "Austin, TX",
                "total_experience": 2.5,
                "education_level": "BACHELORS",
                "education_details": "BS in Information Technology, UT Austin",
                "summary": "Junior-to-Mid Python developer proficient with Flask, FastAPI, SQL queries, and basic CI/CD GitHub Actions.",
                "skills": ["Python", "FastAPI", "Flask", "SQL", "Git", "Linux"]
            },
            {
                "name": "Elena Rostova",
                "email": "elena.rostova@datasolutions.com",
                "phone": "+1 312-555-0176",
                "location": "Chicago, IL",
                "total_experience": 6.5,
                "education_level": "PHD",
                "education_details": "PhD in Computational Science, Northwestern",
                "summary": "Lead Python & Distributed Systems Engineer with expertise in asynchronous programming, PostgreSQL query optimization, and Kubernetes orchestration.",
                "skills": ["Python", "FastAPI", "PostgreSQL", "Docker", "Kubernetes", "Kafka", "AWS"]
            },
            # Java Specialists
            {
                "name": "David Chen",
                "email": "david.chen@javatech.io",
                "phone": "+1 617-555-0193",
                "location": "Boston, MA",
                "total_experience": 5.0,
                "education_level": "BACHELORS",
                "education_details": "BS in Computer Engineering, Northeastern",
                "summary": "Enterprise Java developer with 5 years building resilient financial transaction engines using Spring Boot, Hibernate, Kafka, and SQL.",
                "skills": ["Java", "Spring Boot", "Microservices", "SQL", "Kafka", "Docker", "Hibernate"]
            },
            {
                "name": "Sarah Miller",
                "email": "sarah.miller@enterprisecloud.net",
                "phone": "+1 212-555-0118",
                "location": "New York, NY",
                "total_experience": 7.0,
                "education_level": "MASTERS",
                "education_details": "MS in Software Systems, Columbia",
                "summary": "Senior Java Architect experienced in event-driven microservices, Kafka streaming, Docker, Kubernetes, and enterprise SQL databases.",
                "skills": ["Java", "Spring Boot", "Microservices", "Kafka", "Kubernetes", "Docker", "SQL"]
            },
            {
                "name": "Ahmed Hassan",
                "email": "ahmed.hassan@fintechcore.org",
                "phone": "+1 416-555-0164",
                "location": "Toronto, ON",
                "total_experience": 3.5,
                "education_level": "BACHELORS",
                "education_details": "BSc in Computer Science, University of Toronto",
                "summary": "Mid-level Java Backend Engineer focused on Spring Boot RESTful APIs, relational databases, and automated testing.",
                "skills": ["Java", "Spring Boot", "SQL", "PostgreSQL", "Git", "Docker"]
            },
            {
                "name": "Claire Dubois",
                "email": "claire.dubois@microservices.dev",
                "phone": "+1 514-555-0147",
                "location": "Montreal, QC",
                "total_experience": 6.0,
                "education_level": "BACHELORS",
                "education_details": "BEng Software Engineering, McGill",
                "summary": "Java and Distributed Systems specialist with strong focus on high-concurrency architecture, Hibernate, RabbitMQ, and CI/CD pipelines.",
                "skills": ["Java", "Spring Boot", "Microservices", "SQL", "RabbitMQ", "CI/CD", "Linux"]
            },
            # Data Engineering Specialists
            {
                "name": "Rajesh Kumar",
                "email": "rajesh.kumar@bigdatahub.com",
                "phone": "+1 408-555-0182",
                "location": "San Jose, CA",
                "total_experience": 6.0,
                "education_level": "MASTERS",
                "education_details": "MS in Data Engineering, San Jose State",
                "summary": "Data Platform Architect specializing in petabyte-scale ETL pipelines, Apache Spark, Snowflake, Airflow, and AWS data lakes.",
                "skills": ["Python", "SQL", "Apache Spark", "Airflow", "Snowflake", "AWS", "Data Modeling"]
            },
            {
                "name": "Jessica Taylor",
                "email": "jessica.taylor@datapipelines.io",
                "phone": "+1 303-555-0125",
                "location": "Denver, CO",
                "total_experience": 4.5,
                "education_level": "BACHELORS",
                "education_details": "BS in Applied Mathematics, CU Boulder",
                "summary": "Data Engineer with expertise in building real-time stream processing and batch pipelines using Spark, SQL, Kafka, and Python.",
                "skills": ["Python", "SQL", "Apache Spark", "Data Modeling", "Airflow", "Kafka"]
            },
            {
                "name": "Daniel Kim",
                "email": "daniel.kim@warehouseanalytics.org",
                "phone": "+1 404-555-0199",
                "location": "Atlanta, GA",
                "total_experience": 5.0,
                "education_level": "MASTERS",
                "education_details": "MS in Analytics, Georgia Tech",
                "summary": "Lead Data Pipeline Engineer with hands-on experience in modern data stacks: Snowflake, dbt, Airflow, Python, and dimensional data modeling.",
                "skills": ["Python", "SQL", "Data Modeling", "Snowflake", "Airflow", "AWS"]
            },
            {
                "name": "Fatima Zahra",
                "email": "fatima.zahra@streamdata.net",
                "phone": "+1 713-555-0155",
                "location": "Houston, TX",
                "total_experience": 3.0,
                "education_level": "BACHELORS",
                "education_details": "BS in Computer Science, University of Houston",
                "summary": "Junior-to-Mid Data Engineer knowledgeable in SQL data warehouse schema design, Python automated ingestion, and Apache Spark transformations.",
                "skills": ["Python", "SQL", "Apache Spark", "Data Modeling", "ETL", "Git"]
            },
            # Data Analyst Specialists
            {
                "name": "Emily Watson",
                "email": "emily.watson@bi-insights.com",
                "phone": "+1 619-555-0112",
                "location": "San Diego, CA",
                "total_experience": 4.0,
                "education_level": "BACHELORS",
                "education_details": "BS in Statistics, UC San Diego",
                "summary": "Senior Business Intelligence Analyst proficient in complex SQL analytics, executive Tableau dashboards, Power BI, and Python exploratory data analysis.",
                "skills": ["SQL", "Python", "Tableau", "Power BI", "Data Visualization", "Statistical Analysis"]
            },
            {
                "name": "Carlos Gomez",
                "email": "carlos.gomez@analyticscorp.io",
                "phone": "+1 305-555-0177",
                "location": "Miami, FL",
                "total_experience": 3.5,
                "education_level": "BACHELORS",
                "education_details": "BBA in Business Analytics, FIU",
                "summary": "Data Analyst with a track record of driving revenue growth through cohort analysis, Tableau visual storytelling, SQL modeling, and Excel modeling.",
                "skills": ["SQL", "Tableau", "Data Visualization", "Excel", "Statistical Analysis"]
            },
            {
                "name": "Aisha Patel",
                "email": "aisha.patel@growthmetrics.dev",
                "phone": "+1 214-555-0136",
                "location": "Dallas, TX",
                "total_experience": 5.0,
                "education_level": "MASTERS",
                "education_details": "MS in Business Analytics, UT Dallas",
                "summary": "Lead Marketing & Product Analyst skilled in A/B testing, statistical modeling in Python, SQL querying, and executive KPI reporting in Power BI.",
                "skills": ["SQL", "Python", "Power BI", "Data Visualization", "Statistical Analysis", "Tableau"]
            },
            {
                "name": "Benjamin Scott",
                "email": "benjamin.scott@decisionanalytics.org",
                "phone": "+1 503-555-0184",
                "location": "Portland, OR",
                "total_experience": 2.0,
                "education_level": "BACHELORS",
                "education_details": "BS in Economics, Portland State",
                "summary": "Associate Data Analyst skilled in SQL data extraction, Tableau dashboard generation, and customer segmentation.",
                "skills": ["SQL", "Tableau", "Data Visualization", "Excel", "Python"]
            },
            # DevOps & Cloud Specialists
            {
                "name": "Alexander Wright",
                "email": "alex.wright@clouddevops.io",
                "phone": "+1 206-555-0168",
                "location": "Seattle, WA",
                "total_experience": 5.5,
                "education_level": "BACHELORS",
                "education_details": "BS in Computer Systems, Washington State",
                "summary": "Senior DevOps Engineer specialized in multi-region Kubernetes clusters on AWS, Terraform Infrastructure-as-Code, and Prometheus/Grafana observability.",
                "skills": ["Kubernetes", "Docker", "AWS", "Terraform", "CI/CD", "Linux", "Prometheus"]
            },
            {
                "name": "Zoe Kravitz",
                "email": "zoe.kravitz@infracore.net",
                "phone": "+1 415-555-0105",
                "location": "San Francisco, CA",
                "total_experience": 4.5,
                "education_level": "BACHELORS",
                "education_details": "BS in Networking and Security, UC Berkeley",
                "summary": "DevOps & Cloud Automation Engineer with hands-on mastery of Docker containerization, Kubernetes helm charts, Terraform, and CI/CD pipelines.",
                "skills": ["Kubernetes", "Docker", "AWS", "Terraform", "CI/CD", "Linux"]
            },
            {
                "name": "Tariq Mansoor",
                "email": "tariq.mansoor@platformeng.com",
                "phone": "+1 703-555-0192",
                "location": "Washington, DC",
                "total_experience": 6.5,
                "education_level": "MASTERS",
                "education_details": "MS in Cloud Computing, George Mason",
                "summary": "Platform Infrastructure Lead experienced in zero-downtime AWS migrations, Terraform automation, Kubernetes security, and Grafana monitoring.",
                "skills": ["Kubernetes", "Docker", "AWS", "Terraform", "CI/CD", "Grafana", "Linux"]
            },
            {
                "name": "Hannah Abbott",
                "email": "hannah.abbott@reliability.org",
                "phone": "+1 612-555-0143",
                "location": "Minneapolis, MN",
                "total_experience": 3.0,
                "education_level": "BACHELORS",
                "education_details": "BS in Computer Science, University of Minnesota",
                "summary": "Cloud Operations Engineer proficient in Linux administration, Docker container builds, AWS cloud services, and GitHub Actions CI/CD.",
                "skills": ["Docker", "AWS", "CI/CD", "Linux", "Git", "Kubernetes"]
            }
        ]

        created = []
        for sample in sample_candidates:
            skills = sample.pop("skills")
            sample["resume_filename"] = f"{sample['name'].lower().replace(' ', '_')}_resume.txt"
            sample["resume_raw_text"] = (
                f"{sample['name']}\n{sample['email']} | {sample['phone']} | {sample['location']}\n\n"
                f"SUMMARY:\n{sample['summary']}\n\n"
                f"EXPERIENCE: {sample['total_experience']} years of experience in technical domain.\n"
                f"EDUCATION: {sample['education_details']} ({sample['education_level']})\n"
                f"SKILLS: {', '.join(skills)}\n"
            )

            cand = Candidate(**sample)
            db.add(cand)
            db.flush()

            for s in skills:
                db.add(
                    CandidateSkill(
                        candidate_id=cand.id,
                        skill=s,
                        years_experience=min(cand.total_experience, 4.0),
                        confidence_score=0.92
                    )
                )
            created.append(cand)

        db.commit()
        for c in created:
            db.refresh(c)
        return created


candidate_service = CandidateService()
