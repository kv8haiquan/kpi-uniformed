"""
lms_service/schemas/vi_tri_viec_lam.py
======================================
Pydantic schemas cho CRUD vi tri viec lam.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ViTriViecLamCreate(BaseModel):
    """Schema tao vi tri viec lam moi."""
    ma_vi_tri: str = Field(..., min_length=1, max_length=50)
    ten_vi_tri: str = Field(..., min_length=1, max_length=200)
    mo_ta: Optional[str] = None
    linh_vuc_ids: Optional[list[UUID]] = []
    thu_tu: int = 0


class ViTriViecLamUpdate(BaseModel):
    """Schema cap nhat vi tri viec lam — tat ca optional."""
    ma_vi_tri: Optional[str] = Field(None, min_length=1, max_length=50)
    ten_vi_tri: Optional[str] = Field(None, min_length=1, max_length=200)
    mo_ta: Optional[str] = None
    linh_vuc_ids: Optional[list[UUID]] = None
    thu_tu: Optional[int] = None


class ViTriViecLamResponse(BaseModel):
    """Schema response vi tri viec lam."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    ma_vi_tri: str
    ten_vi_tri: str
    mo_ta: Optional[str] = None
    linh_vuc_ids: Optional[list] = []
    thu_tu: Optional[int] = 0
    is_active: Optional[bool] = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
