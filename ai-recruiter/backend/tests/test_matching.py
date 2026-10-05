import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from app.main import app
from app.ai.matcher import matching_engine
from app.schemas.matching import MatchWeightConfig


def test_matching_engine_calculation():
    # 1. High match scenario
    high_match = matching_engine.calculate_match(
        candidate_skills=["Python", "FastAPI", "PostgreSQL", "Docker", "AWS"],
        candidate_experience=5.0,
        candidate_education="MASTERS",
        candidate_text="Senior Python Backend Engineer with 5 years building scalable FastAPI microservices.",
        job_required_skills=["Python", "FastAPI", "PostgreSQL"],
        job_preferred_skills=["Docker", "AWS"],
        job_min_experience=3.0,
        job_max_experience=6.0,
        job_text="Seeking Senior Python Backend Engineer with FastAPI, PostgreSQL, Docker, and AWS."
    )

    assert high_match["overall_score"] >= 85.0
    assert high_match["required_skills_score"] == 100.0
    assert high_match["preferred_skills_score"] == 100.0
    assert high_match["experience_score"] == 100.0
    assert len(high_match["explanation"].missing_required_skills) == 0

    # 2. Low match scenario
    low_match = matching_engine.calculate_match(
        candidate_skills=["HTML", "CSS", "Excel"],
        candidate_experience=1.0,
        candidate_education="DIPLOMA",
        candidate_text="Junior office assistant with basic web editing.",
        job_required_skills=["Python", "FastAPI", "PostgreSQL"],
        job_preferred_skills=["Docker", "AWS"],
        job_min_experience=4.0,
        job_max_experience=8.0,
        job_text="Seeking Senior Python Backend Engineer with FastAPI, PostgreSQL, Docker, and AWS."
    )

    assert low_match["overall_score"] < 50.0
    assert low_match["required_skills_score"] == 0.0
    assert len(low_match["explanation"].missing_required_skills) == 3


def test_matching_api_workflow():
    with TestClient(app) as client:
        # 1. Login
        login_res = client.post("/api/v1/auth/login", json={
            "email": "recruiter@smartrecruit.ai",
            "password": "Recruiter@123456"
        })
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 2. Ensure seed jobs and candidates exist
        seed_jobs_res = client.post("/api/v1/jobs/seed", headers=headers)
        assert seed_jobs_res.status_code == 200
        jobs = seed_jobs_res.json()
        assert len(jobs) >= 1
        test_job = jobs[0]
        job_id = test_job["id"]

        seed_cand_res = client.post("/api/v1/candidates/seed", headers=headers)
        assert seed_cand_res.status_code == 200

        # 3. Execute matching run
        match_exec_res = client.post(f"/api/v1/jobs/{job_id}/match", json={}, headers=headers)
        assert match_exec_res.status_code == 200, match_exec_res.text
        summary = match_exec_res.json()
        assert summary["evaluated_count"] >= 10

        # 4. Fetch ranked matches
        ranked_res = client.get(f"/api/v1/jobs/{job_id}/matches", headers=headers)
        assert ranked_res.status_code == 200
        ranked_data = ranked_res.json()
        assert ranked_data["total_evaluated"] >= 10
        matches = ranked_data["matches"]

        # Verify ordering by score descending
        scores = [m["overall_score"] for m in matches]
        assert scores == sorted(scores, reverse=True)

        # Inspect top candidate
        top_match = matches[0]
        assert "overall_score" in top_match
        assert "required_skills_score" in top_match
        assert "explanation" in top_match
        assert len(top_match["explanation"]["natural_language_explanation"]) > 10

        # 5. Test filter by min_score
        filtered_res = client.get(f"/api/v1/jobs/{job_id}/matches?min_score=75.0", headers=headers)
        assert filtered_res.status_code == 200
        for m in filtered_res.json()["matches"]:
            assert m["overall_score"] >= 75.0
