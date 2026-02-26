"""
common_service/api/internal/knowledge_base.py
===============================================
Internal API cho Knowledge Base.
Prefix: /internal/v1/knowledge-base
Auth: X-Internal-Key header

Endpoints:
  POST /knowledge-base/cap-nhat-van-ban  — Legal goi khi VB thay doi
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from common_service.dependencies import DatabaseDep, verify_internal_key
from common_service.schemas.base import SuccessResponse
from common_service.schemas.knowledge_base import KBCapNhatVanBanRequest
from common_service.services import knowledge_base_service

router = APIRouter(
    prefix="/knowledge-base",
    tags=["KB Internal"],
    dependencies=[Depends(verify_internal_key)],
)


@router.post("/cap-nhat-van-ban", response_model=SuccessResponse[dict])
async def cap_nhat_van_ban(
    data: KBCapNhatVanBanRequest,
    db: DatabaseDep,
):
    """Legal module goi khi van ban phap luat thay doi.

    Tim tat ca KB co van_ban_lien_quan chua van_ban_id
    va dang DA_XUAT_BAN → chuyen sang CAN_CAP_NHAT.
    """
    count = await knowledge_base_service.danh_dau_can_cap_nhat(db, data.van_ban_id)
    return SuccessResponse(
        data={"updated_count": count},
        message=f"Đã đánh dấu {count} KB cần cập nhật",
    )
