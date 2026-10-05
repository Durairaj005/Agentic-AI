import sys
import os
import uuid
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from app.main import app


def test_auth_workflow():
    with TestClient(app) as client:
        unique_suffix = str(uuid.uuid4())[:8]
        recruiter_email = f"recruiter_{unique_suffix}@test.com"
        password = "TestPassword@123"

        # 1. Register a new recruiter
        reg_payload = {
            "name": "Jane Recruiter",
            "email": recruiter_email,
            "password": password,
            "role": "RECRUITER"
        }
        reg_res = client.post("/api/v1/auth/register", json=reg_payload)
        assert reg_res.status_code == 201, reg_res.text
        user_data = reg_res.json()
        assert user_data["email"] == recruiter_email
        assert user_data["name"] == "Jane Recruiter"
        assert user_data["role"] == "RECRUITER"
        assert "password" not in user_data
        assert "password_hash" not in user_data

        # 2. Duplicate registration should be rejected
        dup_res = client.post("/api/v1/auth/register", json=reg_payload)
        assert dup_res.status_code == 400

        # 3. Login with wrong password should fail
        bad_login = client.post("/api/v1/auth/login", json={
            "email": recruiter_email,
            "password": "WrongPassword!"
        })
        assert bad_login.status_code == 401

        # 4. Login with correct password
        login_res = client.post("/api/v1/auth/login", json={
            "email": recruiter_email,
            "password": password
        })
        assert login_res.status_code == 200
        token_data = login_res.json()
        assert "access_token" in token_data
        assert token_data["token_type"] == "bearer"
        token = token_data["access_token"]

        # 5. Access /auth/me with Bearer token
        me_res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert me_res.status_code == 200
        me_data = me_res.json()
        assert me_data["email"] == recruiter_email

        # 6. Access /auth/me without token should fail
        unauth_res = client.get("/api/v1/auth/me")
        assert unauth_res.status_code == 401

        # 7. Recruiter cannot access Admin-only /users
        forbidden_res = client.get("/api/v1/users", headers={"Authorization": f"Bearer {token}"})
        assert forbidden_res.status_code == 403

        # 8. Test Admin default seed account login
        admin_login = client.post("/api/v1/auth/login", json={
            "email": "admin@smartrecruit.ai",
            "password": "Admin@123456"
        })
        assert admin_login.status_code == 200, admin_login.text
        admin_token = admin_login.json()["access_token"]

        # 9. Admin CAN access /users
        admin_users_res = client.get("/api/v1/users", headers={"Authorization": f"Bearer {admin_token}"})
        assert admin_users_res.status_code == 200
        users_list = admin_users_res.json()
        assert len(users_list) >= 2
