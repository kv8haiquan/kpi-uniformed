"""Schemas cho nghiệp vụ Đánh giá công tác chuẩn bị cuộc họp — G5.3."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from meeting_service.services.danh_gia_service import DIEM_MAX, DIEM_MIN


class DanhGiaGhi(BaseModel):
    diem: int = Field(..., ge=DIEM_MIN, le=DIEM_MAX)
    ghi_chu: Optional[str] = Field(default=None, max_length=2000)
