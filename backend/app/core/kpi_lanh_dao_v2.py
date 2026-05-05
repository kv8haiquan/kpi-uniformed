"""
app/core/kpi_lanh_dao_v2.py
===========================
Service tính KPI lãnh đạo theo công thức MỚI (áp dụng từ tháng 4/2026).

Spec: docs/Ke_khai_LĐ/Phuong phap tinh KPI cho lanh dao.docx

CÔNG THỨC SCOPE SP CHO TỪNG CẤP
-------------------------------
LĐ thật từ tháng 4/2026 đã chuyển sang cùng bảng `kpi_submission` (V2_PL3)
như CC. Scope V2:

- PDV  = SP của chính PDV tự kê + SP của CC do PDV trực tiếp duyệt
- TDV  = toàn bộ SP của người thuộc đơn vị (CC + PDV + TDV tự kê)
         (CC khi kê khai chọn DUY NHẤT 1 người duyệt → không trùng;
          với scope TDV, lọc theo cong_chuc.don_vi_id)
- PCCT = gộp toàn bộ SP của các đơn vị TDV mình phụ trách
- CCT  = gộp SP các đơn vị các PCCT phụ trách + SP các đơn vị CCT trực tiếp
         phụ trách (trùng nếu phân công sai → ràng buộc UI ở phan_cong_phu_trach)

CÔNG THỨC ĐIỂM (giống CC V2 + thêm d/đ/e):
- Mẫu số: tổng SP gốc quy đổi (sum so_sp_goc_quy_doi của các bản DA_PHE_DUYET).
- a = tổng SP đã hoàn thành / mẫu số (tỷ lệ số lượng — DA_PHE_DUYET = hoàn thành).
- b = tổng SP đạt tiến độ (sum so_sp_tien_do) / mẫu số.
- c = tổng SP đạt chất lượng (sum so_sp_chat_luong) / mẫu số.
- d, đ, e từ danh_gia_dde (final / 100), thiếu → 1.0.
- KPI = (a + b + c + d + đ + e) / 6  (∈ [0, 1])

PHIÊN BẢN: 2.0 (05/05/2026) — đổi sang SP quy đổi để khớp UI CC V2.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Optional, Sequence
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.kpi_submission import KeKhaiCongViec, TrangThaiKeKhai
from app.models.leader_kpi import DanhGiaDDE
from app.models.phan_cong_phu_trach import PhanCongPhuTrach
from app.models.user_org import CapBacVaiTro, CongChuc


# =============================================================================
# FEATURE FLAG — TỪ THÁNG NÀO ÁP DỤNG CÔNG THỨC MỚI
# =============================================================================

KPI_LANH_DAO_V2_FROM_NAM = 2026
KPI_LANH_DAO_V2_FROM_THANG = 4


def is_kpi_lanh_dao_v2_active(thang: int, nam: int) -> bool:
    """Trả True nếu (thang, nam) ≥ tháng triển khai công thức mới."""
    return (nam, thang) >= (KPI_LANH_DAO_V2_FROM_NAM, KPI_LANH_DAO_V2_FROM_THANG)


# =============================================================================
# DATA CLASS — 1 BẢN GHI SP QUY ĐỔI TRONG SCOPE
# =============================================================================

@dataclass
class _SP:
    """Bản ghi SP đã quy đổi (từ kpi_submission V2, DA_PHE_DUYET)."""
    cong_chuc_id: UUID
    don_vi_id: Optional[UUID]
    so_sp_goc: float        # so_sp_goc_quy_doi — đóng góp vào mẫu số
    so_sp_chat_luong: float
    so_sp_tien_do: float


def _to_float(v) -> float:
    if v is None:
        return 0.0
    if isinstance(v, Decimal):
        return float(v)
    return float(v)


# =============================================================================
# HELPERS — RESOLVE PHÂN CÔNG PHỤ TRÁCH
# =============================================================================

async def get_don_vi_phu_trach(
    db: AsyncSession,
    lanh_dao_id: UUID,
    ngay: date,
) -> list[UUID]:
    """Trả về list don_vi_id mà 1 LĐ phụ trách tại ngày `ngay`."""
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


def _ngay_chot_cua_thang(thang: int, nam: int) -> date:
    """Ngày dùng để check phân công phụ trách trong tháng (cuối tháng)."""
    if thang == 12:
        return date(nam, 12, 31)
    from datetime import timedelta
    return date(nam, thang + 1, 1) - timedelta(days=1)


# =============================================================================
# HELPERS — LẤY SP THEO SCOPE (TỪ kpi_submission V2 ĐÃ DA_PHE_DUYET)
# =============================================================================

_BASE_SELECT = (
    select(
        KeKhaiCongViec.cong_chuc_id,
        CongChuc.don_vi_id,
        KeKhaiCongViec.so_sp_goc_quy_doi,
        KeKhaiCongViec.so_sp_chat_luong,
        KeKhaiCongViec.so_sp_tien_do,
    )
    .join(CongChuc, CongChuc.id == KeKhaiCongViec.cong_chuc_id)
)


def _row_to_sp(r) -> _SP:
    return _SP(
        cong_chuc_id=r[0],
        don_vi_id=r[1],
        so_sp_goc=_to_float(r[2]),
        so_sp_chat_luong=_to_float(r[3]),
        so_sp_tien_do=_to_float(r[4]),
    )


async def _sp_pdv_scope(
    db: AsyncSession, user_id: UUID, thang: int, nam: int
) -> list[_SP]:
    """
    PDV: SP do user_id tự kê + SP do user_id trực tiếp duyệt.
    PDV không tự duyệt mình (chọn TDV khi kê) → OR không trùng.
    """
    stmt = _BASE_SELECT.where(
        KeKhaiCongViec.thang == thang,
        KeKhaiCongViec.nam == nam,
        KeKhaiCongViec.is_deleted == False,  # noqa: E712
        KeKhaiCongViec.trang_thai == TrangThaiKeKhai.DA_PHE_DUYET,
        or_(
            KeKhaiCongViec.cong_chuc_id == user_id,
            KeKhaiCongViec.nguoi_phe_duyet_id == user_id,
        ),
    )
    rows = (await db.execute(stmt)).all()
    return [_row_to_sp(r) for r in rows]


async def _sp_trong_don_vi(
    db: AsyncSession, don_vi_ids: Sequence[UUID], thang: int, nam: int
) -> list[_SP]:
    """Toàn bộ SP của user thuộc các đơn vị (CC + PDV/TDV tự kê)."""
    if not don_vi_ids:
        return []
    stmt = _BASE_SELECT.where(
        KeKhaiCongViec.thang == thang,
        KeKhaiCongViec.nam == nam,
        KeKhaiCongViec.is_deleted == False,  # noqa: E712
        KeKhaiCongViec.trang_thai == TrangThaiKeKhai.DA_PHE_DUYET,
        CongChuc.don_vi_id.in_(list(don_vi_ids)),
    )
    rows = (await db.execute(stmt)).all()
    return [_row_to_sp(r) for r in rows]


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
        dict với các field (đồng dạng output của tinh_diem_kpi_70_v2 cho CC):
        - cong_chuc_id, thang, nam, cap_bac
        - tong_sp_ke_khai (mẫu số), tong_sp_hoan_thanh
        - sp_chat_luong, sp_tien_do
        - a, b, c (chỉ số 0..1; b = tỷ lệ tiến độ; c = tỷ lệ chất lượng)
        - d, dd, e (chỉ số 0..1)
        - kpi_tong (∈ [0, 1])
        - has_phan_cong (chỉ áp PCCT/CCT)
        - is_v2_active
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

    # Resolve scope SP TỔNG (theo cấp)
    has_phan_cong: Optional[bool] = None
    if cap_bac == CapBacVaiTro.PHO_DON_VI:
        scope_total = await _sp_pdv_scope(db, user.id, thang, nam)
    elif cap_bac == CapBacVaiTro.TRUONG_DON_VI:
        scope_total = await _sp_trong_don_vi(db, [user.don_vi_id], thang, nam)
    else:  # PCCT / CCT
        ngay_chot = _ngay_chot_cua_thang(thang, nam)
        don_vi_ids = await get_don_vi_phu_trach(db, user.id, ngay_chot)
        has_phan_cong = len(don_vi_ids) > 0
        scope_total = await _sp_trong_don_vi(db, don_vi_ids, thang, nam)

    # Tách SP CHÍNH LĐ TỰ KÊ (cong_chuc_id == user.id) vs SP TỔNG
    scope_self = [sp for sp in scope_total if sp.cong_chuc_id == user.id]

    # Tính tổng SP (TỔNG)
    tong_sp_ke_khai = sum(sp.so_sp_goc for sp in scope_total)
    tong_sp_hoan_thanh = tong_sp_ke_khai
    sp_chat_luong = sum(sp.so_sp_chat_luong for sp in scope_total)
    sp_tien_do = sum(sp.so_sp_tien_do for sp in scope_total)

    if tong_sp_ke_khai > 0:
        a = min(1.0, tong_sp_hoan_thanh / tong_sp_ke_khai)
        b = min(1.0, sp_tien_do / tong_sp_ke_khai)
        c = min(1.0, sp_chat_luong / tong_sp_ke_khai)
    else:
        a = b = c = 0.0

    # Tính tổng SP (TỰ KÊ — riêng LĐ)
    tong_sp_self = sum(sp.so_sp_goc for sp in scope_self)
    sp_cl_self = sum(sp.so_sp_chat_luong for sp in scope_self)
    sp_td_self = sum(sp.so_sp_tien_do for sp in scope_self)

    if tong_sp_self > 0:
        a_self = min(1.0, tong_sp_self / tong_sp_self)  # = 1 (đã duyệt = hoàn thành)
        b_self = min(1.0, sp_td_self / tong_sp_self)
        c_self = min(1.0, sp_cl_self / tong_sp_self)
    else:
        a_self = b_self = c_self = 0.0

    # d, đ, e
    d, dd, e = await _get_dde(db, cong_chuc_id, thang, nam)

    # Tổng KPI = (a+b+c+d+đ+e) / 6 — DÙNG SCOPE TỔNG (a/b/c của tổng đơn vị)
    kpi_tong = (a + b + c + d + dd + e) / 6

    return {
        "cong_chuc_id": str(cong_chuc_id),
        "thang": thang,
        "nam": nam,
        "cap_bac": cap_bac_str,
        # ==================== SCOPE TỔNG (dùng để tính KPI chính thức) ====================
        "tong_sp_ke_khai": round(tong_sp_ke_khai, 4),
        "tong_sp_hoan_thanh": round(tong_sp_hoan_thanh, 4),
        "sp_chat_luong": round(sp_chat_luong, 4),
        "sp_tien_do": round(sp_tien_do, 4),
        "so_kekhai_records": len(scope_total),
        "a": round(a, 6),
        "b": round(b, 6),
        "c": round(c, 6),
        # ==================== SCOPE LĐ TỰ KÊ (chỉ thông tin tham khảo) ====================
        "tong_sp_ke_khai_self": round(tong_sp_self, 4),
        "sp_chat_luong_self": round(sp_cl_self, 4),
        "sp_tien_do_self": round(sp_td_self, 4),
        "so_kekhai_records_self": len(scope_self),
        "a_self": round(a_self, 6),
        "b_self": round(b_self, 6),
        "c_self": round(c_self, 6),
        # ==================== d, đ, e từ danh_gia_dde ====================
        "d": round(d, 6),
        "dd": round(dd, 6),
        "e": round(e, 6),
        # ==================== TỔNG KPI ====================
        "kpi_tong": round(kpi_tong, 6),
        "has_phan_cong": has_phan_cong,
        "is_v2_active": is_kpi_lanh_dao_v2_active(thang, nam),
    }
