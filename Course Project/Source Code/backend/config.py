import os
from typing import Optional
from pydantic_settings import BaseSettings
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent

class Settings(BaseSettings):
    APP_NAME: str = "Classroom — Course Organizer"
    APP_VERSION: str = "2.0.0"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

    # Primary Database (SQLite for dev fallback, PostgreSQL for production)
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite+aiosqlite:///{BASE_DIR}/data/organizer.db")
    POSTGRES_URL: Optional[str] = os.getenv("POSTGRES_URL", None)

    # JWT Authentication
    SECRET_KEY: str = os.getenv("SECRET_KEY", "aura-development-secret-key-only-not-for-prod")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24

    # LLM / Gemini Provider
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "models/text-embedding-004")

    # Local Storage Folders
    UPLOAD_DIR: Path = BASE_DIR / "data" / "uploads"
    NOTES_DIR: Path = BASE_DIR / "data" / "notes"
    SUBMISSIONS_DIR: Path = BASE_DIR / "data" / "submissions"

    # S3 / MinIO Object Storage
    STORAGE_BACKEND: str = os.getenv("STORAGE_BACKEND", "local")  # "local" or "s3"
    S3_ENDPOINT_URL: Optional[str] = os.getenv("S3_ENDPOINT_URL", None)
    S3_ACCESS_KEY: Optional[str] = os.getenv("S3_ACCESS_KEY", None)
    S3_SECRET_KEY: Optional[str] = os.getenv("S3_SECRET_KEY", None)
    S3_BUCKET_NOTES: str = os.getenv("S3_BUCKET_NOTES", "aura-notes")
    S3_BUCKET_SUBMISSIONS: str = os.getenv("S3_BUCKET_SUBMISSIONS", "aura-submissions")

    # Model Context Protocol (MCP)
    MCP_SERVER_URL: str = os.getenv("MCP_SERVER_URL", "http://localhost:8001")
    MCP_AUTH_TOKEN: str = os.getenv("MCP_AUTH_TOKEN", "aura-governed-mcp-token-2026")

    # Redis / Background Worker
    REDIS_URL: Optional[str] = os.getenv("REDIS_URL", None)

    # CORS
    ALLOWED_ORIGINS: str = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:3000")

    # Academic Governance & Safety Invariants
    SIMILARITY_THRESHOLD: float = 0.75
    MAX_VALIDATION_ATTEMPTS: int = 3
    MAX_GRADING_RETRIES: int = 3

    model_config = {"env_file": str(BASE_DIR / ".env"), "extra": "ignore"}

settings = Settings()
