"""
chi_tieu_service/config.py
==========================
Cau hinh module Chi tieu Don vi — load tu environment variables.
Dung CHUNG database voi KPI, schema rieng (chi_tieu.*).
"""

from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Cau hinh Chi tieu service."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Debug — đọc DEBUG từ backend/.env (production=false → ẩn /docs, /openapi.json)
    debug: bool = False

    # Database — cung database voi KPI, schema rieng (chi_tieu.*)
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

    # Security — PHAI giong KPI backend (doc tu .env cua KPI)
    secret_key: str = "CHANGE_THIS_IN_PRODUCTION_MUST_BE_AT_LEAST_32_CHARS"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 480

    # Service info
    service_name: str = "chi_tieu"
    service_port: int = 8007

    # CORS
    cors_origins: List[str] = [
        "http://localhost:3000",
        "http://localhost:8080",
    ]

    # Common service internal API (gui thong bao)
    common_internal_url: str = "http://localhost:8005/internal/v1"
    internal_api_key: str = ""  # BẮT BUỘC đặt qua .env (INTERNAL_API_KEY)

    # Moc thoi gian mac dinh (co the override qua platform_config)
    han_dang_ky_ngay: int = 5    # han dang ky trong thang
    han_ket_qua_ngay: int = 3    # han nhap ket qua (thang sau)


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
