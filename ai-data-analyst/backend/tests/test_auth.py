import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.database.connection import engine, Base, get_db
from app.models.user import User

client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup_db():
    # Make sure all tables are created
    Base.metadata.create_all(bind=engine)
    yield
    # Cleanup: remove test users specifically to avoid polluting DB
    db = Session(bind=engine)
    try:
        db.query(User).filter(User.username.like("test_auth_user%")).delete(synchronize_session=False)
        db.commit()
    finally:
        db.close()


def test_register_user_success():
    """Verify that registering a new user is successful."""
    payload = {
        "username": "test_auth_user_1",
        "email": "test_auth_user_1@example.com",
        "password": "strong_password_123"
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == payload["username"]
    assert data["email"] == payload["email"]
    assert "id" in data
    assert "hashed_password" not in data  # password must be serialized out


def test_register_duplicate_username():
    """Verify duplicate username registrations are rejected."""
    payload = {
        "username": "test_auth_user_1",
        "email": "another_email@example.com",
        "password": "some_password_123"
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 409
    assert "already taken" in response.json()["detail"].lower()


def test_register_duplicate_email():
    """Verify duplicate email registrations are rejected."""
    payload = {
        "username": "another_username",
        "email": "test_auth_user_1@example.com",
        "password": "some_password_123"
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 409
    assert "already registered" in response.json()["detail"].lower()


def test_login_user_success():
    """Verify logging in with valid credentials issues a JWT."""
    payload = {
        "username": "test_auth_user_1",
        "password": "strong_password_123"
    }
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_user_invalid_password():
    """Verify login with incorrect password returns 401."""
    payload = {
        "username": "test_auth_user_1",
        "password": "wrong_password"
    }
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 401
    assert "incorrect username or password" in response.json()["detail"].lower()


def test_login_user_non_existent():
    """Verify login for non-existent user returns 401."""
    payload = {
        "username": "non_existent_username",
        "password": "wrong_password"
    }
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 401
    assert "incorrect username or password" in response.json()["detail"].lower()


def test_get_me_unauthorized():
    """Verify /me returns 401 without authentication."""
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_get_me_authorized():
    """Verify /me successfully returns user profile when authenticated."""
    # First login to get a token
    login_payload = {
        "username": "test_auth_user_1",
        "password": "strong_password_123"
    }
    login_response = client.post("/api/v1/auth/login", json=login_payload)
    token = login_response.json()["access_token"]

    # Request profile
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == login_payload["username"]


# Auth endpoints require auth checks removed for public endpoints.
