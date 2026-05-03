"""Schemas Module 10 — Kết luận + Tiến độ."""

from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


MUC_UU_TIEN_VALUES = ["CAO", "TRUNG_BINH", "THAP"]
TRANG_THAI_VALUES = ["CHUA_BAT_DAU", "DANG_LAM", "HOAN_THANH", "TRE_HAN", "HUY"]


class KetLuanCreate(BaseModel):
    noi_dung: str = Field(..., min_length=1)
    nguoi_phu_trach_id: UUID
    don_vi_phu_trach_id: Optional[UUID] = None
    han_hoan_thanh: Optional[date] = None
    muc_uu_tien: str = Field(default="TRUNG_BINH")

    @field_validator("muc_uu_tien")
    @classmethod
    def _check_uu_tien(cls, v: str) -> str:
        if v not in MUC_UU_TIEN_VALUES:
            raise ValueError(f"muc_uu_tien must be one of {MUC_UU_TIEN_VALUES}")
        return v


class KetLuanUpdate(BaseModel):
    noi_dung: Optional[str] = None
    nguoi_phu_trach_id: Optional[UUID] = None
    don_vi_phu_trach_id: Optional[UUID] = None
    han_hoan_thanh: Optional[date] = None
    muc_uu_tien: Optional[str] = None
    trang_thai: Optional[str] = None

    @field_validator("muc_uu_tien")
    @classmethod
    def _check_uu_tien(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in MUC_UU_TIEN_VALUES:
            raise ValueError(f"muc_uu_tien must be one of {MUC_UU_TIEN_VALUES}")
        return v

    @field_validator("trang_thai")
    @classmethod
    def _check_tt(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in TRANG_THAI_VALUES:
            raise ValueError(f"trang_thai must be one of {TRANG_THAI_VALUES}")
        return v


class TienDoCreate(BaseModel):
    phan_tram_sau: int = Field(..., ge=0, le=100)
    mo_ta: str = Field(..., min_length=1)
    file_minh_chung_minio_key: Optional[str] = None


class KetLuanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    cuoc_hop_id: UUID
    noi_dung: str
    nguoi_phu_trach_id: UUID
    don_vi_phu_trach_id: Optional[UUID]
    han_hoan_thanh: Optional[date]
    muc_uu_tien: str
    tien_do_phan_tram: int
    trang_thai: str
    created_at: datetime
    updated_at: datetime


class TienDoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    ket_luan_id: UUID
    mo_ta: str
    phan_tram_truoc: Optional[int]
    phan_tram_sau: int
    file_minh_chung_minio_key: Optional[str]
    nguoi_cap_nhat_id: UUID
    created_at: datetime


class DashboardCaNhan(BaseModel):
    so_cuoc_hop_thang_nay: int
    so_cuoc_hop_tham_du: int
    so_lan_vang: int
    ty_le_tham_du: float  # %
    nhiem_vu_dang_lam: int
    nhiem_vu_qua_han: int


class DashboardDonVi(BaseModel):
    don_vi_id: UUID
    so_cuoc_hop: int
    so_nhiem_vu_giao: int
    so_nhiem_vu_hoan_thanh: int
    so_nhiem_vu_qua_han: int
    ty_le_hoan_thanh: float  # %
