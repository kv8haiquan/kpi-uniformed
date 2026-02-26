"""
forum_service/api/endpoints/chuyen_muc.py
==========================================
Endpoints CRUD Chuyen muc dien dan.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))

from uuid import UUID

from fastapi import APIRouter, Depends, status

from forum_service.dependencies import (
    CurrentUserDep,
    DatabaseDep,
    get_current_user,
    get_db,
    require_platform_role,
)
from forum_service.schemas.chuyen_muc import (
    ChuyenMucCreate,
    ChuyenMucResponse,
    ChuyenMucUpdate,
)
from forum_service.services import chuyen_muc_service
from shared.auth import TokenPayload

router = APIRouter(prefix="/chuyen-muc", tags=["Chuyên mục"])


@router.get("")
async def danh_sach_chuyen_muc(
    db: DatabaseDep,
    current_user: CurrentUserDep,
    is_active: bool = True,
) -> dict:
    """
    Lay danh sach chuyen muc theo dang tree (parent-children).
    Kem thong ke: so_chu_de, so_tra_loi, chu_de_moi_nhat.
    """
    data = await chuyen_muc_service.danh_sach(db=db, is_active=is_active)
    return {
        "success": True,
        "data": data,
        "message": "Lay danh sach chuyen muc thanh cong",
    }


@router.post("", status_code=status.HTTP_201_CREATED)
async def tao_chuyen_muc(
    data: ChuyenMucCreate,
    db: DatabaseDep,
    current_user: TokenPayload = Depends(require_platform_role("DIEU_PHOI_FORUM")),
) -> dict:
    """Tao chuyen muc moi. Yeu cau: DIEU_PHOI_FORUM hoac SUPER_ADMIN."""
    result = await chuyen_muc_service.tao(
        db=db,
        data=data.model_dump(),
        user=current_user,
    )
    return {
        "success": True,
        "data": result,
        "message": "Tao chuyen muc thanh cong",
    }


@router.put("/{chuyen_muc_id}")
async def sua_chuyen_muc(
    chuyen_muc_id: UUID,
    data: ChuyenMucUpdate,
    db: DatabaseDep,
    current_user: TokenPayload = Depends(require_platform_role("DIEU_PHOI_FORUM")),
) -> dict:
    """Cap nhat chuyen muc. Yeu cau: DIEU_PHOI_FORUM hoac SUPER_ADMIN."""
    result = await chuyen_muc_service.sua(
        db=db,
        chuyen_muc_id=chuyen_muc_id,
        data=data.model_dump(exclude_unset=True),
        user=current_user,
    )
    return {
        "success": True,
        "data": result,
        "message": "Cap nhat chuyen muc thanh cong",
    }


@router.delete("/{chuyen_muc_id}")
async def xoa_chuyen_muc(
    chuyen_muc_id: UUID,
    db: DatabaseDep,
    current_user: TokenPayload = Depends(require_platform_role("DIEU_PHOI_FORUM")),
) -> dict:
    """
    Xoa chuyen muc (soft delete — set is_active=False).
    Yeu cau: DIEU_PHOI_FORUM hoac SUPER_ADMIN.
    Reject neu con chu de active.
    """
    await chuyen_muc_service.xoa(
        db=db,
        chuyen_muc_id=chuyen_muc_id,
        user=current_user,
    )
    return {
        "success": True,
        "data": None,
        "message": "Xoa chuyen muc thanh cong",
    }
