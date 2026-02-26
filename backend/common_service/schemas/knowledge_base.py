"""
common_service/schemas/knowledge_base.py
=========================================
Pydantic schemas cho Knowledge Base (SOP/FAQ).

Schemas:
  - KBCreate: tao moi
  - KBUpdate: cap nhat (tat ca optional)
  - KBResponse: chi tiet day du
  - KBListItem: tom tat cho danh sach
  - KBDoiTrangThai: doi trang thai
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field

from .file_storage import UserBrief


# ---------------------------------------------------------------------------
# Cac gia tri hop le
# ---------------------------------------------------------------------------

LOAI_KB = {"SOP", "FAQ"}
TRANG_THAI_KB = {"NHAP", "CHO_DUYET", "DA_XUAT_BAN", "CAN_CAP_NHAT"}

# Workflow transitions: trang_thai_hien_tai -> set(trang_thai_moi cho phep)
KB_WORKFLOW = {
    "NHAP": {"CHO_DUYET"},
    "CHO_DUYET": {"DA_XUAT_BAN", "NHAP"},
    "DA_XUAT_BAN": {"CAN_CAP_NHAT"},
    "CAN_CAP_NHAT": {"NHAP"},
}


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


class KBCreate(BaseModel):
    """Tao Knowledge Base moi."""

    loai: str = Field(description="SOP hoac FAQ")
    tieu_de: str = Field(min_length=1, max_length=500, description="Tieu de bai viet")
    noi_dung: str = Field(min_length=1, description="Noi dung HTML/Markdown")
    chuyen_de: list[str] = Field(default=[], description="Danh sach chuyen de")
    tags: list[str] = Field(default=[], description="Danh sach tags")
    van_ban_lien_quan: Optional[list[uuid.UUID]] = Field(
        default=None, description="Danh sach UUID van ban phap luat lien quan"
    )
    chu_de_forum_lien_quan: Optional[list[uuid.UUID]] = Field(
        default=None, description="Danh sach UUID chu de forum lien quan"
    )


class KBUpdate(BaseModel):
    """Cap nhat Knowledge Base — tat ca optional."""

    tieu_de: Optional[str] = Field(default=None, min_length=1, max_length=500)
    noi_dung: Optional[str] = Field(default=None, min_length=1)
    chuyen_de: Optional[list[str]] = None
    tags: Optional[list[str]] = None
    van_ban_lien_quan: Optional[list[uuid.UUID]] = None
    chu_de_forum_lien_quan: Optional[list[uuid.UUID]] = None


class KBDoiTrangThai(BaseModel):
    """Doi trang thai Knowledge Base."""

    trang_thai_moi: str = Field(description="NHAP, CHO_DUYET, DA_XUAT_BAN, CAN_CAP_NHAT")


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class KBListItem(BaseModel):
    """Tom tat KB cho danh sach — khong co noi_dung day du."""

    id: uuid.UUID
    loai: str
    tieu_de: str
    chuyen_de: Any = []
    tags: Any = []
    trang_thai: str
    phien_ban: int
    chu_so_huu: Optional[UserBrief] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class KBResponse(BaseModel):
    """Chi tiet day du Knowledge Base."""

    id: uuid.UUID
    loai: str
    tieu_de: str
    noi_dung: str
    chuyen_de: Any = []
    tags: Any = []
    chu_so_huu: Optional[UserBrief] = None
    trang_thai: str
    van_ban_lien_quan: Optional[Any] = None
    chu_de_forum_lien_quan: Optional[Any] = None
    phien_ban: int
    ngay_cap_nhat_cuoi: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    is_deleted: bool

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Internal API schemas
# ---------------------------------------------------------------------------


class KBCapNhatVanBanRequest(BaseModel):
    """Request tu Legal module khi van ban thay doi."""

    van_ban_id: uuid.UUID = Field(description="UUID van ban da thay doi")
