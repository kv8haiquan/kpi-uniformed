"""
lms_service/schemas/chuyen_de.py
================================
Pydantic schemas cho CRUD chuyen de dao tao.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ChuyenDeCreate(BaseModel):
    """Schema tao chuyen de moi."""
    ma_chuyen_de: str = Field(..., min_length=1, max_length=50)
    ten_chuyen_de: str = Field(..., min_length=1, max_length=200)
    mo_ta: Optional[str] = None
    thu_tu: int = Field(default=0, ge=0)


class ChuyenDeUpdate(BaseModel):
    """Schema cap nhat chuyen de — tat ca fields optional."""
    ma_chuyen_de: Optional[str] = Field(None, min_length=1, max_length=50)
    ten_chuyen_de: Optional[str] = Field(None, min_length=1, max_length=200)
    mo_ta: Optional[str] = None
    thu_tu: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None


class ChuyenDeResponse(BaseModel):
    """Schema response chuyen de."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    ma_chuyen_de: str
    ten_chuyen_de: str
    mo_ta: Optional[str] = None
    anh_dai_dien: Optional[str] = None
    thu_tu: Optional[int] = 0
    is_active: Optional[bool] = True
    created_by: Optional[UUID] = None
    created_at: Optional[datetime] = None
    so_khoa_hoc: int = 0
