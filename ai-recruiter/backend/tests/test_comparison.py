import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from app.main import app


def test_candidate_comparison_matrix():
    with TestClient(app) as client:
        # 1. Login
        login_res = client.post(
            "/api/v1/auth/login",
            json={"email": "recruiter@smartrecruit.ai", "password": "Recruiter@123456"}
        )
        assert login_res.status_code == 200
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 2. Seed jobs and candidates
        client.post("/api/v1/jobs/seed", headers=headers)
        client.post("/api/v1/candidates/seed", headers=headers)

        cands = client.get("/api/v1/candidates", headers=headers).json()
        jobs = client.get("/api/v1/jobs", headers=headers).json()

        assert len(cands) >= 2
        cand_ids = [cands[0]["id"], cands[1]["id"]]
        job_id = jobs[0]["id"]

        # 3. Compare without job
        res_no_job = client.post(
            "/api/v1/candidates/compare",
            json={"candidate_ids": cand_ids},
            headers=headers
        )
        assert res_no_job.status_code == 200
        data_no_job = res_no_job.json()
        assert len(data_no_job["candidates"]) == 2
        assert "common_skills" in data_no_job
        assert "skill_matrix" in data_no_job
        assert "ai_comparative_synthesis" in data_no_job

        # 4. Compare with target job requisition
        res_with_job = client.post(
            "/api/v1/candidates/compare",
            json={"candidate_ids": cand_ids, "job_id": job_id},
            headers=headers
        )
        assert res_with_job.status_code == 200
        data_with_job = res_with_job.json()
        assert data_with_job["job"] is not None
        assert data_with_job["candidates"][0]["overall_match_score"] is not None
        assert data_with_job["candidates"][1]["overall_match_score"] is not None
        assert len(data_with_job["ai_comparative_synthesis"]) > 100
