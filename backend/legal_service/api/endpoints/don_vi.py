"""
legal_service/api/endpoints/don_vi.py
========================================
Endpoint lay danh sach don vi va cong chuc (READONLY tu public).
Dung de hien thi danh sach chon doi_tuong_ap_dung khi tao van ban.

GET /don-vi       — lay danh sach don vi active kem so CBCC moi don vi
GET /cong-chuc    — tim kiem CBCC (autocomplete, co phan trang)
"""

import os
import sys
from math import ceil
from typing import Optional
from uuid import UUID

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from legal_service.dependencies import get_current_user, get_db
from legal_service.models.base import CongChucRef, DonViRef
from shared.auth import TokenPayload

router = APIRouter(tags=["Don Vi"])


@router.get("/don-vi")
async def danh_sach_don_vi(
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user),
) -> dict:
    """
    Lay danh sach don vi active kem so CBCC.
    Dung de chon doi_tuong_ap_dung khi tao/sua van ban.
    Auth: Tat ca CBCC (can biet don vi de chon).
    """
    result = await db.execute(
        select(
            DonViRef.id,
            DonViRef.ma_don_vi,
            DonViRef.ten_don_vi,
            DonViRef.loai_don_vi,
            func.count(CongChucRef.id).label("so_cbcc"),
        )
        .outerjoin(
            CongChucRef,
            (CongChucRef.don_vi_id == DonViRef.id) & (CongChucRef.is_active.is_(True)),
        )
        .where(DonViRef.is_active.is_(True))
        .group_by(
            DonViRef.id,
            DonViRef.ma_don_vi,
            DonViRef.ten_don_vi,
            DonViRef.loai_don_vi,
        )
        .order_by(DonViRef.ten_don_vi)
    )
    rows = result.all()
    return {
        "success": True,
        "data": [
            {
                "id": str(row.id),
                "ma_don_vi": row.ma_don_vi,
                "ten_don_vi": row.ten_don_vi,
                "loai_don_vi": row.loai_don_vi,
                "so_cbcc": row.so_cbcc,
            }
            for row in rows
        ],
    }


@router.get("/cong-chuc")
async def danh_sach_cong_chuc(
    search: Optional[str] = Query(None, description="Tim kiem theo ho_ten hoac ma_cc"),
    don_vi_id: Optional[str] = Query(None, description="Loc theo UUID don vi"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user),
) -> dict:
    """
    Tim kiem CBCC theo ho_ten hoac ma_cc (dung cho autocomplete chon doi tuong ap dung).
    Tra ve kem thong tin don vi cua moi CBCC.

    Auth: BIEN_TAP hoac QT_NOI_DUNG hoac SUPER_ADMIN.
    """
    platform_roles = current_user.platform_roles or []
    is_admin = current_user.vai_tro == "SUPER_ADMIN" or getattr(current_user, "is_admin", False)
    if (
        not is_admin
        and "BIEN_TAP" not in platform_roles
        and "QT_NOI_DUNG" not in platform_roles
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "error": {
                    "code": "PERM_001",
                    "message": "Yeu cau quyen BIEN_TAP hoac QT_NOI_DUNG de tra cuu cong chuc",
                },
            },
        )

    query = select(CongChucRef).where(CongChucRef.is_active.is_(True))

    if search:
        like = f"%{search}%"
        query = query.where(
            or_(
                CongChucRef.ho_ten.ilike(like),
                CongChucRef.ma_cc.ilike(like),
            )
        )

    if don_vi_id:
        try:
            dv_uuid = UUID(don_vi_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"success": False, "error": {"code": "VAL_001", "message": "don_vi_id khong hop le"}},
            )
        query = query.where(CongChucRef.don_vi_id == dv_uuid)

    query = query.order_by(CongChucRef.ho_ten)

    # Dem tong
    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar_one()

    # Phan trang
    skip = (page - 1) * page_size
    query = query.offset(skip).limit(page_size)
    rows = list((await db.execute(query)).scalars().all())

    total_pages = ceil(total / page_size) if page_size > 0 else 0

    return {
        "success": True,
        "data": [
            {
                "id": str(cc.id),
                "ma_cc": cc.ma_cc,
                "ho_ten": cc.ho_ten,
                "don_vi": {
                    "id": str(cc.don_vi.id),
                    "ten_don_vi": cc.don_vi.ten_don_vi,
                }
                if cc.don_vi
                else None,
            }
            for cc in rows
        ],
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total_items": total,
            "total_pages": total_pages,
        },
    }
