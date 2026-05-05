"""
app/core/kpi_lanh_dao_v2.py
===========================
Service tính KPI lãnh đạo theo công thức MỚI (áp dụng từ tháng 4/2026).

Spec: docs/Ke_khai_LĐ/Phuong phap tinh KPI cho lanh dao.docx

CÔNG THỨC SCOPE SP CHO TỪNG CẤP
-------------------------------
- PDV  = SP tự kê + SP của CC do PDV trực tiếp duyệt
- TDV  = toàn bộ SP của đơn vị (CC + PDV trong đơn vị + TDV tự kê)
         (CC khi kê khai chọn DUY NHẤT 1 người duyệt → không trùng)
- PCCT = gộp toàn bộ SP của các đơn vị TDV mình phụ trách
- CCT  = gộp SP các đơn vị các PCCT phụ trách + SP các đơn vị CCT trực tiếp
         phụ trách
         (Vì 1 đơn vị tại 1 thời điểm chỉ thuộc 1 LĐ cấp Chi cục →
          không đếm trùng giữa SP PCCT và SP TDV trực tiếp)

TỔNG ĐIỂM KPI = (a + b + c + d + đ + e) / 6
- a = số CV hoàn thành / tổng CV
- b = (Σ max(0, 1 - so_loi_tien_do × 0.25)) / tổng CV
- c = (Σ max(0, 1 - so_loi_chat_luong × 0.25)) / tổng CV
- d, đ, e: từ danh_gia_dde (final / 100), thiếu → 1.0

Trong scope:
- "CV của CC" = ke_khai_cong_viec, trạng thái DA_PHE_DUYET, không xóa
- "CV của LĐ tự kê" = ke_khai_lanh_dao, trạng thái DA_PHE_DUYET, không xóa
- Hoàn thành: ke_khai_cong_viec đã DA_PHE_DUYET coi như hoàn thành.
  ke_khai_lanh_dao có trang_thai_hoan_thanh = DA_HOAN_THANH.

PHIÊN BẢN: 1.0 (05/05/2026)
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Optional, Sequence
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.kpi_submission import KeKhaiCongViec, TrangThaiKeKhai
from app.models.leader_kpi import DanhGiaDDE, KeKhaiLanhDao, TrangThaiHoanThanh
from app.models.phan_cong_phu_trach import PhanCongPhuTrach
from app.models.user_org import CapBacVaiTro, CongChuc, DonVi


# =============================================================================
# FEATURE FLAG — TỪ THÁNG NÀO ÁP DỤNG CÔNG THỨC MỚI
# =============================================================================

KPI_LANH_DAO_V2_FROM_NAM = 2026
KPI_LANH_DAO_V2_FROM_THANG = 5  # Đẩy từ 4 → 5 (giữ data tháng 4 trong ke_khai_lanh_dao)


def is_kpi_lanh_dao_v2_active(thang: int, nam: int) -> bool:
    """Trả True nếu (thang, nam) ≥ tháng triển khai công thức mới."""
    return (nam, thang) >= (KPI_LANH_DAO_V2_FROM_NAM, KPI_LANH_DAO_V2_FROM_THANG)


# =============================================================================
# DATA CLASS — 1 BẢN GHI CV TRONG SCOPE
# =============================================================================

@dataclass
class _CV:
    """Bản ghi CV chuẩn hóa (từ ke_khai_cong_viec hoặc ke_khai_lanh_dao)."""
    nguon: str  # "CC" | "LD"
    cong_chuc_id: UUID
    don_vi_id: Optional[UUID]
    so_loi_chat_luong: int
    so_loi_tien_do: int
    hoan_thanh: bool


def _diem_loi(so_loi: int) -> float:
    """Điểm 1 CV theo số lỗi: max(0, 1 - lỗi × 0.25)."""
    if so_loi is None or so_loi < 0:
        return 1.0
    return max(0.0, 1.0 - so_loi * 0.25)


# =============================================================================
# HELPERS — RESOLVE PHÂN CÔNG PHỤ TRÁCH
# =============================================================================

async def get_don_vi_phu_trach(
    db: AsyncSession,
    lanh_dao_id: UUID,
    ngay: date,
) -> list[UUID]:
    """
    Trả về list don_vi_id mà 1 LĐ phụ trách tại ngày `ngay`.

    Đọc bảng phan_cong_phu_trach, filter:
    - is_deleted = False
    - lanh_dao_id = ?
    - hieu_luc_tu <= ngay
    - hieu_luc_den IS NULL OR hieu_luc_den >= ngay
    """
    stmt = (
        select(PhanCongPhuTrach.don_vi_id)
        .where(
            PhanCongPhuTrach.lanh_dao_id == lanh_dao_id,
            PhanCongPhuTrach.is_deleted == False,  # noqa: E712
            PhanCongPhuTrach.hieu_luc_tu <= ngay,
            or_(
                PhanCongPhuTrach.hieu_luc_den.is_(None),
                PhanCongPhuTrach.hieu_luc_den >= ngay,
            ),
        )
    )
    rows = (await db.execute(stmt)).scalars().all()
    return list(rows)


# =============================================================================
# HELPERS — LẤY CV THEO SCOPE
# =============================================================================

def _ngay_chot_cua_thang(thang: int, nam: int) -> date:
    """Ngày dùng để check phân công phụ trách trong tháng (cuối tháng)."""
    if thang == 12:
        return date(nam, 12, 31)
    # Ngày trước ngày 1 của tháng kế tiếp
    from datetime import timedelta
    return date(nam, thang + 1, 1) - timedelta(days=1)


async def _cv_cc_do_nguoi_duyet(
    db: AsyncSession,
    nguoi_phe_duyet_id: UUID,
    thang: int,
    nam: int,
) -> list[_CV]:
    """CV của CC do `nguoi_phe_duyet_id` trực tiếp duyệt, đã DA_PHE_DUYET."""
    stmt = (
        select(
            KeKhaiCongViec.cong_chuc_id,
            CongChuc.don_vi_id,
            KeKhaiCongViec.so_loi_chat_luong,
            KeKhaiCongViec.so_loi_tien_do,
        )
        .join(CongChuc, CongChuc.id == KeKhaiCongViec.cong_chuc_id)
        .where(
            KeKhaiCongViec.thang == thang,
            KeKhaiCongViec.nam == nam,
            KeKhaiCongViec.is_deleted == False,  # noqa: E712
            KeKhaiCongViec.trang_thai == TrangThaiKeKhai.DA_PHE_DUYET,
            KeKhaiCongViec.nguoi_phe_duyet_id == nguoi_phe_duyet_id,
        )
    )
    rows = (await db.execute(stmt)).all()
    return [
        _CV(
            nguon="CC",
            cong_chuc_id=r[0],
            don_vi_id=r[1],
            so_loi_chat_luong=r[2] or 0,
            so_loi_tien_do=r[3] or 0,
            hoan_thanh=True,  # DA_PHE_DUYET = đã hoàn thành
        )
        for r in rows
    ]


async def _cv_cc_trong_don_vi(
    db: AsyncSession,
    don_vi_ids: Sequence[UUID],
    thang: int,
    nam: int,
) -> list[_CV]:
    """Toàn bộ CV của CC trong các đơn vị, đã DA_PHE_DUYET."""
    if not don_vi_ids:
        return []
    stmt = (
        select(
            KeKhaiCongViec.cong_chuc_id,
            CongChuc.don_vi_id,
            KeKhaiCongViec.so_loi_chat_luong,
            KeKhaiCongViec.so_loi_tien_do,
        )
        .join(CongChuc, CongChuc.id == KeKhaiCongViec.cong_chuc_id)
        .where(
            KeKhaiCongViec.thang == thang,
            KeKhaiCongViec.nam == nam,
            KeKhaiCongViec.is_deleted == False,  # noqa: E712
            KeKhaiCongViec.trang_thai == TrangThaiKeKhai.DA_PHE_DUYET,
            CongChuc.don_vi_id.in_(list(don_vi_ids)),
        )
    )
    rows = (await db.execute(stmt)).all()
    return [
        _CV(
            nguon="CC",
            cong_chuc_id=r[0],
            don_vi_id=r[1],
            so_loi_chat_luong=r[2] or 0,
            so_loi_tien_do=r[3] or 0,
            hoan_thanh=True,
        )
        for r in rows
    ]


async def _cv_ld_tu_ke(
    db: AsyncSession,
    cong_chuc_ids: Sequence[UUID],
    thang: int,
    nam: int,
) -> list[_CV]:
    """CV của LĐ tự kê (ke_khai_lanh_dao), đã DA_PHE_DUYET."""
    if not cong_chuc_ids:
        return []
    stmt = (
        select(
            KeKhaiLanhDao.cong_chuc_id,
            CongChuc.don_vi_id,
            KeKhaiLanhDao.so_loi_chat_luong,
            KeKhaiLanhDao.so_loi_tien_do,
            KeKhaiLanhDao.trang_thai_hoan_thanh,
        )
        .join(CongChuc, CongChuc.id == KeKhaiLanhDao.cong_chuc_id)
        .where(
            KeKhaiLanhDao.thang == thang,
            KeKhaiLanhDao.nam == nam,
            KeKhaiLanhDao.is_deleted == False,  # noqa: E712
            KeKhaiLanhDao.trang_thai == "DA_PHE_DUYET",
            KeKhaiLanhDao.cong_chuc_id.in_(list(cong_chuc_ids)),
        )
    )
    rows = (await db.execute(stmt)).all()
    return [
        _CV(
            nguon="LD",
            cong_chuc_id=r[0],
            don_vi_id=r[1],
            so_loi_chat_luong=r[2] or 0,
            so_loi_tien_do=r[3] or 0,
            hoan_thanh=(r[4] == TrangThaiHoanThanh.DA_HOAN_THANH),
        )
        for r in rows
    ]


async def _list_lanh_dao_cua_don_vi(
    db: AsyncSession,
    don_vi_ids: Sequence[UUID],
    cap_bacs: Sequence[CapBacVaiTro],
) -> list[UUID]:
    """List ID các LĐ thuộc đơn vị (filter theo cấp bậc)."""
    if not don_vi_ids:
        return []
    from app.models.user_org import VaiTro
    stmt = (
        select(CongChuc.id)
        .join(VaiTro, VaiTro.id == CongChuc.vai_tro_id)
        .where(
            CongChuc.don_vi_id.in_(list(don_vi_ids)),
            CongChuc.is_deleted == False,  # noqa: E712
            CongChuc.is_active == True,  # noqa: E712
            VaiTro.cap_bac.in_(list(cap_bacs)),
        )
    )
    rows = (await db.execute(stmt)).scalars().all()
    return list(rows)


# =============================================================================
# RESOLVE SCOPE THEO CẤP
# =============================================================================

async def _scope_pdv(
    db: AsyncSession, user: CongChuc, thang: int, nam: int
) -> list[_CV]:
    """PDV: SP tự kê + SP CC do PDV trực tiếp duyệt."""
    cv_self = await _cv_ld_tu_ke(db, [user.id], thang, nam)
    cv_duyet = await _cv_cc_do_nguoi_duyet(db, user.id, thang, nam)
    return cv_self + cv_duyet


async def _scope_tdv(
    db: AsyncSession, user: CongChuc, thang: int, nam: int
) -> list[_CV]:
    """TDV: toàn bộ CV của CC trong đơn vị + CV PDV/TDV tự kê."""
    don_vi_ids = [user.don_vi_id]
    cv_cc = await _cv_cc_trong_don_vi(db, don_vi_ids, thang, nam)

    # Lấy cả TDV (chính user) + tất cả PDV trong đơn vị → CV tự kê
    leader_ids = await _list_lanh_dao_cua_don_vi(
        db,
        don_vi_ids,
        [CapBacVaiTro.TRUONG_DON_VI, CapBacVaiTro.PHO_DON_VI],
    )
    cv_ld = await _cv_ld_tu_ke(db, leader_ids, thang, nam)

    return cv_cc + cv_ld


async def _scope_pcct_or_cct(
    db: AsyncSession, user: CongChuc, thang: int, nam: int
) -> list[_CV]:
    """
    PCCT/CCT: gộp toàn bộ SP của các đơn vị mình phụ trách
    (theo bảng phan_cong_phu_trach tại ngày cuối tháng).

    Bao gồm:
    - CV của CC trong các đơn vị
    - CV PDV/TDV trong các đơn vị tự kê
    """
    ngay_chot = _ngay_chot_cua_thang(thang, nam)
    don_vi_ids = await get_don_vi_phu_trach(db, user.id, ngay_chot)
    if not don_vi_ids:
        # Chưa có phân công → scope rỗng
        return []

    cv_cc = await _cv_cc_trong_don_vi(db, don_vi_ids, thang, nam)
    leader_ids = await _list_lanh_dao_cua_don_vi(
        db,
        don_vi_ids,
        [CapBacVaiTro.TRUONG_DON_VI, CapBacVaiTro.PHO_DON_VI],
    )
    cv_ld = await _cv_ld_tu_ke(db, leader_ids, thang, nam)

    return cv_cc + cv_ld


# =============================================================================
# d, đ, e
# =============================================================================

async def _get_dde(
    db: AsyncSession, cong_chuc_id: UUID, thang: int, nam: int
) -> tuple[float, float, float]:
    """Lấy d, đ, e từ danh_gia_dde đã DA_PHE_DUYET. Mặc định 1.0 nếu thiếu."""
    stmt = select(DanhGiaDDE).where(
        DanhGiaDDE.cong_chuc_id == cong_chuc_id,
        DanhGiaDDE.thang == thang,
        DanhGiaDDE.nam == nam,
        DanhGiaDDE.trang_thai == "DA_PHE_DUYET",
    )
    dde = (await db.execute(stmt)).scalar_one_or_none()
    if not dde:
        return 1.0, 1.0, 1.0
    return dde.d_percent, dde.dd_percent, dde.e_percent


# =============================================================================
# MAIN — TÍNH KPI V2 CHO 1 LĐ
# =============================================================================

async def calc_kpi_lanh_dao_v2(
    db: AsyncSession,
    cong_chuc_id: UUID,
    thang: int,
    nam: int,
) -> dict:
    """
    Tính KPI lãnh đạo theo công thức MỚI cho 1 LĐ ở 1 tháng.

    Returns:
        dict với các field:
        - cong_chuc_id, thang, nam
        - cap_bac (PDV/TDV/PCCT/CCT)
        - tong_cv, tong_hoan_thanh
        - tong_cv_cc, tong_cv_ld (breakdown theo nguồn)
        - a, b, c, d, dd, e (chỉ số 0..1)
        - kpi_tong (0..1)
        - has_phan_cong (bool — chỉ áp với PCCT/CCT)
        - is_v2_active (bool)
    """
    from sqlalchemy.orm import selectinload

    # Load LĐ
    stmt = (
        select(CongChuc)
        .options(selectinload(CongChuc.vai_tro))
        .where(CongChuc.id == cong_chuc_id, CongChuc.is_deleted == False)  # noqa: E712
    )
    user = (await db.execute(stmt)).scalar_one_or_none()
    if not user or not user.vai_tro:
        raise ValueError(f"Không tìm thấy lãnh đạo {cong_chuc_id}")

    cap_bac = user.vai_tro.cap_bac
    cap_bac_str_map = {
        CapBacVaiTro.PHO_DON_VI: "PDV",
        CapBacVaiTro.TRUONG_DON_VI: "TDV",
        CapBacVaiTro.PHO_CHI_CUC_TRUONG: "PCCT",
        CapBacVaiTro.CHI_CUC_TRUONG: "CCT",
    }
    if cap_bac not in cap_bac_str_map:
        raise ValueError(
            f"calc_kpi_lanh_dao_v2 chỉ hỗ trợ LĐ (PDV/TDV/PCCT/CCT), "
            f"không hỗ trợ {cap_bac}"
        )
    cap_bac_str = cap_bac_str_map[cap_bac]

    # Resolve scope
    if cap_bac == CapBacVaiTro.PHO_DON_VI:
        scope = await _scope_pdv(db, user, thang, nam)
    elif cap_bac == CapBacVaiTro.TRUONG_DON_VI:
        scope = await _scope_tdv(db, user, thang, nam)
    else:  # PCCT / CCT
        scope = await _scope_pcct_or_cct(db, user, thang, nam)

    # Tính a, b, c
    n = len(scope)
    if n == 0:
        a = b = c = 0.0
        tong_hoan_thanh = 0
    else:
        tong_hoan_thanh = sum(1 for cv in scope if cv.hoan_thanh)
        sum_td = sum(_diem_loi(cv.so_loi_tien_do) for cv in scope)
        sum_cl = sum(_diem_loi(cv.so_loi_chat_luong) for cv in scope)
        a = tong_hoan_thanh / n
        b = sum_td / n
        c = sum_cl / n

    # d, đ, e
    d, dd, e = await _get_dde(db, cong_chuc_id, thang, nam)

    # Tổng KPI = (a+b+c+d+đ+e) / 6
    kpi_tong = (a + b + c + d + dd + e) / 6

    # Phân công phụ trách (chỉ áp PCCT/CCT)
    has_phan_cong: Optional[bool] = None
    if cap_bac in (CapBacVaiTro.PHO_CHI_CUC_TRUONG, CapBacVaiTro.CHI_CUC_TRUONG):
        ngay_chot = _ngay_chot_cua_thang(thang, nam)
        dvs = await get_don_vi_phu_trach(db, cong_chuc_id, ngay_chot)
        has_phan_cong = len(dvs) > 0

    return {
        "cong_chuc_id": str(cong_chuc_id),
        "thang": thang,
        "nam": nam,
        "cap_bac": cap_bac_str,
        "tong_cv": n,
        "tong_hoan_thanh": tong_hoan_thanh,
        "tong_cv_cc": sum(1 for cv in scope if cv.nguon == "CC"),
        "tong_cv_ld": sum(1 for cv in scope if cv.nguon == "LD"),
        "a": round(a, 6),
        "b": round(b, 6),
        "c": round(c, 6),
        "d": round(d, 6),
        "dd": round(dd, 6),
        "e": round(e, 6),
        "kpi_tong": round(kpi_tong, 6),
        "has_phan_cong": has_phan_cong,
        "is_v2_active": is_kpi_lanh_dao_v2_active(thang, nam),
    }
