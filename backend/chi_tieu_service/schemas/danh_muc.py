"""
chi_tieu_service/schemas/danh_muc.py
====================================
Pydantic schemas CRUD danh muc chi tieu.
"""

from datetime import datetime
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

KieuDuLieu = Literal["SO_NGUYEN", "THAP_PHAN", "PHAN_TRAM"]


class DanhMucChiTieuCreate(BaseModel):
    linh_vuc_id: UUID
    ma_chi_tieu: str = Field(..., min_length=1, max_length=30)
    ten_chi_tieu: str = Field(..., min_length=1, max_length=500)
    don_vi_tinh: str = Field(..., min_length=1, max_length=50)
    kieu_du_lieu: KieuDuLieu = "THAP_PHAN"
    co_phan_dau: bool = False
    van_ban_giao: Optional[str] = Field(None, max_length=300)
    mo_ta: Optional[str] = None
    thu_tu: int = 0


class DanhMucChiTieuUpdate(BaseModel):
    linh_vuc_id: Optional[UUID] = None
    ma_chi_tieu: Optional[str] = Field(None, min_length=1, max_length=30)
    ten_chi_tieu: Optional[str] = Field(None, min_length=1, max_length=500)
    don_vi_tinh: Optional[str] = Field(None, min_length=1, max_length=50)
    kieu_du_lieu: Optional[KieuDuLieu] = None
    co_phan_dau: Optional[bool] = None
    van_ban_giao: Optional[str] = Field(None, max_length=300)
    mo_ta: Optional[str] = None
    thu_tu: Optional[int] = None


class DanhMucChiTieuResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    linh_vuc_id: UUID
    ma_chi_tieu: str
    ten_chi_tieu: str
    don_vi_tinh: str
    kieu_du_lieu: str
    co_phan_dau: Optional[bool] = False
    van_ban_giao: Optional[str] = None
    mo_ta: Optional[str] = None
    thu_tu: Optional[int] = 0
    is_active: Optional[bool] = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
