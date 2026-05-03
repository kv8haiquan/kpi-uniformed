"""Schemas Module 5 — Xin phép vắng họp."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


TRANG_THAI_VALUES = ["CHO_DUYET", "DA_DUYET", "TU_CHOI", "TU_DONG_DUYET"]
QUYET_DINH_VALUES = ["DA_DUYET", "TU_CHOI"]


class XinPhepVangCreate(BaseModel):
    cuoc_hop_id: UUID
    ly_do: str = Field(..., min_length=1)
    nguoi_du_thay_id: Optional[UUID] = None
    minio_key: Optional[str] = None  # nếu có upload đính kèm trước


class XinPhepVangDuyet(BaseModel):
    quyet_dinh: str
    ly_do_tu_choi: Optional[str] = None

    @field_validator("quyet_dinh")
    @classmethod
    def _check(cls, v: str) -> str:
        if v not in QUYET_DINH_VALUES:
            raise ValueError(f"quyet_dinh must be one of {QUYET_DINH_VALUES}")
        return v


class XinPhepVangResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    cuoc_hop_id: UUID
    cong_chuc_id: UUID
    ly_do: str
    nguoi_du_thay_id: Optional[UUID]
    minio_key: Optional[str]
    trang_thai: str
    auto_approved: bool
    nguoi_duyet_id: Optional[UUID]
    thoi_gian_duyet: Optional[datetime]
    ly_do_tu_choi: Optional[str]
    created_at: datetime
