"""
forum_service/api/endpoints/tra_loi.py
=======================================
Endpoints CRUD Tra loi / Reply.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))

from uuid import UUID

from fastapi import APIRouter, Depends

from forum_service.dependencies import (
    CurrentUserDep,
    DatabaseDep,
    get_current_user,
    get_db,
    require_platform_role,
)
from forum_service.schemas.tra_loi import TraLoiUpdate
from forum_service.services import tra_loi_service
from shared.auth import TokenPayload

router = APIRouter(prefix="/tra-loi", tags=["Trả lời"])


@router.put("/{tra_loi_id}")
async def sua_tra_loi(
    tra_loi_id: UUID,
    data: TraLoiUpdate,
    db: DatabaseDep,
    current_user: CurrentUserDep,
) -> dict:
    """
    Cap nhat tra loi.

    Quy tac:
      - Author: chi trong 24h sau khi tao
      - DIEU_PHOI/SUPER_ADMIN: luon duoc sua
    """
    result = await tra_loi_service.sua(
        db=db,
        tra_loi_id=tra_loi_id,
        data=data.model_dump(exclude_unset=True),
        user=current_user,
    )
    return {
        "success": True,
        "data": result,
        "message": "Cap nhat tra loi thanh cong",
    }


@router.delete("/{tra_loi_id}")
async def xoa_tra_loi(
    tra_loi_id: UUID,
    db: DatabaseDep,
    current_user: CurrentUserDep,
) -> dict:
    """
    Xoa tra loi (soft delete).

    Quy tac:
      - Author OR DIEU_PHOI/SUPER_ADMIN
      - Decrement chu_de.so_tra_loi -= 1
    """
    await tra_loi_service.xoa(
        db=db,
        tra_loi_id=tra_loi_id,
        user=current_user,
    )
    return {
        "success": True,
        "data": None,
        "message": "Xoa tra loi thanh cong",
    }


@router.patch("/{tra_loi_id}/an")
async def an_tra_loi(
    tra_loi_id: UUID,
    db: DatabaseDep,
    current_user: TokenPayload = Depends(require_platform_role("DIEU_PHOI_FORUM")),
) -> dict:
    """
    An tra loi (set is_an = True).
    Yeu cau: DIEU_PHOI_FORUM hoac SUPER_ADMIN.
    """
    await tra_loi_service.an(
        db=db,
        tra_loi_id=tra_loi_id,
        user=current_user,
    )
    return {
        "success": True,
        "data": None,
        "message": "An tra loi thanh cong",
    }
