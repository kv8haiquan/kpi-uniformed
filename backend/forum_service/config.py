"""
forum_service/config.py
========================
Cau hinh module Dien dan - Load tu environment variables.
"""

from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Cau hinh Dien dan service."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Database — cung database voi KPI, dung schema rieng (forum.*)
    database_url: str = "postgresql+asyncpg://kpi_user:password@localhost:5433/kpi_haiquan"

    # Security — PHAI giong KPI backend
    secret_key: str = "CHANGE_THIS_IN_PRODUCTION_MUST_BE_AT_LEAST_32_CHARS"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 480

    # Service info
    service_name: str = "forum"
    service_port: int = 8002

    # CORS
    cors_origins: List[str] = [
        "http://localhost:3000",
        "http://localhost:8080",
    ]

    # Redis (cache/queue)
    redis_url: str = "redis://localhost:6379/0"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
