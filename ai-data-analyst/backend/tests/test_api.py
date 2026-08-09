import io
import os
from pathlib import Path
from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.config import settings
from app.tools.pandas_tools import ToolResult
from app.database.connection import engine, Base

from app.core.dependencies import get_current_user
from app.models.user import User

@pytest.fixture(scope="module", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield

@pytest.fixture(scope="module", autouse=True)
def override_auth():
    dummy_user = User(id=1, username="test_api_user", email="test_api_user@example.com")
    app.dependency_overrides[get_current_user] = lambda: dummy_user
    yield
    app.dependency_overrides.clear()

client = TestClient(app)

@pytest.fixture
def temp_csv_file(tmp_path):
    """Fixture that yields a valid temporary CSV file path."""
    content = "region,sales,profit\nNorth,100,50\nSouth,200,80\nEast,150,60"
    file_path = tmp_path / "test_api_sales.csv"
    file_path.write_text(content)
    yield file_path
    # cleanup
    if file_path.exists():
        os.remove(file_path)

def test_health_check():
    """Verify that the health check / root endpoint is up."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert "service" in data

def test_upload_invalid_extension():
    """Verify that uploads with unsupported extensions are rejected."""
    file_data = {"file": ("test.txt", io.BytesIO(b"dummy data"), "text/plain")}
    response = client.post("/api/v1/datasets/upload", files=file_data)
    assert response.status_code == 400
    assert "Unsupported file type" in response.json()["detail"]

def test_upload_valid_csv(temp_csv_file):
    """Verify uploading a valid CSV successfully profiles the file."""
    # Ensure settings.upload_dir is redirected or clean for test
    original_upload_dir = settings.upload_dir
    test_upload_dir = Path("uploads_test")
    os.makedirs(test_upload_dir, exist_ok=True)
    settings.upload_dir = str(test_upload_dir)

    try:
        with open(temp_csv_file, "rb") as f:
            file_data = {"file": ("test_api_sales.csv", f, "text/csv")}
            response = client.post("/api/v1/datasets/upload", files=file_data)

        assert response.status_code == 201
        data = response.json()
        assert data["filename"] == "test_api_sales.csv"
        assert data["total_rows"] == 3
        assert data["total_columns"] == 3
        assert "profile" in data
        assert "region" in data["profile"]["categorical_columns"]
        assert "sales" in data["profile"]["numeric_columns"]

        # Verify profile retrieval GET endpoint works
        get_response = client.get(f"/api/v1/datasets/profile/test_api_sales.csv")
        assert get_response.status_code == 200
        get_data = get_response.json()
        assert get_data["total_rows"] == 3

    finally:
        # cleanup uploads_test file and folder
        uploaded_file = test_upload_dir / "test_api_sales.csv"
        if uploaded_file.exists():
            os.remove(uploaded_file)
        if test_upload_dir.exists():
            os.rmdir(test_upload_dir)
        settings.upload_dir = original_upload_dir

def test_profile_not_found():
    """Verify getting a profile for a non-existent dataset raises 404."""
    response = client.get("/api/v1/datasets/profile/non_existent_file.csv")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()

@patch("app.services.agent_service.AgentService.run")
def test_query_analysis_success(mock_agent_run, temp_csv_file):
    """Verify the analysis endpoint executes AgentService.run successfully."""
    # Mock the return values of agent.run()
    mock_agent_run.return_value = (
        "Here is a summary of sales by region...",
        ToolResult(
            success=True,
            tool_name="plot_bar_chart",
            result="exports/charts/sales_by_region.png",
            description="Bar chart generated."
        ),
        []
    )

    # Put temp file in upload_dir so mock run passes existence validation
    original_upload_dir = settings.upload_dir
    test_upload_dir = Path("uploads_test")
    os.makedirs(test_upload_dir, exist_ok=True)
    settings.upload_dir = str(test_upload_dir)

    try:
        # copy dummy file to test upload directory
        target_path = test_upload_dir / "test_api_sales.csv"
        with open(temp_csv_file, "r") as src, open(target_path, "w") as dest:
            dest.write(src.read())

        payload = {
            "filename": "test_api_sales.csv",
            "query": "plot sales by region"
        }
        
        # We must also mock require_llm_key to bypass missing key checks if keys aren't set
        with patch("app.core.config.Settings.require_llm_key") as mock_key:
            mock_key.return_value = "dummy-key"
            response = client.post("/api/v1/analysis/query", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "summary of sales" in data["explanation"]
        assert data["result"] == "exports/charts/sales_by_region.png"
        assert len(data["errors"]) == 0

    finally:
        target_path = test_upload_dir / "test_api_sales.csv"
        if target_path.exists():
            os.remove(target_path)
        if test_upload_dir.exists():
            os.rmdir(test_upload_dir)
        settings.upload_dir = original_upload_dir

def test_query_file_not_found():
    """Verify query endpoint raises 404 if file does not exist."""
    payload = {
        "filename": "non_existent.csv",
        "query": "total sales"
    }
    response = client.post("/api/v1/analysis/query", json=payload)
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]
