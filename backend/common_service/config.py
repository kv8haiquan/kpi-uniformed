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
    #
    # Đây CHỈ là mã định danh. Bộ tham số của từng template (đặc biệt là có
    # `ma_hop` hay không) khai trong services/zalo/templates.py — đổi template
    # sang cái khác thì phải xem lại chỗ đó, không chỉ sửa .env.
    zalo_tpl_moi_hop: str = ""  # 623165 Giấy mời họp
    zalo_tpl_nhac_hop: str = ""  # 623236 Nhắc họp không giấy
    zalo_tpl_thay_doi_hop: str = ""  # 623180 Thay đổi lịch họp
    zalo_tpl_huy_hop: str = ""  # 623182 Hủy họp không giấy

    # Phạm vi bật: danh sách `loai` trong common.thong_bao được phép gửi Zalo.
    # Giai đoạn 1 chỉ HKG. Muốn bật thêm KPI/LMS chỉ cần sửa biến môi trường.
    zalo_loai_bat: str = "MEETING"

    # ------------------------------------------------------------------
    # Trần chi tiêu — chốt chặn cuối trước khi tiền ra (services/zalo/tran_chi.py)
    # ------------------------------------------------------------------
    # Hạn mức kỹ thuật Zalo cấp là 20.000 tin/ngày ⇒ 16.000.000đ/ngày nếu
    # không có gì chặn. Trần đặt bằng ĐỒNG vì ngân sách được duyệt bằng tiền;
    # quy đổi sang số tin theo `zalo_don_gia_tin` ở tran_chi.py.
    #
    # QUY ƯỚC GIÁ TRỊ — chọn thế này để không có cách gõ nhầm nào gây hại:
    #   -1 (hoặc âm) = KHÔNG giới hạn  ← mặc định, để merge code không âm thầm
    #                                     chặn tin của ai
    #    0           = CHẶN HOÀN TOÀN, không gửi tin nào
    #   >0           = trần theo đồng
    # Nếu để 0 mang nghĩa "không giới hạn" thì người muốn khóa chi tiêu bằng
    # cách gõ 0 sẽ mở toang hạn mức — đúng ngược ý định.
    zalo_don_gia_tin: int = 800  # đồng/tin (cả 4 template ZNS hiện dùng)
    zalo_tran_ngay_dong: int = -1
    zalo_tran_thang_dong: int = -1
    zalo_nguong_canh_bao_pc: int = 80  # báo quản trị khi đạt % trần này

    # Tin xếp hàng quá số giờ này thì bỏ, không gửi nữa. Cần thiết để trần
    # chi tiêu có nghĩa: không có nó, tin bị chặn chỉ dồn lại rồi bắn ra một
    # lượt khi sang kỳ mới — nhắc họp đã diễn ra từ tuần trước.
    # Ngưỡng phải lớn hơn mọi độ trễ bình thường: giờ yên tĩnh hoãn tối đa
    # 8 tiếng (22h→6h), backoff thử lại tối đa 1 tiếng.
    zalo_han_gui_gio: int = 12

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
