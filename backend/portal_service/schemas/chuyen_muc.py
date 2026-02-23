"""
portal_service/schemas/chuyen_muc.py
=====================================
Schemas Pydantic cho chuyên mục bài viết portal.
"""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ChuyenMucCreate(BaseModel):
    """Tạo chuyên mục mới."""

    ten: str = Field(..., min_length=1, max_length=200, description="Tên chuyên mục")
    slug: Optional[str] = Field(
        None, max_length=200, description="Slug URL — tự sinh từ tên nếu để trống"
    )
    mo_ta: Optional[str] = Field(None, description="Mô tả chuyên mục")
    loai: Optional[str] = Field(
        "TIN_TUC", description="Loại: TIN_TUC | PHAP_LUAT | TAI_LIEU | KHAC"
    )
    thu_tu: Optional[int] = Field(0, ge=0, description="Thứ tự hiển thị (tăng dần)")


class ChuyenMucUpdate(BaseModel):
    """Cập nhật chuyên mục — tất cả field optional."""

    ten: Optional[str] = Field(None, min_length=1, max_length=200)
    slug: Optional[str] = Field(None, max_length=200)
    mo_ta: Optional[str] = None
    loai: Optional[str] = None
    thu_tu: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None


class ChuyenMucResponse(BaseModel):
    """Response đầy đủ thông tin chuyên mục."""

    id: uuid.UUID
    ten: str
    slug: str
    mo_ta: Optional[str] = None
    loai: str
    thu_tu: int
    is_active: bool
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
