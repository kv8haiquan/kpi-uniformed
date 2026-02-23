"""
lms_service/schemas/dang_ky.py
==============================
Pydantic schemas cho dang ky / giao khoa hoc.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class DangKyResponse(BaseModel):
    """Schema response dang ky khoa hoc."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    cong_chuc_id: UUID
    khoa_hoc_id: UUID
    loai_dang_ky: Optional[str] = "TU_NGUYEN"
    trang_thai: Optional[str] = "CHUA_BAT_DAU"
    phan_tram_hoan_thanh: Optional[Decimal] = Decimal("0")
    han_hoan_thanh: Optional[date] = None
    ngay_bat_dau_hoc: Optional[datetime] = None
    ngay_hoan_thanh: Optional[datetime] = None
    diem_cao_nhat: Optional[Decimal] = None
    created_at: Optional[datetime] = None
    # Fields tu JOIN
    khoa_hoc_ten: Optional[str] = None
    khoa_hoc_ma: Optional[str] = None
    khoa_hoc_loai: Optional[str] = None
    giang_vien_ho_ten: Optional[str] = None


LOAI_GIAO_BAI = ["BAT_BUOC", "GIAO_VIEC"]


class GiaoBaiRequest(BaseModel):
    """Schema giao bai bat buoc. It nhat 1 trong cong_chuc_ids hoac don_vi_ids."""
    cong_chuc_ids: Optional[list[UUID]] = None
    don_vi_ids: Optional[list[UUID]] = None
    loai_dang_ky: str = Field(default="BAT_BUOC")
    han_hoan_thanh: Optional[date] = None

    @model_validator(mode="after")
    def validate_target(self):
        if not self.cong_chuc_ids and not self.don_vi_ids:
            raise ValueError("Phải cung cấp ít nhất cong_chuc_ids hoặc don_vi_ids")
        if self.loai_dang_ky not in LOAI_GIAO_BAI:
            raise ValueError(f"loai_dang_ky phải thuộc: {LOAI_GIAO_BAI}")
        return self


class GiaoBaiResponse(BaseModel):
    """Ket qua giao bai."""
    da_giao: int = 0
    da_co: int = 0
    tong: int = 0


class HocVienListItem(BaseModel):
    """Thong tin hoc vien cua khoa hoc."""
    model_config = ConfigDict(from_attributes=True)

    cong_chuc_id: UUID
    ho_ten: Optional[str] = None
    ma_cc: Optional[str] = None
    don_vi_ten: Optional[str] = None
    trang_thai: Optional[str] = "CHUA_BAT_DAU"
    phan_tram_hoan_thanh: Optional[Decimal] = Decimal("0")
    loai_dang_ky: Optional[str] = None
    ngay_dang_ky: Optional[datetime] = None
    ngay_bat_dau_hoc: Optional[datetime] = None
    ngay_hoan_thanh: Optional[datetime] = None
