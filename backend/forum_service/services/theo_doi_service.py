"""
forum_service/services/theo_doi_service.py
===========================================
Business logic cho theo doi chu de.

Features:
  - Theo doi chu de (idempotent — ignore duplicate)
  - Bo theo doi
  - Danh sach chu de dang theo doi (paginated)
"""

import os
import sys
from datetime import datetime, timezone
from math import ceil
from uuid import UUID

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from forum_service.models import ChuDe, TheoDoi
from forum_service.models.base import CongChucRef, DonViRef
from shared.auth import TokenPayload


def _now() -> datetime:
    """Lay thoi gian hien tai (UTC)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _build_user_brief(cong_chuc: CongChucRef) -> dict:
    """Build UserBrief tu CongChucRef + DonViRef."""
    if not cong_chuc:
        return None
    return {
        "id": cong_chuc.id,
        "ma_cc": cong_chuc.ma_cc,
        "ho_ten": cong_chuc.ho_ten,
        "chuc_vu": cong_chuc.chuc_vu,
        "don_vi_ten": cong_chuc.don_vi.ten_don_vi if cong_chuc.don_vi else None,
    }


def _compute_noi_dung_tom_tat(noi_dung: str) -> str:
    """Tao tom tat tu noi dung (200 ky tu dau, strip HTML)."""
    clean = noi_dung.replace("<br>", " ").replace("<p>", " ").replace("</p>", " ")
    clean = clean.replace("<", " ").replace(">", " ")
    clean = " ".join(clean.split())
    return clean[:200]


async def theo_doi(
    db: AsyncSession,
    chu_de_id: UUID,
    user: TokenPayload,
) -> dict:
    """
    Theo doi chu de.

    Idempotent: neu da theo doi roi thi khong lam gi (ignore duplicate).

    Args:
        db: Database session
        chu_de_id: ID chu de can theo doi
        user: Current user

    Returns:
        dict with message
    """
    # Validate chu de exists
    cd_stmt = select(ChuDe.id).where(ChuDe.id == chu_de_id, ChuDe.is_deleted == False)
    cd_exists = (await db.execute(cd_stmt)).scalar_one_or_none()
    if not cd_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": {
                    "code": "FORUM_ERR_001",
                    "message": "Khong tim thay chu de",
                },
            },
        )

    user_uuid = UUID(user.sub)

    # Check da theo doi chua
    existing_stmt = select(TheoDoi.cong_chuc_id).where(
        TheoDoi.cong_chuc_id == user_uuid,
        TheoDoi.chu_de_id == chu_de_id,
    )
    existing = (await db.execute(existing_stmt)).scalar_one_or_none()

    if existing:
        # Da theo doi roi — idempotent
        return {"message": "Ban da theo doi chu de nay"}

    # Tao ban ghi theo doi
    theo_doi_obj = TheoDoi(
        cong_chuc_id=user_uuid,
        chu_de_id=chu_de_id,
        created_at=_now(),
    )
    db.add(theo_doi_obj)
    await db.commit()

    return {"message": "Theo doi chu de thanh cong"}


async def bo_theo_doi(
    db: AsyncSession,
    chu_de_id: UUID,
    user: TokenPayload,
) -> dict:
    """
    Bo theo doi chu de.

    Args:
        db: Database session
        chu_de_id: ID chu de can bo theo doi
        user: Current user

    Returns:
        dict with message
    """
    user_uuid = UUID(user.sub)

    # Find existing theo doi
    existing_stmt = select(TheoDoi).where(
        TheoDoi.cong_chuc_id == user_uuid,
        TheoDoi.chu_de_id == chu_de_id,
    )
    existing = (await db.execute(existing_stmt)).scalar_one_or_none()

    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": {
                    "code": "FORUM_ERR_001",
                    "message": "Ban chua theo doi chu de nay",
                },
            },
        )

    await db.delete(existing)
    await db.commit()

    return {"message": "Da bo theo doi chu de"}


async def danh_sach_cua_toi(
    db: AsyncSession,
    user: TokenPayload,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    """
    Lay danh sach chu de dang theo doi cua user hien tai.

    Returns:
        Paginated response with ChuDeListItem
    """
    user_uuid = UUID(user.sub)

    # Query chu de dang theo doi
    query = (
        select(ChuDe)
        .join(TheoDoi, TheoDoi.chu_de_id == ChuDe.id)
        .where(TheoDoi.cong_chuc_id == user_uuid)
        .where(ChuDe.is_deleted == False)
        .order_by(TheoDoi.created_at.desc())
    )

    # Dem tong
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar_one()

    # Phan trang
    skip = (page - 1) * page_size
    query = query.offset(skip).limit(page_size)
    chu_de_list = list((await db.execute(query)).scalars().all())

    # Build items
    items = []
    for cd in chu_de_list:
        tac_gia = _build_user_brief(cd.tac_gia)
        noi_dung_tom_tat = _compute_noi_dung_tom_tat(cd.noi_dung)
        co_dap_an_chuan = cd.tra_loi_chuan_id is not None

        items.append({
            "id": cd.id,
            "tieu_de": cd.tieu_de,
            "noi_dung_tom_tat": noi_dung_tom_tat,
            "tags": cd.tags or [],
            "tac_gia": tac_gia,
            "trang_thai": cd.trang_thai,
            "is_ghim": cd.is_ghim,
            "is_khoa": cd.is_khoa,
            "so_luot_xem": cd.so_luot_xem,
            "so_tra_loi": cd.so_tra_loi,
            "so_upvote": cd.so_upvote,
            "co_dap_an_chuan": co_dap_an_chuan,
            "created_at": cd.created_at,
            "updated_at": cd.updated_at,
        })

    total_pages = ceil(total / page_size) if page_size > 0 else 0
    return {
        "items": items,
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total_items": total,
            "total_pages": total_pages,
        },
    }
