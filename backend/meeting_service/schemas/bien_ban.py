"""Schemas Module 9 — Biên bản họp + Mock CKS."""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


TRANG_THAI_VALUES = ["DANG_SOAN", "TRINH_KY", "DA_KY", "CONG_BO"]


class BienBanUpdate(BaseModel):
    """PUT /cuoc-hop/{id}/bien-ban — Thư ký lưu nội dung."""
    noi_dung_json: dict[str, Any]
    noi_dung_html: Optional[str] = None


class BienBanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    cuoc_hop_id: UUID
    noi_dung_json: Optional[dict[str, Any]]
    noi_dung_html: Optional[str]
    trang_thai: str
    file_pdf_minio_key: Optional[str]
    file_docx_minio_key: Optional[str]
    is_mock_signed: bool
    qr_xac_thuc: Optional[str]
    hash_noi_dung: Optional[str]
    nguoi_soan_id: UUID
    nguoi_ky_id: Optional[UUID]
    thoi_gian_ky: Optional[datetime]
    created_at: datetime
    updated_at: datetime


class XuatBienBanResponse(BaseModel):
    minio_key: str
    url_tai: str
    file_size: int
    hash_noi_dung: Optional[str]
