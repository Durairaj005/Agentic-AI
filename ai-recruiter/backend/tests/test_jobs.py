import sys
import os
import uuid
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from app.main import app


def test_jobs_crud_workflow():
    with TestClient(app) as client:
        # 1. Login as Recruiter
        login_res = client.post("/api/v1/auth/login", json={
            "email": "recruiter@smartrecruit.ai",
            "password": "Recruiter@123456"
        })
        assert login_res.status_code == 200
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 2. Create a Job Requisition
        job_payload = {
            "title": "Full Stack React & Python Engineer",
            "company": "Apex NextGen",
            "description": "Building full stack AI applications using React, TypeScript, and FastAPI.",
            "location": "San Francisco, CA",
            "employment_type": "FULL_TIME",
            "experience_min": 3.0,
            "experience_max": 6.0,
            "status": "ACTIVE",
            "skills": [
                {"skill": "Python", "importance": "HIGH", "required": True},
                {"skill": "React", "importance": "HIGH", "required": True},
                {"skill": "TypeScript", "importance": "MEDIUM", "required": True},
                {"skill": "Docker", "importance": "MEDIUM", "required": False},
                {"skill": "AWS", "importance": "LOW", "required": False}
            ]
        }
        create_res = client.post("/api/v1/jobs", json=job_payload, headers=headers)
        assert create_res.status_code == 201, create_res.text
        job_data = create_res.json()
        job_id = job_data["id"]
        assert job_data["title"] == "Full Stack React & Python Engineer"
        assert len(job_data["skills"]) == 5
        required_skills = [s for s in job_data["skills"] if s["required"]]
        preferred_skills = [s for s in job_data["skills"] if not s["required"]]
        assert len(required_skills) == 3
        assert len(preferred_skills) == 2

        # 3. Retrieve Job by ID
        get_res = client.get(f"/api/v1/jobs/{job_id}", headers=headers)
        assert get_res.status_code == 200
        assert get_res.json()["id"] == job_id

        # 4. Search and filter jobs
        search_res = client.get("/api/v1/jobs?search=Apex", headers=headers)
        assert search_res.status_code == 200
        found_jobs = search_res.json()
        assert any(j["id"] == job_id for j in found_jobs)

        # 5. Update Job
        update_payload = {
            "title": "Lead Full Stack AI Engineer",
            "experience_max": 7.5,
            "skills": [
                {"skill": "Python", "importance": "HIGH", "required": True},
                {"skill": "React", "importance": "HIGH", "required": True},
                {"skill": "FastAPI", "importance": "HIGH", "required": True},
                {"skill": "Kubernetes", "importance": "LOW", "required": False}
            ]
        }
        update_res = client.put(f"/api/v1/jobs/{job_id}", json=update_payload, headers=headers)
        assert update_res.status_code == 200
        updated_data = update_res.json()
        assert updated_data["title"] == "Lead Full Stack AI Engineer"
        assert updated_data["experience_max"] == 7.5
        assert len(updated_data["skills"]) == 4

        # 6. Toggle Status
        toggle_res = client.patch(f"/api/v1/jobs/{job_id}/toggle-status", headers=headers)
        assert toggle_res.status_code == 200
        assert toggle_res.json()["status"] == "CLOSED"

        toggle_back = client.patch(f"/api/v1/jobs/{job_id}/toggle-status", headers=headers)
        assert toggle_back.status_code == 200
        assert toggle_back.json()["status"] == "ACTIVE"

        # 7. Seed sample jobs
        seed_res = client.post("/api/v1/jobs/seed", headers=headers)
        assert seed_res.status_code == 200
        seeded_jobs = seed_res.json()
        assert len(seeded_jobs) >= 5

        # 8. Delete Job
        del_res = client.delete(f"/api/v1/jobs/{job_id}", headers=headers)
        assert del_res.status_code == 200
        del_check = client.get(f"/api/v1/jobs/{job_id}", headers=headers)
        assert del_check.status_code == 404
