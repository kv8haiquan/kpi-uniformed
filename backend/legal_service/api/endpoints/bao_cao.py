"""
legal_service/api/endpoints/bao_cao.py
========================================
Endpoints Bao cao va Dashboard.

GET /dashboard/summary          — tong hop so lieu cho CBCC (login)
GET /bao-cao/ca-nhan            — bao cao ca nhan trong thang (login)
GET /bao-cao/don-vi/{don_vi_id} — bao cao don vi (QT_NOI_DUNG, Lanh dao)
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from legal_service.dependencies import get_current_user, get_db
from legal_service.services import xac_nhan_doc_service
from shared.auth import TokenPayload

router = APIRouter(tags=["Bao Cao"])


@router.get("/dashboard/summary")
async def dashboard_summary(
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user),
) -> dict:
    """
    Lay tong hop so lieu dashboard cho CBCC hien tai.
    Tra ve: vb_moi_tuan, vb_chua_doc, vb_khan, vb_sap_het_han, quiz_chua_lam.
    """
    result = await xac_nhan_doc_service.dashboard_summary(
        db=db,
        user_id=current_user.sub,
    )
    return {
        "success": True,
        "data": result,
        "message": "Lay dashboard thanh cong",
    }


@router.get("/bao-cao/ca-nhan")
async def bao_cao_ca_nhan(
    thang: int = Query(ge=1, le=12),
    nam: int = Query(ge=2020),
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user),
) -> dict:
    """Bao cao doc van ban ca nhan trong thang."""
    result = await xac_nhan_doc_service.bao_cao_ca_nhan(
        db=db,
        user_id=current_user.sub,
        thang=thang,
        nam=nam,
    )
    return {
        "success": True,
        "data": result,
        "message": "Lay bao cao ca nhan thanh cong",
    }


@router.get("/bao-cao/don-vi/{don_vi_id}")
async def bao_cao_don_vi(
    don_vi_id: UUID,
    thang: int = Query(ge=1, le=12),
    nam: int = Query(ge=2020),
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user),
) -> dict:
    """
    Bao cao tuan thu doc van ban theo don vi trong thang.
    QT_NOI_DUNG: xem tat ca don vi.
    Lanh dao: chi xem don vi cua minh.
    """
    result = await xac_nhan_doc_service.bao_cao_don_vi(
        db=db,
        user=current_user,
        don_vi_id=don_vi_id,
        thang=thang,
        nam=nam,
    )
    return {
        "success": True,
        "data": result,
        "message": "Lay bao cao don vi thanh cong",
    }
