"""
portal_service/schemas/bai_viet.py
====================================
Schemas Pydantic cho bài viết portal (CMS tin tức nội bộ).

Workflow trạng thái:
  NHAP → KIEM_TRA → DUYET → XUAT_BAN → THU_HOI
"""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Sub-schemas nhúng trong response
# ---------------------------------------------------------------------------


class UserBrief(BaseModel):
    """Thông tin tóm tắt người dùng (nhúng trong BaiViet)."""

    id: uuid.UUID
    ma_cc: str
    ho_ten: str

    model_config = {"from_attributes": True}


class ChuyenMucBrief(BaseModel):
    """Thông tin tóm tắt chuyên mục (nhúng trong BaiViet)."""

    id: uuid.UUID
    ten: str
    slug: str
    loai: str

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Input schemas
# ---------------------------------------------------------------------------


class BaiVietCreate(BaseModel):
    """Tạo bài viết mới."""

    chuyen_muc_id: Optional[uuid.UUID] = Field(None, description="ID chuyên mục")
    tieu_de: str = Field(..., min_length=1, max_length=500, description="Tiêu đề bài viết")
    tom_tat: Optional[str] = Field(None, description="Tóm tắt nội dung (hiện trong danh sách)")
    noi_dung: str = Field(..., min_length=1, description="Nội dung đầy đủ (HTML)")
    anh_dai_dien: Optional[str] = Field(None, description="URL ảnh đại diện")


class BaiVietUpdate(BaseModel):
    """Cập nhật bài viết — tất cả optional, chỉ sửa được khi NHAP."""

    chuyen_muc_id: Optional[uuid.UUID] = None
    tieu_de: Optional[str] = Field(None, min_length=1, max_length=500)
    tom_tat: Optional[str] = None
    noi_dung: Optional[str] = Field(None, min_length=1)
    anh_dai_dien: Optional[str] = None


class DoiTrangThaiRequest(BaseModel):
    """Request đổi trạng thái workflow."""

    trang_thai_moi: str = Field(
        ...,
        description=(
            "Trạng thái mới: KIEM_TRA | DUYET | XUAT_BAN | NHAP | THU_HOI"
        ),
    )
    ly_do: Optional[str] = Field(None, description="Lý do từ chối / thu hồi (tuỳ chọn)")


class GhimRequest(BaseModel):
    """Request ghim/bỏ ghim bài viết."""

    is_ghim: bool = Field(..., description="True = ghim lên đầu trang, False = bỏ ghim")


# ---------------------------------------------------------------------------
# Output schemas
# ---------------------------------------------------------------------------


class BaiVietListResponse(BaseModel):
    """Response tóm tắt bài viết dùng cho danh sách (không kèm nội dung đầy đủ)."""

    id: uuid.UUID
    tieu_de: str
    tom_tat: Optional[str] = None
    anh_dai_dien: Optional[str] = None
    trang_thai: str
    is_ghim: bool
    so_luot_xem: int
    ngay_xuat_ban: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # Nested objects
    chuyen_muc: Optional[ChuyenMucBrief] = None
    nguoi_soan: Optional[UserBrief] = None

    model_config = {"from_attributes": True}


class BaiVietResponse(BaseModel):
    """Response đầy đủ bài viết kèm nội dung và thông tin duyệt."""

    id: uuid.UUID
    tieu_de: str
    tom_tat: Optional[str] = None
    noi_dung: str
    anh_dai_dien: Optional[str] = None
    trang_thai: str
    is_ghim: bool
    so_luot_xem: int
    ngay_xuat_ban: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # Nested objects
    chuyen_muc: Optional[ChuyenMucBrief] = None
    nguoi_soan: Optional[UserBrief] = None
    nguoi_kiem_tra: Optional[UserBrief] = None
    nguoi_duyet: Optional[UserBrief] = None

    model_config = {"from_attributes": True}
