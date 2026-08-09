import os
import json
import uuid
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
import redis

from app.main import app
from app.services.cache_service import cache_service
from app.services.job_service import job_service

from app.core.dependencies import get_current_user
from app.models.user import User

@pytest.fixture(scope="module", autouse=True)
def override_auth():
    dummy_user = User(id=1, username="test_api_user", email="test_api_user@example.com")
    app.dependency_overrides[get_current_user] = lambda: dummy_user
    yield
    app.dependency_overrides.clear()

client = TestClient(app)

def test_cache_service_store_retrieve():
    """Verify that writing to and reading from cache_service successfully serializes and stores objects."""
    if not cache_service.is_available():
        pytest.skip("Local Redis server is not running or unreachable.")

    dataset_id = 999
    query = "select maximum profit from sales"
    mock_response = {
        "success": True,
        "explanation": "Maximum profit is $2000 in North region.",
        "result": None,
        "errors": []
    }

    # Clean old cache if exists
    cache_service.invalidate_dataset_cache(dataset_id)

    # 1. Set cache
    cache_service.set_cached_query(dataset_id, query, mock_response)

    # 2. Get cache and assert equality
    cached = cache_service.get_cached_query(dataset_id, query)
    assert cached == mock_response

    # 3. Invalidate and check it is gone
    cache_service.invalidate_dataset_cache(dataset_id)
    assert cache_service.get_cached_query(dataset_id, query) is None

def test_redis_graceful_degradation():
    """Verify that when Redis is unreachable, CacheService and JobService degrade gracefully to non-crashing modes."""
    # Temporarily mock the redis client to raise connection errors
    original_client = cache_service.redis_client
    mock_client = MagicMock()
    mock_client.ping.side_effect = redis.exceptions.ConnectionError("Redis connection timed out.")
    mock_client.get.side_effect = redis.exceptions.ConnectionError("Redis connection timed out.")
    mock_client.setex.side_effect = redis.exceptions.ConnectionError("Redis connection timed out.")
    
    cache_service.redis_client = mock_client
    try:
        # Cache gets should return None instead of crashing
        res = cache_service.get_cached_query(1, "query")
        assert res is None

        # Cache sets should ignore the exception and pass quietly
        cache_service.set_cached_query(1, "query", {"data": "test"})

        # Job service should fallback to thread-safe dictionary memory storage automatically
        job_id = "test-job-uuid-1234"
        job_service.set_job_status(job_id, "RUNNING")
        
        status_data = job_service.get_job_status(job_id)
        assert status_data is not None
        assert status_data["status"] == "RUNNING"
        
    finally:
        # Restore original client
        cache_service.redis_client = original_client

def test_async_query_polling_endpoints():
    """Verify async query endpoint accepts query, schedules background worker, and enables status polling."""
    # Ensure database is configured with setup_db tables
    from app.database.connection import engine, Base
    Base.metadata.create_all(bind=engine)

    # We will mock the database query to mock a dataset existence
    from app.models.dataset import Dataset
    from app.database.connection import SessionLocal

    db = SessionLocal()
    # Ensure test file exists in db
    test_ds = db.query(Dataset).filter(Dataset.filename == "test_cache_sales.csv").first()
    if not test_ds:
        test_ds = Dataset(
            filename="test_cache_sales.csv",
            filepath="backend/tests/test_api_sales.csv",  # dummy path
            total_rows=10,
            total_columns=2,
            profile_json="{}"
        )
        db.add(test_ds)
        db.commit()
        db.refresh(test_ds)
    db.close()

    payload = {
        "filename": "test_cache_sales.csv",
        "query": "find average profit"
    }

    # Mock the background worker function to avoid running full LangGraph cycle inside unit test
    with patch("app.api.v1.analysis._run_async_analysis_task") as mock_async_worker:
        response = client.post("/api/v1/analysis/query/async", json=payload)
        
        assert response.status_code == 202
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "RUNNING"
        
        job_id = data["job_id"]
        
        # Verify job status can be successfully polled
        status_response = client.get(f"/api/v1/analysis/jobs/{job_id}")
        assert status_response.status_code == 200
        status_data = status_response.json()
        assert status_data["job_id"] == job_id
        assert status_data["status"] == "RUNNING"

    # Cleanup test dataset from db
    db = SessionLocal()
    db.delete(test_ds)
    db.commit()
    db.close()
