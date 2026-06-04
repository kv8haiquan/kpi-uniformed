"""
chi_tieu_service/schemas/dang_ky.py
===================================
Pydantic schemas dang ky + ket qua thang, duyet, lich su.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class DangKyCreate(BaseModel):
    """Tao moi ban ghi dang ky thang (trang thai NHAP)."""
    don_vi_id: UUID
    chi_tieu_id: UUID
    thang: int = Field(..., ge=1, le=12)
    nam: int = Field(..., ge=2025)
    khong_dang_ky: bool = False
    gia_tri_dang_ky: Optional[Decimal] = None


class DangKyUpdate(BaseModel):
    """Sua dang ky khi dang o trang thai NHAP."""
    khong_dang_ky: Optional[bool] = None
    gia_tri_dang_ky: Optional[Decimal] = None


class YeuCauSuaRequest(BaseModel):
    """Yeu cau sua dang ky da duyet."""
    gia_tri_dang_ky_moi: Decimal
    ly_do: Optional[str] = None


class NhapKetQuaRequest(BaseModel):
    """Nhap (luu nhap) ket qua cuoi thang."""
    gia_tri_ket_qua: Decimal
    danh_gia_ghi_chu: Optional[str] = Field(None, max_length=200)


class TuChoiRequest(BaseModel):
    ly_do_tu_choi: str = Field(..., min_length=1)


class DangKyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    don_vi_id: UUID
    chi_tieu_id: UUID
    thang: int
    nam: int
    khong_dang_ky: Optional[bool] = False
    gia_tri_dang_ky: Optional[Decimal] = None
    gia_tri_ket_qua: Optional[Decimal] = None
    danh_gia_tu_dong: Optional[str] = None
    danh_gia_ghi_chu: Optional[str] = None
    trang_thai: str
    nguoi_theo_doi_id: UUID
    nguoi_duyet_id: Optional[UUID] = None
    ngay_gui_dang_ky: Optional[datetime] = None
    ngay_duyet_dang_ky: Optional[datetime] = None
    ngay_gui_ket_qua: Optional[datetime] = None
    ngay_duyet_ket_qua: Optional[datetime] = None
    ly_do_tu_choi: Optional[str] = None
    is_khoa: Optional[bool] = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class LichSuResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    dang_ky_thang_id: UUID
    hanh_dong: str
    nguoi_thuc_hien_id: UUID
    ghi_chu: Optional[str] = None
    created_at: Optional[datetime] = None
