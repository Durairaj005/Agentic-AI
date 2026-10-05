import os
import sys
import pytest
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from app.main import app


def test_pipeline_workflow():
    with TestClient(app) as client:
        # 1. Login as recruiter
        login_res = client.post(
            "/api/v1/auth/login",
            json={"email": "recruiter@smartrecruit.ai", "password": "Recruiter@123456"}
        )
        assert login_res.status_code == 200
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 2. Seed jobs and candidates to ensure data exists
        client.post("/api/v1/jobs/seed", headers=headers)
        client.post("/api/v1/candidates/seed", headers=headers)

        # 3. Seed pipeline demo data
        seed_res = client.post("/api/v1/pipeline/seed", headers=headers)
        assert seed_res.status_code == 200
        assert "total_applications" in seed_res.json()

        # 4. Fetch applications
        apps_res = client.get("/api/v1/applications", headers=headers)
        assert apps_res.status_code == 200
        applications = apps_res.json()
        assert len(applications) > 0

        target_app = applications[0]
        app_id = target_app["id"]
        cand_id = target_app["candidate_id"]

        # 5. Update stage with recruiter notes
        stage_res = client.put(
            f"/api/v1/applications/{app_id}/stage",
            json={"status": "SHORTLISTED", "recruiter_notes": "Candidate passed initial screening with flying colors."},
            headers=headers
        )
        assert stage_res.status_code == 200
        assert stage_res.json()["status"] == "SHORTLISTED"

        # 6. Candidate notes
        note_res = client.post(
            f"/api/v1/candidates/{cand_id}/notes",
            json={"note": "Verified portfolio projects and GitHub activity. Highly impressive system architecture."},
            headers=headers
        )
        assert note_res.status_code == 200
        assert "Verified portfolio" in note_res.json()["note"]

        get_notes_res = client.get(f"/api/v1/candidates/{cand_id}/notes", headers=headers)
        assert get_notes_res.status_code == 200
        assert len(get_notes_res.json()) >= 1

        # 7. Follow-up reminder
        tomorrow = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        followup_res = client.post(
            "/api/v1/followups",
            json={
                "candidate_id": cand_id,
                "followup_date": tomorrow,
                "method": "EMAIL",
                "notes": "Send technical screening assignment link."
            },
            headers=headers
        )
        assert followup_res.status_code == 200
        followup_id = followup_res.json()["id"]

        # Update follow-up status to COMPLETED
        patch_f_res = client.patch(
            f"/api/v1/followups/{followup_id}",
            json={"status": "COMPLETED", "notes": "Assignment sent via email."},
            headers=headers
        )
        assert patch_f_res.status_code == 200
        assert patch_f_res.json()["status"] == "COMPLETED"

        # 8. Schedule Interview
        interview_date = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
        int_res = client.post(
            "/api/v1/interviews",
            json={
                "application_id": app_id,
                "interview_date": interview_date,
                "interview_type": "TECHNICAL",
                "interviewer": "Lead Architect",
                "feedback": None,
                "rating": None
            },
            headers=headers
        )
        assert int_res.status_code == 200
        interview_id = int_res.json()["id"]

        # Submit interview feedback
        patch_int_res = client.patch(
            f"/api/v1/interviews/{interview_id}",
            json={
                "status": "COMPLETED",
                "rating": 5,
                "feedback": "Outstanding candidate. Excellent grasp of distributed caching and microservice patterns."
            },
            headers=headers
        )
        assert patch_int_res.status_code == 200
        assert patch_int_res.json()["rating"] == 5
        assert patch_int_res.json()["status"] == "COMPLETED"
