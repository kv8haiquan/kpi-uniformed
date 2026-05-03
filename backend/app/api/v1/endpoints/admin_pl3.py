"""
app/api/v1/endpoints/admin_pl3.py
=================================
Admin CRUD danh mục PL3 (Phase C — 28/04/2026).

Routes:
- GET    /admin/danh-muc-pl3                   List có filter
- POST   /admin/danh-muc-pl3                   Tạo mới (manual entry)
- GET    /admin/danh-muc-pl3/{id}              Detail
- PUT    /admin/danh-muc-pl3/{id}              Sửa
- DELETE /admin/danh-muc-pl3/{id}              Soft delete (is_active=FALSE)

- GET    /admin/danh-muc-v1                    List V1 (read-only sau cutover)
- PUT    /admin/danh-muc-v1/{id}/deactivate    Soft deactivate

- PUT    /admin/cong-chuc/{id}/kpi-version     Pin version cho 1 CC
- PUT    /admin/don-vi/{id}/kpi-version        Bulk pin cho cả đơn vị

LOCKED 13: Snapshot final — sửa danh mục KHÔNG ảnh hưởng kê khai cũ
(snapshot lưu trong ke_khai_cong_viec.he_so_quy_doi_snapshot lúc tạo).

Audit log: mọi UPDATE/DELETE/CREATE đều ghi vào audit_log.
"""

from decimal import Decimal
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, Request, status
from sqlalchemy import func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import AdminUserDep, DatabaseDep
from app.models.audit_log import AuditAction, AuditLog
from app.models.task_catalog import DanhMucSpCongViec
from app.models.user_org import CongChuc, DonVi
from app.schemas.admin_pl3 import (
    NHOM_KHUNG_MAP,
    DanhMucPL3CreateRequest,
    DanhMucPL3Response,
    DanhMucPL3UpdateRequest,
    KpiVersionPinRequest,
)
from app.schemas.common import (
    DataResponse,
    Pagination,
    PaginatedResponse,
    error_response,
    success_response,
)


router = APIRouter()


# =============================================================================
# HELPERS
# =============================================================================

async def _get_dm_or_404(db: AsyncSession, dm_id: UUID, expect_pl3: bool = True) -> DanhMucSpCongViec:
    stmt = (
        select(DanhMucSpCongViec)
        .where(DanhMucSpCongViec.id == dm_id)
        .where(DanhMucSpCongViec.is_deleted == False)  # noqa: E712
    )
    dm = (await db.execute(stmt)).scalar_one_or_none()
    if not dm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response(code="NOT_FOUND", message="Không tìm thấy danh mục"),
        )
    if expect_pl3 and dm.nguon_du_lieu != "PL3":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_response(
                code="WRONG_VERSION",
                message=f"Mục này là V1 ('{dm.ma_danh_muc}'), không thể sửa qua endpoint PL3",
            ),
        )
    return dm


async def _lookup_ten_linh_vuc(db: AsyncSession, linh_vuc: str) -> Optional[str]:
    """Tìm ten_linh_vuc đã có trong dataset PL3 cho linh_vuc=X."""
    stmt = (
        select(DanhMucSpCongViec.ten_linh_vuc)
        .where(DanhMucSpCongViec.linh_vuc == linh_vuc)
        .where(DanhMucSpCongViec.ten_linh_vuc.isnot(None))
        .limit(1)
    )
    return (await db.execute(stmt)).scalar_one_or_none()


def _to_response(dm: DanhMucSpCongViec) -> dict:
    return {
        "id": dm.id,
        "ma_danh_muc": dm.ma_danh_muc,
        "ten_cong_viec": dm.ten_cong_viec,
        "mo_ta": dm.mo_ta,
        "nguon_du_lieu": dm.nguon_du_lieu,
        "linh_vuc": dm.linh_vuc,
        "ten_linh_vuc": dm.ten_linh_vuc,
        "nhiem_vu": dm.nhiem_vu,
        "cong_viec_chi_tiet": dm.cong_viec_chi_tiet,
        "san_pham_dau_ra": dm.san_pham_dau_ra,
        "nhom_pl3": dm.nhom_pl3,
        "khung_diem_toi_da": dm.khung_diem_toi_da,
        "diem_cham": dm.diem_cham,
        "he_so_quy_doi": float(dm.he_so_quy_doi) if dm.he_so_quy_doi is not None else None,
        "is_active": dm.is_active,
        "created_at": dm.created_at,
        "updated_at": dm.updated_at,
    }


def _dm_snapshot_dict(dm: DanhMucSpCongViec) -> dict:
    """Snapshot dict dùng cho audit_log."""
    return {
        "ma_danh_muc": dm.ma_danh_muc,
        "ten_cong_viec": dm.ten_cong_viec,
        "linh_vuc": dm.linh_vuc,
        "nhom_pl3": dm.nhom_pl3,
        "diem_cham": dm.diem_cham,
        "he_so_quy_doi": float(dm.he_so_quy_doi) if dm.he_so_quy_doi is not None else None,
        "khung_diem_toi_da": dm.khung_diem_toi_da,
        "is_active": dm.is_active,
        "nguon_du_lieu": dm.nguon_du_lieu,
    }


def _audit(
    db: AsyncSession,
    table_name: str,
    record_id: UUID,
    action: AuditAction,
    user_id: UUID,
    request: Request,
    old_value: Optional[dict] = None,
    new_value: Optional[dict] = None,
) -> None:
    """Helper ghi audit log."""
    log = AuditLog.create_log(
        table_name=table_name,
        record_id=record_id,
        action=action,
        user_id=user_id,
        old_value=old_value,
        new_value=new_value,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    db.add(log)


# =============================================================================
# CRUD danh mục PL3
# =============================================================================

@router.get("/danh-muc-pl3", summary="List danh mục PL3 với filter (admin)")
async def list_danh_muc_pl3(
    db: DatabaseDep,
    current_user: AdminUserDep,
    linh_vuc: Optional[str] = Query(default=None),
    nhom_pl3: Optional[int] = Query(default=None, ge=1, le=5),
    search: Optional[str] = Query(default=None, min_length=1, max_length=200),
    is_active: Optional[bool] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
) -> dict:
    base_q = (
        select(DanhMucSpCongViec)
        .where(DanhMucSpCongViec.nguon_du_lieu == "PL3")
        .where(DanhMucSpCongViec.is_deleted == False)  # noqa: E712
    )
    count_q = (
        select(func.count(DanhMucSpCongViec.id))
        .where(DanhMucSpCongViec.nguon_du_lieu == "PL3")
        .where(DanhMucSpCongViec.is_deleted == False)  # noqa: E712
    )

    if linh_vuc:
        base_q = base_q.where(DanhMucSpCongViec.linh_vuc == linh_vuc.upper())
        count_q = count_q.where(DanhMucSpCongViec.linh_vuc == linh_vuc.upper())
    if nhom_pl3 is not None:
        base_q = base_q.where(DanhMucSpCongViec.nhom_pl3 == nhom_pl3)
        count_q = count_q.where(DanhMucSpCongViec.nhom_pl3 == nhom_pl3)
    if is_active is not None:
        base_q = base_q.where(DanhMucSpCongViec.is_active == is_active)
        count_q = count_q.where(DanhMucSpCongViec.is_active == is_active)
    if search:
        pat = f"%{search}%"
        cond = or_(
            DanhMucSpCongViec.ten_cong_viec.ilike(pat),
            DanhMucSpCongViec.ma_danh_muc.ilike(pat),
            DanhMucSpCongViec.cong_viec_chi_tiet.ilike(pat),
        )
        base_q = base_q.where(cond)
        count_q = count_q.where(cond)

    total = (await db.execute(count_q)).scalar() or 0
    offset = (page - 1) * page_size
    base_q = base_q.order_by(
        DanhMucSpCongViec.linh_vuc.asc(),
        DanhMucSpCongViec.ma_danh_muc.asc(),
    ).offset(offset).limit(page_size)
    rows = (await db.execute(base_q)).scalars().all()

    pagination = Pagination.create(page=page, page_size=page_size, total_items=total)
    return {
        "success": True,
        "data": [_to_response(r) for r in rows],
        "pagination": pagination.model_dump(),
    }


@router.get("/danh-muc-pl3/{dm_id}", summary="Detail mục PL3")
async def get_danh_muc_pl3(
    dm_id: UUID,
    db: DatabaseDep,
    current_user: AdminUserDep,
) -> dict:
    dm = await _get_dm_or_404(db, dm_id, expect_pl3=True)
    return success_response(data=_to_response(dm))


@router.post("/danh-muc-pl3", status_code=status.HTTP_201_CREATED, summary="Tạo mục PL3")
async def create_danh_muc_pl3(
    payload: DanhMucPL3CreateRequest,
    db: DatabaseDep,
    current_user: AdminUserDep,
    request: Request,
) -> dict:
    # Check unique ma_danh_muc
    exists = (await db.execute(
        select(DanhMucSpCongViec.id).where(DanhMucSpCongViec.ma_danh_muc == payload.ma_danh_muc)
    )).scalar_one_or_none()
    if exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_response(
                code="DUPLICATE_MA",
                message=f"ma_danh_muc='{payload.ma_danh_muc}' đã tồn tại",
            ),
        )

    # Auto-compute
    he_so_quy_doi = Decimal(payload.diem_cham) / Decimal("25")
    khung_diem_toi_da = NHOM_KHUNG_MAP[payload.nhom_pl3]
    ten_linh_vuc = await _lookup_ten_linh_vuc(db, payload.linh_vuc)

    dm = DanhMucSpCongViec(
        ma_danh_muc=payload.ma_danh_muc,
        ten_cong_viec=payload.ten_cong_viec,
        mo_ta=payload.mo_ta,
        nguon_du_lieu="PL3",
        linh_vuc=payload.linh_vuc,
        ten_linh_vuc=ten_linh_vuc,
        nhiem_vu=payload.nhiem_vu,
        cong_viec_chi_tiet=payload.cong_viec_chi_tiet,
        san_pham_dau_ra=payload.san_pham_dau_ra,
        nhom_pl3=payload.nhom_pl3,
        khung_diem_toi_da=khung_diem_toi_da,
        diem_cham=payload.diem_cham,
        he_so_quy_doi=he_so_quy_doi,
        is_active=payload.is_active,
        sp_chuan_id=None,
        don_vi_ap_dung_id=None,
    )
    db.add(dm)
    await db.flush()

    _audit(
        db,
        table_name="danh_muc_sp_cong_viec",
        record_id=dm.id,
        action=AuditAction.INSERT,
        user_id=current_user.id,
        request=request,
        new_value=_dm_snapshot_dict(dm),
    )
    await db.commit()
    await db.refresh(dm)
    return success_response(data=_to_response(dm), message="Đã tạo mục PL3")


@router.put("/danh-muc-pl3/{dm_id}", summary="Sửa mục PL3")
async def update_danh_muc_pl3(
    dm_id: UUID,
    payload: DanhMucPL3UpdateRequest,
    db: DatabaseDep,
    current_user: AdminUserDep,
    request: Request,
) -> dict:
    dm = await _get_dm_or_404(db, dm_id, expect_pl3=True)
    old_snap = _dm_snapshot_dict(dm)

    update_data = payload.model_dump(exclude_unset=True)

    # Apply field updates
    if "ten_cong_viec" in update_data:
        dm.ten_cong_viec = update_data["ten_cong_viec"]
    if "mo_ta" in update_data:
        dm.mo_ta = update_data["mo_ta"]
    if "nhiem_vu" in update_data:
        dm.nhiem_vu = update_data["nhiem_vu"]
    if "cong_viec_chi_tiet" in update_data:
        dm.cong_viec_chi_tiet = update_data["cong_viec_chi_tiet"]
    if "san_pham_dau_ra" in update_data:
        dm.san_pham_dau_ra = update_data["san_pham_dau_ra"]
    if "is_active" in update_data:
        dm.is_active = update_data["is_active"]

    # linh_vuc đổi → cập nhật ten_linh_vuc
    if "linh_vuc" in update_data:
        dm.linh_vuc = update_data["linh_vuc"]
        dm.ten_linh_vuc = await _lookup_ten_linh_vuc(db, dm.linh_vuc)

    # nhom_pl3 hoặc diem_cham đổi → cross-validate + auto-compute
    new_nhom = update_data.get("nhom_pl3", dm.nhom_pl3)
    new_diem_cham = update_data.get("diem_cham", dm.diem_cham)
    if "nhom_pl3" in update_data or "diem_cham" in update_data:
        if new_nhom is None or new_diem_cham is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_response(
                    code="INCOMPLETE",
                    message="Thiếu nhom_pl3 hoặc diem_cham",
                ),
            )
        khung = NHOM_KHUNG_MAP.get(new_nhom)
        if khung is None or new_diem_cham > khung:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_response(
                    code="DIEM_CHAM_OVERFLOW",
                    message=f"diem_cham={new_diem_cham} vượt khung Nhóm {new_nhom} (max {khung})",
                ),
            )
        dm.nhom_pl3 = new_nhom
        dm.diem_cham = new_diem_cham
        dm.khung_diem_toi_da = khung
        dm.he_so_quy_doi = Decimal(new_diem_cham) / Decimal("25")

    await db.flush()

    _audit(
        db,
        table_name="danh_muc_sp_cong_viec",
        record_id=dm.id,
        action=AuditAction.UPDATE,
        user_id=current_user.id,
        request=request,
        old_value=old_snap,
        new_value=_dm_snapshot_dict(dm),
    )
    await db.commit()
    await db.refresh(dm)

    return success_response(data=_to_response(dm), message="Đã cập nhật")


@router.delete("/danh-muc-pl3/{dm_id}", summary="Soft delete (is_active=FALSE)")
async def delete_danh_muc_pl3(
    dm_id: UUID,
    db: DatabaseDep,
    current_user: AdminUserDep,
    request: Request,
) -> dict:
    dm = await _get_dm_or_404(db, dm_id, expect_pl3=True)

    # Check còn được dùng trong kê khai chưa khoá không
    from app.models.kpi_submission import KeKhaiCongViec
    used_count = (
        await db.execute(
            select(func.count(KeKhaiCongViec.id))
            .where(KeKhaiCongViec.danh_muc_sp_id == dm.id)
            .where(KeKhaiCongViec.is_khoa == False)  # noqa: E712
            .where(KeKhaiCongViec.is_deleted == False)  # noqa: E712
        )
    ).scalar() or 0

    if used_count > 0:
        # Vẫn cho deactivate (snapshot immutable, kê khai cũ không bị ảnh hưởng)
        # nhưng cảnh báo qua message.
        warn = f" (lưu ý: đang được dùng trong {used_count} kê khai chưa khoá)"
    else:
        warn = ""

    old_snap = _dm_snapshot_dict(dm)
    dm.is_active = False
    await db.flush()

    _audit(
        db,
        table_name="danh_muc_sp_cong_viec",
        record_id=dm.id,
        action=AuditAction.UPDATE,
        user_id=current_user.id,
        request=request,
        old_value=old_snap,
        new_value=_dm_snapshot_dict(dm),
    )
    await db.commit()

    return success_response(
        data={"id": dm.id, "ma_danh_muc": dm.ma_danh_muc, "is_active": False},
        message=f"Đã vô hiệu hóa '{dm.ma_danh_muc}'{warn}",
    )


# =============================================================================
# V1 read-only + deactivate
# =============================================================================

@router.get("/danh-muc-v1", summary="List V1 (legacy, read-only sau cutover)")
async def list_danh_muc_v1(
    db: DatabaseDep,
    current_user: AdminUserDep,
    is_active: Optional[bool] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
) -> dict:
    base_q = (
        select(DanhMucSpCongViec)
        .where(DanhMucSpCongViec.nguon_du_lieu == "V1")
        .where(DanhMucSpCongViec.is_deleted == False)  # noqa: E712
    )
    count_q = (
        select(func.count(DanhMucSpCongViec.id))
        .where(DanhMucSpCongViec.nguon_du_lieu == "V1")
        .where(DanhMucSpCongViec.is_deleted == False)  # noqa: E712
    )
    if is_active is not None:
        base_q = base_q.where(DanhMucSpCongViec.is_active == is_active)
        count_q = count_q.where(DanhMucSpCongViec.is_active == is_active)

    total = (await db.execute(count_q)).scalar() or 0
    offset = (page - 1) * page_size
    base_q = base_q.order_by(DanhMucSpCongViec.ma_danh_muc.asc()).offset(offset).limit(page_size)
    rows = (await db.execute(base_q)).scalars().all()

    pagination = Pagination.create(page=page, page_size=page_size, total_items=total)
    return {
        "success": True,
        "data": [_to_response(r) for r in rows],
        "pagination": pagination.model_dump(),
    }


@router.put("/danh-muc-v1/{dm_id}/deactivate", summary="Deactivate V1 mục")
async def deactivate_danh_muc_v1(
    dm_id: UUID,
    db: DatabaseDep,
    current_user: AdminUserDep,
    request: Request,
) -> dict:
    dm = await _get_dm_or_404(db, dm_id, expect_pl3=False)
    if dm.nguon_du_lieu != "V1":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_response(code="WRONG_VERSION", message="Mục này không phải V1"),
        )
    old_snap = _dm_snapshot_dict(dm)
    dm.is_active = False
    await db.flush()
    _audit(
        db,
        table_name="danh_muc_sp_cong_viec",
        record_id=dm.id,
        action=AuditAction.UPDATE,
        user_id=current_user.id,
        request=request,
        old_value=old_snap,
        new_value=_dm_snapshot_dict(dm),
    )
    await db.commit()
    return success_response(
        data={"id": dm.id, "ma_danh_muc": dm.ma_danh_muc, "is_active": False},
        message="Đã deactivate V1",
    )


# =============================================================================
# kpi_version_pinned (Task C.4)
# =============================================================================

@router.put("/cong-chuc/{cc_id}/kpi-version", summary="Pin KPI version cho 1 CC")
async def pin_cc_version(
    cc_id: UUID,
    payload: KpiVersionPinRequest,
    db: DatabaseDep,
    current_user: AdminUserDep,
    request: Request,
) -> dict:
    cc = (await db.execute(
        select(CongChuc).where(CongChuc.id == cc_id).where(CongChuc.is_deleted == False)  # noqa: E712
    )).scalar_one_or_none()
    if not cc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response(code="NOT_FOUND", message="Không tìm thấy công chức"),
        )

    old_value = {"kpi_version_pinned": cc.kpi_version_pinned}
    cc.kpi_version_pinned = payload.kpi_version_pinned
    await db.flush()

    _audit(
        db,
        table_name="cong_chuc",
        record_id=cc.id,
        action=AuditAction.UPDATE,
        user_id=current_user.id,
        request=request,
        old_value=old_value,
        new_value={"kpi_version_pinned": payload.kpi_version_pinned},
    )
    await db.commit()
    return success_response(
        data={"id": cc.id, "ma_cc": cc.ma_cc, "kpi_version_pinned": payload.kpi_version_pinned},
        message="Đã set version cho công chức",
    )


@router.put("/don-vi/{dv_id}/kpi-version", summary="Pin KPI version cho cả đơn vị (bulk)")
async def pin_don_vi_version(
    dv_id: UUID,
    payload: KpiVersionPinRequest,
    db: DatabaseDep,
    current_user: AdminUserDep,
    request: Request,
) -> dict:
    dv = (await db.execute(
        select(DonVi).where(DonVi.id == dv_id).where(DonVi.is_deleted == False)  # noqa: E712
    )).scalar_one_or_none()
    if not dv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response(code="NOT_FOUND", message="Không tìm thấy đơn vị"),
        )

    # Lấy tất cả CC active của đơn vị
    cc_rows = (await db.execute(
        select(CongChuc)
        .where(CongChuc.don_vi_id == dv_id)
        .where(CongChuc.is_active == True)  # noqa: E712
        .where(CongChuc.is_deleted == False)  # noqa: E712
    )).scalars().all()

    updated = 0
    for cc in cc_rows:
        if cc.kpi_version_pinned == payload.kpi_version_pinned:
            continue
        old_value = {"kpi_version_pinned": cc.kpi_version_pinned}
        cc.kpi_version_pinned = payload.kpi_version_pinned
        _audit(
            db,
            table_name="cong_chuc",
            record_id=cc.id,
            action=AuditAction.UPDATE,
            user_id=current_user.id,
            request=request,
            old_value=old_value,
            new_value={"kpi_version_pinned": payload.kpi_version_pinned},
        )
        updated += 1

    await db.commit()
    return success_response(
        data={
            "don_vi_id": dv.id,
            "ten_don_vi": dv.ten_don_vi,
            "total_cc": len(cc_rows),
            "updated": updated,
            "kpi_version_pinned": payload.kpi_version_pinned,
        },
        message=f"Đã update {updated}/{len(cc_rows)} CC",
    )
