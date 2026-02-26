"""
common_service/api/internal/thong_bao.py
=========================================
Internal API cho Notification Center.
Prefix: /internal/v1/thong-bao
Auth: X-Internal-Key header (module noi bo)

Endpoints:
  POST   /thong-bao        — Tao 1 thong bao
  POST   /thong-bao/bulk   — Tao hang loat (nhieu nguoi nhan)
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from common_service.dependencies import DatabaseDep, verify_internal_key
from common_service.schemas.base import SuccessResponse
from common_service.schemas.thong_bao import (
    ThongBaoCreateBulk,
    ThongBaoCreateInternal,
    ThongBaoResponse,
)
from common_service.services import thong_bao_service

router = APIRouter(
    prefix="/thong-bao",
    tags=["Thông báo Internal"],
    dependencies=[Depends(verify_internal_key)],
)


@router.post("", response_model=SuccessResponse[ThongBaoResponse], status_code=201)
async def tao_thong_bao(
    data: ThongBaoCreateInternal,
    db: DatabaseDep,
):
    """Tao 1 thong bao — chi module noi bo duoc goi.

    Validate: loai phai nam trong [KPI, LMS, FORUM, LEGAL, PORTAL, HE_THONG].
    """
    tb = await thong_bao_service.tao_thong_bao(db, data)
    return SuccessResponse(
        data=ThongBaoResponse.model_validate(tb),
        message="Tạo thông báo thành công",
    )


@router.post("/bulk", response_model=SuccessResponse[dict], status_code=201)
async def tao_thong_bao_hang_loat(
    data: ThongBaoCreateBulk,
    db: DatabaseDep,
):
    """Tao thong bao hang loat cho nhieu nguoi — chi module noi bo duoc goi.

    Vi du: Gui thong bao van ban khan cho tat ca CBCC trong 1 don vi.
    """
    count = await thong_bao_service.tao_thong_bao_hang_loat(db, data)
    return SuccessResponse(
        data={"created_count": count},
        message=f"Đã tạo {count} thông báo",
    )
