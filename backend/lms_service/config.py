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

    # Debug — đọc DEBUG từ backend/.env (production=false → ẩn /docs, /openapi.json)
    debug: bool = False

    # Database — cung database voi KPI, dung schema rieng (lms.*)
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
    max_file_size_mb: int = 500            # Giới hạn kích thước file (khớp mặc định frontend)

    # Common service internal API
    common_internal_url: str = "http://localhost:8005/internal/v1"
    internal_api_key: str = ""  # BẮT BUỘC đặt qua .env (INTERNAL_API_KEY)

    # ------------------------------------------------------------------
    # Câu hỏi ĐGNL hằng ngày — endpoint cho chatbot Zalo gọi từ bên ngoài
    # ------------------------------------------------------------------
    # Khoá RIÊNG cho bot, KHÔNG dùng chung internal_api_key: khoá đó mở cửa
    # cho các endpoint nội bộ khác (thông báo, văn bản...). Bot chạy ở hạ tầng
    # ngoài nên khoá của nó sẽ nằm trong cấu hình của bên thứ ba — lộ thì chỉ
    # mất một endpoint chỉ-đọc.
    # Để TRỐNG = tắt hẳn tính năng (fail closed), không phải mở toang.
    zalo_bot_api_key: str = ""  # đặt qua .env (ZALO_BOT_API_KEY)

    # 9 lĩnh vực đầu được phép lấy câu hỏi hằng ngày, khai theo `ma_linh_vuc`.
    # KHÔNG suy ra bằng cách cắt tiền tố số của mã: cột `thu_tu` của mọi lĩnh
    # vực trong bảng đều bằng 0 nên không sắp xếp được, và các mã 10./11./13.
    # /14. cũng bắt đầu bằng chữ số. Liệt kê tường minh là cách duy nhất chắc.
    dgnl_daily_ma_linh_vuc: str = (
        "1. LHQ,2. LTXNK,3. LQLT,4. LXLVPHC,5. LCBCC,"
        "6. QCLV,7. QCCV,8. LCDS,9. STVB"
    )

    @property
    def dgnl_daily_linh_vuc_list(self) -> List[str]:
        """Danh sách mã lĩnh vực đã tách, bỏ khoảng trắng thừa."""
        return [m.strip() for m in self.dgnl_daily_ma_linh_vuc.split(",") if m.strip()]


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
