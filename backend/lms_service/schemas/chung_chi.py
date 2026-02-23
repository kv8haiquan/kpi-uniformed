"""
lms_service/schemas/chung_chi.py
================================
Pydantic schemas cho chung chi va khao sat.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


def tinh_xep_loai(diem: Decimal) -> str:
    """Tinh xep loai tu diem tong ket."""
    if diem >= 90:
        return "XUAT_SAC"
    elif diem >= 80:
        return "GIOI"
    elif diem >= 65:
        return "KHA"
    elif diem >= 50:
        return "DAT"
    return "KHONG_DAT"


class ChungChiResponse(BaseModel):
    """Schema response chung chi."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    ma_chung_chi: str
    cong_chuc_id: UUID
    khoa_hoc_id: UUID
    ten_chung_chi: Optional[str] = None
    diem_dat: Optional[Decimal] = None
    ngay_cap: Optional[datetime] = None
    nguoi_cap_id: Optional[UUID] = None
    file_url: Optional[str] = None
    # JOIN fields
    khoa_hoc_ten: Optional[str] = None
    khoa_hoc_ma: Optional[str] = None
    ho_ten: Optional[str] = None
    ma_cc: Optional[str] = None
    xep_loai: Optional[str] = None


class KhaoSatCreate(BaseModel):
    """Schema gui khao sat."""
    khoa_hoc_id: UUID
    noi_dung: dict  # JSONB flexible: {"chat_luong": 4, "giang_vien": 5, "nhan_xet": "Tot"}


class KhaoSatResponse(BaseModel):
    """Schema response khao sat."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    cong_chuc_id: UUID
    khoa_hoc_id: UUID
    noi_dung: dict
    created_at: Optional[datetime] = None


class ThongKeKhaoSat(BaseModel):
    """Thong ke khao sat cua 1 khoa hoc."""
    khoa_hoc_id: UUID
    tong_khao_sat: int = 0
    phan_bo: Optional[dict] = None  # tong hop noi_dung
