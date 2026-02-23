"""
legal_service/schemas/xac_nhan_doc.py
=======================================
Pydantic schemas cho Xac nhan doc van ban, Dashboard, Bao cao.
"""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class XacNhanDocCreate(BaseModel):
    """Schema xac nhan da doc van ban."""

    da_xac_nhan: bool = True
    ghi_chu: Optional[str] = None


class TrackingDocInput(BaseModel):
    """Schema ghi nhan thoi gian doc thuc te."""

    # Thoi gian tinh bang giay CBCC da mo van ban
    thoi_gian_doc_giay: int


# ---------------------------------------------------------------------------
# Dashboard schemas
# ---------------------------------------------------------------------------


class DashboardSummary(BaseModel):
    """Tong hop so lieu dashboard cho CBCC."""

    vb_moi_tuan: int  # Van ban moi trong 7 ngay qua
    vb_chua_doc: int  # Van ban bat_buoc_doc chua xac nhan
    vb_khan: int  # Van ban KHAN chua doc
    vb_sap_het_han: int  # Van ban co han_xac_nhan trong 3 ngay toi
    quiz_chua_lam: int  # Quiz cua VB da doc ma chua lam


# ---------------------------------------------------------------------------
# Bao cao schemas
# ---------------------------------------------------------------------------


class BaoCaoCaNhan(BaseModel):
    """Bao cao doc van ban theo ca nhan trong thang."""

    thang: int
    nam: int
    vb_da_doc: int
    vb_chua_doc: int
    vb_qua_han: int  # Da qua han xac nhan ma chua xac nhan
    quiz_hoan_thanh: int
    quiz_diem_tb: Optional[float] = None
    thoi_gian_doc_tb_giay: Optional[float] = None


class ChiTietDoc(BaseModel):
    """Chi tiet trang thai doc cua 1 CBCC voi 1 van ban."""

    cong_chuc: dict  # {"ho_ten": "...", "don_vi": "..."}
    da_doc: bool
    da_xac_nhan: bool
    ngay_doc: Optional[datetime] = None
    ngay_xac_nhan: Optional[datetime] = None
    thoi_gian_doc_giay: Optional[int] = None


class BaoCaoDocResponse(BaseModel):
    """Bao cao trang thai doc cua 1 van ban (cho QT_NOI_DUNG va Lanh dao)."""

    van_ban: dict  # {"so_hieu": "...", "han_xac_nhan": "..."}
    tong_doi_tuong: int  # Tong so CBCC duoc yeu cau doc
    da_doc: int
    da_xac_nhan: int
    chua_doc: int
    qua_han: int  # Chua xac nhan ma da qua han_xac_nhan
    chi_tiet: list[ChiTietDoc]


class CbccChuaDoc(BaseModel):
    """Thong tin CBCC chua doc van ban trong don vi."""

    ho_ten: str
    vb_chua_doc: int  # So van ban bat_buoc chua doc
    vb_qua_han: int  # So van ban da qua han chua xac nhan


class BaoCaoDonVi(BaseModel):
    """Bao cao tuan thu doc van ban theo don vi."""

    don_vi: dict  # {"ten_don_vi": "..."}
    tong_cbcc: int
    thong_ke: (
        dict  # vb_bat_buoc_trong_thang, ty_le_da_doc, ty_le_xac_nhan, ty_le_qua_han, quiz_diem_tb
    )
    cbcc_chua_doc: list[CbccChuaDoc]
