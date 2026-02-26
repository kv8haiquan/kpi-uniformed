"""
common_service/schemas/file_storage.py
=======================================
Pydantic schemas cho File Storage.

Schemas:
  - UserBrief: thong tin nguoi dung tom tat (dung chung)
  - FileUploadResponse: ket qua upload file
  - FileInfoResponse: thong tin chi tiet file + nguoi tai len
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Cac gia tri hop le
# ---------------------------------------------------------------------------

ALLOWED_MODULES = {"LMS", "FORUM", "LEGAL", "PORTAL"}


# ---------------------------------------------------------------------------
# Sub-schemas
# ---------------------------------------------------------------------------


class UserBrief(BaseModel):
    """Thong tin nguoi dung tom tat — dung chung cho nhieu response."""

    id: uuid.UUID
    ma_cc: str
    ho_ten: str

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class FileUploadResponse(BaseModel):
    """Ket qua upload file — tra ve ngay sau khi upload thanh cong."""

    id: uuid.UUID
    file_url: str
    file_name: str
    file_size_bytes: Optional[int] = None
    mime_type: Optional[str] = None
    module: str
    created_at: datetime

    model_config = {"from_attributes": True}


class FileInfoResponse(BaseModel):
    """Thong tin chi tiet file — bao gom nguoi tai len."""

    id: uuid.UUID
    file_name: str
    file_path: str
    file_url: str
    file_size_bytes: Optional[int] = None
    mime_type: Optional[str] = None
    module: str
    doi_tuong_type: Optional[str] = None
    doi_tuong_id: Optional[uuid.UUID] = None
    nguoi_tai_len: Optional[UserBrief] = None
    created_at: datetime
    is_deleted: bool

    model_config = {"from_attributes": True}
