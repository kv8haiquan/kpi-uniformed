"""
common_service/schemas/thong_bao.py
====================================
Pydantic schemas cho Notification Center.

Public API schemas:
  - ThongBaoResponse: chi tiet thong bao
  - ThongBaoListItem: tom tat cho danh sach
  - ThongBaoCountResponse: dem chua doc theo muc do

Internal API schemas:
  - ThongBaoCreateInternal: tao 1 thong bao
  - ThongBaoCreateBulk: tao hang loat
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Cac gia tri hop le
# ---------------------------------------------------------------------------

LOAI_THONG_BAO = {"KPI", "LMS", "FORUM", "LEGAL", "PORTAL", "HE_THONG"}
MUC_DO_THONG_BAO = {"KHAN", "QUAN_TRONG", "BINH_THUONG"}


# ---------------------------------------------------------------------------
# Public API — Response schemas
# ---------------------------------------------------------------------------


class ThongBaoResponse(BaseModel):
    """Chi tiet day du 1 thong bao."""

    id: uuid.UUID
    tieu_de: str
    noi_dung: Optional[str] = None
    loai: str
    muc_do: str
    link_url: Optional[str] = None
    doi_tuong_type: Optional[str] = None
    doi_tuong_id: Optional[uuid.UUID] = None
    da_doc: bool
    ngay_doc: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ThongBaoListItem(BaseModel):
    """Tom tat thong bao cho danh sach — khong co noi_dung day du."""

    id: uuid.UUID
    tieu_de: str
    loai: str
    muc_do: str
    link_url: Optional[str] = None
    doi_tuong_type: Optional[str] = None
    doi_tuong_id: Optional[uuid.UUID] = None
    da_doc: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class ThongBaoCountResponse(BaseModel):
    """So luong thong bao chua doc — phan loai theo muc do."""

    count: int = Field(description="Tong so thong bao chua doc")
    khan: int = Field(default=0, description="So thong bao khan cap")
    quan_trong: int = Field(default=0, description="So thong bao quan trong")
    binh_thuong: int = Field(default=0, description="So thong bao binh thuong")


# ---------------------------------------------------------------------------
# Internal API — Request schemas (module khac goi)
# ---------------------------------------------------------------------------


class ThongBaoCreateInternal(BaseModel):
    """Tao 1 thong bao — Internal API."""

    nguoi_nhan_id: uuid.UUID = Field(description="UUID cong_chuc nhan thong bao")
    tieu_de: str = Field(min_length=1, max_length=300, description="Tieu de thong bao")
    noi_dung: Optional[str] = Field(default=None, description="Noi dung chi tiet")
    loai: str = Field(description="Loai: KPI, LMS, FORUM, LEGAL, PORTAL, HE_THONG")
    muc_do: str = Field(default="BINH_THUONG", description="KHAN, QUAN_TRONG, BINH_THUONG")
    link_url: Optional[str] = Field(default=None, description="URL den doi tuong")
    doi_tuong_type: Optional[str] = Field(default=None, description="Loai doi tuong: KHOA_HOC, VAN_BAN, ...")
    doi_tuong_id: Optional[uuid.UUID] = Field(default=None, description="UUID doi tuong")


class ThongBaoCreateBulk(BaseModel):
    """Tao thong bao hang loat cho nhieu nguoi — Internal API."""

    nguoi_nhan_ids: list[uuid.UUID] = Field(
        min_length=1,
        description="Danh sach UUID cong_chuc nhan thong bao",
    )
    tieu_de: str = Field(min_length=1, max_length=300, description="Tieu de thong bao")
    noi_dung: Optional[str] = Field(default=None, description="Noi dung chi tiet")
    loai: str = Field(description="Loai: KPI, LMS, FORUM, LEGAL, PORTAL, HE_THONG")
    muc_do: str = Field(default="BINH_THUONG", description="KHAN, QUAN_TRONG, BINH_THUONG")
    link_url: Optional[str] = Field(default=None, description="URL den doi tuong")
    doi_tuong_type: Optional[str] = Field(default=None, description="Loai doi tuong")
    doi_tuong_id: Optional[uuid.UUID] = Field(default=None, description="UUID doi tuong")
