"""
lms_service/config.py
========================
Cau hinh module Dao tao - Load tu environment variables.
"""

from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Cau hinh Dao tao service."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Database — cung database voi KPI, dung schema rieng (lms.*)
    # Default khop voi backend/.env (postgres user, port 5433)
    database_url: str = "postgresql+asyncpg://postgres:postgres123@localhost:5433/kpi_haiquan"

    # Security — PHAI giong KPI backend (doc tu .env cua KPI)
    secret_key: str = "CHANGE_THIS_IN_PRODUCTION_MUST_BE_AT_LEAST_32_CHARS"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 480

    # Service info
    service_name: str = "lms"
    service_port: int = 8001

    # CORS
    cors_origins: List[str] = [
        "http://localhost:3000",
        "http://localhost:8080",
    ]

    # Redis (cache/queue)
    redis_url: str = "redis://localhost:6379/0"

    # File upload
    upload_dir: str = "uploads/lms"        # Thư mục lưu file (relative to working dir)
    max_file_size_mb: int = 100            # Giới hạn kích thước file


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()


# Danh sách định dạng file được phép upload (module-level constant)
ALLOWED_EXTENSIONS: frozenset = frozenset({
    # Tài liệu
    ".pdf", ".doc", ".docx", ".ppt", ".pptx", ".xls", ".xlsx",
    # Video
    ".mp4", ".webm", ".avi", ".mov",
    # Ảnh
    ".jpg", ".jpeg", ".png", ".gif", ".webp",
    # Nội dung web
    ".html", ".htm",
})
