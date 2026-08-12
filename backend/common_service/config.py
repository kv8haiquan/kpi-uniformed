"""
common_service/config.py
========================
Cau hinh module Common — Load tu environment variables.
"""

from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Cau hinh Common service."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Debug — đọc DEBUG từ backend/.env (production=false → ẩn /docs, /openapi.json)
    debug: bool = False

    # Internal API key — xác thực module nội bộ (BẮT BUỘC đặt qua .env)
    internal_api_key: str = ""

    # Database — cung database voi KPI, dung schema rieng (common.*)
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
    service_name: str = "common"
    service_port: int = 8005

    # CORS
    cors_origins: List[str] = [
        "http://localhost:3000",
        "http://localhost:8080",
    ]

    # Redis (cache/queue)
    redis_url: str = "redis://localhost:6379/0"

    # ------------------------------------------------------------------
    # Zalo OA — kênh đẩy thông báo (xem services/zalo/)
    # ------------------------------------------------------------------
    # HAI LỚP CỜ AN TOÀN, cả hai đều mặc định ở trạng thái KHÔNG gửi thật:
    #   zalo_enabled=False  → worker không chạy vòng lặp nào
    #   zalo_dry_run=True   → có chạy, có xếp hàng, nhưng CHỈ GHI LOG,
    #                          không gọi API Zalo, không tốn tin nhắn
    # Muốn gửi thật phải chủ động đặt CẢ HAI trong .env. Nhờ vậy code này
    # merge vào nhánh chính cũng không thể vô tình nhắn cho ai.
    zalo_enabled: bool = False
    zalo_dry_run: bool = True

    # Credential — BẮT BUỘC đặt qua .env, KHÔNG hardcode (xem đợt vá bảo mật
    # 31/07/2026: mật khẩu DB từng nằm làm default trong 7 file config.py)
    zalo_app_id: str = ""
    zalo_oa_secret: str = ""
    # KHÔNG dùng trong lời gọi API (access_token đã định danh OA). Chỉ ghi lại
    # để biết hệ thống đang gắn với OA nào — phục vụ đối soát và hồ sơ ATTT.
    # Để trống cũng chạy bình thường.
    zalo_oa_id: str = ""

    # Endpoint — tách ra config để test trỏ về mock server được
    zalo_oauth_url: str = "https://oauth.zaloapp.com/v4/oa/access_token"
    zalo_zns_url: str = "https://business.openapi.zalo.me/message/template"

    # Template ID do Zalo cấp sau khi duyệt. Để trống = chưa có → worker
    # đánh dấu BO_QUA/KHONG_CO_TEMPLATE thay vì gửi lỗi.
    zalo_tpl_moi_hop: str = ""
    zalo_tpl_nhac_hop: str = ""
    zalo_tpl_thay_doi_hop: str = ""
    zalo_tpl_huy_hop: str = ""

    # Nút bấm trong tin ZNS có mang tham số mã cuộc họp hay không.
    # False → nút trỏ tới URL cố định (/hop-khong-giay), KHÔNG gửi tham số ma_hop.
    # True  → nút dạng .../chi-tiet/{{ma_hop}}, hệ thống gửi kèm mã cuộc họp.
    # Chỉ bật SAU KHI template đã khai tham số ma_hop và được Zalo duyệt —
    # gửi thừa tham số so với template sẽ bị Zalo từ chối cả tin.
    zalo_nut_tham_so: bool = False

    # Phạm vi bật: danh sách `loai` trong common.thong_bao được phép gửi Zalo.
    # Giai đoạn 1 chỉ HKG. Muốn bật thêm KPI/LMS chỉ cần sửa biến môi trường.
    zalo_loai_bat: str = "MEETING"

    # Vận hành worker
    zalo_chu_ky_giay: int = 60  # nhịp quét hàng đợi
    zalo_cua_so_quet_phut: int = 120  # chỉ nhặt thông báo mới trong N phút qua
    zalo_so_lan_thu_toi_da: int = 4
    zalo_moi_lan_gui: int = 50  # số tin tối đa mỗi vòng, tránh dồn tải
    zalo_khong_gui_truoc_gio: int = 6  # giờ VN — không nhắn lúc rạng sáng
    zalo_khong_gui_sau_gio: int = 22

    @property
    def zalo_danh_sach_loai(self) -> List[str]:
        """Parse zalo_loai_bat thành list, ví dụ 'MEETING,KPI' → [...]."""
        return [x.strip().upper() for x in self.zalo_loai_bat.split(",") if x.strip()]


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
