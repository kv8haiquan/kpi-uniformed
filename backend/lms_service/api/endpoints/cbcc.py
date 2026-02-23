"""
lms_service/api/endpoints/cbcc.py
==================================
Endpoints helper tra cuu CBCC va Don vi tu public schema.
Dung cho chuc nang giao bai, chon hoc vien ma khong can biet UUID truoc.

Endpoints:
  GET /cbcc/search    Tim kiem CBCC theo ten hoac ma so (GIANG_VIEN, QT_DAO_TAO, ADMIN, Lanh dao)
  GET /don-vi         Danh sach tat ca don vi (tat ca CBCC da dang nhap)
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from lms_service.dependencies import get_db, get_current_user
from lms_service.models.base import CongChucRef, DonViRef
from shared.auth import TokenPayload

router = APIRouter(tags=["CBCC & Đơn vị"])


# =============================================================================
# GET /cbcc/search — Tim kiem CBCC theo keyword
# =============================================================================

@router.get("/cbcc/search")
async def search_cbcc(
    q: str = Query(..., min_length=1, description="Từ khoá: tên hoặc mã CBCC"),
    don_vi_id: Optional[UUID] = Query(None, description="UUID đơn vị để lọc thêm"),
    page_size: int = Query(20, ge=1, le=100, description="Số kết quả tối đa"),
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    """
    Tìm kiếm CBCC theo tên hoặc mã số công chức.
    Dùng cho form giao bài / chọn học viên.

    Auth: GIANG_VIEN, QT_DAO_TAO, SUPER_ADMIN, Lãnh đạo.
    """
    # Kiem tra quyen: GIANG_VIEN | QT_DAO_TAO | is_admin | is_lanh_dao | SUPER_ADMIN
    platform_roles = set(user.platform_roles or [])
    co_quyen = (
        user.is_admin
        or user.vai_tro == "SUPER_ADMIN"
        or "GIANG_VIEN" in platform_roles
        or "QT_DAO_TAO" in platform_roles
        or user.is_lanh_dao
    )
    if not co_quyen:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "error": {
                    "code": "PERM_001",
                    "message": "Yêu cầu vai trò GIANG_VIEN, QT_DAO_TAO hoặc Lãnh đạo",
                },
            },
        )

    keyword = f"%{q.strip()}%"

    stmt = (
        select(
            CongChucRef.id,
            CongChucRef.ma_cc,
            CongChucRef.ho_ten,
            CongChucRef.chuc_vu,
            DonViRef.ten_don_vi.label("don_vi_ten"),
        )
        .outerjoin(DonViRef, DonViRef.id == CongChucRef.don_vi_id)
        .where(CongChucRef.is_active.is_(True))
        .where(
            or_(
                CongChucRef.ma_cc.ilike(keyword),
                CongChucRef.ho_ten.ilike(keyword),
            )
        )
        .order_by(CongChucRef.ho_ten)
        .limit(page_size)
    )

    if don_vi_id is not None:
        stmt = stmt.where(CongChucRef.don_vi_id == don_vi_id)

    result = await db.execute(stmt)
    rows = result.mappings().all()

    data = [
        {
            "id": str(row["id"]),
            "ma_cc": row["ma_cc"],
            "ho_ten": row["ho_ten"],
            "chuc_vu": row["chuc_vu"],
            "don_vi_ten": row["don_vi_ten"],
        }
        for row in rows
    ]

    return {
        "success": True,
        "data": data,
        "message": f"Tìm thấy {len(data)} CBCC",
    }


# =============================================================================
# GET /don-vi — Danh sach tat ca don vi
# =============================================================================

@router.get("/don-vi")
async def danh_sach_don_vi(
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    """
    Lấy danh sách tất cả đơn vị từ public.don_vi.
    Auth: Tất cả CBCC đã đăng nhập.
    """
    stmt = (
        select(
            DonViRef.id,
            DonViRef.ma_don_vi,
            DonViRef.ten_don_vi,
        )
        .order_by(DonViRef.ma_don_vi)
    )

    result = await db.execute(stmt)
    rows = result.mappings().all()

    data = [
        {
            "id": str(row["id"]),
            "ma_don_vi": row["ma_don_vi"],
            "ten_don_vi": row["ten_don_vi"],
        }
        for row in rows
    ]

    return {
        "success": True,
        "data": data,
        "message": f"Lấy {len(data)} đơn vị thành công",
    }
