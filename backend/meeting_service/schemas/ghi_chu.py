"""Schemas cho nghiệp vụ Ghi chú và chia sẻ — G5.2."""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

PHAM_VI_VALUES = ["TAT_CA", "CUA_TOI", "DUOC_CHIA_SE"]


class GhiChuCreate(BaseModel):
    tieu_de: str = Field(..., min_length=1, max_length=300)
    noi_dung: Optional[str] = None
    cuoc_hop_id: Optional[UUID] = None
    is_ghim: bool = False

    @field_validator("tieu_de")
    @classmethod
    def _tieu_de(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Tiêu đề không được để trống")
        return v


class GhiChuUpdate(BaseModel):
    """PATCH — trường vắng mặt nghĩa là giữ nguyên.

    `cuoc_hop_id = null` là gỡ ghi chú khỏi cuộc họp, khác hẳn với vắng mặt,
    nên endpoint phải dùng `exclude_unset` chứ không `exclude_none`.
    """

    tieu_de: Optional[str] = Field(default=None, min_length=1, max_length=300)
    noi_dung: Optional[str] = None
    cuoc_hop_id: Optional[UUID] = None
    is_ghim: Optional[bool] = None


class ChiaSeCreate(BaseModel):
    nguoi_nhan_ids: list[UUID] = Field(..., min_length=1, max_length=100)
    loi_nhan: Optional[str] = Field(default=None, max_length=1000)
