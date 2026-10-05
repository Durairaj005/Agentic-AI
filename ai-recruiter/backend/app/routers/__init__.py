from app.routers.auth import router as auth_router
from app.routers.users import router as users_router
from app.routers.jobs import router as jobs_router
from app.routers.candidates import router as candidates_router
from app.routers.ai_skills import router as ai_skills_router
from app.routers.matching import router as matching_router
from app.routers.pipeline import router as pipeline_router
from app.routers.analytics import router as analytics_router
from app.routers.assistant import router as assistant_router
from app.routers.comparison import router as comparison_router

__all__ = [
    "auth_router",
    "users_router",
    "jobs_router",
    "candidates_router",
    "ai_skills_router",
    "matching_router",
    "pipeline_router",
    "analytics_router",
    "assistant_router",
    "comparison_router"
]
