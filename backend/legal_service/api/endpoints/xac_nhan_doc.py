"""
legal_service/api/endpoints/xac_nhan_doc.py
=============================================
Endpoints Xac nhan doc van ban.

POST  /van-ban/{id}/xac-nhan    — CBCC xac nhan da doc (login)
PATCH /van-ban/{id}/tracking    — Ghi nhan thoi gian doc (login)
GET   /van-ban/{id}/bao-cao-doc — Bao cao doc theo VB (QT_NOI_DUNG, Lanh dao)
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from legal_service.dependencies import (
    get_current_user,
    get_db,
)
from legal_service.schemas.xac_nhan_doc import TrackingDocInput, XacNhanDocCreate
from legal_service.services import xac_nhan_doc_service
from shared.auth import TokenPayload

router = APIRouter(tags=["Xac Nhan Doc"])


@router.post("/van-ban/{van_ban_id}/xac-nhan")
async def xac_nhan_da_doc(
    van_ban_id: UUID,
    data: XacNhanDocCreate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user),
) -> dict:
    """
    CBCC xac nhan da doc va hieu van ban.
    Moi CBCC chi xac nhan 1 lan cho moi van ban.
    """
    result = await xac_nhan_doc_service.xac_nhan_da_doc(
        db=db,
        user_id=current_user.sub,
        van_ban_id=van_ban_id,
        data=data,
    )
    return {
        "success": True,
        "data": result,
        "message": "Xac nhan doc thanh cong",
    }


@router.patch("/van-ban/{van_ban_id}/tracking")
async def tracking_thoi_gian_doc(
    van_ban_id: UUID,
    data: TrackingDocInput,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user),
) -> dict:
    """Ghi nhan/cong don thoi gian doc thuc te cua CBCC."""
    result = await xac_nhan_doc_service.tracking_doc(
        db=db,
        user_id=current_user.sub,
        van_ban_id=van_ban_id,
        data=data,
    )
    return {
        "success": True,
        "data": result,
        "message": "Cap nhat thoi gian doc thanh cong",
    }


@router.get("/van-ban/{van_ban_id}/bao-cao-doc")
async def bao_cao_doc_van_ban(
    van_ban_id: UUID,
    don_vi_id: Optional[UUID] = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user),
) -> dict:
    """
    Bao cao trang thai doc theo tung van ban.
    QT_NOI_DUNG: xem tat ca.
    Lanh dao: xem don vi cua minh.
    """
    result = await xac_nhan_doc_service.bao_cao_doc(
        db=db,
        user=current_user,
        van_ban_id=van_ban_id,
        don_vi_id=don_vi_id,
    )
    return {
        "success": True,
        "data": result,
        "message": "Lay bao cao doc van ban thanh cong",
    }
