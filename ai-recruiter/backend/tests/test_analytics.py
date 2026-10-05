import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from app.main import app


def test_analytics_overview_endpoint():
    with TestClient(app) as client:
        # 1. Login
        login_res = client.post(
            "/api/v1/auth/login",
            json={"email": "recruiter@smartrecruit.ai", "password": "Recruiter@123456"}
        )
        assert login_res.status_code == 200
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 2. Ensure seed data
        client.post("/api/v1/jobs/seed", headers=headers)
        client.post("/api/v1/candidates/seed", headers=headers)
        client.post("/api/v1/pipeline/seed", headers=headers)

        # 3. Fetch analytics overview
        res = client.get("/api/v1/analytics/overview", headers=headers)
        assert res.status_code == 200
        data = res.json()

        assert "total_jobs" in data
        assert "total_candidates" in data
        assert "total_applications" in data
        assert "funnel" in data
        assert "score_distribution" in data
        assert "skills_gap" in data
        assert "education_breakdown" in data
        assert "recent_activity" in data

        assert len(data["funnel"]) == 8
        assert len(data["score_distribution"]) == 5
        assert data["total_jobs"] >= 5
        assert data["total_candidates"] >= 20
        assert data["total_applications"] > 0
