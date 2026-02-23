"""
lms_service/schemas/cau_hoi.py
==============================
Pydantic schemas cho CRUD cau hoi (ngan hang cau hoi).
"""

from datetime import datetime
from decimal import Decimal
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


LOAI_CAU_HOI = ["TRAC_NGHIEM_1", "TRAC_NGHIEM_NHIEU", "DUNG_SAI", "GHEP_DOI", "TU_LUAN"]
DO_KHO = ["DE", "TRUNG_BINH", "KHO"]


class CauHoiCreate(BaseModel):
    """Schema tao cau hoi moi."""
    khoa_hoc_id: Optional[UUID] = None
    chuyen_de_id: Optional[UUID] = None
    bai_kiem_tra_id: Optional[UUID] = None
    noi_dung: str = Field(..., min_length=1)
    giai_thich: Optional[str] = None
    loai: str
    dap_an: dict
    diem: Decimal = Field(default=Decimal("1.0"), ge=0)
    do_kho: str = Field(default="TRUNG_BINH")
    van_ban_lien_quan_ids: Optional[list] = None

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


class CauHoiUpdate(BaseModel):
    """Schema cap nhat cau hoi — tat ca optional."""
    noi_dung: Optional[str] = Field(None, min_length=1)
    giai_thich: Optional[str] = None
    loai: Optional[str] = None
    dap_an: Optional[dict] = None
    diem: Optional[Decimal] = Field(None, ge=0)
    do_kho: Optional[str] = None
    khoa_hoc_id: Optional[UUID] = None
    van_ban_lien_quan_ids: Optional[list] = None

    @field_validator("loai")
    @classmethod
    def validate_loai(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in LOAI_CAU_HOI:
            raise ValueError(f"Loại câu hỏi phải thuộc: {LOAI_CAU_HOI}")
        return v


class CauHoiResponse(BaseModel):
    """Schema response cau hoi (day du, cho quan tri)."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    khoa_hoc_id: Optional[UUID] = None
    chuyen_de_id: Optional[UUID] = None
    bai_kiem_tra_id: Optional[UUID] = None
    noi_dung: str
    giai_thich: Optional[str] = None
    loai: str
    dap_an: dict
    diem: Optional[Decimal] = Decimal("1.0")
    do_kho: Optional[str] = "TRUNG_BINH"
    van_ban_lien_quan_ids: Optional[list] = None
    nguoi_tao_id: Optional[UUID] = None
    is_active: Optional[bool] = True
    created_at: Optional[datetime] = None
    # JOIN fields
    khoa_hoc_ten: Optional[str] = None
    chuyen_de_ten: Optional[str] = None
    bai_kiem_tra_ten: Optional[str] = None
    nguoi_tao_ho_ten: Optional[str] = None


class CauHoiForExam(BaseModel):
    """Schema cau hoi cho thi sinh — KHONG co dap an dung."""
    id: UUID
    thu_tu: Optional[int] = None
    noi_dung: str
    loai: str
    diem: Optional[Decimal] = Decimal("1.0")
    lua_chon: Optional[list] = None  # Chi cac lua chon, KHONG co dap_an_dung
