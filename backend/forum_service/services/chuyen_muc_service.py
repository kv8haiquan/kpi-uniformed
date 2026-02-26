"""
forum_service/services/chuyen_muc_service.py
==============================================
Business logic cho quan ly chuyen muc dien dan.

Features:
  - Danh sach tree chuyen muc (cha-con) kem stats
  - Tao/sua/xoa chuyen muc (chi DIEU_PHOI/SUPER_ADMIN)
  - Thong ke: so_chu_de, so_tra_loi, chu_de_moi_nhat
"""

import os
import sys
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from forum_service.models import ChuyenMuc, ChuDe, TraLoi
from shared.auth import TokenPayload


def _now() -> datetime:
    """Lay thoi gian hien tai (UTC)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _is_dieu_phoi(user: TokenPayload) -> bool:
    """Kiem tra user co quyen dieu phoi forum (DIEU_PHOI_FORUM hoac SUPER_ADMIN)."""
    if user.vai_tro == "SUPER_ADMIN" or user.is_admin:
        return True
    return "DIEU_PHOI_FORUM" in (user.platform_roles or [])


async def danh_sach(
    db: AsyncSession,
    is_active: Optional[bool] = None,
) -> list[dict]:
    """
    Lay danh sach chuyen muc theo dang tree (parent-children).

    Query chi lay chuyen muc goc (parent_id IS NULL), sau do build tree.
    Tinh toan stats:
      - so_chu_de: dem chu de trong chuyen muc nay + children
      - so_tra_loi: dem tra loi thuoc cac chu de
      - chu_de_moi_nhat: chu de moi nhat trong chuyen muc

    Args:
        db: Database session
        is_active: Loc theo is_active (None = tat ca)

    Returns:
        List chuyen muc tree format
    """
    # Query parent categories (parent_id IS NULL)
    query = select(ChuyenMuc).where(ChuyenMuc.parent_id.is_(None))
    if is_active is not None:
        query = query.where(ChuyenMuc.is_active == is_active)
    query = query.order_by(ChuyenMuc.thu_tu.asc().nullslast(), ChuyenMuc.ten_chuyen_muc)

    result = await db.execute(query)
    categories = list(result.scalars().all())

    # Build tree with stats
    tree = []
    for cat in categories:
        cat_dict = await _build_chuyen_muc_tree(db, cat)
        tree.append(cat_dict)

    return tree


async def _build_chuyen_muc_tree(db: AsyncSession, cat: ChuyenMuc) -> dict:
    """
    Build tree node cho chuyen muc kem stats.
    Recursive: neu co children thi build children tree.
    """
    # Tinh so chu de trong chuyen muc nay
    chu_de_count_stmt = select(func.count(ChuDe.id)).where(
        ChuDe.chuyen_muc_id == cat.id,
        ChuDe.is_deleted == False
    )
    so_chu_de = (await db.execute(chu_de_count_stmt)).scalar_one()

    # Tinh so tra loi cho cac chu de trong chuyen muc nay
    tra_loi_count_stmt = (
        select(func.count(TraLoi.id))
        .join(ChuDe, TraLoi.chu_de_id == ChuDe.id)
        .where(
            ChuDe.chuyen_muc_id == cat.id,
            ChuDe.is_deleted == False,
            TraLoi.is_deleted == False
        )
    )
    so_tra_loi = (await db.execute(tra_loi_count_stmt)).scalar_one()

    # Lay chu de moi nhat
    chu_de_moi_stmt = (
        select(ChuDe)
        .where(ChuDe.chuyen_muc_id == cat.id, ChuDe.is_deleted == False)
        .order_by(ChuDe.created_at.desc())
        .limit(1)
    )
    chu_de_moi = (await db.execute(chu_de_moi_stmt)).scalar_one_or_none()

    chu_de_moi_nhat = None
    if chu_de_moi:
        chu_de_moi_nhat = {
            "id": chu_de_moi.id,
            "tieu_de": chu_de_moi.tieu_de,
            "created_at": chu_de_moi.created_at,
        }

    # Build children recursively — query rieng, khong dung relationship lazy load
    children_stmt = (
        select(ChuyenMuc)
        .where(ChuyenMuc.parent_id == cat.id)
        .order_by(ChuyenMuc.thu_tu.asc().nullslast(), ChuyenMuc.ten_chuyen_muc)
    )
    children_result = await db.execute(children_stmt)
    child_cats = list(children_result.scalars().all())

    children = []
    for child_cat in child_cats:
        child_dict = await _build_chuyen_muc_tree(db, child_cat)
        children.append(child_dict)
        # Cong stats children vao parent
        so_chu_de += child_dict["so_chu_de"]
        so_tra_loi += child_dict["so_tra_loi"]

    return {
        "id": cat.id,
        "ten_chuyen_muc": cat.ten_chuyen_muc,
        "mo_ta": cat.mo_ta,
        "icon": cat.icon,
        "thu_tu": cat.thu_tu,
        "parent_id": cat.parent_id,
        "chi_doc": cat.chi_doc,
        "yeu_cau_duyet": cat.yeu_cau_duyet,
        "is_active": cat.is_active,
        "created_at": cat.created_at,
        "so_chu_de": so_chu_de,
        "so_tra_loi": so_tra_loi,
        "chu_de_moi_nhat": chu_de_moi_nhat,
        "children": children,
    }


async def tao(
    db: AsyncSession,
    data: dict,
    user: TokenPayload,
) -> dict:
    """
    Tao chuyen muc moi.

    Quy tac:
      - Chi DIEU_PHOI_FORUM hoac SUPER_ADMIN moi tao duoc
      - Neu co parent_id: validate parent ton tai va la chuyen muc goc (parent.parent_id IS NULL)
        → Tranh tao chuyen muc cap 3 (grandchildren)

    Args:
        db: Database session
        data: ChuyenMucCreate data
        user: Current user

    Returns:
        Chuyen muc vua tao
    """
    # Kiem tra quyen
    if not _is_dieu_phoi(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "error": {
                    "code": "PERM_001",
                    "message": "Yeu cau vai tro DIEU_PHOI_FORUM hoac SUPER_ADMIN",
                },
            },
        )

    # Validate parent_id neu co
    parent_id = data.get("parent_id")
    if parent_id:
        parent_stmt = select(ChuyenMuc).where(ChuyenMuc.id == parent_id)
        parent = (await db.execute(parent_stmt)).scalar_one_or_none()
        if not parent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "success": False,
                    "error": {
                        "code": "FORUM_ERR_001",
                        "message": "Chuyen muc cha khong ton tai",
                    },
                },
            )
        # Parent phai la chuyen muc goc (khong cho tao chuyen muc cap 3)
        if parent.parent_id is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "success": False,
                    "error": {
                        "code": "FORUM_ERR_002",
                        "message": "Chi ho tro toi da 2 cap chuyen muc (cha-con). Khong the tao chuyen muc con cho chuyen muc da la con.",
                    },
                },
            )

    # Tao chuyen muc
    cat = ChuyenMuc(
        ten_chuyen_muc=data["ten_chuyen_muc"],
        mo_ta=data.get("mo_ta"),
        icon=data.get("icon"),
        thu_tu=data.get("thu_tu"),
        parent_id=parent_id,
        chi_doc=data.get("chi_doc", False),
        yeu_cau_duyet=data.get("yeu_cau_duyet", False),
        is_active=True,
        created_at=_now(),
    )
    db.add(cat)
    await db.commit()
    await db.refresh(cat)

    return {
        "id": cat.id,
        "ten_chuyen_muc": cat.ten_chuyen_muc,
        "mo_ta": cat.mo_ta,
        "icon": cat.icon,
        "thu_tu": cat.thu_tu,
        "parent_id": cat.parent_id,
        "chi_doc": cat.chi_doc,
        "yeu_cau_duyet": cat.yeu_cau_duyet,
        "is_active": cat.is_active,
        "created_at": cat.created_at,
        "so_chu_de": 0,
        "so_tra_loi": 0,
        "chu_de_moi_nhat": None,
        "children": [],
    }


async def sua(
    db: AsyncSession,
    chuyen_muc_id: UUID,
    data: dict,
    user: TokenPayload,
) -> dict:
    """
    Cap nhat chuyen muc.

    Quy tac:
      - Chi DIEU_PHOI_FORUM hoac SUPER_ADMIN

    Args:
        db: Database session
        chuyen_muc_id: ID chuyen muc can sua
        data: ChuyenMucUpdate data (chi cap nhat field khac None)
        user: Current user

    Returns:
        Chuyen muc sau khi update
    """
    # Kiem tra quyen
    if not _is_dieu_phoi(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "error": {
                    "code": "PERM_001",
                    "message": "Yeu cau vai tro DIEU_PHOI_FORUM hoac SUPER_ADMIN",
                },
            },
        )

    # Load chuyen muc
    stmt = select(ChuyenMuc).where(ChuyenMuc.id == chuyen_muc_id)
    cat = (await db.execute(stmt)).scalar_one_or_none()
    if not cat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": {
                    "code": "FORUM_ERR_001",
                    "message": "Khong tim thay chuyen muc",
                },
            },
        )

    # Cap nhat cac field co gia tri
    if data.get("ten_chuyen_muc") is not None:
        cat.ten_chuyen_muc = data["ten_chuyen_muc"]
    if "mo_ta" in data:
        cat.mo_ta = data["mo_ta"]
    if "icon" in data:
        cat.icon = data["icon"]
    if "thu_tu" in data:
        cat.thu_tu = data["thu_tu"]
    if data.get("chi_doc") is not None:
        cat.chi_doc = data["chi_doc"]
    if data.get("yeu_cau_duyet") is not None:
        cat.yeu_cau_duyet = data["yeu_cau_duyet"]
    if data.get("is_active") is not None:
        cat.is_active = data["is_active"]

    await db.commit()
    await db.refresh(cat)

    # Build response with stats
    return await _build_chuyen_muc_tree(db, cat)


async def xoa(
    db: AsyncSession,
    chuyen_muc_id: UUID,
    user: TokenPayload,
) -> None:
    """
    Soft delete chuyen muc (set is_active = False).

    Quy tac:
      - Chi DIEU_PHOI_FORUM hoac SUPER_ADMIN
      - Reject neu chuyen muc con chu de dang active (is_deleted=False)

    Args:
        db: Database session
        chuyen_muc_id: ID chuyen muc can xoa
        user: Current user
    """
    # Kiem tra quyen
    if not _is_dieu_phoi(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "error": {
                    "code": "PERM_001",
                    "message": "Yeu cau vai tro DIEU_PHOI_FORUM hoac SUPER_ADMIN",
                },
            },
        )

    # Load chuyen muc
    stmt = select(ChuyenMuc).where(ChuyenMuc.id == chuyen_muc_id)
    cat = (await db.execute(stmt)).scalar_one_or_none()
    if not cat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": {
                    "code": "FORUM_ERR_001",
                    "message": "Khong tim thay chuyen muc",
                },
            },
        )

    # Kiem tra con chu de active khong
    chu_de_count_stmt = select(func.count(ChuDe.id)).where(
        ChuDe.chuyen_muc_id == chuyen_muc_id,
        ChuDe.is_deleted == False
    )
    chu_de_count = (await db.execute(chu_de_count_stmt)).scalar_one()

    if chu_de_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "error": {
                    "code": "FORUM_ERR_006",
                    "message": f"Khong the xoa chuyen muc con {chu_de_count} chu de dang hoat dong. Hay xoa/chuyen chu de truoc.",
                },
            },
        )

    # Soft delete
    cat.is_active = False
    await db.commit()
