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
    """Bản ghi SP đã quy đổi (từ kpi_submission V2 + override điều chỉnh)."""
    ke_khai_id: UUID
    cong_chuc_id: UUID
    don_vi_id: Optional[UUID]
    trang_thai: TrangThaiKeKhai
    so_luong: int
    so_sp_goc: float                 # so_sp_goc_quy_doi → mẫu số
    so_sp_chat_luong_chot: float     # so_sp_chat_luong (chỉ dùng khi DA_PHE_DUYET)
    so_sp_tien_do_chot: float
    tu_dg_cl: int                    # tu_danh_gia_chat_luong (cho NHAP/CHO)
    tu_dg_td: int
    he_so_quy_doi: float             # snapshot — dùng khi recompute sau override
    is_chua_hoan_thanh: bool         # từ dieu_chinh_kqcv override (mặc định false)


def _to_float(v) -> float:
    if v is None:
        return 0.0
    if isinstance(v, Decimal):
        return float(v)
    return float(v)


def _resolve_sp_cl_td(sp: _SP) -> tuple[float, float]:
    """
    Trả (sp_chat_luong, sp_tien_do) tùy trạng thái:
    - DA_PHE_DUYET: dùng giá trị đã chốt (LĐ duyệt).
    - NHAP/CHO_PHE_DUYET (tạm tính): tính từ tu_danh_gia của CC.
      Mỗi CV đóng góp: max(0, so_sp_goc - 0.25 × so_loi × sp_per_unit)
    """
    if sp.trang_thai == TrangThaiKeKhai.DA_PHE_DUYET:
        return sp.so_sp_chat_luong_chot, sp.so_sp_tien_do_chot

    so_luong_v = sp.so_luong or 1
    if sp.so_sp_goc > 0 and so_luong_v > 0:
        sp_per_unit = sp.so_sp_goc / so_luong_v
        max_loi = so_luong_v * 4
        loi_cl = min(sp.tu_dg_cl or 0, max_loi)
        loi_td = min(sp.tu_dg_td or 0, max_loi)
        return (
            max(sp.so_sp_goc - 0.25 * loi_cl * sp_per_unit, 0.0),
            max(sp.so_sp_goc - 0.25 * loi_td * sp_per_unit, 0.0),
        )
    return sp.so_sp_goc, sp.so_sp_goc


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
        KeKhaiCongViec.id,
        KeKhaiCongViec.cong_chuc_id,
        CongChuc.don_vi_id,
        KeKhaiCongViec.trang_thai,
        KeKhaiCongViec.so_luong,
        KeKhaiCongViec.so_sp_goc_quy_doi,
        KeKhaiCongViec.so_sp_chat_luong,
        KeKhaiCongViec.so_sp_tien_do,
        KeKhaiCongViec.tu_danh_gia_chat_luong,
        KeKhaiCongViec.tu_danh_gia_tien_do,
        KeKhaiCongViec.he_so_quy_doi_snapshot,
    )
    .join(CongChuc, CongChuc.id == KeKhaiCongViec.cong_chuc_id)
)


def _row_to_sp(r) -> _SP:
    return _SP(
        ke_khai_id=r[0],
        cong_chuc_id=r[1],
        don_vi_id=r[2],
        trang_thai=r[3],
        so_luong=r[4] or 1,
        so_sp_goc=_to_float(r[5]),
        so_sp_chat_luong_chot=_to_float(r[6]),
        so_sp_tien_do_chot=_to_float(r[7]),
        tu_dg_cl=r[8] or 0,
        tu_dg_td=r[9] or 0,
        he_so_quy_doi=_to_float(r[10]) if r[10] else 0.0,
        is_chua_hoan_thanh=False,  # default; sẽ override từ dieu_chinh_kqcv
    )


# =============================================================================
# OVERRIDE TỪ dieu_chinh_kqcv (Yêu cầu 2 mới — chỉ ảnh hưởng KPI LĐ)
# =============================================================================

async def _load_dieu_chinh_overrides(
    db: AsyncSession, ke_khai_ids: Sequence[UUID]
) -> dict[UUID, dict]:
    """
    Trả map ke_khai_id → {so_loi_chat_luong, so_loi_tien_do, is_chua_hoan_thanh}
    của bản điều chỉnh DA_PHE_DUYET MỚI NHẤT cho mỗi CV.

    Dùng để override khi tính KPI LĐ. KPI CC không gọi function này → giữ
    giá trị gốc trong kpi_submission.
    """
    if not ke_khai_ids:
        return {}
    from app.models.dieu_chinh_kqcv import DieuChinhKqcv
    stmt = (
        select(DieuChinhKqcv)
        .where(
            DieuChinhKqcv.ke_khai_id.in_(list(ke_khai_ids)),
            DieuChinhKqcv.trang_thai == "DA_PHE_DUYET",
            DieuChinhKqcv.is_deleted == False,  # noqa: E712
        )
        .order_by(DieuChinhKqcv.ke_khai_id, DieuChinhKqcv.ngay_phe_duyet.desc())
    )
    rows = (await db.execute(stmt)).scalars().all()
    out: dict[UUID, dict] = {}
    for r in rows:
        # Lấy bản đầu tiên gặp = mới nhất (đã ORDER ngay_phe_duyet DESC)
        if r.ke_khai_id in out:
            continue
        new = r.gia_tri_moi or {}
        out[r.ke_khai_id] = {
            "so_loi_chat_luong": int(new.get("so_loi_chat_luong", 0)),
            "so_loi_tien_do": int(new.get("so_loi_tien_do", 0)),
            "is_chua_hoan_thanh": bool(new.get("is_chua_hoan_thanh", False)),
        }
    return out


def _apply_overrides_inplace(scope: list[_SP], overrides: dict[UUID, dict]) -> None:
    """
    Apply override từ dieu_chinh_kqcv vào _SP list (mutate inplace).
    Recompute SP CL/TĐ từ so_loi_* mới + he_so_quy_doi đã snapshot.
    """
    if not overrides:
        return
    for sp in scope:
        ov = overrides.get(sp.ke_khai_id)
        if not ov:
            continue
        sp.is_chua_hoan_thanh = ov["is_chua_hoan_thanh"]
        # Recompute sp_cl/sp_td theo so_loi mới (chỉ áp khi CV đã DA_PHE_DUYET)
        if sp.trang_thai == TrangThaiKeKhai.DA_PHE_DUYET and sp.he_so_quy_doi > 0:
            so_luong_v = sp.so_luong or 1
            sp_per_unit = sp.so_sp_goc / so_luong_v if so_luong_v > 0 else 0
            max_loi = so_luong_v * 4
            loi_cl = min(ov["so_loi_chat_luong"], max_loi)
            loi_td = min(ov["so_loi_tien_do"], max_loi)
            sp.so_sp_chat_luong_chot = max(sp.so_sp_goc - 0.25 * loi_cl * sp_per_unit, 0.0)
            sp.so_sp_tien_do_chot = max(sp.so_sp_goc - 0.25 * loi_td * sp_per_unit, 0.0)
            # Cập nhật tu_dg để consistent (cho UI hiển thị nếu cần)
            sp.tu_dg_cl = loi_cl
            sp.tu_dg_td = loi_td


def _allowed_states(tam_tinh: bool) -> list[TrangThaiKeKhai]:
    if tam_tinh:
        return [
            TrangThaiKeKhai.NHAP,
            TrangThaiKeKhai.CHO_PHE_DUYET,
            TrangThaiKeKhai.DA_PHE_DUYET,
        ]
    return [TrangThaiKeKhai.DA_PHE_DUYET]


async def _sp_pdv_scope(
    db: AsyncSession,
    user_id: UUID,
    thang: int,
    nam: int,
    tam_tinh: bool = False,
) -> list[_SP]:
    """
    PDV: SP do user_id tự kê + SP do user_id trực tiếp duyệt.
    Apply override từ dieu_chinh_kqcv (chỉ ảnh hưởng KPI LĐ).
    """
    stmt = _BASE_SELECT.where(
        KeKhaiCongViec.thang == thang,
        KeKhaiCongViec.nam == nam,
        KeKhaiCongViec.is_deleted == False,  # noqa: E712
        KeKhaiCongViec.trang_thai.in_(_allowed_states(tam_tinh)),
        or_(
            KeKhaiCongViec.cong_chuc_id == user_id,
            KeKhaiCongViec.nguoi_phe_duyet_id == user_id,
        ),
    )
    rows = (await db.execute(stmt)).all()
    scope = [_row_to_sp(r) for r in rows]
    overrides = await _load_dieu_chinh_overrides(db, [sp.ke_khai_id for sp in scope])
    _apply_overrides_inplace(scope, overrides)
    return scope


async def _sp_trong_don_vi(
    db: AsyncSession,
    don_vi_ids: Sequence[UUID],
    thang: int,
    nam: int,
    tam_tinh: bool = False,
) -> list[_SP]:
    """Toàn bộ SP của user thuộc các đơn vị (CC + PDV/TDV tự kê).
    Apply override từ dieu_chinh_kqcv (chỉ ảnh hưởng KPI LĐ)."""
    if not don_vi_ids:
        return []
    stmt = _BASE_SELECT.where(
        KeKhaiCongViec.thang == thang,
        KeKhaiCongViec.nam == nam,
        KeKhaiCongViec.is_deleted == False,  # noqa: E712
        KeKhaiCongViec.trang_thai.in_(_allowed_states(tam_tinh)),
        CongChuc.don_vi_id.in_(list(don_vi_ids)),
    )
    rows = (await db.execute(stmt)).all()
    scope = [_row_to_sp(r) for r in rows]
    overrides = await _load_dieu_chinh_overrides(db, [sp.ke_khai_id for sp in scope])
    _apply_overrides_inplace(scope, overrides)
    return scope


# =============================================================================
# d, đ, e
# =============================================================================

async def _get_dde(
    db: AsyncSession, cong_chuc_id: UUID, thang: int, nam: int,
    *, tam_tinh: bool = False,
) -> tuple[float, float, float]:
    """Lấy d, đ, e từ danh_gia_dde. Mặc định 1.0 nếu thiếu.

    Args:
        tam_tinh: False (default — engine chính thức) chỉ lấy DA_PHE_DUYET.
                  True → lấy thêm NHAP + CHO_PHE_DUYET cho tab "Tạm tính" UI
                  (đồng nhất với tinh_diem_kpi_70_lanh_dao(tam_tinh=True)).
                  Bản chưa duyệt → final = COALESCE(*_phe_duyet, *_ket_qua_don_vi)
                  rơi xuống giá trị tự đánh giá. KHÔNG ảnh hưởng engine
                  chính thức (vẫn DA_PHE_DUYET only).
    """
    if tam_tinh:
        statuses = ("NHAP", "CHO_PHE_DUYET", "DA_PHE_DUYET")
        stmt = select(DanhGiaDDE).where(
            DanhGiaDDE.cong_chuc_id == cong_chuc_id,
            DanhGiaDDE.thang == thang,
            DanhGiaDDE.nam == nam,
            DanhGiaDDE.trang_thai.in_(statuses),
        )
    else:
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

async def list_cong_viec_lanh_dao_v2(
    db: AsyncSession,
    cong_chuc_id: UUID,
    thang: int,
    nam: int,
    *,
    tam_tinh: bool = False,
    loai: str = "all",
) -> list[dict]:
    """
    List chi tiết CV trong scope KPI của 1 LĐ — phục vụ trang xem chi tiết.

    Args:
        loai: "tu_lam" (chỉ CV LĐ tự kê) | "cap_duoi" (chỉ CV của người khác)
              | "all" (tất cả).

    Returns: list dict gồm thông tin CV + người kê + danh mục SP + SP quy đổi.
    """
    from sqlalchemy.orm import selectinload as _sel

    # Load LĐ
    user = (
        await db.execute(
            select(CongChuc)
            .options(_sel(CongChuc.vai_tro))
            .where(CongChuc.id == cong_chuc_id, CongChuc.is_deleted == False)  # noqa: E712
        )
    ).scalar_one_or_none()
    if not user or not user.vai_tro:
        raise ValueError(f"Không tìm thấy lãnh đạo {cong_chuc_id}")

    cap_bac = user.vai_tro.cap_bac

    # Resolve scope (giống calc_kpi_lanh_dao_v2 nhưng query chi tiết hơn)
    from app.models.task_catalog import DanhMucSpCongViec

    base_q = (
        select(KeKhaiCongViec, CongChuc, DanhMucSpCongViec)
        .join(CongChuc, CongChuc.id == KeKhaiCongViec.cong_chuc_id)
        .join(
            DanhMucSpCongViec,
            DanhMucSpCongViec.id == KeKhaiCongViec.danh_muc_sp_id,
            isouter=True,
        )
        .where(
            KeKhaiCongViec.thang == thang,
            KeKhaiCongViec.nam == nam,
            KeKhaiCongViec.is_deleted == False,  # noqa: E712
            KeKhaiCongViec.trang_thai.in_(_allowed_states(tam_tinh)),
        )
    )

    if cap_bac == CapBacVaiTro.PHO_DON_VI:
        base_q = base_q.where(
            or_(
                KeKhaiCongViec.cong_chuc_id == user.id,
                KeKhaiCongViec.nguoi_phe_duyet_id == user.id,
            )
        )
    elif cap_bac == CapBacVaiTro.TRUONG_DON_VI:
        base_q = base_q.where(CongChuc.don_vi_id == user.don_vi_id)
    elif cap_bac in (CapBacVaiTro.PHO_CHI_CUC_TRUONG, CapBacVaiTro.CHI_CUC_TRUONG):
        ngay_chot = _ngay_chot_cua_thang(thang, nam)
        don_vi_ids = await get_don_vi_phu_trach(db, user.id, ngay_chot)
        if not don_vi_ids:
            return []
        base_q = base_q.where(CongChuc.don_vi_id.in_(don_vi_ids))
    else:
        raise ValueError(f"Cấp bậc {cap_bac} không hỗ trợ V2")

    # Filter "loai"
    if loai == "tu_lam":
        base_q = base_q.where(KeKhaiCongViec.cong_chuc_id == user.id)
    elif loai == "cap_duoi":
        base_q = base_q.where(KeKhaiCongViec.cong_chuc_id != user.id)

    base_q = base_q.order_by(KeKhaiCongViec.ngay_thuc_hien.desc(), CongChuc.ho_ten)

    rows = (await db.execute(base_q)).all()

    # Load overrides cho LĐ — lấy giá trị mới nếu CV đã có điều chỉnh DA_PHE_DUYET
    ke_khai_ids = [kk.id for kk, _, _ in rows]
    overrides = await _load_dieu_chinh_overrides(db, ke_khai_ids)

    out = []
    for kk, cc, dm in rows:
        ov = overrides.get(kk.id)
        # Áp dụng override (nếu có) — đây là giá trị LĐ đang dùng tính KPI
        eff_loi_cl = ov["so_loi_chat_luong"] if ov else (kk.so_loi_chat_luong or 0)
        eff_loi_td = ov["so_loi_tien_do"] if ov else (kk.so_loi_tien_do or 0)
        eff_chua_ht = ov["is_chua_hoan_thanh"] if ov else False

        sp_obj = _SP(
            ke_khai_id=kk.id,
            cong_chuc_id=cc.id,
            don_vi_id=cc.don_vi_id,
            trang_thai=kk.trang_thai,
            so_luong=kk.so_luong or 1,
            so_sp_goc=_to_float(kk.so_sp_goc_quy_doi),
            so_sp_chat_luong_chot=_to_float(kk.so_sp_chat_luong),
            so_sp_tien_do_chot=_to_float(kk.so_sp_tien_do),
            tu_dg_cl=kk.tu_danh_gia_chat_luong or 0,
            tu_dg_td=kk.tu_danh_gia_tien_do or 0,
            he_so_quy_doi=_to_float(kk.he_so_quy_doi_snapshot) if kk.he_so_quy_doi_snapshot else 0.0,
            is_chua_hoan_thanh=eff_chua_ht,
        )
        if ov:
            _apply_overrides_inplace([sp_obj], {kk.id: ov})
        sp_cl, sp_td = _resolve_sp_cl_td(sp_obj)
        is_self = cc.id == user.id
        out.append({
            "ke_khai_id": str(kk.id),
            "loai": "TU_LAM" if is_self else "CAP_DUOI",
            "cong_chuc_id": str(cc.id),
            "ma_cc": cc.ma_cc,
            "ho_ten": cc.ho_ten,
            "chuc_vu": cc.chuc_vu,
            "danh_muc_sp_id": str(dm.id) if dm else None,
            "ma_danh_muc": dm.ma_danh_muc if dm else None,
            "ten_cong_viec": dm.ten_cong_viec if dm else None,
            "linh_vuc": dm.linh_vuc if dm else None,
            "nhom_pl3": dm.nhom_pl3 if dm else None,
            "ngay_thuc_hien": kk.ngay_thuc_hien.isoformat() if kk.ngay_thuc_hien else None,
            "so_luong": kk.so_luong,
            "so_sp_goc_quy_doi": _to_float(kk.so_sp_goc_quy_doi),
            "sp_chat_luong": sp_cl,
            "sp_tien_do": sp_td,
            # Giá trị HIỆU LỰC (sau override) — LĐ đang dùng tính KPI
            "so_loi_chat_luong": eff_loi_cl,
            "so_loi_tien_do": eff_loi_td,
            "tu_danh_gia_chat_luong": kk.tu_danh_gia_chat_luong or 0,
            "tu_danh_gia_tien_do": kk.tu_danh_gia_tien_do or 0,
            "trang_thai": kk.trang_thai.value if hasattr(kk.trang_thai, "value") else str(kk.trang_thai),
            "is_chua_hoan_thanh": eff_chua_ht,
            "co_dieu_chinh": ov is not None,  # NEW: badge cho UI
            # Giá trị gốc của CC (để hiển thị "đã điều chỉnh từ X → Y")
            "so_loi_chat_luong_goc": kk.so_loi_chat_luong or 0,
            "so_loi_tien_do_goc": kk.so_loi_tien_do or 0,
        })
    return out


async def calc_kpi_lanh_dao_v2(
    db: AsyncSession,
    cong_chuc_id: UUID,
    thang: int,
    nam: int,
    *,
    tam_tinh: bool = False,
) -> dict:
    """
    Tính KPI lãnh đạo theo công thức MỚI cho 1 LĐ ở 1 tháng.

    Args:
        tam_tinh: False (default) → chỉ DA_PHE_DUYET (chính thức).
                  True → cả NHAP/CHO_PHE_DUYET/DA_PHE_DUYET (dùng tu_danh_gia
                  cho bản chưa duyệt).
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
        scope_total = await _sp_pdv_scope(db, user.id, thang, nam, tam_tinh=tam_tinh)
    elif cap_bac == CapBacVaiTro.TRUONG_DON_VI:
        scope_total = await _sp_trong_don_vi(
            db, [user.don_vi_id], thang, nam, tam_tinh=tam_tinh
        )
    else:  # PCCT / CCT
        ngay_chot = _ngay_chot_cua_thang(thang, nam)
        don_vi_ids = await get_don_vi_phu_trach(db, user.id, ngay_chot)
        has_phan_cong = len(don_vi_ids) > 0
        scope_total = await _sp_trong_don_vi(
            db, don_vi_ids, thang, nam, tam_tinh=tam_tinh
        )

    # Tách SP CHÍNH LĐ TỰ KÊ (cong_chuc_id == user.id) vs SP TỔNG
    scope_self = [sp for sp in scope_total if sp.cong_chuc_id == user.id]

    # Tính tổng SP (TỔNG)
    # Mẫu số: TẤT CẢ SP gốc (kể cả CV chưa HT)
    # Tử số a/b/c: CV is_chua_hoan_thanh = true → đóng 0 (giảm cả 3 chỉ số)
    tong_sp_ke_khai = sum(sp.so_sp_goc for sp in scope_total)
    sp_hoan_thanh = 0.0
    sp_chat_luong = 0.0
    sp_tien_do = 0.0
    for sp in scope_total:
        if sp.is_chua_hoan_thanh:
            continue  # CV chưa HT → tử số += 0
        cl, td = _resolve_sp_cl_td(sp)
        sp_hoan_thanh += sp.so_sp_goc
        sp_chat_luong += cl
        sp_tien_do += td

    # NAMING LEGACY (07/05/2026): b=CHẤT LƯỢNG, c=TIẾN ĐỘ — đồng bộ với
    # convention UI và CC V2. (Spec gốc viết b=TĐ, c=CL nhưng codebase
    # đã dùng legacy reversed ở mọi nơi → giữ consistency.)
    if tong_sp_ke_khai > 0:
        a = min(1.0, sp_hoan_thanh / tong_sp_ke_khai)
        b = min(1.0, sp_chat_luong / tong_sp_ke_khai)  # Chất lượng
        c = min(1.0, sp_tien_do / tong_sp_ke_khai)    # Tiến độ
    else:
        a = b = c = 0.0

    # Tính tổng SP (TỰ KÊ — riêng LĐ)
    tong_sp_self = sum(sp.so_sp_goc for sp in scope_self)
    sp_ht_self = 0.0
    sp_cl_self = 0.0
    sp_td_self = 0.0
    for sp in scope_self:
        if sp.is_chua_hoan_thanh:
            continue
        cl, td = _resolve_sp_cl_td(sp)
        sp_ht_self += sp.so_sp_goc
        sp_cl_self += cl
        sp_td_self += td

    if tong_sp_self > 0:
        a_self = min(1.0, sp_ht_self / tong_sp_self)
        b_self = min(1.0, sp_cl_self / tong_sp_self)  # Chất lượng
        c_self = min(1.0, sp_td_self / tong_sp_self)  # Tiến độ
    else:
        a_self = b_self = c_self = 0.0

    # tong_sp_hoan_thanh dùng cho response field
    tong_sp_hoan_thanh = sp_hoan_thanh

    # d, đ, e — truyền tam_tinh xuống để tab "Tạm tính" UI thấy bản CHO_PHE_DUYET
    d, dd, e = await _get_dde(db, cong_chuc_id, thang, nam, tam_tinh=tam_tinh)

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
        "tam_tinh": tam_tinh,
    }
