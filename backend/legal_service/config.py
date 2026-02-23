"""
legal_service/config.py
========================
Cau hinh module Phap luat - Load tu environment variables.
"""

from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Cau hinh Phap luat service."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Database — cung database voi KPI, dung schema rieng (legal.*)
    # Default khop voi backend/.env (postgres user, port 5433)
    database_url: str = "postgresql+asyncpg://postgres:postgres123@localhost:5433/kpi_haiquan"

    # Security — PHAI giong KPI backend
    secret_key: str = "CHANGE_THIS_IN_PRODUCTION_MUST_BE_AT_LEAST_32_CHARS"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 480

    # Service info
    service_name: str = "legal"
    service_port: int = 8003

    # CORS
    cors_origins: List[str] = [
        "http://localhost:3000",
        "http://localhost:8080",
    ]

    # Redis (cache/queue)
    redis_url: str = "redis://localhost:6379/0"

    # Internal API key — dung de cac service goi nhau
    internal_api_key: str = "internal-secret-key-legal-2024"

    # Upload file — luu tren local filesystem (tuong tu LMS)
    upload_dir: str = "uploads/legal"
    max_file_size_mb: int = 50


# Dinh dang file hop le cho van ban phap luat
ALLOWED_LEGAL_EXTENSIONS = frozenset({".pdf", ".doc", ".docx"})


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
