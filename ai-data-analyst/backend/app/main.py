import os
import asyncio
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.database.connection import engine, Base
from app.api.v1.datasets import router as datasets_router
from app.api.v1.analysis import router as analysis_router
from app.api.v1.auth import router as auth_router
from app.services.cleanup_service import start_cleanup_worker

# import models to register them in Base metadata before tables creation
import app.models.dataset
import app.models.analysis_run
import app.models.user

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Automatically create all tables on startup (works on MySQL or SQLite)
    Base.metadata.create_all(bind=engine)
    
    # 2. Start periodic background cleanup task (purges data older than 4 hours, checks every 15 minutes)
    cleanup_task = asyncio.create_task(
        start_cleanup_worker(interval_seconds=900, retention_hours=4)
    )
    
    yield
    
    # 3. Clean up the task on application shutdown
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass

# 1. Initialize FastAPI application with lifespan context manager
app = FastAPI(
    title="AI Data Analyst REST API",
    description="Backend API exposing dataset profiling and LangGraph agent workflow analysis.",
    version="1.0.0",
    lifespan=lifespan
)

# 2. Configure CORS Middleware
# Allows frontend dashboard (Phase 8 React Vite) to call endpoints
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # open for local development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. Mount Static Files
# Serves generated Plotly chart images directly via HTTP URLs
charts_dir = Path("exports/charts")
os.makedirs(charts_dir, exist_ok=True)
app.mount("/exports/charts", StaticFiles(directory=str(charts_dir)), name="charts")

# Ensure uploads folder exists
uploads_dir = Path(settings.upload_dir)
os.makedirs(uploads_dir, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(uploads_dir)), name="uploads")

# 4. Register Routers
app.include_router(auth_router,     prefix="/api/v1/auth",     tags=["auth"])
app.include_router(datasets_router, prefix="/api/v1/datasets", tags=["datasets"])
app.include_router(analysis_router, prefix="/api/v1/analysis", tags=["analysis"])

# 5. Service Health Check Endpoint
@app.get("/", tags=["health"])
async def health_check():
    return {
        "status": "online",
        "service": "AI Data Analyst Agent REST API",
        "environment": settings.app_env,
        "max_upload_size_mb": settings.max_upload_size_mb,
        "llm_provider": settings.llm_provider,
        "llm_model": settings.llm_model
    }
