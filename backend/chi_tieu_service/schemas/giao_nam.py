"""
chi_tieu_service/schemas/giao_nam.py
====================================
Pydantic schemas giao chi tieu nam cho don vi.
"""

from datetime import datetime
from decimal import Decimal
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

LoaiMuc = Literal["PHAP_LENH", "PHAN_DAU"]


class GiaoNamCreate(BaseModel):
    don_vi_id: UUID
    chi_tieu_id: UUID
    nam: int = Field(..., ge=2025)
    loai_muc: LoaiMuc = "PHAP_LENH"
    gia_tri_giao: Decimal
    luy_ke_dau_ky: Decimal = Decimal("0")
    ghi_chu: Optional[str] = None


class GiaoNamUpdate(BaseModel):
    gia_tri_giao: Optional[Decimal] = None
    luy_ke_dau_ky: Optional[Decimal] = None
    ghi_chu: Optional[str] = None


class GiaoNamResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    don_vi_id: UUID
    chi_tieu_id: UUID
    nam: int
    loai_muc: str
    gia_tri_giao: Decimal
    luy_ke_dau_ky: Optional[Decimal] = Decimal("0")
    nguoi_giao_id: Optional[UUID] = None
    ghi_chu: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
