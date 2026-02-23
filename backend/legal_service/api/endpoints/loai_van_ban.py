"""
legal_service/api/endpoints/loai_van_ban.py
=============================================
Endpoints danh muc Loai Van Ban.

GET    /loai-van-ban        — tat ca user dang nhap
POST   /loai-van-ban        — QT_NOI_DUNG, SUPER_ADMIN
PUT    /loai-van-ban/{id}   — QT_NOI_DUNG, SUPER_ADMIN
DELETE /loai-van-ban/{id}   — QT_NOI_DUNG, SUPER_ADMIN
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from legal_service.dependencies import (
    get_current_user,
    get_db,
    require_platform_role,
)
from legal_service.schemas.loai_van_ban import (
    LoaiVanBanCreate,
    LoaiVanBanUpdate,
)
from legal_service.services import loai_van_ban_service
from shared.auth import TokenPayload

router = APIRouter(tags=["Loai Van Ban"])


@router.get("/loai-van-ban")
async def lay_danh_sach_loai_van_ban(
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user),
) -> dict:
    """Lay tat ca loai van ban, sap xep theo thu_tu."""
    items = await loai_van_ban_service.danh_sach(db)
    return {
        "success": True,
        "data": [
            {
                "id": str(item.id),
                "ma": item.ma,
                "ten": item.ten,
                "thu_tu": item.thu_tu or 0,
            }
            for item in items
        ],
        "message": "Lay danh sach loai van ban thanh cong",
    }


@router.post("/loai-van-ban")
async def tao_loai_van_ban(
    data: LoaiVanBanCreate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_platform_role("QT_NOI_DUNG")),
) -> dict:
    """Tao loai van ban moi. Yeu cau: QT_NOI_DUNG hoac SUPER_ADMIN."""
    item = await loai_van_ban_service.tao(db, data)
    return {
        "success": True,
        "data": {
            "id": str(item.id),
            "ma": item.ma,
            "ten": item.ten,
            "thu_tu": item.thu_tu or 0,
        },
        "message": "Tao loai van ban thanh cong",
    }


@router.put("/loai-van-ban/{loai_vb_id}")
async def cap_nhat_loai_van_ban(
    loai_vb_id: UUID,
    data: LoaiVanBanUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_platform_role("QT_NOI_DUNG")),
) -> dict:
    """Cap nhat loai van ban. Yeu cau: QT_NOI_DUNG hoac SUPER_ADMIN."""
    item = await loai_van_ban_service.cap_nhat(db, loai_vb_id, data)
    return {
        "success": True,
        "data": {
            "id": str(item.id),
            "ma": item.ma,
            "ten": item.ten,
            "thu_tu": item.thu_tu or 0,
        },
        "message": "Cap nhat loai van ban thanh cong",
    }


@router.delete("/loai-van-ban/{loai_vb_id}")
async def xoa_loai_van_ban(
    loai_vb_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_platform_role("QT_NOI_DUNG")),
) -> dict:
    """Xoa loai van ban. Yeu cau: QT_NOI_DUNG hoac SUPER_ADMIN."""
    await loai_van_ban_service.xoa(db, loai_vb_id)
    return {
        "success": True,
        "data": None,
        "message": "Xoa loai van ban thanh cong",
    }
