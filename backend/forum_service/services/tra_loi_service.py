"""
forum_service/services/tra_loi_service.py
==========================================
Business logic cho tra loi / binh luan.

Features:
  - Tao tra loi (handle nested reply, flatten level-3, auto theo doi)
  - Sua tra loi (author 24h OR DIEU_PHOI)
  - Xoa tra loi (soft delete, decrement so_tra_loi)
  - An tra loi (DIEU_PHOI only)
"""

import os
import sys
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from fastapi import HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from forum_service.models import ChuDe, TheoDoi, TraLoi
from shared.auth import TokenPayload


def _now() -> datetime:
    """Lay thoi gian hien tai (UTC)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _is_dieu_phoi(user: TokenPayload) -> bool:
    """Kiem tra user co quyen dieu phoi forum (DIEU_PHOI_FORUM hoac SUPER_ADMIN)."""
    if user.vai_tro == "SUPER_ADMIN" or user.is_admin:
        return True
    return "DIEU_PHOI_FORUM" in (user.platform_roles or [])


async def tao(
    db: AsyncSession,
    chu_de_id: UUID,
    data: dict,
    user: TokenPayload,
) -> dict:
    """
    Tao tra loi moi cho chu de.

    Quy tac:
      - Validate chu_de exists, not deleted, not locked (is_khoa → 403 FORUM_ERR_003)
      - Handle nested reply: neu parent_id tro den level-2 reply → flatten to level-1 parent
        (Tranh tao reply qua 2 cap)
      - Tang chu_de.so_tra_loi += 1
      - Auto tao TheoDoi cho responder (idempotent)

    Args:
        db: Database session
        chu_de_id: ID chu de
        data: TraLoiCreate (noi_dung, parent_id, can_cu_phap_ly)
        user: Current user

    Returns:
        TraLoiResponse
    """
    # Validate chu de
    cd_stmt = select(ChuDe).where(ChuDe.id == chu_de_id, ChuDe.is_deleted == False)
    cd = (await db.execute(cd_stmt)).scalar_one_or_none()
    if not cd:
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

    # Check chu de khong bi khoa
    if cd.is_khoa:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "error": {
                    "code": "FORUM_ERR_003",
                    "message": "Chu de da bi khoa, khong the tra loi",
                },
            },
        )

    # Handle nested reply: neu parent_id la level-2 → flatten to level-1
    parent_id = data.get("parent_id")
    if parent_id:
        parent_stmt = select(TraLoi).where(TraLoi.id == parent_id, TraLoi.is_deleted == False)
        parent_tl = (await db.execute(parent_stmt)).scalar_one_or_none()
        if not parent_tl:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "success": False,
                    "error": {
                        "code": "FORUM_ERR_001",
                        "message": "Tra loi cha khong ton tai",
                    },
                },
            )
        # Neu parent la level-2 (parent.parent_id IS NOT NULL) → flatten to level-1
        if parent_tl.parent_id is not None:
            parent_id = parent_tl.parent_id

    # Tao tra loi
    user_uuid = UUID(user.sub)
    tl = TraLoi(
        chu_de_id=chu_de_id,
        parent_id=parent_id,
        noi_dung=data["noi_dung"],
        tac_gia_id=user_uuid,
        is_dap_an_chuan=False,
        is_an=False,
        so_upvote=0,
        can_cu_phap_ly=data.get("can_cu_phap_ly"),
        created_at=_now(),
        updated_at=_now(),
    )
    db.add(tl)

    # Tang so_tra_loi cua chu de
    await db.execute(
        update(ChuDe)
        .where(ChuDe.id == chu_de_id)
        .values(so_tra_loi=ChuDe.so_tra_loi + 1)
    )

    # Auto tao TheoDoi cho responder (idempotent — ignore duplicate)
    td_stmt = select(TheoDoi.cong_chuc_id).where(
        TheoDoi.cong_chuc_id == user_uuid,
        TheoDoi.chu_de_id == chu_de_id,
    )
    existing_td = (await db.execute(td_stmt)).scalar_one_or_none()
    if not existing_td:
        theo_doi = TheoDoi(
            cong_chuc_id=user_uuid,
            chu_de_id=chu_de_id,
            created_at=_now(),
        )
        db.add(theo_doi)

    await db.commit()
    await db.refresh(tl)

    # Build response
    tac_gia = None
    if tl.tac_gia:
        tac_gia = {
            "id": tl.tac_gia.id,
            "ma_cc": tl.tac_gia.ma_cc,
            "ho_ten": tl.tac_gia.ho_ten,
            "chuc_vu": tl.tac_gia.chuc_vu,
            "don_vi_ten": tl.tac_gia.don_vi.ten_don_vi if tl.tac_gia.don_vi else None,
        }

    return {
        "id": tl.id,
        "chu_de_id": tl.chu_de_id,
        "parent_id": tl.parent_id,
        "noi_dung": tl.noi_dung,
        "tac_gia": tac_gia,
        "is_dap_an_chuan": tl.is_dap_an_chuan,
        "is_an": tl.is_an,
        "so_upvote": tl.so_upvote,
        "can_cu_phap_ly": tl.can_cu_phap_ly,
        "created_at": tl.created_at,
        "updated_at": tl.updated_at,
    }


async def sua(
    db: AsyncSession,
    tra_loi_id: UUID,
    data: dict,
    user: TokenPayload,
) -> dict:
    """
    Cap nhat tra loi.

    Quy tac:
      - Author trong 24h OR DIEU_PHOI/SUPER_ADMIN

    Args:
        db: Database session
        tra_loi_id: ID tra loi can sua
        data: TraLoiUpdate (noi_dung, can_cu_phap_ly)
        user: Current user

    Returns:
        TraLoiResponse
    """
    # Load tra loi
    stmt = select(TraLoi).where(TraLoi.id == tra_loi_id, TraLoi.is_deleted == False)
    tl = (await db.execute(stmt)).scalar_one_or_none()
    if not tl:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": {
                    "code": "FORUM_ERR_001",
                    "message": "Khong tim thay tra loi",
                },
            },
        )

    user_uuid = UUID(user.sub)
    is_dp = _is_dieu_phoi(user)
    is_author = tl.tac_gia_id == user_uuid

    # Kiem tra quyen sua
    if is_author:
        # Author chi sua trong 24h
        cutoff = _now() - timedelta(hours=24)
        if tl.created_at < cutoff:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "success": False,
                    "error": {
                        "code": "FORUM_ERR_005",
                        "message": "Chi co the sua tra loi trong vong 24 gio sau khi tao",
                    },
                },
            )
    elif not is_dp:
        # Khong phai author, khong phai DIEU_PHOI
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "error": {
                    "code": "FORUM_ERR_008",
                    "message": "Ban khong co quyen sua tra loi nay",
                },
            },
        )

    # Cap nhat fields
    if data.get("noi_dung") is not None:
        tl.noi_dung = data["noi_dung"]
    if "can_cu_phap_ly" in data:
        tl.can_cu_phap_ly = data["can_cu_phap_ly"]

    tl.updated_at = _now()
    await db.commit()
    await db.refresh(tl)

    # Build response
    tac_gia = None
    if tl.tac_gia:
        tac_gia = {
            "id": tl.tac_gia.id,
            "ma_cc": tl.tac_gia.ma_cc,
            "ho_ten": tl.tac_gia.ho_ten,
            "chuc_vu": tl.tac_gia.chuc_vu,
            "don_vi_ten": tl.tac_gia.don_vi.ten_don_vi if tl.tac_gia.don_vi else None,
        }

    return {
        "id": tl.id,
        "chu_de_id": tl.chu_de_id,
        "parent_id": tl.parent_id,
        "noi_dung": tl.noi_dung,
        "tac_gia": tac_gia,
        "is_dap_an_chuan": tl.is_dap_an_chuan,
        "is_an": tl.is_an,
        "so_upvote": tl.so_upvote,
        "can_cu_phap_ly": tl.can_cu_phap_ly,
        "created_at": tl.created_at,
        "updated_at": tl.updated_at,
    }


async def xoa(
    db: AsyncSession,
    tra_loi_id: UUID,
    user: TokenPayload,
) -> None:
    """
    Xoa tra loi (soft delete).

    Quy tac:
      - Author OR DIEU_PHOI/SUPER_ADMIN
      - Decrement chu_de.so_tra_loi -= 1

    Args:
        db: Database session
        tra_loi_id: ID tra loi can xoa
        user: Current user
    """
    # Load tra loi
    stmt = select(TraLoi).where(TraLoi.id == tra_loi_id, TraLoi.is_deleted == False)
    tl = (await db.execute(stmt)).scalar_one_or_none()
    if not tl:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": {
                    "code": "FORUM_ERR_001",
                    "message": "Khong tim thay tra loi",
                },
            },
        )

    user_uuid = UUID(user.sub)
    is_dp = _is_dieu_phoi(user)
    is_author = tl.tac_gia_id == user_uuid

    # Kiem tra quyen xoa
    if not (is_author or is_dp):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "error": {
                    "code": "FORUM_ERR_008",
                    "message": "Ban khong co quyen xoa tra loi nay",
                },
            },
        )

    # Soft delete
    tl.is_deleted = True
    tl.updated_at = _now()

    # Decrement so_tra_loi
    await db.execute(
        update(ChuDe)
        .where(ChuDe.id == tl.chu_de_id)
        .values(so_tra_loi=ChuDe.so_tra_loi - 1)
    )

    await db.commit()


async def an(
    db: AsyncSession,
    tra_loi_id: UUID,
    user: TokenPayload,
) -> None:
    """
    An tra loi (set is_an = True).

    Quy tac:
      - Chi DIEU_PHOI/SUPER_ADMIN

    Args:
        db: Database session
        tra_loi_id: ID tra loi can an
        user: Current user
    """
    # Require DIEU_PHOI
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

    # Load tra loi
    stmt = select(TraLoi).where(TraLoi.id == tra_loi_id, TraLoi.is_deleted == False)
    tl = (await db.execute(stmt)).scalar_one_or_none()
    if not tl:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": {
                    "code": "FORUM_ERR_001",
                    "message": "Khong tim thay tra loi",
                },
            },
        )

    # An tra loi
    tl.is_an = True
    tl.updated_at = _now()
    await db.commit()
