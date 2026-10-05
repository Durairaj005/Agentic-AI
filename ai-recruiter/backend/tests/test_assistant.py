import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from app.main import app


def test_ai_assistant_workflow():
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
        cand_seed_res = client.post("/api/v1/candidates/seed", headers=headers)
        assert cand_seed_res.status_code == 200

        # 3. Reindex FAISS vector store
        reindex_res = client.post("/api/v1/ai/assistant/reindex-vectors", headers=headers)
        assert reindex_res.status_code == 200
        assert "total_vectors" in reindex_res.json()
        assert reindex_res.json()["total_vectors"] >= 20

        # 4. Semantic search in FAISS
        search_res = client.get("/api/v1/ai/assistant/search-candidates?q=distributed+python+kubernetes&top_k=3", headers=headers)
        assert search_res.status_code == 200
        search_data = search_res.json()
        assert search_data["total_results"] > 0
        assert "similarity_score" in search_data["results"][0]

        # 5. Fetch a candidate and job for targeted queries
        cands_res = client.get("/api/v1/candidates", headers=headers)
        jobs_res = client.get("/api/v1/jobs", headers=headers)
        sample_cand = cands_res.json()[0]
        sample_job = jobs_res.json()[0]

        # 6. Chat with assistant: Interview questions intent
        chat_q_res = client.post(
            "/api/v1/ai/assistant/chat",
            json={
                "message": f"Generate interview questions for {sample_cand['name']} for the {sample_job['title']} role",
                "candidate_id": sample_cand["id"],
                "job_id": sample_job["id"]
            },
            headers=headers
        )
        assert chat_q_res.status_code == 200
        chat_q_data = chat_q_res.json()
        assert chat_q_data["intent"] == "INTERVIEW_QUESTIONS"
        assert len(chat_q_data["reply"]) > 50

        # 7. Chat with assistant: Outreach email intent
        chat_email_res = client.post(
            "/api/v1/ai/assistant/chat",
            json={
                "message": f"Draft an outreach email to {sample_cand['name']}",
                "candidate_id": sample_cand["id"],
                "job_id": sample_job["id"]
            },
            headers=headers
        )
        assert chat_email_res.status_code == 200
        assert chat_email_res.json()["intent"] == "OUTREACH_EMAIL"

        # 8. Dedicated generate-questions endpoint
        gen_q_res = client.post(
            "/api/v1/ai/assistant/generate-questions",
            json={"candidate_id": sample_cand["id"], "job_id": sample_job["id"]},
            headers=headers
        )
        assert gen_q_res.status_code == 200
        assert gen_q_res.json()["intent"] == "INTERVIEW_QUESTIONS"

        # 9. Dedicated draft-outreach endpoint
        gen_outreach_res = client.post(
            "/api/v1/ai/assistant/draft-outreach",
            json={"candidate_id": sample_cand["id"], "job_id": sample_job["id"]},
            headers=headers
        )
        assert gen_outreach_res.status_code == 200
        assert gen_outreach_res.json()["intent"] == "OUTREACH_EMAIL"
