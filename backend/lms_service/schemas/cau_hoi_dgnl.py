"""
lms_service/schemas/cau_hoi_dgnl.py
===================================
Pydantic schemas cho ngan hang cau hoi DGNL.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


LOAI_CAU_HOI = ["TRAC_NGHIEM_1", "TRAC_NGHIEM_NHIEU", "DUNG_SAI", "TU_LUAN"]
DO_KHO = ["DE", "TRUNG_BINH", "KHO"]


class CauHoiDgnlCreate(BaseModel):
    """Schema tao cau hoi DGNL."""
    linh_vuc_id: UUID  # BAT BUOC
    noi_dung: str = Field(..., min_length=1)
    giai_thich: Optional[str] = None
    loai: str
    dap_an: dict
    diem: Decimal = Field(default=Decimal("1.0"), ge=0)
    do_kho: str = Field(default="TRUNG_BINH")

    @field_validator("loai")
    @classmethod
    def validate_loai(cls, v: str) -> str:
        if v not in LOAI_CAU_HOI:
            raise ValueError(f"Loại câu hỏi phải thuộc: {LOAI_CAU_HOI}")
        return v

    @field_validator("do_kho")
    @classmethod
    def validate_do_kho(cls, v: str) -> str:
        if v not in DO_KHO:
            raise ValueError(f"Độ khó phải thuộc: {DO_KHO}")
        return v


class CauHoiDgnlUpdate(BaseModel):
    """Schema cap nhat cau hoi DGNL."""
    linh_vuc_id: Optional[UUID] = None
    noi_dung: Optional[str] = Field(None, min_length=1)
    giai_thich: Optional[str] = None
    loai: Optional[str] = None
    dap_an: Optional[dict] = None
    diem: Optional[Decimal] = Field(None, ge=0)
    do_kho: Optional[str] = None

    @field_validator("loai")
    @classmethod
    def validate_loai(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in LOAI_CAU_HOI:
            raise ValueError(f"Loại câu hỏi phải thuộc: {LOAI_CAU_HOI}")
        return v

    @field_validator("do_kho")
    @classmethod
    def validate_do_kho(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in DO_KHO:
            raise ValueError(f"Độ khó phải thuộc: {DO_KHO}")
        return v


class CauHoiDgnlXoaNhieu(BaseModel):
    """Schema xoa nhieu cau hoi DGNL (soft delete).

    Hai che do:
      - Truyen danh sach `ids`     -> xoa dung cac cau hoi da chon.
      - `tat_ca_theo_bo_loc=True`  -> xoa TOAN BO cau hoi khop bo loc
                                      (linh_vuc_id / do_kho / loai / search).
                                      Dung de clear ca mot linh vuc.
    """
    ids: Optional[list[UUID]] = None
    tat_ca_theo_bo_loc: bool = False
    linh_vuc_id: Optional[UUID] = None
    do_kho: Optional[str] = None
    loai: Optional[str] = None
    search: Optional[str] = None


class CauHoiDgnlResponse(BaseModel):
    """Schema response cau hoi DGNL."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    linh_vuc_id: UUID
    noi_dung: str
    giai_thich: Optional[str] = None
    loai: str
    dap_an: dict
    diem: Optional[Decimal] = Decimal("1.0")
    do_kho: Optional[str] = "TRUNG_BINH"
    nguoi_tao_id: Optional[UUID] = None
    is_active: Optional[bool] = True
    created_at: Optional[datetime] = None
    # JOIN fields
    linh_vuc_ten: Optional[str] = None
    nguoi_tao_ho_ten: Optional[str] = None


class ThongKeNganHang(BaseModel):
    """Thong ke ngan hang cau hoi DGNL theo linh vuc + do kho."""
    linh_vuc_id: str
    linh_vuc_ten: str
    so_cau_de: int = 0
    so_cau_trung_binh: int = 0
    so_cau_kho: int = 0
    tong: int = 0
