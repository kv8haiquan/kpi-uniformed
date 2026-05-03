"""Schemas Module 4 — Điểm danh."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


HINH_THUC_VALUES = ["QR", "BAM_TAY"]
TRANG_THAI_VALUES = ["CO_MAT", "DEN_MUON", "VANG_CO_PHEP", "VANG_KHONG_PHEP"]


class QRTokenResponse(BaseModel):
    token: str
    qr_url: str
    expires_in_seconds: int


class QRSubmit(BaseModel):
    """CBCC submit token sau khi quét QR."""
    token: str


class BamTayItem(BaseModel):
    cong_chuc_id: UUID
    trang_thai: str = "CO_MAT"
    ghi_chu: Optional[str] = None

    @field_validator("trang_thai")
    @classmethod
    def _check_tt(cls, v: str) -> str:
        if v not in TRANG_THAI_VALUES:
            raise ValueError(f"trang_thai must be one of {TRANG_THAI_VALUES}")
        return v


class BamTayBulk(BaseModel):
    cuoc_hop_id: UUID
    diem_danh: list[BamTayItem] = Field(min_length=1)


class DiemDanhResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    cuoc_hop_id: UUID
    cong_chuc_id: UUID
    hinh_thuc: str
    trang_thai: str
    gio_diem_danh: Optional[datetime]
    ghi_chu: Optional[str]
    nguoi_diem_danh_id: Optional[UUID]


class DiemDanhSummary(BaseModel):
    tong_so: int
    co_mat: int
    den_muon: int
    vang_co_phep: int
    vang_khong_phep: int
    chua_diem_danh: int
    chi_tiet: list[DiemDanhResponse]
