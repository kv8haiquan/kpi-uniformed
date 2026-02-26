"""
forum_service/api/endpoints/bieu_quyet.py
==========================================
Endpoints Upvote / Downvote.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))

from fastapi import APIRouter, Depends

from forum_service.dependencies import (
    CurrentUserDep,
    DatabaseDep,
    get_current_user,
    get_db,
)
from forum_service.schemas.bieu_quyet import (
    BieuQuyetCreate,
    BieuQuyetDelete,
    BieuQuyetResponse,
)
from forum_service.services import bieu_quyet_service

router = APIRouter(prefix="/bieu-quyet", tags=["Biểu quyết"])


@router.post("")
async def vote(
    data: BieuQuyetCreate,
    db: DatabaseDep,
    current_user: CurrentUserDep,
) -> dict:
    """
    Vote (upvote/downvote) cho chu de hoac tra loi.

    Toggle logic:
      1. No vote → INSERT, update so_upvote (+1 UP, -1 DOWN)
      2. Same type → DELETE (toggle off), update so_upvote (reverse)
      3. Different type → UPDATE loai, update so_upvote (±2)

    Rang buoc:
      - User khong the vote cho content cua chinh minh
    """
    result = await bieu_quyet_service.vote(
        db=db,
        user=current_user,
        data=data.model_dump(),
    )
    return {
        "success": True,
        "data": result,
        "message": "Vote thanh cong",
    }


@router.delete("")
async def xoa_vote(
    data: BieuQuyetDelete,
    db: DatabaseDep,
    current_user: CurrentUserDep,
) -> dict:
    """
    Xoa vote cua user cho doi tuong (chu de hoac tra loi).
    """
    result = await bieu_quyet_service.xoa_vote(
        db=db,
        user=current_user,
        data=data.model_dump(),
    )
    return {
        "success": True,
        "data": result,
        "message": result["message"],
    }
