"""
portal_service/schemas/vinh_danh_thang.py
==========================================
Schemas Pydantic cho VinhDanhThang.

Workflow trang thai: DRAFT -> PUBLISHED
"""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Sub-schemas
# ---------------------------------------------------------------------------


class CongChucBrief(BaseModel):
    """Thong tin tom tat cong chuc."""

    id: uuid.UUID
    ma_cc: str
    ho_ten: str
    chuc_vu: Optional[str] = None

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Input schemas
# ---------------------------------------------------------------------------


class VinhDanhThangCreate(BaseModel):
    """Tao moi ban ghi vinh danh (DRAFT)."""

    thang: int = Field(..., ge=1, le=12, description="Thang vinh danh (1-12)")
    nam: int = Field(..., ge=2020, le=2100, description="Nam vinh danh")
    cong_chuc_id: uuid.UUID = Field(..., description="ID cong chuc duoc vinh danh")
    tieu_de: str = Field(..., min_length=1, max_length=200, description="Tieu de")
    ly_do: str = Field(..., min_length=1, description="Ly do / cau chuyen vinh danh")
    anh_chan_dung: Optional[str] = Field(None, max_length=500, description="URL anh")
    anh_vi_tri: Optional[str] = Field(
        None, max_length=20, description="Vi tri anh trong khung tron (CSS object-position)"
    )
    loi_tuyen_duong: Optional[str] = Field(None, description="Loi tuyen duong (banner)")


class VinhDanhThangUpdate(BaseModel):
    """Cap nhat vinh danh — tat ca optional."""

    thang: Optional[int] = Field(None, ge=1, le=12)
    nam: Optional[int] = Field(None, ge=2020, le=2100)
    cong_chuc_id: Optional[uuid.UUID] = None
    tieu_de: Optional[str] = Field(None, min_length=1, max_length=200)
    ly_do: Optional[str] = Field(None, min_length=1)
    anh_chan_dung: Optional[str] = Field(None, max_length=500)
    anh_vi_tri: Optional[str] = Field(None, max_length=20)
    loi_tuyen_duong: Optional[str] = None


# ---------------------------------------------------------------------------
# Output schemas
# ---------------------------------------------------------------------------


class VinhDanhThangResponse(BaseModel):
    """Response day du cua mot ban ghi vinh danh."""

    id: uuid.UUID
    thang: int
    nam: int
    tieu_de: str
    ly_do: str
    anh_chan_dung: Optional[str] = None
    anh_vi_tri: Optional[str] = None
    loi_tuyen_duong: Optional[str] = None
    trang_thai: str
    ngay_cong_bo: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    cong_chuc: Optional[CongChucBrief] = None
    nguoi_tao: Optional[CongChucBrief] = None

    model_config = {"from_attributes": True}


class UploadAnhResponse(BaseModel):
    """Response khi upload anh chan dung thanh cong."""

    url: str = Field(..., description="URL truy cap anh da upload")
