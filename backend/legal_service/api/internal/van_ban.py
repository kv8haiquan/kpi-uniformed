"""
legal_service/api/internal/van_ban.py
=======================================
Internal API cho van ban — chi cac module khac goi (khong phai frontend).

Xac thuc: Header X-Internal-Key phai bang settings.internal_api_key.

GET /van-ban/{id}/summary  — lay thong tin tom tat van ban
GET /van-ban/search        — tim kiem van ban (autocomplete)
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from legal_service.config import settings
from legal_service.dependencies import get_db
from legal_service.services import van_ban_service

router = APIRouter(tags=["Internal - Van Ban"])


def verify_internal_key(x_internal_key: str = Header(...)):
    """
    Xac thuc internal API key tu Header X-Internal-Key.
    Chi cac module trusted moi biet key nay.
    """
    if x_internal_key != settings.internal_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "success": False,
                "error": {
                    "code": "AUTH_002",
                    "message": "Internal API key khong hop le",
                },
            },
        )


@router.get("/van-ban/search")
async def tim_kiem_van_ban(
    q: str = Query(min_length=2),
    limit: int = Query(default=10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(verify_internal_key),
) -> dict:
    """
    Tim kiem van ban theo tu khoa (autocomplete).
    Chi tra ve VB DA_XUAT_BAN.

    QUAN TRONG: Route nay phai dang ky TRUOC /{van_ban_id}/summary
    de tranh FastAPI parse "search" nhu UUID (se raise 422).
    """
    items = await van_ban_service.search_van_ban(db=db, q=q, limit=limit)
    return {
        "success": True,
        "data": items,
        "message": f"Tim thay {len(items)} ket qua",
    }


@router.get("/van-ban/{van_ban_id}/summary")
async def lay_tom_tat_van_ban(
    van_ban_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(verify_internal_key),
) -> dict:
    """
    Lay thong tin tom tat van ban cho cac module khac.
    VD: Forum hien thi trich yeu VB trong bai dang.
    """
    summary = await van_ban_service.get_summary(db=db, van_ban_id=van_ban_id)
    if summary is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": {
                    "code": "LEGAL_ERR_001",
                    "message": "Khong tim thay van ban",
                },
            },
        )
    return {
        "success": True,
        "data": summary,
        "message": "Lay tom tat van ban thanh cong",
    }
