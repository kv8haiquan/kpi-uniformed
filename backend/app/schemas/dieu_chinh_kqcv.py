"""
app/schemas/dieu_chinh_kqcv.py
==============================
Pydantic schemas cho điều chỉnh KQCV (Yêu cầu 2 — 06/05/2026).
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class GiaTriKQCV(BaseModel):
    """3 trường LĐ có thể sửa."""
    so_loi_chat_luong: int = Field(default=0, ge=0)
    so_loi_tien_do: int = Field(default=0, ge=0)
    is_chua_hoan_thanh: bool = Field(default=False, description="Đánh dấu CV chưa hoàn thành (a/b/c đều giảm)")


class DieuChinhCreateRequest(BaseModel):
    ke_khai_id: UUID
    gia_tri_moi: GiaTriKQCV
    ly_do: str = Field(..., min_length=5, max_length=2000)


class DieuChinhUpdateRequest(BaseModel):
    """Sửa NHAP trước khi gửi duyệt."""
    gia_tri_moi: Optional[GiaTriKQCV] = None
    ly_do: Optional[str] = Field(default=None, min_length=5, max_length=2000)


class PheDuyetRequest(BaseModel):
    y_kien: Optional[str] = Field(default=None, max_length=2000)


class TuChoiRequest(BaseModel):
    y_kien: str = Field(..., min_length=1, max_length=2000)


# =============================================================================
# RESPONSE
# =============================================================================

class CongChucBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    ma_cc: str
    ho_ten: str
    chuc_vu: Optional[str] = None


class KeKhaiBrief(BaseModel):
    """Thông tin gọn về CV bị điều chỉnh."""
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    cong_chuc_id: UUID
    thang: int
    nam: int
    so_luong: int
    so_loi_chat_luong: int
    so_loi_tien_do: int
    is_chua_hoan_thanh: bool


class DieuChinhResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    ke_khai_id: UUID
    nguoi_dieu_chinh_id: UUID
    nguoi_phe_duyet_id: UUID
    gia_tri_cu: dict
    gia_tri_moi: dict
    ly_do: str
    trang_thai: str
    y_kien_phe_duyet: Optional[str] = None
    ngay_phe_duyet: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    is_deleted: bool

    nguoi_dieu_chinh: Optional[CongChucBrief] = None
    nguoi_phe_duyet: Optional[CongChucBrief] = None
