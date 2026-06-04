"""
chi_tieu_service/schemas/linh_vuc.py
====================================
Pydantic schemas CRUD linh vuc cong tac.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class LinhVucCreate(BaseModel):
    ma_linh_vuc: str = Field(..., min_length=1, max_length=30)
    ten_linh_vuc: str = Field(..., min_length=1, max_length=200)
    van_ban_ke_hoach: Optional[str] = Field(None, max_length=300)
    thu_tu: int = 0


class LinhVucUpdate(BaseModel):
    ma_linh_vuc: Optional[str] = Field(None, min_length=1, max_length=30)
    ten_linh_vuc: Optional[str] = Field(None, min_length=1, max_length=200)
    van_ban_ke_hoach: Optional[str] = Field(None, max_length=300)
    thu_tu: Optional[int] = None


class LinhVucResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    ma_linh_vuc: str
    ten_linh_vuc: str
    van_ban_ke_hoach: Optional[str] = None
    thu_tu: Optional[int] = 0
    is_active: Optional[bool] = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
