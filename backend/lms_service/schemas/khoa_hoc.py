"""
lms_service/schemas/khoa_hoc.py
===============================
Pydantic schemas cho CRUD + workflow khoa hoc.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


# Gia tri hop le cho cac truong trang thai / loai
LOAI_KHOA_HOC = ["TU_HOC", "BAT_BUOC", "TRUC_TUYEN", "KET_HOP"]
TRANG_THAI_KHOA_HOC = ["NHAP", "CHO_DUYET", "DA_XUAT_BAN", "TAM_DUNG", "DA_DONG"]


class KhoaHocCreate(BaseModel):
    """Schema tao khoa hoc moi."""
    ma_khoa_hoc: str = Field(..., min_length=1, max_length=50)
    ten_khoa_hoc: str = Field(..., min_length=1, max_length=300)
    mo_ta: Optional[str] = None
    chuyen_de_id: Optional[UUID] = None
    loai: str = Field(default="TU_HOC")
    thoi_luong_phut: Optional[int] = Field(None, ge=0)
    diem_dat_yeu_cau: Optional[Decimal] = Field(default=Decimal("70.00"), ge=0, le=100)
    ngay_bat_dau: Optional[date] = None
    ngay_ket_thuc: Optional[date] = None
    dieu_kien_tien_quyet: Optional[list[UUID]] = None

    @field_validator("loai")
    @classmethod
    def validate_loai(cls, v: str) -> str:
        if v not in LOAI_KHOA_HOC:
            raise ValueError(f"Loại khóa học phải thuộc: {LOAI_KHOA_HOC}")
        return v


class KhoaHocUpdate(BaseModel):
    """Schema cap nhat khoa hoc — tat ca fields optional."""
    ten_khoa_hoc: Optional[str] = Field(None, min_length=1, max_length=300)
    mo_ta: Optional[str] = None
    chuyen_de_id: Optional[UUID] = None
    loai: Optional[str] = None
    thoi_luong_phut: Optional[int] = Field(None, ge=0)
    diem_dat_yeu_cau: Optional[Decimal] = Field(None, ge=0, le=100)
    ngay_bat_dau: Optional[date] = None
    ngay_ket_thuc: Optional[date] = None
    dieu_kien_tien_quyet: Optional[list[UUID]] = None
    anh_dai_dien: Optional[str] = None

    @field_validator("loai")
    @classmethod
    def validate_loai(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in LOAI_KHOA_HOC:
            raise ValueError(f"Loại khóa học phải thuộc: {LOAI_KHOA_HOC}")
        return v


class TrangThaiUpdate(BaseModel):
    """Schema chuyen trang thai khoa hoc (workflow)."""
    trang_thai: str
    ghi_chu: Optional[str] = None

    @field_validator("trang_thai")
    @classmethod
    def validate_trang_thai(cls, v: str) -> str:
        if v not in TRANG_THAI_KHOA_HOC:
            raise ValueError(f"Trạng thái phải thuộc: {TRANG_THAI_KHOA_HOC}")
        return v


class DangKyInfo(BaseModel):
    """Thong tin dang ky khoa hoc cua user hien tai."""
    trang_thai: str
    phan_tram_hoan_thanh: float = 0
    loai_dang_ky: str
    han_hoan_thanh: Optional[date] = None


class KhoaHocResponse(BaseModel):
    """Schema response khoa hoc day du."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    ma_khoa_hoc: str
    ten_khoa_hoc: str
    mo_ta: Optional[str] = None
    chuyen_de_id: Optional[UUID] = None
    loai: str = "TU_HOC"
    anh_dai_dien: Optional[str] = None
    thoi_luong_phut: Optional[int] = None
    so_bai_hoc: Optional[int] = 0
    dieu_kien_tien_quyet: Optional[list] = None
    diem_dat_yeu_cau: Optional[Decimal] = None
    ngay_bat_dau: Optional[date] = None
    ngay_ket_thuc: Optional[date] = None
    giang_vien_id: Optional[UUID] = None
    trang_thai: Optional[str] = "NHAP"
    nguoi_duyet_id: Optional[UUID] = None
    ngay_duyet: Optional[datetime] = None
    is_active: Optional[bool] = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    # Fields tu JOIN
    chuyen_de_ten: Optional[str] = None
    giang_vien_ho_ten: Optional[str] = None
    nguoi_duyet_ho_ten: Optional[str] = None
    so_hoc_vien: int = 0
    # Trang thai dang ky cua user hien tai (None = chua dang ky)
    dang_ky: Optional[DangKyInfo] = None


class KhoaHocListItem(BaseModel):
    """Schema response khoa hoc cho danh sach (bot fields)."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    ma_khoa_hoc: str
    ten_khoa_hoc: str
    loai: str = "TU_HOC"
    trang_thai: Optional[str] = "NHAP"
    anh_dai_dien: Optional[str] = None
    chuyen_de_ten: Optional[str] = None
    giang_vien_ho_ten: Optional[str] = None
    so_bai_hoc: Optional[int] = 0
    so_hoc_vien: int = 0
    thoi_luong_phut: Optional[int] = None
    ngay_bat_dau: Optional[date] = None
    ngay_ket_thuc: Optional[date] = None
