"""
legal_service/schemas/quiz.py
================================
Pydantic schemas cho Quiz phap luat.

Cau hoi duoc nhung truc tiep vao JSONB — khong co ngan hang cau hoi rieng.
"""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator


class CauHoiInput(BaseModel):
    """Schema cho 1 cau hoi trong quiz."""

    noi_dung: str
    dap_an: list[str]  # Dung 4 dap an
    correct: int  # Index dap an dung (0-based)
    giai_thich: str = ""  # Giai thich sau khi nop bai


class QuizCreate(BaseModel):
    """Schema tao quiz moi cho van ban."""

    tieu_de: str
    thoi_gian_phut: Optional[int] = None  # NULL = khong gioi han
    diem_dat: float = 70.0  # % can dat (0-100)
    cau_hoi: list[CauHoiInput]  # 5-20 cau

    @field_validator("cau_hoi")
    @classmethod
    def validate_so_cau(cls, v: list) -> list:
        """Validate so luong cau hoi 5-20."""
        if len(v) < 5 or len(v) > 20:
            raise ValueError("So cau hoi phai tu 5 den 20")
        return v


class TraLoiInput(BaseModel):
    """Schema tra loi 1 cau hoi."""

    cau: int  # Index cau hoi (0-based)
    dap_an: int  # Index dap an chon (0-based)


class LamBaiInput(BaseModel):
    """Schema nop bai quiz."""

    tra_loi: list[TraLoiInput]


class QuizResponse(BaseModel):
    """Response schema cho quiz."""

    id: UUID
    van_ban_id: UUID
    tieu_de: str
    so_cau_hoi: int
    thoi_gian_phut: Optional[int] = None
    diem_dat: float
    # cau_hoi: list cau hoi, an "correct" khi CBCC xem
    cau_hoi: list[Any]
    is_active: bool
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class KetQuaChiTiet(BaseModel):
    """Chi tiet 1 cau tra loi trong ket qua."""

    cau: int
    tra_loi: int
    dung: bool
    giai_thich: str = ""


class KetQuaQuizResponse(BaseModel):
    """Response ket qua sau khi lam quiz."""

    id: UUID
    quiz_id: UUID
    diem: float
    so_cau_dung: int
    dat_yeu_cau: bool
    chi_tiet: list[Any]  # [{"cau": 0, "tra_loi": 3, "dung": true, "giai_thich": "..."}]
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
