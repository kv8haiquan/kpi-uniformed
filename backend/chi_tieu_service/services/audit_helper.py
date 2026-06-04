"""
chi_tieu_service/services/audit_helper.py
=========================================
Helper ghi lich su duyet + snapshot ban ghi dang_ky_thang.
"""

from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from chi_tieu_service.models.dang_ky_thang import DangKyThang
from chi_tieu_service.models.lich_su_duyet import LichSuDuyet


def snapshot(dk: DangKyThang) -> dict:
    """Snapshot cac truong nghiep vu cua ban ghi (de luu vao lich su)."""
    def _num(v: Optional[Decimal]):
        return str(v) if isinstance(v, Decimal) else v
    return {
        "trang_thai": dk.trang_thai,
        "khong_dang_ky": dk.khong_dang_ky,
        "gia_tri_dang_ky": _num(dk.gia_tri_dang_ky),
        "gia_tri_ket_qua": _num(dk.gia_tri_ket_qua),
        "danh_gia_tu_dong": dk.danh_gia_tu_dong,
        "danh_gia_ghi_chu": dk.danh_gia_ghi_chu,
    }


def ghi_lich_su(
    db: AsyncSession,
    dang_ky_thang_id: UUID,
    hanh_dong: str,
    nguoi_thuc_hien_id: UUID,
    noi_dung_truoc: Optional[dict] = None,
    noi_dung_sau: Optional[dict] = None,
    ghi_chu: Optional[str] = None,
) -> None:
    """Them 1 dong lich su (KHONG commit — de caller commit chung transaction)."""
    db.add(LichSuDuyet(
        dang_ky_thang_id=dang_ky_thang_id,
        hanh_dong=hanh_dong,
        nguoi_thuc_hien_id=nguoi_thuc_hien_id,
        noi_dung_truoc=noi_dung_truoc,
        noi_dung_sau=noi_dung_sau,
        ghi_chu=ghi_chu,
    ))
