from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from fastapi import HTTPException, status
from app.models.job import Job, JobSkill
from app.models.application import Application
from app.schemas.job import JobCreate, JobUpdate, JobResponse


class JobService:
    @staticmethod
    def _enrich_job(job: Job) -> JobResponse:
        """Helper to attach applicant_count to job model for response serialization."""
        applicant_count = len(job.applications) if job.applications else 0
        job_dict = {
            "id": job.id,
            "title": job.title,
            "company": job.company,
            "description": job.description,
            "location": job.location,
            "employment_type": job.employment_type,
            "experience_min": job.experience_min,
            "experience_max": job.experience_max,
            "status": job.status,
            "created_by": job.created_by,
            "created_at": job.created_at,
            "updated_at": job.updated_at,
            "skills": job.skills,
            "applicant_count": applicant_count
        }
        return JobResponse(**job_dict)

    @classmethod
    def list_jobs(
        cls,
        db: Session,
        skip: int = 0,
        limit: int = 50,
        status_filter: Optional[str] = None,
        search: Optional[str] = None,
        employment_type: Optional[str] = None
    ) -> List[JobResponse]:
        query = db.query(Job)

        if status_filter and status_filter.upper() != "ALL":
            query = query.filter(Job.status == status_filter.upper())

        if employment_type and employment_type.upper() != "ALL":
            query = query.filter(Job.employment_type == employment_type.upper())

        if search:
            search_term = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    Job.title.ilike(search_term),
                    Job.company.ilike(search_term),
                    Job.location.ilike(search_term),
                    Job.description.ilike(search_term)
                )
            )

        query = query.order_by(Job.created_at.desc())
        jobs = query.offset(skip).limit(limit).all()
        return [cls._enrich_job(j) for j in jobs]

    @classmethod
    def get_job(cls, db: Session, job_id: str) -> JobResponse:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job requisition with id {job_id} not found"
            )
        return cls._enrich_job(job)

    @classmethod
    def create_job(cls, db: Session, job_in: JobCreate, user_id: str) -> JobResponse:
        new_job = Job(
            title=job_in.title.strip(),
            company=job_in.company.strip(),
            description=job_in.description.strip(),
            location=job_in.location.strip(),
            employment_type=job_in.employment_type,
            experience_min=job_in.experience_min,
            experience_max=job_in.experience_max,
            status=job_in.status,
            created_by=user_id
        )
        db.add(new_job)
        db.flush()

        for s in job_in.skills:
            skill_obj = JobSkill(
                job_id=new_job.id,
                skill=s.skill.strip(),
                importance=s.importance,
                required=s.required
            )
            db.add(skill_obj)

        db.commit()
        db.refresh(new_job)
        return cls._enrich_job(new_job)

    @classmethod
    def update_job(
        cls,
        db: Session,
        job_id: str,
        job_in: JobUpdate,
        user_id: str,
        is_admin: bool = False
    ) -> JobResponse:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        # Authorization: creator or admin
        if job.created_by != user_id and not is_admin:
            raise HTTPException(status_code=403, detail="You do not have permission to modify this requisition")

        update_data = job_in.model_dump(exclude_unset=True)
        skills_data = update_data.pop("skills", None)

        for key, value in update_data.items():
            setattr(job, key, value)

        if skills_data is not None:
            # Replace skills
            db.query(JobSkill).filter(JobSkill.job_id == job.id).delete()
            for s in skills_data:
                skill_obj = JobSkill(
                    job_id=job.id,
                    skill=s["skill"].strip(),
                    importance=s.get("importance", "HIGH"),
                    required=s.get("required", True)
                )
                db.add(skill_obj)

        db.commit()
        db.refresh(job)
        return cls._enrich_job(job)

    @classmethod
    def delete_job(cls, db: Session, job_id: str, user_id: str, is_admin: bool = False) -> dict:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        if job.created_by != user_id and not is_admin:
            raise HTTPException(status_code=403, detail="You do not have permission to delete this requisition")

        db.delete(job)
        db.commit()
        return {"success": True, "message": f"Job requisition {job_id} deleted successfully"}

    @classmethod
    def toggle_status(cls, db: Session, job_id: str, user_id: str, is_admin: bool = False) -> JobResponse:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        if job.created_by != user_id and not is_admin:
            raise HTTPException(status_code=403, detail="Unauthorized")

        job.status = "CLOSED" if job.status == "ACTIVE" else "ACTIVE"
        db.commit()
        db.refresh(job)
        return cls._enrich_job(job)

    @classmethod
    def seed_default_jobs(cls, db: Session, user_id: str) -> List[JobResponse]:
        """Seed 5 realistic technical job requisitions if fewer than 5 exist."""
        current_count = db.query(Job).count()
        if current_count >= 5:
            return [cls._enrich_job(j) for j in db.query(Job).all()]

        sample_definitions = [
            {
                "title": "Senior Python Backend Engineer",
                "company": "CloudScale Systems",
                "location": "Remote",
                "employment_type": "FULL_TIME",
                "experience_min": 3.0,
                "experience_max": 7.0,
                "description": "We are seeking an experienced Senior Python Backend Engineer to architect, build, and optimize high-throughput distributed microservices. You will collaborate with cross-functional product and infrastructure teams to design resilient RESTful APIs, scale PostgreSQL databases, and lead async pipeline enhancements.",
                "skills": [
                    {"skill": "Python", "importance": "HIGH", "required": True},
                    {"skill": "FastAPI", "importance": "HIGH", "required": True},
                    {"skill": "Django", "importance": "MEDIUM", "required": True},
                    {"skill": "PostgreSQL", "importance": "HIGH", "required": True},
                    {"skill": "Docker", "importance": "MEDIUM", "required": False},
                    {"skill": "AWS", "importance": "MEDIUM", "required": False},
                    {"skill": "Redis", "importance": "LOW", "required": False},
                ]
            },
            {
                "title": "Senior Java Developer",
                "company": "Apex Fintech Solutions",
                "location": "New York, NY (Hybrid)",
                "employment_type": "FULL_TIME",
                "experience_min": 4.0,
                "experience_max": 8.0,
                "description": "Looking for a seasoned Java Engineer with enterprise experience building resilient transaction engines using Spring Boot, Kafka, and microservices architecture. Strong knowledge of multi-threading, Hibernate, and clean architecture is essential.",
                "skills": [
                    {"skill": "Java", "importance": "HIGH", "required": True},
                    {"skill": "Spring Boot", "importance": "HIGH", "required": True},
                    {"skill": "Microservices", "importance": "HIGH", "required": True},
                    {"skill": "SQL", "importance": "HIGH", "required": True},
                    {"skill": "Kafka", "importance": "HIGH", "required": False},
                    {"skill": "Docker", "importance": "MEDIUM", "required": False},
                    {"skill": "Kubernetes", "importance": "MEDIUM", "required": False},
                ]
            },
            {
                "title": "Lead Data Engineer",
                "company": "DataNexus Analytics",
                "location": "San Francisco, CA (Remote)",
                "employment_type": "FULL_TIME",
                "experience_min": 4.0,
                "experience_max": 9.0,
                "description": "Join our Core Data Platform team to build reliable petabyte-scale data pipelines. You will orchestrate batch and real-time ingestion pipelines using Apache Spark, Airflow, and Snowflake, establishing robust data quality and governance standards.",
                "skills": [
                    {"skill": "Python", "importance": "HIGH", "required": True},
                    {"skill": "SQL", "importance": "HIGH", "required": True},
                    {"skill": "Apache Spark", "importance": "HIGH", "required": True},
                    {"skill": "Data Modeling", "importance": "HIGH", "required": True},
                    {"skill": "Airflow", "importance": "MEDIUM", "required": False},
                    {"skill": "Snowflake", "importance": "MEDIUM", "required": False},
                    {"skill": "AWS", "importance": "MEDIUM", "required": False},
                ]
            },
            {
                "title": "Senior Data Analyst",
                "company": "MetricWorks Digital",
                "location": "Austin, TX (Remote)",
                "employment_type": "FULL_TIME",
                "experience_min": 2.5,
                "experience_max": 6.0,
                "description": "Seeking an analytical problem solver to drive business insights through advanced SQL querying, data modeling, statistical testing, and executive Tableau dashboards. You will work directly with leadership to formulate KPIs and identify growth levers.",
                "skills": [
                    {"skill": "SQL", "importance": "HIGH", "required": True},
                    {"skill": "Python", "importance": "MEDIUM", "required": True},
                    {"skill": "Tableau", "importance": "HIGH", "required": True},
                    {"skill": "Data Visualization", "importance": "HIGH", "required": True},
                    {"skill": "Power BI", "importance": "MEDIUM", "required": False},
                    {"skill": "Statistical Analysis", "importance": "MEDIUM", "required": False},
                    {"skill": "Excel", "importance": "LOW", "required": False},
                ]
            },
            {
                "title": "DevOps & Cloud Infrastructure Engineer",
                "company": "InfraCore Cloud",
                "location": "Seattle, WA (Remote)",
                "employment_type": "FULL_TIME",
                "experience_min": 3.5,
                "experience_max": 8.0,
                "description": "We are seeking a DevOps Engineer to advance our Infrastructure-as-Code automation, Kubernetes cluster operations, and CI/CD pipelines. You will enhance platform security, observability (Prometheus/Grafana), and disaster recovery across multi-region AWS environments.",
                "skills": [
                    {"skill": "Kubernetes", "importance": "HIGH", "required": True},
                    {"skill": "Docker", "importance": "HIGH", "required": True},
                    {"skill": "AWS", "importance": "HIGH", "required": True},
                    {"skill": "Terraform", "importance": "HIGH", "required": True},
                    {"skill": "CI/CD", "importance": "HIGH", "required": True},
                    {"skill": "Linux", "importance": "MEDIUM", "required": False},
                    {"skill": "Prometheus", "importance": "LOW", "required": False},
                ]
            }
        ]

        created_jobs = []
        for sample in sample_definitions:
            skills = sample.pop("skills")
            job_obj = Job(**sample, created_by=user_id, status="ACTIVE")
            db.add(job_obj)
            db.flush()
            for s in skills:
                db.add(JobSkill(job_id=job_obj.id, **s))
            created_jobs.append(job_obj)

        db.commit()
        for j in created_jobs:
            db.refresh(j)
        return [cls._enrich_job(j) for j in created_jobs]


job_service = JobService()
