"""
app/api/v1/endpoints/dieu_chinh_kqcv.py
=======================================
API điều chỉnh KQCV của LĐ (Yêu cầu 2 — 06/05/2026).

Workflow:
1. POST /          : LĐ tạo bản đề xuất (auto NHAP → CHO_PHE_DUYET nếu auto_submit=true)
2. PUT /{id}       : Sửa khi NHAP
3. POST /{id}/gui-duyet
4. POST /{id}/phe-duyet  (chỉ nguoi_phe_duyet_id) → APPLY vào kpi_submission
5. POST /{id}/tu-choi
6. DELETE /{id}    : Xóa bản NHAP của chính mình
7. GET  /me            : list của mình (đã/đang đề xuất)
8. GET  /cho-toi-duyet : list chờ tôi duyệt
9. GET  /lich-su-cv/{ke_khai_id} : tất cả lần điều chỉnh của 1 CV
"""

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import ActiveUserDep, DatabaseDep
from app.core.kpi_calculator_v2 import calculate_sp_dat_v2
from app.core.kpi_lanh_dao_v2 import (
    _ngay_chot_cua_thang,
    get_don_vi_phu_trach,
    is_kpi_lanh_dao_v2_active,
)
from app.models.dieu_chinh_kqcv import DieuChinhKqcv
from app.models.kpi_submission import KeKhaiCongViec, TrangThaiKeKhai
from app.models.phan_cong_phu_trach import PhanCongPhuTrach
from app.models.user_org import CapBacVaiTro, CongChuc, VaiTro
from app.schemas.common import success_response
from app.schemas.dieu_chinh_kqcv import (
    DieuChinhCreateRequest,
    DieuChinhResponse,
    DieuChinhUpdateRequest,
    GiaTriKQCV,
    PheDuyetRequest,
    TuChoiRequest,
)


router = APIRouter()


TT_NHAP = "NHAP"
TT_CHO = "CHO_PHE_DUYET"
TT_DA = "DA_PHE_DUYET"
TT_TC = "TU_CHOI"


# =============================================================================
# HELPERS
# =============================================================================

LANH_DAO_CAP_BAC = {
    CapBacVaiTro.PHO_DON_VI,
    CapBacVaiTro.TRUONG_DON_VI,
    CapBacVaiTro.PHO_CHI_CUC_TRUONG,
    CapBacVaiTro.CHI_CUC_TRUONG,
}


def _ensure_lanh_dao(user: CongChuc) -> None:
    if not user.vai_tro or user.vai_tro.cap_bac not in LANH_DAO_CAP_BAC:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "error": {"code": "DCKQCV_403", "message": "Chỉ lãnh đạo có chức năng này"},
            },
        )


async def _resolve_nguoi_phe_duyet_for_dc(
    db: AsyncSession, user: CongChuc
) -> Optional[UUID]:
    """
    Xác định cấp trên duyệt điều chỉnh theo cấp bậc của LĐ điều chỉnh:
    - PDV → TDV cùng đơn vị (fallback CCT)
    - TDV → CCT
    - PCCT → CCT
    - CCT → tự duyệt (chính mình)
    """
    if user.vai_tro is None:
        return None
    cap_bac = user.vai_tro.cap_bac

    if cap_bac == CapBacVaiTro.CHI_CUC_TRUONG:
        return user.id

    cct_stmt = (
        select(CongChuc.id)
        .join(VaiTro, VaiTro.id == CongChuc.vai_tro_id)
        .where(
            VaiTro.cap_bac == CapBacVaiTro.CHI_CUC_TRUONG,
            CongChuc.is_deleted == False,  # noqa: E712
            CongChuc.is_active == True,  # noqa: E712
        )
        .limit(1)
    )
    cct_id = (await db.execute(cct_stmt)).scalar_one_or_none()

    if cap_bac in (CapBacVaiTro.PHO_CHI_CUC_TRUONG, CapBacVaiTro.TRUONG_DON_VI):
        return cct_id

    if cap_bac == CapBacVaiTro.PHO_DON_VI:
        stmt = (
            select(CongChuc.id)
            .join(VaiTro, VaiTro.id == CongChuc.vai_tro_id)
            .where(
                CongChuc.don_vi_id == user.don_vi_id,
                VaiTro.cap_bac == CapBacVaiTro.TRUONG_DON_VI,
                CongChuc.is_deleted == False,  # noqa: E712
                CongChuc.is_active == True,  # noqa: E712
            )
            .limit(1)
        )
        tdv_id = (await db.execute(stmt)).scalar_one_or_none()
        return tdv_id or cct_id

    return None


async def _check_ke_khai_in_scope(
    db: AsyncSession, user: CongChuc, ke_khai: KeKhaiCongViec
) -> None:
    """LĐ chỉ điều chỉnh được CV trong scope KPI của mình."""
    cap_bac = user.vai_tro.cap_bac

    if cap_bac == CapBacVaiTro.PHO_DON_VI:
        ok = (
            ke_khai.cong_chuc_id == user.id
            or ke_khai.nguoi_phe_duyet_id == user.id
        )
    elif cap_bac == CapBacVaiTro.TRUONG_DON_VI:
        # Toàn đơn vị → check don_vi của người kê
        cc = (
            await db.execute(
                select(CongChuc).where(CongChuc.id == ke_khai.cong_chuc_id)
            )
        ).scalar_one()
        ok = cc.don_vi_id == user.don_vi_id
    elif cap_bac in (CapBacVaiTro.PHO_CHI_CUC_TRUONG, CapBacVaiTro.CHI_CUC_TRUONG):
        ngay_chot = _ngay_chot_cua_thang(ke_khai.thang, ke_khai.nam)
        don_vi_ids = await get_don_vi_phu_trach(db, user.id, ngay_chot)
        cc = (
            await db.execute(
                select(CongChuc).where(CongChuc.id == ke_khai.cong_chuc_id)
            )
        ).scalar_one()
        ok = cc.don_vi_id in don_vi_ids
    else:
        ok = False

    if not ok:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "error": {
                    "code": "DCKQCV_403_SCOPE",
                    "message": "CV này không nằm trong scope KPI của bạn",
                },
            },
        )


async def _snapshot_kk(db: AsyncSession, kk: KeKhaiCongViec) -> dict:
    """
    Snapshot giá trị HIỆU LỰC HIỆN TẠI cho LĐ trước khi sửa:
    - Nếu CV đã có 1 bản điều chỉnh DA_PHE_DUYET trước đó → snapshot lấy từ đó
      (= giá trị LĐ đang dùng tính KPI).
    - Nếu chưa có → lấy từ kpi_submission (giá trị gốc của CC).
    """
    from app.core.kpi_lanh_dao_v2 import _load_dieu_chinh_overrides
    overrides = await _load_dieu_chinh_overrides(db, [kk.id])
    ov = overrides.get(kk.id)
    if ov:
        return {
            "so_loi_chat_luong": ov["so_loi_chat_luong"],
            "so_loi_tien_do": ov["so_loi_tien_do"],
            "is_chua_hoan_thanh": ov["is_chua_hoan_thanh"],
        }
    return {
        "so_loi_chat_luong": int(kk.so_loi_chat_luong or 0),
        "so_loi_tien_do": int(kk.so_loi_tien_do or 0),
        "is_chua_hoan_thanh": False,
    }


async def _load_dc(db: AsyncSession, dc_id: UUID) -> DieuChinhKqcv:
    stmt = (
        select(DieuChinhKqcv)
        .options(
            selectinload(DieuChinhKqcv.nguoi_dieu_chinh),
            selectinload(DieuChinhKqcv.nguoi_phe_duyet),
        )
        .where(DieuChinhKqcv.id == dc_id, DieuChinhKqcv.is_deleted == False)  # noqa: E712
    )
    dc = (await db.execute(stmt)).scalar_one_or_none()
    if not dc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": {"code": "DCKQCV_404", "message": "Không tìm thấy bản điều chỉnh"},
            },
        )
    return dc


async def _flush_and_response(db: AsyncSession, dc: DieuChinhKqcv) -> dict:
    await db.flush()
    await db.refresh(dc, ["updated_at", "ngay_phe_duyet", "trang_thai"])
    return DieuChinhResponse.model_validate(dc).model_dump(mode="json")


def _to_response(dc: DieuChinhKqcv) -> dict:
    return DieuChinhResponse.model_validate(dc).model_dump(mode="json")


# Note (06/05/2026): _apply_to_kekhai đã bị BỎ.
# Theo quyết định nghiệp vụ mới: điều chỉnh CHỈ ảnh hưởng KPI LĐ, KHÔNG đụng
# kpi_submission. KPI CC giữ nguyên giá trị gốc; KPI LĐ đọc override từ
# bảng dieu_chinh_kqcv (xem _load_dieu_chinh_overrides trong kpi_lanh_dao_v2.py).


# =============================================================================
# CREATE
# =============================================================================

@router.post(
    "",
    summary="LĐ tạo bản đề xuất điều chỉnh CV",
    status_code=status.HTTP_201_CREATED,
)
async def create_dieu_chinh(
    payload: DieuChinhCreateRequest,
    db: DatabaseDep,
    current_user: ActiveUserDep,
):
    _ensure_lanh_dao(current_user)

    # Load CV
    kk = (
        await db.execute(
            select(KeKhaiCongViec).where(
                KeKhaiCongViec.id == payload.ke_khai_id,
                KeKhaiCongViec.is_deleted == False,  # noqa: E712
            )
        )
    ).scalar_one_or_none()
    if not kk:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"success": False, "error": {"code": "DCKQCV_404_KK", "message": "Không tìm thấy CV"}},
        )

    # Chặn nếu báo cáo xếp loại đã chốt
    if kk.is_khoa:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "error": {"code": "DCKQCV_400_KHOA", "message": "CV đã bị khóa, không thể điều chỉnh"},
            },
        )

    # Chặn nếu tháng < flag (V2 chưa active → không có cơ chế điều chỉnh KPI v2)
    if not is_kpi_lanh_dao_v2_active(kk.thang, kk.nam):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "error": {"code": "DCKQCV_400_V1", "message": "Chỉ điều chỉnh được CV V2 (từ tháng 4/2026)"},
            },
        )

    await _check_ke_khai_in_scope(db, current_user, kk)

    # Resolve người duyệt
    npd_id = await _resolve_nguoi_phe_duyet_for_dc(db, current_user)
    if not npd_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"success": False, "error": {"code": "DCKQCV_400_NPD", "message": "Không xác định được người phê duyệt"}},
        )

    dc = DieuChinhKqcv(
        ke_khai_id=kk.id,
        nguoi_dieu_chinh_id=current_user.id,
        nguoi_phe_duyet_id=npd_id,
        gia_tri_cu=await _snapshot_kk(db, kk),
        gia_tri_moi=payload.gia_tri_moi.model_dump(),
        ly_do=payload.ly_do,
        trang_thai=TT_NHAP,
    )
    db.add(dc)
    await db.flush()
    await db.refresh(dc, ["nguoi_dieu_chinh", "nguoi_phe_duyet"])

    return success_response(data=_to_response(dc), message="Tạo bản điều chỉnh (NHAP) thành công")


# =============================================================================
# UPDATE (chỉ NHAP của chính mình)
# =============================================================================

@router.put("/{dc_id}", summary="Sửa bản điều chỉnh khi còn NHAP")
async def update_dieu_chinh(
    dc_id: UUID,
    payload: DieuChinhUpdateRequest,
    db: DatabaseDep,
    current_user: ActiveUserDep,
):
    _ensure_lanh_dao(current_user)
    dc = await _load_dc(db, dc_id)

    if dc.nguoi_dieu_chinh_id != current_user.id:
        raise HTTPException(status_code=403, detail={"success": False, "error": {"code": "DCKQCV_403_OWN", "message": "Chỉ chủ bản điều chỉnh được sửa"}})
    if dc.trang_thai != TT_NHAP:
        raise HTTPException(status_code=400, detail={"success": False, "error": {"code": "DCKQCV_400_STATE", "message": "Chỉ sửa khi đang NHAP"}})

    if payload.gia_tri_moi is not None:
        dc.gia_tri_moi = payload.gia_tri_moi.model_dump()
    if payload.ly_do is not None:
        dc.ly_do = payload.ly_do
    data = await _flush_and_response(db, dc)
    return success_response(data=data, message="Cập nhật thành công")


# =============================================================================
# DELETE (NHAP)
# =============================================================================

@router.delete("/{dc_id}", summary="Xóa bản điều chỉnh NHAP")
async def delete_dieu_chinh(dc_id: UUID, db: DatabaseDep, current_user: ActiveUserDep):
    _ensure_lanh_dao(current_user)
    dc = await _load_dc(db, dc_id)
    if dc.nguoi_dieu_chinh_id != current_user.id:
        raise HTTPException(status_code=403, detail={"success": False, "error": {"code": "DCKQCV_403_OWN", "message": "Chỉ chủ bản điều chỉnh được xóa"}})
    if dc.trang_thai != TT_NHAP:
        raise HTTPException(status_code=400, detail={"success": False, "error": {"code": "DCKQCV_400_STATE", "message": "Chỉ xóa khi đang NHAP"}})
    dc.is_deleted = True
    await db.flush()
    return success_response(data={"id": str(dc_id)}, message="Đã xóa")


# =============================================================================
# GỬI DUYỆT
# =============================================================================

@router.post("/{dc_id}/gui-duyet", summary="LĐ gửi điều chỉnh lên cấp trên duyệt")
async def gui_duyet(dc_id: UUID, db: DatabaseDep, current_user: ActiveUserDep):
    _ensure_lanh_dao(current_user)
    dc = await _load_dc(db, dc_id)
    if dc.nguoi_dieu_chinh_id != current_user.id:
        raise HTTPException(status_code=403, detail={"success": False, "error": {"code": "DCKQCV_403_OWN", "message": "Không phải chủ"}})
    if dc.trang_thai != TT_NHAP:
        raise HTTPException(status_code=400, detail={"success": False, "error": {"code": "DCKQCV_400_STATE", "message": "Chỉ gửi khi NHAP"}})
    dc.trang_thai = TT_CHO
    data = await _flush_and_response(db, dc)
    return success_response(data=data, message="Đã gửi duyệt")


# =============================================================================
# PHÊ DUYỆT (cấp trên) → APPLY
# =============================================================================

@router.post("/{dc_id}/phe-duyet", summary="Cấp trên duyệt + áp dụng vào kpi_submission")
async def phe_duyet(
    dc_id: UUID,
    payload: PheDuyetRequest,
    db: DatabaseDep,
    current_user: ActiveUserDep,
):
    _ensure_lanh_dao(current_user)
    dc = await _load_dc(db, dc_id)
    if dc.nguoi_phe_duyet_id != current_user.id:
        raise HTTPException(status_code=403, detail={"success": False, "error": {"code": "DCKQCV_403_NPD", "message": "Bạn không phải người phê duyệt"}})
    if dc.trang_thai != TT_CHO:
        raise HTTPException(status_code=400, detail={"success": False, "error": {"code": "DCKQCV_400_STATE", "message": "Chỉ duyệt khi đang CHO_PHE_DUYET"}})

    # Phê duyệt → KPI LĐ đọc override từ bảng này (KHÔNG đụng kpi_submission của CC)
    dc.trang_thai = TT_DA
    dc.y_kien_phe_duyet = payload.y_kien
    dc.ngay_phe_duyet = datetime.now(tz=timezone.utc)
    data = await _flush_and_response(db, dc)
    return success_response(data=data, message="Đã duyệt — KPI lãnh đạo đã cập nhật")


# =============================================================================
# TỪ CHỐI
# =============================================================================

@router.post("/{dc_id}/tu-choi", summary="Cấp trên từ chối điều chỉnh")
async def tu_choi(
    dc_id: UUID,
    payload: TuChoiRequest,
    db: DatabaseDep,
    current_user: ActiveUserDep,
):
    _ensure_lanh_dao(current_user)
    dc = await _load_dc(db, dc_id)
    if dc.nguoi_phe_duyet_id != current_user.id:
        raise HTTPException(status_code=403, detail={"success": False, "error": {"code": "DCKQCV_403_NPD", "message": "Không phải NPD"}})
    if dc.trang_thai != TT_CHO:
        raise HTTPException(status_code=400, detail={"success": False, "error": {"code": "DCKQCV_400_STATE", "message": "Chỉ từ chối khi CHO_PHE_DUYET"}})
    dc.trang_thai = TT_TC
    dc.y_kien_phe_duyet = payload.y_kien
    dc.ngay_phe_duyet = datetime.now(tz=timezone.utc)
    data = await _flush_and_response(db, dc)
    return success_response(data=data, message="Đã từ chối")


# =============================================================================
# LIST: của tôi / chờ tôi duyệt / lịch sử CV
# =============================================================================

@router.get("/me", summary="List bản điều chỉnh tôi đề xuất")
async def list_me(
    db: DatabaseDep,
    current_user: ActiveUserDep,
    trang_thai: Optional[str] = Query(default=None),
):
    _ensure_lanh_dao(current_user)
    stmt = (
        select(DieuChinhKqcv)
        .options(
            selectinload(DieuChinhKqcv.nguoi_dieu_chinh),
            selectinload(DieuChinhKqcv.nguoi_phe_duyet),
        )
        .where(
            DieuChinhKqcv.nguoi_dieu_chinh_id == current_user.id,
            DieuChinhKqcv.is_deleted == False,  # noqa: E712
        )
        .order_by(DieuChinhKqcv.created_at.desc())
    )
    if trang_thai:
        stmt = stmt.where(DieuChinhKqcv.trang_thai == trang_thai)
    rows = (await db.execute(stmt)).scalars().unique().all()
    return success_response(data=[_to_response(r) for r in rows])


@router.get("/cho-toi-duyet", summary="List bản điều chỉnh chờ tôi duyệt")
async def list_cho_toi_duyet(db: DatabaseDep, current_user: ActiveUserDep):
    _ensure_lanh_dao(current_user)
    stmt = (
        select(DieuChinhKqcv)
        .options(
            selectinload(DieuChinhKqcv.nguoi_dieu_chinh),
            selectinload(DieuChinhKqcv.nguoi_phe_duyet),
        )
        .where(
            DieuChinhKqcv.nguoi_phe_duyet_id == current_user.id,
            DieuChinhKqcv.trang_thai == TT_CHO,
            DieuChinhKqcv.is_deleted == False,  # noqa: E712
        )
        .order_by(DieuChinhKqcv.created_at.desc())
    )
    rows = (await db.execute(stmt)).scalars().unique().all()
    return success_response(data=[_to_response(r) for r in rows])


@router.get("/lich-su-cv/{ke_khai_id}", summary="Lịch sử mọi lần điều chỉnh của 1 CV")
async def list_lich_su_cv(
    ke_khai_id: UUID, db: DatabaseDep, current_user: ActiveUserDep
):
    """Cho cả LĐ + CC sở hữu CV xem được."""
    # Validate quyền: CC sở hữu CV / LĐ trong scope / Admin
    kk = (
        await db.execute(
            select(KeKhaiCongViec).where(KeKhaiCongViec.id == ke_khai_id)
        )
    ).scalar_one_or_none()
    if not kk:
        raise HTTPException(
            status_code=404, detail={"success": False, "error": {"code": "DCKQCV_404_KK", "message": "Không tìm thấy CV"}}
        )

    is_owner = kk.cong_chuc_id == current_user.id
    is_admin = getattr(current_user.vai_tro, "is_system_admin", False) if current_user.vai_tro else False
    is_ld = current_user.vai_tro and current_user.vai_tro.cap_bac in LANH_DAO_CAP_BAC
    if not (is_owner or is_admin or is_ld):
        raise HTTPException(status_code=403, detail={"success": False, "error": {"code": "DCKQCV_403", "message": "Không có quyền xem"}})

    stmt = (
        select(DieuChinhKqcv)
        .options(
            selectinload(DieuChinhKqcv.nguoi_dieu_chinh),
            selectinload(DieuChinhKqcv.nguoi_phe_duyet),
        )
        .where(
            DieuChinhKqcv.ke_khai_id == ke_khai_id,
            DieuChinhKqcv.is_deleted == False,  # noqa: E712
        )
        .order_by(DieuChinhKqcv.created_at.desc())
    )
    rows = (await db.execute(stmt)).scalars().unique().all()
    return success_response(data=[_to_response(r) for r in rows])
