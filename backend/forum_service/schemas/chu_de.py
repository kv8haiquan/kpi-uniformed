"""Pydantic schemas cho chu de / thread."""
from datetime import datetime
from typing import Any, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class UserBrief(BaseModel):
    """Thong tin user tom tat — dung khi tra ve kem entity."""
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    ma_cc: Optional[str] = None
    ho_ten: str
    chuc_vu: Optional[str] = None
    don_vi_ten: Optional[str] = None  # tu CongChucRef.don_vi.ten_don_vi


class ChuDeCreate(BaseModel):
    chuyen_muc_id: UUID
    tieu_de: str = Field(..., min_length=10, max_length=500)
    noi_dung: str = Field(..., min_length=30)
    tags: list[str] = Field(default_factory=list, max_length=5)
    van_ban_lien_quan: Optional[list[UUID]] = None
    sop_lien_quan: Optional[list[UUID]] = None


class ChuDeUpdate(BaseModel):
    tieu_de: Optional[str] = Field(None, min_length=10, max_length=500)
    noi_dung: Optional[str] = Field(None, min_length=30)
    tags: Optional[list[str]] = Field(None, max_length=5)
    van_ban_lien_quan: Optional[list[UUID]] = None
    sop_lien_quan: Optional[list[UUID]] = None


class HanhDongChuDe(BaseModel):
    """Schema cho PATCH hanh-dong (ghim/khoa/duyet/an)."""
    hanh_dong: str = Field(..., pattern="^(GHIM|BO_GHIM|KHOA|MO_KHOA|AN|DUYET)$")
    ly_do: Optional[str] = None


class ChonDapAnChuan(BaseModel):
    """Schema cho PATCH dap-an-chuan."""
    tra_loi_id: UUID


class ChuDeListItem(BaseModel):
    """Response item trong danh sach chu de."""
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    tieu_de: str
    noi_dung_tom_tat: str = ""
    tags: list[str] = []
    tac_gia: Optional[UserBrief] = None
    trang_thai: str = "MO"
    is_ghim: bool = False
    is_khoa: bool = False
    so_luot_xem: int = 0
    so_tra_loi: int = 0
    so_upvote: int = 0
    co_dap_an_chuan: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class TraLoiInChuDe(BaseModel):
    """Tra loi nested trong chi tiet chu de."""
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    noi_dung: str
    tac_gia: Optional[UserBrief] = None
    is_dap_an_chuan: bool = False
    is_an: bool = False
    so_upvote: int = 0
    da_upvote: Optional[bool] = None  # fill boi service
    can_cu_phap_ly: Optional[list[Any]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    children: list["TraLoiInChuDe"] = []


class ChuDeDetail(BaseModel):
    """Response chi tiet chu de."""
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    chuyen_muc_id: UUID
    tieu_de: str
    noi_dung: str
    tags: list[str] = []
    tac_gia: Optional[UserBrief] = None
    trang_thai: str = "MO"
    is_ghim: bool = False
    is_khoa: bool = False
    so_luot_xem: int = 0
    so_tra_loi: int = 0
    so_upvote: int = 0
    tra_loi_chuan_id: Optional[UUID] = None
    van_ban_lien_quan: Optional[list[Any]] = None
    sop_lien_quan: Optional[list[Any]] = None
    nguoi_duyet_id: Optional[UUID] = None
    ngay_duyet: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    # Fill boi service cho user hien tai
    da_upvote: Optional[bool] = None
    da_theo_doi: Optional[bool] = None
    co_dap_an_chuan: bool = False
    # Danh sach tra loi nested
    tra_loi: list[TraLoiInChuDe] = []
