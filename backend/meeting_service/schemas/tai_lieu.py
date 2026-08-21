"""Schemas Module 3 — Tài liệu họp."""

from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

# Danh mục mức phân quyền nằm ở services/phan_quyen_tai_lieu.py cùng với luật
# so bậc — một chỗ duy nhất, để schema không trôi khỏi CHECK trong CSDL.
from meeting_service.services.phan_quyen_tai_lieu import (  # noqa: F401
    PHAN_QUYEN_VALUES,
)


class TaiLieuResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    cuoc_hop_id: Optional[UUID]
    ten_tai_lieu: str
    mo_ta: Optional[str]
    minio_bucket: str
    minio_key: str
    file_size: int
    mime_type: Optional[str]
    extension: Optional[str]
    phan_quyen: str
    cho_phep_tai: bool
    cho_phep_in: bool
    created_at: datetime
    created_by: UUID


class TaiLieuListItem(BaseModel):
    """Item trong list — kèm URL view sinh sẵn."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    ten_tai_lieu: str
    mo_ta: Optional[str]
    extension: Optional[str]
    file_size: int
    mime_type: Optional[str]
    phan_quyen: str
    cho_phep_tai: bool
    cho_phep_in: bool
    url_xem: Optional[str] = None  # populated từ endpoint
    created_at: datetime


class TaiLieuMetadataUpdate(BaseModel):
    """Sửa metadata (không upload lại file)."""
    ten_tai_lieu: Optional[str] = Field(None, min_length=1, max_length=500)
    mo_ta: Optional[str] = None
    phan_quyen: Optional[str] = None
    cho_phep_tai: Optional[bool] = None
    cho_phep_in: Optional[bool] = None

    @field_validator("phan_quyen")
    @classmethod
    def _check_pq(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in PHAN_QUYEN_VALUES:
            raise ValueError(f"phan_quyen must be one of {PHAN_QUYEN_VALUES}")
        return v


class TaiLieuKhoItem(BaseModel):
    """Một tài liệu trong kho chung, kèm cuộc họp mà nó thuộc về.

    Dùng cho màn hình Thư viện tài liệu (`/tai-lieu`) — người dùng duyệt cả
    kho như duyệt Drive, nên phải thấy tài liệu này của cuộc họp nào; nếu
    không thì 866 file chỉ là một danh sách tên rời rạc.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    ten_tai_lieu: str
    mo_ta: Optional[str] = None
    extension: Optional[str] = None
    file_size: int
    mime_type: Optional[str] = None
    phan_quyen: str
    cho_phep_tai: bool
    created_at: datetime

    # Ngữ cảnh cuộc họp
    cuoc_hop_id: UUID
    nguon: str
    ma_lich: Optional[str] = None
    tieu_de: str
    ngay_hop: Optional[date] = None
    duong_dan_cuoc_hop: str
