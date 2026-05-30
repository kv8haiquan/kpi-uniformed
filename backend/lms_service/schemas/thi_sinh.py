"""
lms_service/schemas/thi_sinh.py
===============================
Pydantic schemas cho thi sinh DGNL: giao thi sinh, lam bai, nop bai, ket qua.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# ============================================================
# Giao thi sinh
# ============================================================

class ThiSinhItem(BaseModel):
    """1 thi sinh trong batch."""
    cong_chuc_id: UUID
    vi_tri_id: UUID


class ThiSinhBatchCreate(BaseModel):
    """Giao thi sinh theo danh sach."""
    danh_sach: Optional[list[ThiSinhItem]] = None
    # Hoac giao theo don vi
    don_vi_ids: Optional[list[UUID]] = None
    vi_tri_id: Optional[UUID] = None  # Bat buoc khi giao theo don_vi


class LichSuThiSummary(BaseModel):
    """Summary 1 lan thi de hien thi trong expand panel."""
    lan: int
    diem: float = 0
    xep_loai: Optional[str] = None
    so_cau_dung: Optional[int] = None
    so_cau_sai: Optional[int] = None
    tong_so_cau: Optional[int] = None
    thoi_gian_bat_dau: Optional[str] = None
    thoi_gian_nop: Optional[str] = None
    thoi_gian_lam_giay: Optional[int] = None
    has_chi_tiet: bool = False  # FE dung de enable/disable nut "Xem bai lam"


class ThiSinhResponse(BaseModel):
    """Response 1 thi sinh."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    ky_thi_id: UUID
    cong_chuc_id: UUID
    vi_tri_id: UUID
    trang_thai: Optional[str] = "CHUA_THI"
    lan_thi_hien_tai: Optional[int] = 0
    diem_tong: Optional[Decimal] = None
    xep_loai: Optional[str] = None
    so_cau_dung: Optional[int] = None
    so_cau_sai: Optional[int] = None
    tong_so_cau: Optional[int] = None
    diem_theo_linh_vuc: Optional[dict] = None
    thoi_gian_bat_dau: Optional[datetime] = None
    thoi_gian_nop: Optional[datetime] = None
    thoi_gian_lam_giay: Optional[int] = None
    created_at: Optional[datetime] = None
    # JOIN fields
    ho_ten: Optional[str] = None
    ma_cc: Optional[str] = None
    don_vi_ten: Optional[str] = None
    vi_tri_ten: Optional[str] = None
    # Lich su cac lan thi truoc (summary)
    lich_su_thi: Optional[list[LichSuThiSummary]] = None


# ============================================================
# Lam bai / Nop bai
# ============================================================

class CauTraLoi(BaseModel):
    """1 cau tra loi cua thi sinh."""
    cau_hoi_id: UUID
    tra_loi: Optional[dict] = None  # Cau truc giong dap_an cua cau_hoi


class NopBaiRequest(BaseModel):
    """Body nop bai thi."""
    cau_tra_loi: list[CauTraLoi] = []


class LuuNhapRequest(BaseModel):
    """Body luu nhap (auto-save moi 30s)."""
    cau_tra_loi: list[CauTraLoi] = []
    so_lan_vi_pham: int = 0


# ============================================================
# Ket qua
# ============================================================

class DiemLinhVuc(BaseModel):
    """Diem theo 1 linh vuc."""
    linh_vuc: str
    so_cau_dung: int = 0
    tong_cau: int = 0
    phan_tram: float = 0.0


class KetQuaResponse(BaseModel):
    """Response ket qua ca nhan."""
    ky_thi: dict
    thi_sinh: dict
    ket_qua: dict
    diem_theo_linh_vuc: list[DiemLinhVuc] = []
    chi_tiet: Optional[list] = None  # Chi hien neu ky_thi.hien_dap_an = true
    # Summary cac lan thi (KHONG kem chi_tiet_tra_loi de gon payload). FE goi
    # endpoint drill-down /ket-qua/{lan} de xem chi tiet 1 lan cu the.
    lich_su_thi: Optional[list[LichSuThiSummary]] = None
