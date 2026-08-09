"""
core/config.py — Central Configuration Loader
==============================================

PURPOSE:
  Loads environment variables from .env file into a typed settings object.
  Every component that needs configuration imports from here.

WHY THIS EXISTS:
  Without this, you'd scatter `os.getenv("KEY")` calls everywhere.
  If a variable name changes, you'd have to update 20 files.
  Here, you update ONE place.

HOW IT WORKS:
  python-dotenv reads your .env file.
  The Settings class declares what variables are expected.
  If a REQUIRED variable is missing, the app raises a clear error immediately.

FUTURE PHASES:
  Phase 2 — LLM_API_KEY will be required (raises error if missing)
  Phase 5 — APP_HOST, APP_PORT used by FastAPI startup
  Phase 6 — DB_* used by SQLAlchemy engine
  Phase 7 — REDIS_* used by Redis client
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# ── Locate and load the .env file ───────────────────────────────────────────
# Walk up from this file's location to find the project root's .env
_here = Path(__file__).resolve().parent           # .../backend/app/core/
_project_root = _here.parents[2]                  # .../ai-data-analyst/
_env_path = _project_root / ".env"

if _env_path.exists():
    load_dotenv(dotenv_path=_env_path)
else:
    # .env doesn't exist yet — that's fine for Phase 1 (no API keys needed)
    load_dotenv()  # will try cwd fallback


class Settings:
    """
    Typed access to all environment variables.

    Usage:
        from app.core.config import settings
        print(settings.llm_api_key)
    """

    # ── Application ──────────────────────────────────────────────────────────
    app_env: str = os.getenv("APP_ENV", "development")
    app_host: str = os.getenv("APP_HOST", "0.0.0.0")
    app_port: int = int(os.getenv("APP_PORT", "8000"))

    # ── LLM (Phase 2+) ───────────────────────────────────────────────────────
    llm_provider: str = os.getenv("LLM_PROVIDER", "gemini")
    llm_api_key: str | None = os.getenv("LLM_API_KEY")
    llm_model: str = os.getenv("LLM_MODEL", "gemini-1.5-flash")

    # ── Tavily (Phase 9+) ─────────────────────────────────────────────────────
    tavily_api_key: str | None = os.getenv("TAVILY_API_KEY")

    # ── Database (Phase 6+) ──────────────────────────────────────────────────
    mysql_host: str = os.getenv("MYSQL_HOST", "localhost")
    mysql_port: int = int(os.getenv("MYSQL_PORT", "3306"))
    mysql_user: str = os.getenv("MYSQL_USER", "root")
    mysql_password: str = os.getenv("MYSQL_PASSWORD", "")
    mysql_database: str = os.getenv("MYSQL_DATABASE", "ai_data_analyst")

    # ── Redis (Phase 7+) ─────────────────────────────────────────────────────
    redis_host: str = os.getenv("REDIS_HOST", "localhost")
    redis_port: int = int(os.getenv("REDIS_PORT", "6379"))
    redis_password: str | None = os.getenv("REDIS_PASSWORD") or None
    redis_db: int = int(os.getenv("REDIS_DB", "0"))

    # ── JWT (Phase 10+) ──────────────────────────────────────────────────────
    secret_key: str = os.getenv("SECRET_KEY", "dev-only-secret-change-in-production")
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    jwt_expire_minutes: int = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

    # ── File Upload (Phase 5+) ───────────────────────────────────────────────
    max_upload_size_mb: int = int(os.getenv("MAX_UPLOAD_SIZE_MB", "50"))
    upload_dir: str = os.getenv("UPLOAD_DIR", "./uploads")

    # ── Logging ──────────────────────────────────────────────────────────────
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

    def require_llm_key(self) -> str:
        """
        Call this when an LLM key is actually needed (Phase 2+).
        Raises a clear, helpful error instead of a cryptic AttributeError.
        """
        if not self.llm_api_key:
            raise EnvironmentError(
                "\n\n"
                "  ❌  LLM_API_KEY is not set.\n"
                "  ──────────────────────────────────────────────\n"
                "  1. Copy .env.example to .env\n"
                "  2. Add your Google Gemini API key:\n"
                "     LLM_API_KEY=your_actual_key_here\n"
                "  3. Get a free key at: https://aistudio.google.com/\n"
            )
        return self.llm_api_key

    def require_tavily_key(self) -> str:
        """Call this when Tavily is actually invoked (Phase 9+)."""
        if not self.tavily_api_key:
            raise EnvironmentError(
                "\n\n"
                "  ❌  TAVILY_API_KEY is not set.\n"
                "  1. Get a free key at: https://tavily.com/\n"
                "  2. Add to .env: TAVILY_API_KEY=your_key\n"
            )
        return self.tavily_api_key

    @property
    def database_url(self) -> str:
        """SQLAlchemy-compatible MySQL connection string (Phase 6+)."""
        return (
            f"mysql+pymysql://{self.mysql_user}:{self.mysql_password}"
            f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}"
        )

    @property
    def redis_url(self) -> str:
        """Redis connection string (Phase 7+)."""
        auth = f":{self.redis_password}@" if self.redis_password else ""
        return f"redis://{auth}{self.redis_host}:{self.redis_port}/{self.redis_db}"


# ── Singleton instance ────────────────────────────────────────────────────────
# All modules import this one object.
# It's instantiated once when the module is first imported.
settings = Settings()
