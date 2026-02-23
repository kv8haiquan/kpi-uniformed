"""
legal_service/schemas/van_ban.py
==================================
Pydantic schemas cho Van Ban phap luat — phan complex nhat.

Workflow: NHAP → CHO_DUYET → DA_DUYET → DA_XUAT_BAN
Trang thai hieu luc: CON_HIEU_LUC | HET_HIEU_LUC | BI_THAY_THE | DANG_SUA_DOI
Muc do: KHAN | QUAN_TRONG | BINH_THUONG
"""

from datetime import date, datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

# ---------------------------------------------------------------------------
# Input schemas
# ---------------------------------------------------------------------------


class VanBanLienKetInput(BaseModel):
    """Input khi tao/cap nhat lien ket van ban."""

    van_ban_lien_quan_id: UUID
    # THAY_THE | BO_SUNG | HUONG_DAN | LIEN_QUAN
    loai_lien_ket: str


class VanBanCreate(BaseModel):
    """Schema tao van ban moi."""

    so_hieu: str = Field(..., min_length=1, max_length=100, description="So hieu van ban, VD: 335/2025/ND-CP")
    trich_yeu: str = Field(..., min_length=1, max_length=500, description="Trich yeu noi dung van ban")
    loai_van_ban_id: UUID
    co_quan_ban_hanh: Optional[str] = None
    ngay_ban_hanh: Optional[date] = None
    ngay_hieu_luc: Optional[date] = None
    ngay_het_hieu_luc: Optional[date] = None
    trang_thai_hieu_luc: str = "CON_HIEU_LUC"
    van_ban_thay_the_id: Optional[UUID] = None
    tom_tat: Optional[str] = None
    noi_dung_html: Optional[str] = None
    file_goc_url: Optional[str] = None
    # JSONB lists
    chuyen_de: list = []
    doi_tuong_ap_dung: list = []
    tags: list = []
    # Dac trung HQKV8
    diem_moi: Optional[str] = None
    viec_can_lam: Optional[str] = None
    muc_do: str = "BINH_THUONG"
    bat_buoc_doc: bool = False
    han_xac_nhan: Optional[date] = None
    # Lien ket voi van ban khac
    van_ban_lien_ket: list[VanBanLienKetInput] = []


class VanBanUpdate(BaseModel):
    """Schema cap nhat van ban — tat ca optional."""

    so_hieu: Optional[str] = None
    trich_yeu: Optional[str] = None
    loai_van_ban_id: Optional[UUID] = None
    co_quan_ban_hanh: Optional[str] = None
    ngay_ban_hanh: Optional[date] = None
    ngay_hieu_luc: Optional[date] = None
    ngay_het_hieu_luc: Optional[date] = None
    trang_thai_hieu_luc: Optional[str] = None
    van_ban_thay_the_id: Optional[UUID] = None
    tom_tat: Optional[str] = None
    noi_dung_html: Optional[str] = None
    file_goc_url: Optional[str] = None
    chuyen_de: Optional[list] = None
    doi_tuong_ap_dung: Optional[list] = None
    tags: Optional[list] = None
    diem_moi: Optional[str] = None
    viec_can_lam: Optional[str] = None
    muc_do: Optional[str] = None
    bat_buoc_doc: Optional[bool] = None
    han_xac_nhan: Optional[date] = None
    van_ban_lien_ket: Optional[list[VanBanLienKetInput]] = None


class TrangThaiDuyetUpdate(BaseModel):
    """Schema cap nhat trang thai duyet (workflow transition)."""

    # Cac gia tri hop le theo WORKFLOW_TRANSITIONS
    trang_thai_duyet: str = Field(
        ...,
        pattern="^(NHAP|CHO_DUYET|DA_DUYET|DA_XUAT_BAN)$",
        description="Trang thai duyet moi: NHAP | CHO_DUYET | DA_DUYET | DA_XUAT_BAN",
    )
    ghi_chu: Optional[str] = None


# ---------------------------------------------------------------------------
# Response schemas — brief/summary
# ---------------------------------------------------------------------------


class LoaiVanBanBrief(BaseModel):
    """Thong tin ngan gon loai van ban trong response."""

    id: UUID
    ma: str
    ten: str

    model_config = ConfigDict(from_attributes=True)


class CongChucBrief(BaseModel):
    """Thong tin ngan gon cong chuc trong response."""

    id: UUID
    ho_ten: str
    don_vi: Optional[str] = None  # ten_don_vi

    model_config = ConfigDict(from_attributes=True)


class VanBanLienKetDetail(BaseModel):
    """Chi tiet van ban lien ket."""

    van_ban_lien_quan_id: UUID
    so_hieu: str
    trich_yeu: str
    loai_lien_ket: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class XacNhanInfo(BaseModel):
    """Thong tin xac nhan doc cua user hien tai."""

    da_doc: bool = False
    ngay_doc: Optional[datetime] = None
    da_xac_nhan: bool = False
    ngay_xac_nhan: Optional[datetime] = None


class QuizBrief(BaseModel):
    """Thong tin ngan gon quiz."""

    id: UUID
    tieu_de: str
    so_cau_hoi: int
    thoi_gian_phut: Optional[int] = None
    diem_dat: float = 70.0
    is_active: bool = True

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Response schemas — list item
# ---------------------------------------------------------------------------


class VanBanListItem(BaseModel):
    """Schema cho item trong danh sach van ban (API 3.1)."""

    id: UUID
    so_hieu: str
    trich_yeu: str
    loai_van_ban: Optional[LoaiVanBanBrief] = None
    co_quan_ban_hanh: Optional[str] = None
    ngay_ban_hanh: Optional[date] = None
    ngay_hieu_luc: Optional[date] = None
    trang_thai_hieu_luc: str
    trang_thai_duyet: str
    muc_do: str
    bat_buoc_doc: bool
    han_xac_nhan: Optional[date] = None
    ngay_xuat_ban: Optional[datetime] = None
    tom_tat: Optional[str] = None
    diem_moi: Optional[str] = None
    # Trang thai doc cua user hien tai
    da_doc: bool = False
    da_xac_nhan: bool = False
    # Co diem moi khong (de UI hien thi badge)
    co_diem_moi: bool = False

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Response schemas — full detail
# ---------------------------------------------------------------------------


class VanBanDetail(BaseModel):
    """Schema day du cho chi tiet van ban (API 3.3)."""

    id: UUID
    so_hieu: str
    trich_yeu: str
    loai_van_ban: Optional[LoaiVanBanBrief] = None
    co_quan_ban_hanh: Optional[str] = None
    ngay_ban_hanh: Optional[date] = None
    ngay_hieu_luc: Optional[date] = None
    ngay_het_hieu_luc: Optional[date] = None
    trang_thai_hieu_luc: str
    van_ban_thay_the_id: Optional[UUID] = None
    tom_tat: Optional[str] = None
    noi_dung_html: Optional[str] = None
    file_goc_url: Optional[str] = None
    chuyen_de: list = []
    doi_tuong_ap_dung: list = []
    tags: list = []
    diem_moi: Optional[str] = None
    viec_can_lam: Optional[str] = None
    muc_do: str
    bat_buoc_doc: bool
    han_xac_nhan: Optional[date] = None
    trang_thai_duyet: str
    ngay_xuat_ban: Optional[datetime] = None
    phien_ban: int = 1
    nguoi_nhap: Optional[dict] = None
    nguoi_duyet: Optional[dict] = None
    van_ban_lien_ket: list[VanBanLienKetDetail] = []
    xac_nhan: Optional[XacNhanInfo] = None
    quizzes: list[QuizBrief] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
