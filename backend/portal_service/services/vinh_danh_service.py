"""
portal_service/services/vinh_danh_service.py
=============================================
Business logic cho VinhDanhThang.

Workflow trang thai:
  DRAFT     -> PUBLISHED   Admin cong bo (set ngay_cong_bo)
  PUBLISHED -> DRAFT       Admin go cong bo (clear ngay_cong_bo)

Quy tac:
  - Chi 1 ban ghi PUBLISHED cho moi (thang, nam) — enforce boi UNIQUE partial index
  - Chi xoa duoc khi DRAFT
  - Chi SUPER_ADMIN / QT_NOI_DUNG co quyen CRUD
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import and_, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from portal_service.models.vinh_danh_thang import VinhDanhThang
from portal_service.models.base import CongChucRef
from portal_service.schemas.vinh_danh_thang import (
    VinhDanhThangCreate,
    VinhDanhThangUpdate,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _lay_theo_id(db: AsyncSession, vd_id: uuid.UUID) -> VinhDanhThang:
    """Lay ban ghi theo ID, raise 404 neu khong ton tai."""
    stmt = select(VinhDanhThang).where(VinhDanhThang.id == vd_id)
    result = await db.execute(stmt)
    vd = result.scalar_one_or_none()
    if not vd:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": {
                    "code": "PORTAL_VD_001",
                    "message": "Khong tim thay ban ghi vinh danh",
                },
            },
        )
    return vd


async def _kiem_tra_cong_chuc_ton_tai(
    db: AsyncSession, cong_chuc_id: uuid.UUID
) -> None:
    """Kiem tra cong chuc co ton tai va con active khong."""
    stmt = select(CongChucRef).where(CongChucRef.id == cong_chuc_id)
    result = await db.execute(stmt)
    cc = result.scalar_one_or_none()
    if not cc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "error": {
                    "code": "PORTAL_VD_002",
                    "message": "Khong tim thay cong chuc",
                },
            },
        )


# ---------------------------------------------------------------------------
# Danh sach
# ---------------------------------------------------------------------------


async def danh_sach(
    db: AsyncSession,
    nam: Optional[int] = None,
    thang: Optional[int] = None,
    trang_thai: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[VinhDanhThang], int]:
    """Danh sach vinh danh, sap xep moi nhat truoc."""
    stmt = select(VinhDanhThang)

    if nam is not None:
        stmt = stmt.where(VinhDanhThang.nam == nam)
    if thang is not None:
        stmt = stmt.where(VinhDanhThang.thang == thang)
    if trang_thai:
        stmt = stmt.where(VinhDanhThang.trang_thai == trang_thai)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0

    stmt = stmt.order_by(
        VinhDanhThang.nam.desc(),
        VinhDanhThang.thang.desc(),
        VinhDanhThang.created_at.desc(),
    )
    offset = (page - 1) * page_size
    stmt = stmt.offset(offset).limit(page_size)

    result = await db.execute(stmt)
    return list(result.scalars().all()), total


async def lay_vinh_danh_thang_hien_tai(
    db: AsyncSession,
) -> Optional[VinhDanhThang]:
    """Lay vinh danh PUBLISHED cua thang hien tai (cho widget dashboard)."""
    now = datetime.now(timezone.utc)
    stmt = select(VinhDanhThang).where(
        and_(
            VinhDanhThang.nam == now.year,
            VinhDanhThang.thang == now.month,
            VinhDanhThang.trang_thai == "PUBLISHED",
        )
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def chi_tiet(db: AsyncSession, vd_id: uuid.UUID) -> VinhDanhThang:
    """Lay chi tiet ban ghi vinh danh."""
    return await _lay_theo_id(db, vd_id)


# ---------------------------------------------------------------------------
# Tao moi (DRAFT)
# ---------------------------------------------------------------------------


async def tao_moi(
    db: AsyncSession,
    data: VinhDanhThangCreate,
    nguoi_tao_id: uuid.UUID,
) -> VinhDanhThang:
    """Tao ban ghi vinh danh moi o trang thai DRAFT."""
    await _kiem_tra_cong_chuc_ton_tai(db, data.cong_chuc_id)

    vd = VinhDanhThang(
        thang=data.thang,
        nam=data.nam,
        cong_chuc_id=data.cong_chuc_id,
        tieu_de=data.tieu_de,
        ly_do=data.ly_do,
        anh_chan_dung=data.anh_chan_dung,
        loi_tuyen_duong=data.loi_tuyen_duong,
        trang_thai="DRAFT",
        nguoi_tao_id=nguoi_tao_id,
    )
    db.add(vd)
    await db.commit()
    await db.refresh(vd)
    return vd


# ---------------------------------------------------------------------------
# Cap nhat
# ---------------------------------------------------------------------------


async def cap_nhat(
    db: AsyncSession,
    vd_id: uuid.UUID,
    data: VinhDanhThangUpdate,
) -> VinhDanhThang:
    """Cap nhat ban ghi vinh danh.

    Cho phep sua o ca DRAFT lan PUBLISHED (admin chinh sua noi dung sau cong bo).
    Neu cong_chuc_id thay doi, kiem tra cong chuc moi co ton tai khong.
    """
    vd = await _lay_theo_id(db, vd_id)

    if data.cong_chuc_id is not None and data.cong_chuc_id != vd.cong_chuc_id:
        await _kiem_tra_cong_chuc_ton_tai(db, data.cong_chuc_id)

    if data.thang is not None:
        vd.thang = data.thang
    if data.nam is not None:
        vd.nam = data.nam
    if data.cong_chuc_id is not None:
        vd.cong_chuc_id = data.cong_chuc_id
    if data.tieu_de is not None:
        vd.tieu_de = data.tieu_de
    if data.ly_do is not None:
        vd.ly_do = data.ly_do
    if data.anh_chan_dung is not None:
        vd.anh_chan_dung = data.anh_chan_dung
    if data.loi_tuyen_duong is not None:
        vd.loi_tuyen_duong = data.loi_tuyen_duong

    vd.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "success": False,
                "error": {
                    "code": "PORTAL_VD_003",
                    "message": (
                        f"Da co ban ghi vinh danh PUBLISHED cho thang "
                        f"{vd.thang}/{vd.nam}"
                    ),
                },
            },
        )
    await db.refresh(vd)
    return vd


# ---------------------------------------------------------------------------
# Cong bo / Go cong bo
# ---------------------------------------------------------------------------


async def cong_bo(db: AsyncSession, vd_id: uuid.UUID) -> VinhDanhThang:
    """Chuyen DRAFT -> PUBLISHED, set ngay_cong_bo.

    Raise 409 neu da co ban ghi PUBLISHED khac cho thang/nam tuong ung.
    """
    vd = await _lay_theo_id(db, vd_id)

    if vd.trang_thai == "PUBLISHED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "error": {
                    "code": "PORTAL_VD_004",
                    "message": "Ban ghi da o trang thai PUBLISHED",
                },
            },
        )

    vd.trang_thai = "PUBLISHED"
    vd.ngay_cong_bo = datetime.now(timezone.utc).replace(tzinfo=None)
    vd.updated_at = vd.ngay_cong_bo

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "success": False,
                "error": {
                    "code": "PORTAL_VD_003",
                    "message": (
                        f"Da co ban ghi vinh danh PUBLISHED cho thang "
                        f"{vd.thang}/{vd.nam}. Vui long go cong bo ban cu truoc."
                    ),
                },
            },
        )
    await db.refresh(vd)
    return vd


async def go_cong_bo(db: AsyncSession, vd_id: uuid.UUID) -> VinhDanhThang:
    """Chuyen PUBLISHED -> DRAFT, clear ngay_cong_bo."""
    vd = await _lay_theo_id(db, vd_id)

    if vd.trang_thai != "PUBLISHED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "error": {
                    "code": "PORTAL_VD_005",
                    "message": "Chi co the go cong bo ban ghi PUBLISHED",
                },
            },
        )

    vd.trang_thai = "DRAFT"
    vd.ngay_cong_bo = None
    vd.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)

    await db.commit()
    await db.refresh(vd)
    return vd


# ---------------------------------------------------------------------------
# Xoa
# ---------------------------------------------------------------------------


async def xoa(db: AsyncSession, vd_id: uuid.UUID) -> dict:
    """Xoa ban ghi vinh danh.

    Chi xoa duoc khi DRAFT (de bao toan lich su cong bo).
    """
    vd = await _lay_theo_id(db, vd_id)

    if vd.trang_thai != "DRAFT":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "error": {
                    "code": "PORTAL_VD_006",
                    "message": "Chi co the xoa ban ghi DRAFT. Hay go cong bo truoc.",
                },
            },
        )

    await db.delete(vd)
    await db.commit()
    return {"message": "Da xoa ban ghi vinh danh"}
