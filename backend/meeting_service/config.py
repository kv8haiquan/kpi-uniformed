"""
meeting_service/config.py
==========================
Cấu hình HKG service. Load từ env. SECRET_KEY phải trùng với KPI backend.
"""

from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        populate_by_name=True,  # cho phép cả alias HKG_UPLOAD_DIR + field name upload_dir
    )

    # Database — chung kpi_haiquan, schema meeting + common
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "kpi_haiquan"
    db_user: str = "kpi_user"
    db_password: str = "KpiHaiQuan2026!"

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    # Security — phải trùng KPI
    secret_key: str = "CHANGE_THIS_IN_PRODUCTION_MUST_BE_AT_LEAST_32_CHARS"
    algorithm: str = "HS256"

    # Service info
    service_name: str = "meeting"
    service_port: int = 8006

    # CORS — chỉ local dev cho tới UAT (xem README)
    cors_origins: List[str] = [
        "http://localhost:3000",
    ]

    # Storage — filesystem (LMS pattern).
    # G4-fix-8 (02/05/2026): alias HKG_UPLOAD_DIR để tách production vs test.
    # - Production: set absolute path trong .env (vd: HKG_UPLOAD_DIR=/var/data/hkg/uploads)
    # - Test: conftest.py set HKG_UPLOAD_DIR=<tmpdir> trước khi import service
    # - Default: "uploads/meeting" (relative — dev local)
    upload_dir: str = Field(default="uploads/meeting", alias="HKG_UPLOAD_DIR")
    max_file_size_mb: int = 100  # spec HKG: tối đa 100MB/file


# Extension cho phép upload tài liệu họp (Module 3)
ALLOWED_EXTENSIONS: frozenset = frozenset({
    ".pdf", ".doc", ".docx", ".ppt", ".pptx", ".xls", ".xlsx",
    ".jpg", ".jpeg", ".png", ".gif", ".webp",
    ".txt",
})


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
