"""
lms_service/schemas/linh_vuc.py
===============================
Pydantic schemas cho CRUD linh vuc nghiep vu.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class LinhVucCreate(BaseModel):
    """Schema tao linh vuc moi."""
    ma_linh_vuc: str = Field(..., min_length=1, max_length=50)
    ten_linh_vuc: str = Field(..., min_length=1, max_length=200)
    mo_ta: Optional[str] = None
    thu_tu: int = 0


class LinhVucUpdate(BaseModel):
    """Schema cap nhat linh vuc — tat ca optional."""
    ma_linh_vuc: Optional[str] = Field(None, min_length=1, max_length=50)
    ten_linh_vuc: Optional[str] = Field(None, min_length=1, max_length=200)
    mo_ta: Optional[str] = None
    thu_tu: Optional[int] = None


class LinhVucResponse(BaseModel):
    """Schema response linh vuc."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    ma_linh_vuc: str
    ten_linh_vuc: str
    mo_ta: Optional[str] = None
    thu_tu: Optional[int] = 0
    is_active: Optional[bool] = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
