"""Pydantic schemas cho chuyen muc dien dan."""
from datetime import datetime
from typing import Any, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class ChuyenMucCreate(BaseModel):
    ten_chuyen_muc: str = Field(..., min_length=1, max_length=200)
    mo_ta: Optional[str] = None
    icon: Optional[str] = Field(None, max_length=50)
    thu_tu: Optional[int] = None
    parent_id: Optional[UUID] = None
    chi_doc: bool = False
    yeu_cau_duyet: bool = False


class ChuyenMucUpdate(BaseModel):
    ten_chuyen_muc: Optional[str] = Field(None, min_length=1, max_length=200)
    mo_ta: Optional[str] = None
    icon: Optional[str] = Field(None, max_length=50)
    thu_tu: Optional[int] = None
    chi_doc: Optional[bool] = None
    yeu_cau_duyet: Optional[bool] = None
    is_active: Optional[bool] = None


class ChuDeMoiNhat(BaseModel):
    """Chu de moi nhat trong chuyen muc — dung cho danh sach chuyen muc."""
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    tieu_de: str
    created_at: datetime


class ChuyenMucResponse(BaseModel):
    """Response chuyen muc — co the co children (tree)."""
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    ten_chuyen_muc: str
    mo_ta: Optional[str] = None
    icon: Optional[str] = None
    thu_tu: Optional[int] = None
    parent_id: Optional[UUID] = None
    chi_doc: bool = False
    yeu_cau_duyet: bool = False
    is_active: bool = True
    created_at: datetime
    # Thong ke — fill boi service
    so_chu_de: int = 0
    so_tra_loi: int = 0
    chu_de_moi_nhat: Optional[ChuDeMoiNhat] = None
    children: list["ChuyenMucResponse"] = []
