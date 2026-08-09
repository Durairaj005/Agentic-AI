import os
import json
import datetime
from pathlib import Path
import pandas as pd
from fastapi import APIRouter, File, UploadFile, HTTPException, Depends, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database.connection import get_db
from app.models.dataset import Dataset
from app.models.user import User
from app.profiler.data_profiler import DataProfiler
from app.schemas.dataset_schemas import UploadResponse
from app.core.dependencies import get_current_user

router = APIRouter()
profiler = DataProfiler()

ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".xls"}

def _get_upload_path(filename: str) -> Path:
    """Helper to get upload path and ensure parent directories exist."""
    upload_dir = Path(settings.upload_dir)
    os.makedirs(upload_dir, exist_ok=True)
    return upload_dir / filename

@router.post("/upload", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_dataset(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Upload a CSV or Excel dataset, save it, profile it, and record it in the database.
    """
    # 1. Validate file extension
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type '{ext}'. Only CSV and Excel (.xlsx, .xls) are allowed."
        )

    # 2. Validate file size
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)

    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    if file_size > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum allowed upload size of {settings.max_upload_size_mb} MB."
        )

    # 3. Save file to uploads directory
    target_path = _get_upload_path(file.filename)
    try:
        content = await file.read()
        with open(target_path, "wb") as f:
            f.write(content)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save uploaded file: {str(e)}"
        )

    # 4. Load dataset and generate profile
    try:
        if ext == ".csv":
            df = pd.read_csv(target_path)
        else:
            df = pd.read_excel(target_path)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Failed to parse dataset file: {str(e)}"
        )

    try:
        profile = profiler.profile(df, file.filename)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to profile dataset: {str(e)}"
        )

    # 5. Persist metadata to database
    try:
        existing_ds = db.query(Dataset).filter(Dataset.filename == file.filename).first()
        if existing_ds:
            # Refresh details and extend retention duration
            existing_ds.filepath = str(target_path)
            existing_ds.total_rows = profile.total_rows
            existing_ds.total_columns = profile.total_columns
            existing_ds.profile_json = profile.to_json()
            existing_ds.created_at = datetime.datetime.now(datetime.timezone.utc)
            db.commit()
            db.refresh(existing_ds)
        else:
            db_dataset = Dataset(
                filename=file.filename,
                filepath=str(target_path),
                total_rows=profile.total_rows,
                total_columns=profile.total_columns,
                profile_json=profile.to_json()
            )
            db.add(db_dataset)
            db.commit()
            db.refresh(db_dataset)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database persistence failed: {str(e)}"
        )

    return UploadResponse(
        filename=file.filename,
        total_rows=profile.total_rows,
        total_columns=profile.total_columns,
        profile=profile.to_dict()
    )

@router.get("/profile/{filename}")
async def get_dataset_profile(
    filename: str,
    db: Session = Depends(get_db),
):
    """
    Retrieve the structured profile metadata of a previously uploaded dataset.
    Reads directly from database cache.
    """
    db_dataset = db.query(Dataset).filter(Dataset.filename == filename).first()
    if not db_dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset '{filename}' not found in database. Please upload it first."
        )

    try:
        return json.loads(db_dataset.profile_json)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to parse saved dataset profile: {str(e)}"
        )
