"""
legal_service/schemas/loai_van_ban.py
======================================
Pydantic schemas cho Loai Van Ban (danh muc phan loai van ban phap luat).
"""

from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class LoaiVanBanResponse(BaseModel):
    """Response schema cho loai van ban."""

    id: UUID
    ma: str
    ten: str
    thu_tu: int = 0

    model_config = ConfigDict(from_attributes=True)


class LoaiVanBanCreate(BaseModel):
    """Schema tao loai van ban moi."""

    # Ma ngan gon: LUAT, NGHI_DINH, THONG_TU, QUYET_DINH, CONG_VAN, CHI_THI, HUONG_DAN, NOI_BO
    ma: str
    ten: str
    thu_tu: int = 0


class LoaiVanBanUpdate(BaseModel):
    """Schema cap nhat loai van ban — tat ca optional."""

    ten: Optional[str] = None
    thu_tu: Optional[int] = None
