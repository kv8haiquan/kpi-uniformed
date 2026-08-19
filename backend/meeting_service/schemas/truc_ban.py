"""Schemas cho nghiệp vụ Trực ban — G4.7, G4.8."""

from __future__ import annotations

from datetime import date
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from meeting_service.services.truc_ban_service import (
    CA_TRUC_VALUES,
    LOAI_TRUC_VALUES,
)


class TrucBanCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ngay_truc: date
    tru_so_id: UUID
    ho_ten: str = Field(..., min_length=1, max_length=100)
    chuc_vu: Optional[str] = Field(default=None, max_length=100)
    so_dien_thoai: Optional[str] = Field(default=None, max_length=20)
    cong_chuc_id: Optional[UUID] = None
    loai_truc: str = "CUOI_TUAN"
    ca_truc: str = "CA_NGAY"
    ghi_chu: Optional[str] = None

    @field_validator("loai_truc")
    @classmethod
    def _loai(cls, v: str) -> str:
        if v not in LOAI_TRUC_VALUES:
            raise ValueError(f"loai_truc phải thuộc {LOAI_TRUC_VALUES}")
        return v

    @field_validator("ca_truc")
    @classmethod
    def _ca(cls, v: str) -> str:
        if v not in CA_TRUC_VALUES:
            raise ValueError(f"ca_truc phải thuộc {CA_TRUC_VALUES}")
        return v


class TrucBanUpdate(BaseModel):
    ho_ten: Optional[str] = Field(default=None, min_length=1, max_length=100)
    chuc_vu: Optional[str] = Field(default=None, max_length=100)
    so_dien_thoai: Optional[str] = Field(default=None, max_length=20)
    cong_chuc_id: Optional[UUID] = None
    loai_truc: Optional[str] = None
    ca_truc: Optional[str] = None
    ghi_chu: Optional[str] = None

    @field_validator("loai_truc")
    @classmethod
    def _loai(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in LOAI_TRUC_VALUES:
            raise ValueError(f"loai_truc phải thuộc {LOAI_TRUC_VALUES}")
        return v

    @field_validator("ca_truc")
    @classmethod
    def _ca(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in CA_TRUC_VALUES:
            raise ValueError(f"ca_truc phải thuộc {CA_TRUC_VALUES}")
        return v


class TrucBanNop(BaseModel):
    ngay_truc: date
    tru_so_id: UUID


class DongNhapExcel(BaseModel):
    """Một dòng sau khi đọc từ Excel, kèm kết quả kiểm tra.

    Dòng hỏng KHÔNG chặn cả file — báo rõ dòng nào hỏng vì sao rồi cho người
    dùng quyết định có ghi phần còn lại hay không.
    """
    dong: int
    ngay_truc: Optional[date] = None
    ma_tru_so: Optional[str] = None
    tru_so_id: Optional[UUID] = None
    ten_tru_so: Optional[str] = None
    ho_ten: Optional[str] = None
    chuc_vu: Optional[str] = None
    so_dien_thoai: Optional[str] = None
    ca_truc: str = "CA_NGAY"
    loai_truc: str = "CUOI_TUAN"
    ghi_chu: Optional[str] = None
    hop_le: bool = True
    loi: list[str] = Field(default_factory=list)


class KetQuaXemTruoc(BaseModel):
    tong_dong: int
    so_hop_le: int
    so_loi: int
    dong: list[DongNhapExcel]


class YeuCauGhiNhap(BaseModel):
    """Ghi những dòng đã xem trước. Chỉ nhận dòng hợp lệ."""
    dong: list[DongNhapExcel]
    ghi_de: bool = Field(
        default=False,
        description="Xoá lịch trực cũ của các (ngày, trụ sở) có trong file "
                    "trước khi ghi. Mặc định là thêm vào.")
