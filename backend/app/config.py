"""
app/config.py
=============
Quản lý cấu hình ứng dụng sử dụng Pydantic Settings.
Tự động load từ biến môi trường hoặc file .env
"""

from functools import lru_cache
from typing import List, Optional

from pydantic import field_validator, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Cấu hình ứng dụng - Load từ environment variables.
    Ưu tiên: ENV vars > .env file > default values
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"  # Bỏ qua các biến không định nghĩa
    )
    
    # -------------------------------------------------------------------------
    # APPLICATION
    # -------------------------------------------------------------------------
    app_name: str = "Hải quan KV8 - KPI System"
    app_env: str = "development"  # development | staging | production
    debug: bool = True
    api_v1_prefix: str = "/api/v1"
    
    # -------------------------------------------------------------------------
    # DATABASE
    # -------------------------------------------------------------------------
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "haiquan_kv8"
    db_user: str = "postgres"
    db_password: str = "postgres123"
    
    @property
    def database_url(self) -> str:
        """
        Build async PostgreSQL connection string.
        Format: postgresql+asyncpg://user:pass@host:port/db
        """
        return (
            f"postgresql+asyncpg://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )
    
    @property
    def database_url_sync(self) -> str:
        """
        Build sync PostgreSQL connection string (cho Alembic migrations).
        Format: postgresql://user:pass@host:port/db
        """
        return (
            f"postgresql://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )
    
    # -------------------------------------------------------------------------
    # SECURITY
    # -------------------------------------------------------------------------
    secret_key: str = "CHANGE_THIS_IN_PRODUCTION_MUST_BE_AT_LEAST_32_CHARS"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 480  # 8 tiếng làm việc
    
    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        """Đảm bảo secret_key đủ dài trong production"""
        if len(v) < 32:
            raise ValueError("SECRET_KEY phải có ít nhất 32 ký tự")
        return v
    
    # -------------------------------------------------------------------------
    # CORS
    # -------------------------------------------------------------------------
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:8080"]
    
    # -------------------------------------------------------------------------
    # LOGGING
    # -------------------------------------------------------------------------
    log_level: str = "INFO"
    log_format: str = "json"  # json | text
    
    # -------------------------------------------------------------------------
    # FILE PATHS
    # -------------------------------------------------------------------------
    data_dir: str = "./data"
    upload_dir: str = "./uploads"
    
    # -------------------------------------------------------------------------
    # HELPER PROPERTIES
    # -------------------------------------------------------------------------
    @property
    def is_production(self) -> bool:
        """Kiểm tra môi trường production"""
        return self.app_env.lower() == "production"
    
    @property
    def is_development(self) -> bool:
        """Kiểm tra môi trường development"""
        return self.app_env.lower() == "development"


@lru_cache()
def get_settings() -> Settings:
    """
    Singleton pattern - Chỉ tạo Settings object một lần.
    Sử dụng lru_cache để cache kết quả.
    
    Usage:
        from app.config import get_settings
        settings = get_settings()
    """
    return Settings()


# Tạo instance mặc định để import trực tiếp
settings = get_settings()
