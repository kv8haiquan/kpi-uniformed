"""
lms_service/schemas/bai_hoc.py
==============================
Pydantic schemas cho CRUD bai hoc + tien do hoc tap.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


LOAI_NOI_DUNG = ["VIDEO", "PDF", "SLIDE", "HTML", "SCORM", "QUIZ"]


class BaiHocCreate(BaseModel):
    """Schema tao bai hoc moi."""
    tieu_de: str = Field(..., min_length=1, max_length=300)
    loai_noi_dung: str
    noi_dung: Optional[str] = None
    file_url: Optional[str] = None
    pdf_url: Optional[str] = None
    file_size_mb: Optional[Decimal] = Field(None, ge=0)
    thoi_luong_phut: Optional[int] = Field(None, ge=0)
    thu_tu: Optional[int] = Field(None, ge=0)
    phai_xem_het: bool = True
    thoi_gian_toi_thieu_giay: Optional[int] = Field(None, ge=0)

    @field_validator("loai_noi_dung")
    @classmethod
    def validate_loai(cls, v: str) -> str:
        if v not in LOAI_NOI_DUNG:
            raise ValueError(f"Loại nội dung phải thuộc: {LOAI_NOI_DUNG}")
        return v


class BaiHocUpdate(BaseModel):
    """Schema cap nhat bai hoc — tat ca fields optional."""
    tieu_de: Optional[str] = Field(None, min_length=1, max_length=300)
    loai_noi_dung: Optional[str] = None
    noi_dung: Optional[str] = None
    file_url: Optional[str] = None
    pdf_url: Optional[str] = None
    file_size_mb: Optional[Decimal] = Field(None, ge=0)
    thoi_luong_phut: Optional[int] = Field(None, ge=0)
    phai_xem_het: Optional[bool] = None
    thoi_gian_toi_thieu_giay: Optional[int] = Field(None, ge=0)

    @field_validator("loai_noi_dung")
    @classmethod
    def validate_loai(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in LOAI_NOI_DUNG:
            raise ValueError(f"Loại nội dung phải thuộc: {LOAI_NOI_DUNG}")
        return v


class TienDoResponse(BaseModel):
    """Tien do ca nhan cho 1 bai hoc."""
    trang_thai: str = "CHUA_XEM"
    thoi_gian_xem_giay: int = 0
    ngay_hoan_thanh: Optional[datetime] = None


class BaiHocResponse(BaseModel):
    """Schema response bai hoc."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    khoa_hoc_id: UUID
    thu_tu: int
    tieu_de: str
    loai_noi_dung: str
    noi_dung: Optional[str] = None
    file_url: Optional[str] = None
    pdf_url: Optional[str] = None
    file_size_mb: Optional[Decimal] = None
    thoi_luong_phut: Optional[int] = None
    phai_xem_het: Optional[bool] = True
    thoi_gian_toi_thieu_giay: Optional[int] = None
    is_active: Optional[bool] = True
    created_at: Optional[datetime] = None
    tien_do_ca_nhan: Optional[TienDoResponse] = None


class SapXepItem(BaseModel):
    """1 item trong danh sach sap xep."""
    bai_hoc_id: UUID
    thu_tu: int = Field(..., ge=0)


class SapXepRequest(BaseModel):
    """Yeu cau sap xep lai bai hoc."""
    thu_tu: list[SapXepItem]


class TienDoUpdate(BaseModel):
    """Schema cap nhat tien do hoc."""
    thoi_gian_xem_giay: int = Field(default=0, ge=0)
    hoan_thanh: bool = False
