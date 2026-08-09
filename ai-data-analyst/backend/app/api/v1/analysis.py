import os
import json
import uuid
from pathlib import Path
import pandas as pd
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database.connection import get_db
from app.models.dataset import Dataset
from app.models.analysis_run import AnalysisRun
from app.models.user import User
from app.services.agent_service import AgentService
from app.services.cache_service import cache_service
from app.services.job_service import job_service
from app.schemas.analysis_schemas import AnalysisRequest, AnalysisResponse
from app.core.dependencies import get_current_user

router = APIRouter()

def _run_async_analysis_task(job_id: str, payload: AnalysisRequest, db_url: str):
    """
    Worker task executed asynchronously in the background.
    Runs the agent and updates the job status with the result.
    """
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    try:
        # Create scoped session inside the thread
        engine = create_engine(db_url)
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()
        
        try:
            # 1. Fetch dataset
            db_dataset = db.query(Dataset).filter(Dataset.filename == payload.filename).first()
            if not db_dataset:
                job_service.set_job_status(
                    job_id, 
                    "FAILED", 
                    error=f"Dataset '{payload.filename}' not found in database."
                )
                return

            target_path = Path(db_dataset.filepath)
            if not target_path.exists():
                job_service.set_job_status(
                    job_id, 
                    "FAILED", 
                    error=f"Dataset CSV file not found on storage."
                )
                return

            # 2. Parse CSV
            ext = target_path.suffix.lower()
            if ext == ".csv":
                df = pd.read_csv(target_path)
            else:
                df = pd.read_excel(target_path)

            # 3. Check Cache
            cached_res = cache_service.get_cached_query(db_dataset.id, payload.query)
            if cached_res:
                job_service.set_job_status(job_id, "COMPLETED", result=cached_res)
                return

            # 4. Run Agent
            settings.require_llm_key()
            agent = AgentService(df, payload.filename)
            explanation, tool_res, errors = agent.run(payload.query)

            success = tool_res.success if tool_res else False
            result_val = str(tool_res.result) if (tool_res and tool_res.result) else None

            # Detect chart output — normalize Windows backslashes
            chart_url = None
            if result_val and "exports" in result_val and ".png" in result_val:
                chart_rel = result_val.replace("\\", "/")
                if chart_rel.startswith("./"):
                    chart_rel = chart_rel[2:]
                chart_url = f"http://localhost:8000/{chart_rel}"

            response_dict = {
                "success": success,
                "explanation": explanation or "",
                "result": result_val,
                "chart_url": chart_url,
                "errors": errors or []
            }

            # 5. Cache response
            cache_service.set_cached_query(db_dataset.id, payload.query, response_dict)

            # 6. Save analysis run log to database
            try:
                db_run = AnalysisRun(
                    dataset_id=db_dataset.id,
                    query=payload.query,
                    explanation=explanation or "",
                    result=result_val,
                    errors_json=json.dumps(errors or [])
                )
                db.add(db_run)
                db.commit()
            except Exception as db_err:
                db.rollback()
                print(f"Database logging failed during async run: {str(db_err)}")

            job_service.set_job_status(job_id, "COMPLETED", result=response_dict)
            
        finally:
            db.close()
            
    except Exception as e:
        job_service.set_job_status(job_id, "FAILED", error=str(e))


@router.post("/query", response_model=AnalysisResponse)
async def query_dataset(
    payload: AnalysisRequest,
    db: Session = Depends(get_db),
):
    """
    Submit a natural-language query about an uploaded dataset.
    Features Redis caching to bypass identical query processing times.
    """
    # 1. Fetch dataset from database
    db_dataset = db.query(Dataset).filter(Dataset.filename == payload.filename).first()
    if not db_dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset '{payload.filename}' not found. Please upload it first."
        )

    # 2. Check Redis Cache
    cached_res = cache_service.get_cached_query(db_dataset.id, payload.query)
    if cached_res:
        return AnalysisResponse(
            success=cached_res.get("success", False),
            explanation=cached_res.get("explanation", ""),
            result=cached_res.get("result"),
            errors=cached_res.get("errors", [])
        )

    # 3. Parse file to Pandas DataFrame
    target_path = Path(db_dataset.filepath)
    if not target_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Physical file for dataset '{payload.filename}' not found."
        )

    ext = target_path.suffix.lower()
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

    # 4. Execute query via LangGraph agent
    try:
        settings.require_llm_key()
        
        agent = AgentService(df, payload.filename)
        explanation, tool_res, errors = agent.run(payload.query)
        
        success = tool_res.success if tool_res else False
        result_val = str(tool_res.result) if (tool_res and tool_res.result) else None

        # Detect chart output — normalize backslashes so URL works cross-platform
        chart_url = None
        if result_val and "exports" in result_val and ".png" in result_val:
            # Convert Windows backslash path to forward-slash URL path
            chart_rel = result_val.replace("\\", "/")
            # Strip leading ./ if present
            if chart_rel.startswith("./"):
                chart_rel = chart_rel[2:]
            chart_url = f"http://localhost:8000/{chart_rel}"

        response_dict = {
            "success": success,
            "explanation": explanation or "",
            "result": result_val,
            "chart_url": chart_url,
            "errors": errors or []
        }

        # 5. Cache response in Redis
        cache_service.set_cached_query(db_dataset.id, payload.query, response_dict)

        # 6. Save log in database
        try:
            db_run = AnalysisRun(
                dataset_id=db_dataset.id,
                query=payload.query,
                explanation=explanation or "",
                result=result_val,
                errors_json=json.dumps(errors or [])
            )
            db.add(db_run)
            db.commit()
        except Exception as db_err:
            db.rollback()
            print(f"Database logging failed: {str(db_err)}")
        
        return AnalysisResponse(**response_dict)
        
    except EnvironmentError as env_err:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(env_err)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent workflow execution failed: {str(e)}"
        )


@router.post("/query/async", status_code=status.HTTP_202_ACCEPTED)
async def query_dataset_async(
    payload: AnalysisRequest, 
    background_tasks: BackgroundTasks, 
    db: Session = Depends(get_db),
):
    """
    Asynchronously submit an analysis query.
    Returns a Job ID immediately so the client can poll the status.
    """
    # Verify dataset exists before starting thread
    db_dataset = db.query(Dataset).filter(Dataset.filename == payload.filename).first()
    if not db_dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset '{payload.filename}' not found. Please upload it first."
        )

    job_id = str(uuid.uuid4())
    job_service.set_job_status(job_id, "RUNNING")

    # Get connection URL for background thread database access
    db_url = db.bind.url.render_as_string(hide_password=False)

    background_tasks.add_task(
        _run_async_analysis_task, 
        job_id, 
        payload, 
        db_url
    )

    return {
        "job_id": job_id,
        "status": "RUNNING"
    }


@router.get("/jobs/{job_id}")
async def get_job_status(
    job_id: str,
):
    """
    Fetch the execution status and output details of an async analysis task.
    """
    job_data = job_service.get_job_status(job_id)
    if not job_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job '{job_id}' not found."
        )
    return job_data
