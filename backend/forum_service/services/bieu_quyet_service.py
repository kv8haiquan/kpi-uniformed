"""
forum_service/services/bieu_quyet_service.py
=============================================
Business logic cho upvote / downvote.

Toggle logic:
  1. No existing vote → INSERT, update so_upvote (+1 for UP, -1 for DOWN)
  2. Same type → DELETE (toggle off), update so_upvote (reverse)
  3. Different type → UPDATE loai, update so_upvote (±2 because direction change)

Rang buoc:
  - User khong the vote cho chu de/tra loi cua chinh minh
  - UNIQUE(cong_chuc_id, doi_tuong_type, doi_tuong_id)
"""

import os
import sys
from datetime import datetime, timezone
from uuid import UUID

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from fastapi import HTTPException, status
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from forum_service.models import BieuQuyet, ChuDe, TraLoi
from shared.auth import TokenPayload


def _now() -> datetime:
    """Lay thoi gian hien tai (UTC)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


async def vote(
    db: AsyncSession,
    user: TokenPayload,
    data: dict,
) -> dict:
    """
    Vote (upvote/downvote) cho chu de hoac tra loi.

    Toggle logic:
      1. No vote → INSERT, update so_upvote (+1 UP, -1 DOWN)
      2. Same type → DELETE (toggle off), update so_upvote (reverse)
      3. Different type → UPDATE loai, update so_upvote (±2)

    Rang buoc:
      - User khong the vote cho content cua chinh minh

    Args:
        db: Database session
        user: Current user
        data: BieuQuyetCreate (doi_tuong_type, doi_tuong_id, loai)

    Returns:
        BieuQuyetResponse (hanh_dong, loai, so_upvote_moi)
    """
    doi_tuong_type = data["doi_tuong_type"]
    doi_tuong_id = data["doi_tuong_id"]
    loai = data["loai"]  # UP or DOWN
    user_uuid = UUID(user.sub)

    # Validate target exists
    tac_gia_id = None
    if doi_tuong_type == "CHU_DE":
        target_stmt = select(ChuDe).where(ChuDe.id == doi_tuong_id, ChuDe.is_deleted == False)
        target = (await db.execute(target_stmt)).scalar_one_or_none()
        if not target:
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
        tac_gia_id = target.tac_gia_id
    elif doi_tuong_type == "TRA_LOI":
        target_stmt = select(TraLoi).where(TraLoi.id == doi_tuong_id, TraLoi.is_deleted == False)
        target = (await db.execute(target_stmt)).scalar_one_or_none()
        if not target:
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
        tac_gia_id = target.tac_gia_id
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": f"doi_tuong_type khong hop le: {doi_tuong_type}",
                },
            },
        )

    # Check khong vote cho content cua minh
    if tac_gia_id == user_uuid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "error": {
                    "code": "FORUM_ERR_011",
                    "message": "Ban khong the vote cho noi dung cua chinh minh",
                },
            },
        )

    # Check existing vote
    existing_vote_stmt = select(BieuQuyet).where(
        BieuQuyet.cong_chuc_id == user_uuid,
        BieuQuyet.doi_tuong_type == doi_tuong_type,
        BieuQuyet.doi_tuong_id == doi_tuong_id,
    )
    existing_vote = (await db.execute(existing_vote_stmt)).scalar_one_or_none()

    hanh_dong = ""
    loai_result = loai
    delta = 0

    if existing_vote is None:
        # Case 1: No vote → INSERT
        new_vote = BieuQuyet(
            cong_chuc_id=user_uuid,
            doi_tuong_type=doi_tuong_type,
            doi_tuong_id=doi_tuong_id,
            loai=loai,
            created_at=_now(),
        )
        db.add(new_vote)
        hanh_dong = "CREATED"
        delta = 1 if loai == "UP" else -1

    elif existing_vote.loai == loai:
        # Case 2: Same type → DELETE (toggle off)
        await db.delete(existing_vote)
        hanh_dong = "TOGGLED_OFF"
        loai_result = None
        delta = -1 if loai == "UP" else 1  # reverse

    else:
        # Case 3: Different type → UPDATE
        existing_vote.loai = loai
        hanh_dong = "CHANGED"
        # UP→DOWN: delta = -2, DOWN→UP: delta = +2
        delta = 2 if loai == "UP" else -2

    # Update so_upvote cua target
    if doi_tuong_type == "CHU_DE":
        await db.execute(
            update(ChuDe)
            .where(ChuDe.id == doi_tuong_id)
            .values(so_upvote=ChuDe.so_upvote + delta)
        )
    else:  # TRA_LOI
        await db.execute(
            update(TraLoi)
            .where(TraLoi.id == doi_tuong_id)
            .values(so_upvote=TraLoi.so_upvote + delta)
        )

    await db.commit()

    # Lay so_upvote moi
    if doi_tuong_type == "CHU_DE":
        target_stmt = select(ChuDe.so_upvote).where(ChuDe.id == doi_tuong_id)
    else:
        target_stmt = select(TraLoi.so_upvote).where(TraLoi.id == doi_tuong_id)
    so_upvote_moi = (await db.execute(target_stmt)).scalar_one()

    return {
        "hanh_dong": hanh_dong,
        "loai": loai_result,
        "so_upvote_moi": so_upvote_moi,
    }


async def xoa_vote(
    db: AsyncSession,
    user: TokenPayload,
    data: dict,
) -> dict:
    """
    Xoa vote cua user cho doi tuong (chu de hoac tra loi).

    Args:
        db: Database session
        user: Current user
        data: BieuQuyetDelete (doi_tuong_type, doi_tuong_id)

    Returns:
        dict with message
    """
    doi_tuong_type = data["doi_tuong_type"]
    doi_tuong_id = data["doi_tuong_id"]
    user_uuid = UUID(user.sub)

    # Find existing vote
    existing_vote_stmt = select(BieuQuyet).where(
        BieuQuyet.cong_chuc_id == user_uuid,
        BieuQuyet.doi_tuong_type == doi_tuong_type,
        BieuQuyet.doi_tuong_id == doi_tuong_id,
    )
    existing_vote = (await db.execute(existing_vote_stmt)).scalar_one_or_none()

    if not existing_vote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": {
                    "code": "FORUM_ERR_001",
                    "message": "Ban chua vote cho doi tuong nay",
                },
            },
        )

    # Reverse so_upvote
    delta = -1 if existing_vote.loai == "UP" else 1
    if doi_tuong_type == "CHU_DE":
        await db.execute(
            update(ChuDe)
            .where(ChuDe.id == doi_tuong_id)
            .values(so_upvote=ChuDe.so_upvote + delta)
        )
    else:  # TRA_LOI
        await db.execute(
            update(TraLoi)
            .where(TraLoi.id == doi_tuong_id)
            .values(so_upvote=TraLoi.so_upvote + delta)
        )

    # Delete vote
    await db.delete(existing_vote)
    await db.commit()

    return {"message": "Da xoa vote"}
