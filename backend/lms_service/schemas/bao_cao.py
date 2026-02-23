"""
lms_service/schemas/bao_cao.py
==============================
Pydantic schemas cho bao cao va dashboard.
"""

from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class BaoCaoCaNhan(BaseModel):
    """Bao cao ca nhan cua 1 CBCC."""
    tong_khoa_da_dang_ky: int = 0
    khoa_dang_hoc: int = 0
    khoa_hoan_thanh: int = 0
    khoa_chua_bat_dau: int = 0
    tong_chung_chi: int = 0
    tong_gio_hoc: int = 0
    khoa_hoc_gan_day: list[dict] = []
    chung_chi_gan_day: list[dict] = []


class BaoCaoDonVi(BaseModel):
    """Bao cao don vi."""
    don_vi_id: UUID
    ten_don_vi: str = ""
    tong_cbcc: int = 0
    cbcc_dang_hoc: int = 0
    cbcc_hoan_thanh_it_nhat_1: int = 0
    tong_dang_ky: int = 0
    tong_hoan_thanh: int = 0
    ti_le_hoan_thanh: Optional[Decimal] = Decimal("0")
    top_khoa_hoc: list[dict] = []


class BaoCaoKhoaHoc(BaseModel):
    """Bao cao 1 khoa hoc."""
    khoa_hoc_id: UUID
    ten_khoa_hoc: str = ""
    ma_khoa_hoc: str = ""
    tong_dang_ky: int = 0
    dang_hoc: int = 0
    hoan_thanh: int = 0
    chua_bat_dau: int = 0
    ti_le_hoan_thanh: Optional[Decimal] = Decimal("0")
    diem_trung_binh_bkt: Optional[Decimal] = None
    phan_bo_trang_thai: dict = {}


class DashboardSummary(BaseModel):
    """Dashboard summary cho widget frontend."""
    khoa_dang_hoc: int = 0
    khoa_sap_het_han: list[dict] = []
    chung_chi_moi: list[dict] = []
