"""
common_service/services/thong_bao_service.py
=============================================
Business logic cho Notification Center.

Public methods (frontend goi):
  - danh_sach: lay thong bao cua user, phan trang + loc
  - dem_chua_doc: dem so thong bao chua doc theo muc do
  - danh_dau_da_doc: danh dau 1 thong bao da doc
  - danh_dau_tat_ca_da_doc: danh dau tat ca chua doc -> da doc

Internal methods (module khac goi):
  - tao_thong_bao: tao 1 thong bao
  - tao_thong_bao_hang_loat: tao N thong bao (bulk insert)
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import case, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from common_service.models.thong_bao import ThongBao
from common_service.schemas.thong_bao import (
    LOAI_THONG_BAO,
    MUC_DO_THONG_BAO,
    ThongBaoCountResponse,
    ThongBaoCreateBulk,
    ThongBaoCreateInternal,
)


# ---------------------------------------------------------------------------
# Public methods — User-facing
# ---------------------------------------------------------------------------


async def danh_sach(
    db: AsyncSession,
    user_id: str,
    *,
    da_doc: Optional[bool] = None,
    loai: Optional[str] = None,
    muc_do: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[ThongBao], int]:
    """Lay danh sach thong bao cua user, phan trang + loc.

    Sap xep: muc_do KHAN dau tien, roi created_at DESC.
    Chi tra thong bao CUA MINH (nguoi_nhan_id = user.id).

    Returns:
        (items, total_count)
    """
    # Base query — chi cua user dang dang nhap
    base_filter = ThongBao.nguoi_nhan_id == uuid.UUID(user_id)

    # Loc theo da_doc
    if da_doc is not None:
        base_filter = base_filter & (ThongBao.da_doc == da_doc)

    # Loc theo loai
    if loai is not None:
        base_filter = base_filter & (ThongBao.loai == loai)

    # Loc theo muc do
    if muc_do is not None:
        base_filter = base_filter & (ThongBao.muc_do == muc_do)

    # Dem tong
    count_q = select(func.count()).select_from(ThongBao).where(base_filter)
    total = (await db.execute(count_q)).scalar() or 0

    # Sap xep: KHAN truoc, roi QUAN_TRONG, roi BINH_THUONG, sau do created_at DESC
    muc_do_order = case(
        (ThongBao.muc_do == "KHAN", 0),
        (ThongBao.muc_do == "QUAN_TRONG", 1),
        else_=2,
    )

    # Query phan trang
    offset = (page - 1) * page_size
    items_q = (
        select(ThongBao)
        .where(base_filter)
        .order_by(muc_do_order, ThongBao.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    result = await db.execute(items_q)
    items = list(result.scalars().all())

    return items, total


async def dem_chua_doc(
    db: AsyncSession,
    user_id: str,
) -> ThongBaoCountResponse:
    """Dem so thong bao chua doc cua user, phan loai theo muc do.

    Su dung partial index idx_common_tb_chua_doc (WHERE da_doc = FALSE).
    """
    q = (
        select(
            func.count().label("total"),
            func.count().filter(ThongBao.muc_do == "KHAN").label("khan"),
            func.count().filter(ThongBao.muc_do == "QUAN_TRONG").label("quan_trong"),
            func.count().filter(ThongBao.muc_do == "BINH_THUONG").label("binh_thuong"),
        )
        .select_from(ThongBao)
        .where(
            ThongBao.nguoi_nhan_id == uuid.UUID(user_id),
            ThongBao.da_doc == False,  # noqa: E712
        )
    )
    row = (await db.execute(q)).one()
    return ThongBaoCountResponse(
        count=row.total,
        khan=row.khan,
        quan_trong=row.quan_trong,
        binh_thuong=row.binh_thuong,
    )


async def danh_dau_da_doc(
    db: AsyncSession,
    thong_bao_id: uuid.UUID,
    user_id: str,
) -> ThongBao:
    """Danh dau 1 thong bao da doc.

    - 404 neu khong tim thay
    - 403 neu thong bao khong phai cua user
    - Tra ve thong bao da cap nhat
    """
    q = select(ThongBao).where(ThongBao.id == thong_bao_id)
    result = await db.execute(q)
    tb = result.scalar_one_or_none()

    if tb is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": {
                    "code": "CMN_ERR_003",
                    "message": "Thông báo không tồn tại",
                },
            },
        )

    if str(tb.nguoi_nhan_id) != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "error": {
                    "code": "PERM_001",
                    "message": "Bạn không có quyền thao tác thông báo này",
                },
            },
        )

    if not tb.da_doc:
        tb.da_doc = True
        tb.ngay_doc = datetime.utcnow()
        await db.flush()

    return tb


async def danh_dau_tat_ca_da_doc(
    db: AsyncSession,
    user_id: str,
) -> int:
    """Danh dau tat ca thong bao chua doc cua user -> da doc.

    Returns:
        So luong thong bao da cap nhat.
    """
    now = datetime.utcnow()
    stmt = (
        update(ThongBao)
        .where(
            ThongBao.nguoi_nhan_id == uuid.UUID(user_id),
            ThongBao.da_doc == False,  # noqa: E712
        )
        .values(da_doc=True, ngay_doc=now)
    )
    result = await db.execute(stmt)
    await db.flush()
    return result.rowcount


# ---------------------------------------------------------------------------
# Internal methods — Module khac goi
# ---------------------------------------------------------------------------


def _validate_loai(loai: str) -> None:
    """Validate loai thong bao."""
    if loai not in LOAI_THONG_BAO:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "error": {
                    "code": "CMN_ERR_004",
                    "message": f"Loại thông báo không hợp lệ: {loai}. "
                    f"Chấp nhận: {', '.join(sorted(LOAI_THONG_BAO))}",
                },
            },
        )


def _validate_muc_do(muc_do: str) -> None:
    """Validate muc do thong bao."""
    if muc_do not in MUC_DO_THONG_BAO:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "error": {
                    "code": "CMN_ERR_004",
                    "message": f"Mức độ không hợp lệ: {muc_do}. "
                    f"Chấp nhận: {', '.join(sorted(MUC_DO_THONG_BAO))}",
                },
            },
        )


async def tao_thong_bao(
    db: AsyncSession,
    data: ThongBaoCreateInternal,
) -> ThongBao:
    """Tao 1 thong bao moi — Internal API.

    Validate loai va muc_do truoc khi insert.
    """
    _validate_loai(data.loai)
    _validate_muc_do(data.muc_do)

    tb = ThongBao(
        nguoi_nhan_id=data.nguoi_nhan_id,
        tieu_de=data.tieu_de,
        noi_dung=data.noi_dung,
        loai=data.loai,
        muc_do=data.muc_do,
        link_url=data.link_url,
        doi_tuong_type=data.doi_tuong_type,
        doi_tuong_id=data.doi_tuong_id,
    )
    db.add(tb)
    await db.flush()
    await db.refresh(tb)
    return tb


async def tao_thong_bao_hang_loat(
    db: AsyncSession,
    data: ThongBaoCreateBulk,
) -> int:
    """Tao thong bao hang loat cho nhieu nguoi — Internal API.

    Bulk insert N records (1 cho moi nguoi_nhan_id).

    Returns:
        So luong thong bao da tao.
    """
    _validate_loai(data.loai)
    _validate_muc_do(data.muc_do)

    # Loai bo trung lap
    unique_ids = list(set(data.nguoi_nhan_ids))

    records = [
        ThongBao(
            nguoi_nhan_id=nhan_id,
            tieu_de=data.tieu_de,
            noi_dung=data.noi_dung,
            loai=data.loai,
            muc_do=data.muc_do,
            link_url=data.link_url,
            doi_tuong_type=data.doi_tuong_type,
            doi_tuong_id=data.doi_tuong_id,
        )
        for nhan_id in unique_ids
    ]
    db.add_all(records)
    await db.flush()
    return len(records)
