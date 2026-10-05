"""
Phase 1 Verification Script
Validates that:
1. All models import cleanly.
2. Tables are created properly in the database.
3. Relationships (User -> Job, Job -> JobSkill, Candidate -> CandidateSkill, Application, etc.) function as expected.
4. Database session opens, inserts, and rolls back cleanly.
"""
import sys
import os

# Add backend to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import Base, engine, SessionLocal, init_db
from app.models import (
    User, Job, JobSkill, Candidate, CandidateSkill, 
    Application, Interview, Note, Followup
)

def test_database_and_models():
    print("[*] Initializing database tables...")
    init_db()
    
    # Inspect tables created
    from sqlalchemy import inspect
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"[+] Tables created ({len(tables)}): {', '.join(sorted(tables))}")
    
    expected_tables = {
        "users", "jobs", "job_skills", "candidates", 
        "candidate_skills", "applications", "interviews", 
        "notes", "followups"
    }
    missing = expected_tables - set(tables)
    assert not missing, f"Missing tables: {missing}"
    print("[+] All 9 core domain tables verified!")
    
    # Test session and cascade functionality
    db = SessionLocal()
    try:
        # Create a test recruiter
        test_user = User(
            name="Test Recruiter",
            email="recruiter.test@smartrecruit.ai",
            password_hash="fake_hash_phase_1",
            role="RECRUITER"
        )
        db.add(test_user)
        db.flush()
        print(f"[+] Created test user: {test_user.name} ({test_user.id})")
        
        # Create a test job with skills
        test_job = Job(
            title="Senior Python Backend Engineer",
            company="TechInnovate",
            description="Developing high throughput FastAPI services.",
            location="Remote",
            employment_type="FULL_TIME",
            experience_min=3.0,
            experience_max=8.0,
            created_by=test_user.id
        )
        db.add(test_job)
        db.flush()
        
        skill1 = JobSkill(job_id=test_job.id, skill="Python", importance="HIGH", required=True)
        skill2 = JobSkill(job_id=test_job.id, skill="FastAPI", importance="HIGH", required=True)
        skill3 = JobSkill(job_id=test_job.id, skill="Docker", importance="MEDIUM", required=False)
        db.add_all([skill1, skill2, skill3])
        db.flush()
        print(f"[+] Created test job '{test_job.title}' with {len(test_job.skills)} skills")
        
        # Create a test candidate
        candidate = Candidate(
            name="Alice Walker",
            email="alice.walker@example.com",
            phone="+1 555-0199",
            location="Austin, TX",
            total_experience=4.5,
            education_level="BACHELORS",
            education_details="BS in Computer Science",
            summary="Full-stack Python specialist with microservice background."
        )
        db.add(candidate)
        db.flush()
        
        c_skill1 = CandidateSkill(candidate_id=candidate.id, skill="Python", years_experience=4.5, confidence_score=0.95)
        c_skill2 = CandidateSkill(candidate_id=candidate.id, skill="FastAPI", years_experience=3.0, confidence_score=0.90)
        db.add_all([c_skill1, c_skill2])
        db.flush()
        print(f"[+] Created candidate '{candidate.name}' with {len(candidate.skills)} skills")
        
        # Create an application
        app = Application(
            job_id=test_job.id,
            candidate_id=candidate.id,
            match_score=92.5,
            required_skills_score=100.0,
            preferred_skills_score=75.0,
            experience_score=100.0,
            education_score=100.0,
            semantic_score=85.0,
            status="SCREENING",
            recruiter_notes="Strong resume and relevant FastAPI experience."
        )
        db.add(app)
        db.flush()
        print(f"[+] Created application for {candidate.name} -> {test_job.title} with score {app.match_score}%")
        
        # Roll back so the verification test is non-destructive
        db.rollback()
        print("[+] Test transaction rolled back cleanly. System is ready for Phase 2!")
    finally:
        db.close()

if __name__ == "__main__":
    test_database_and_models()
