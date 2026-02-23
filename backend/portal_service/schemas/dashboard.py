"""
portal_service/schemas/dashboard.py
=====================================
Schemas Pydantic cho Dashboard Portal.

Sử dụng trên trang chủ (widget tin tức, thống kê nhanh).
Dùng cho cả CBCC thường và Lãnh đạo.
"""

import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Sub-schemas
# ---------------------------------------------------------------------------


class TinGhimBrief(BaseModel):
    """Tóm tắt bài viết ghim / tin mới nhất (dùng trên widget trang chủ)."""

    id: uuid.UUID
    tieu_de: str
    tom_tat: Optional[str] = None
    anh_dai_dien: Optional[str] = None
    ngay_xuat_ban: Optional[datetime] = None
    so_luot_xem: int = 0

    model_config = {"from_attributes": True}


class ThongKeChuyenMuc(BaseModel):
    """Thống kê bài viết theo chuyên mục."""

    ten_chuyen_muc: str
    slug: str
    so_bai: int


# ---------------------------------------------------------------------------
# Dashboard CBCC (trang chủ công khai)
# ---------------------------------------------------------------------------


class PortalDashboardSummary(BaseModel):
    """Dữ liệu tổng hợp cho dashboard trang chủ Portal.

    Dùng bởi mọi CBCC đã xác thực.
    """

    # Số liệu tổng quan
    bai_viet_moi: int  # Số bài xuất bản trong 7 ngày qua
    tai_lieu_moi: int  # Số tài liệu upload trong 7 ngày qua

    # Widget bài viết nổi bật
    tin_ghim: List[TinGhimBrief]      # Bài ghim (is_ghim=True, tối đa 3)
    tin_moi_nhat: List[TinGhimBrief]  # 5 bài mới nhất (không ghim)


# ---------------------------------------------------------------------------
# Dashboard Lãnh đạo (thống kê sâu hơn)
# ---------------------------------------------------------------------------


class TinTucStats(BaseModel):
    """Thống kê tin tức / bài viết."""

    tong_bai_xuat_ban: int
    bai_moi_thang_nay: int
    theo_chuyen_muc: List[ThongKeChuyenMuc] = []


class TaiLieuStats(BaseModel):
    """Thống kê tài liệu ECM."""

    tong_tai_lieu: int
    moi_thang_nay: int


class LanhDaoDashboard(BaseModel):
    """Dashboard thống kê dành cho Lãnh đạo — phần Portal.

    Lưu ý: Đây chỉ là phần Portal. Dashboard lãnh đạo đầy đủ (gộp LMS,
    Forum, Legal) sẽ được tổng hợp ở tầng frontend (Prompt 6).
    """

    thang: int   # Tháng thống kê (1-12)
    nam: int     # Năm thống kê

    tin_tuc: TinTucStats
    tai_lieu: TaiLieuStats
