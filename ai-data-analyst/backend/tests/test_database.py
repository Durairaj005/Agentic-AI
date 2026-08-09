import os
import json
import datetime
from pathlib import Path
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.connection import Base
from app.models.dataset import Dataset
from app.models.analysis_run import AnalysisRun
from app.services.cleanup_service import cleanup_expired_datasets

# Setup a clean in-memory SQLite database for testing database modules
@pytest.fixture(scope="function")
def test_db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

def test_dataset_and_analysis_run_persistence(test_db):
    """Verify that Dataset and AnalysisRun models can be successfully saved and retrieved."""
    # 1. Create and save a dataset
    dataset = Dataset(
        filename="sales_test.csv",
        filepath="uploads/sales_test.csv",
        total_rows=100,
        total_columns=5,
        profile_json=json.dumps({"summary": "sales details"})
    )
    test_db.add(dataset)
    test_db.commit()
    test_db.refresh(dataset)

    assert dataset.id is not None
    assert dataset.filename == "sales_test.csv"

    # 2. Log an analysis run associated with this dataset
    run = AnalysisRun(
        dataset_id=dataset.id,
        query="what is total profit?",
        explanation="The total profit is $50,000.",
        result="exports/charts/profit.png",
        errors_json=json.dumps([])
    )
    test_db.add(run)
    test_db.commit()
    test_db.refresh(run)

    assert run.id is not None
    assert run.dataset_id == dataset.id
    assert len(dataset.analysis_runs) == 1

def test_cascade_delete(test_db):
    """Verify that deleting a dataset cascadingly deletes all related analysis runs."""
    dataset = Dataset(
        filename="sales_test.csv",
        filepath="uploads/sales_test.csv",
        total_rows=100,
        total_columns=5,
        profile_json=json.dumps({})
    )
    test_db.add(dataset)
    test_db.commit()

    run = AnalysisRun(
        dataset_id=dataset.id,
        query="what is total profit?",
        explanation="The total profit is $50,000.",
        result="exports/charts/profit.png",
        errors_json=json.dumps([])
    )
    test_db.add(run)
    test_db.commit()

    # Verify both exist
    assert test_db.query(Dataset).count() == 1
    assert test_db.query(AnalysisRun).count() == 1

    # Delete dataset
    test_db.delete(dataset)
    test_db.commit()

    # Verify both are deleted
    assert test_db.query(Dataset).count() == 0
    assert test_db.query(AnalysisRun).count() == 0

def test_auto_cleanup_service(test_db, tmp_path):
    """Verify background retention service deletes expired datasets, physical CSV files, and chart files."""
    # 1. Create temporary mock CSV dataset file
    csv_file = tmp_path / "old_dataset.csv"
    csv_file.write_text("region,sales\nNorth,100")
    
    # 2. Create temporary mock chart PNG file
    chart_dir = tmp_path / "charts"
    os.makedirs(chart_dir, exist_ok=True)
    chart_file = chart_dir / "old_chart.png"
    chart_file.write_text("fake png bytes")

    # 3. Create dataset record created 5 hours ago (retention is 4 hours)
    old_time = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=5)
    dataset = Dataset(
        filename="old_dataset.csv",
        filepath=str(csv_file),
        total_rows=1,
        total_columns=2,
        profile_json=json.dumps({}),
        created_at=old_time
    )
    test_db.add(dataset)
    test_db.commit()
    test_db.refresh(dataset)

    run = AnalysisRun(
        dataset_id=dataset.id,
        query="plot region",
        explanation="Chart created",
        result=str(chart_file),
        errors_json=json.dumps([])
    )
    test_db.add(run)
    test_db.commit()

    # 4. Run cleanup
    purged = cleanup_expired_datasets(test_db, retention_hours=4)
    assert purged == 1

    # 5. Verify records are gone from database
    assert test_db.query(Dataset).count() == 0
    assert test_db.query(AnalysisRun).count() == 0

    # 6. Verify physical assets are deleted from filesystem
    assert not csv_file.exists()
    assert not chart_file.exists()
