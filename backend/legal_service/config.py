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

    # Debug — đọc DEBUG từ backend/.env (production=false → ẩn /docs, /openapi.json)
    debug: bool = False

    # Database — cung database voi KPI, dung schema rieng (legal.*)
    # Doc tu .env chung tai backend/.env (cung cwd voi KPI)
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "kpi_haiquan"
    db_user: str = "kpi_user"
    db_password: str = ""  # BẮT BUỘC đặt qua .env (DB_PASSWORD) — không hardcode

    @property
    def database_url(self) -> str:
        """Build async PostgreSQL connection string."""
        return (
            f"postgresql+asyncpg://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

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
    internal_api_key: str = ""  # BẮT BUỘC đặt qua .env (INTERNAL_API_KEY)

    # Upload file — luu tren local filesystem (tuong tu LMS)
    upload_dir: str = "uploads/legal"
    max_file_size_mb: int = 50


# Dinh dang file hop le cho van ban phap luat
ALLOWED_LEGAL_EXTENSIONS = frozenset({".pdf", ".doc", ".docx"})


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
