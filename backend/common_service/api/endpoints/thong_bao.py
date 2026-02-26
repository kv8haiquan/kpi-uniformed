"""
common_service/api/endpoints/thong_bao.py
==========================================
Public API cho Notification Center.
Prefix: /api/common/v1/thong-bao
Auth: JWT Bearer token — tat ca CBCC co quyen

Endpoints:
  GET    /thong-bao              — Danh sach thong bao cua user
  GET    /thong-bao/count        — Dem chua doc (phan loai muc do)
  PATCH  /thong-bao/{id}/doc     — Danh dau 1 thong bao da doc
  PATCH  /thong-bao/doc-tat-ca   — Danh dau tat ca da doc
"""

from __future__ import annotations

import math
import uuid
from typing import Optional

from fastapi import APIRouter, Query

from common_service.dependencies import CurrentUserDep, DatabaseDep
from common_service.schemas.base import PaginatedResponse, PaginationInfo, SuccessResponse
from common_service.schemas.thong_bao import (
    ThongBaoCountResponse,
    ThongBaoListItem,
    ThongBaoResponse,
)
from common_service.services import thong_bao_service

router = APIRouter(prefix="/thong-bao", tags=["Thông báo"])


@router.get("", response_model=PaginatedResponse[ThongBaoListItem])
async def danh_sach_thong_bao(
    db: DatabaseDep,
    user: CurrentUserDep,
    da_doc: Optional[bool] = Query(default=None, description="Loc theo trang thai doc"),
    loai: Optional[str] = Query(default=None, description="Loc theo loai: KPI, LMS, FORUM, LEGAL, PORTAL, HE_THONG"),
    muc_do: Optional[str] = Query(default=None, description="Loc theo muc do: KHAN, QUAN_TRONG, BINH_THUONG"),
    page: int = Query(default=1, ge=1, description="Trang"),
    page_size: int = Query(default=20, ge=1, le=100, description="So luong moi trang"),
):
    """Lay danh sach thong bao cua user dang dang nhap.

    Chi tra thong bao CUA MINH. Sap xep: KHAN truoc, roi created_at DESC.
    """
    items, total = await thong_bao_service.danh_sach(
        db, user.sub,
        da_doc=da_doc,
        loai=loai,
        muc_do=muc_do,
        page=page,
        page_size=page_size,
    )

    return PaginatedResponse(
        data=[ThongBaoListItem.model_validate(tb) for tb in items],
        pagination=PaginationInfo(
            page=page,
            page_size=page_size,
            total_items=total,
            total_pages=max(1, math.ceil(total / page_size)),
        ),
    )


@router.get("/count", response_model=SuccessResponse[ThongBaoCountResponse])
async def dem_chua_doc(
    db: DatabaseDep,
    user: CurrentUserDep,
):
    """Dem so thong bao chua doc cua user, phan loai theo muc do.

    Dung cho badge 🔔 tren frontend.
    """
    data = await thong_bao_service.dem_chua_doc(db, user.sub)
    return SuccessResponse(data=data)


@router.patch("/doc-tat-ca", response_model=SuccessResponse[dict])
async def danh_dau_tat_ca_da_doc(
    db: DatabaseDep,
    user: CurrentUserDep,
):
    """Danh dau tat ca thong bao chua doc cua user -> da doc."""
    count = await thong_bao_service.danh_dau_tat_ca_da_doc(db, user.sub)
    return SuccessResponse(
        data={"updated_count": count},
        message=f"Đã đánh dấu {count} thông báo đã đọc",
    )


@router.patch("/{thong_bao_id}/doc", response_model=SuccessResponse[ThongBaoResponse])
async def danh_dau_da_doc(
    thong_bao_id: uuid.UUID,
    db: DatabaseDep,
    user: CurrentUserDep,
):
    """Danh dau 1 thong bao da doc.

    - 404 neu thong bao khong ton tai
    - 403 neu thong bao khong phai cua user
    """
    tb = await thong_bao_service.danh_dau_da_doc(db, thong_bao_id, user.sub)
    return SuccessResponse(
        data=ThongBaoResponse.model_validate(tb),
        message="Đã đánh dấu đã đọc",
    )
