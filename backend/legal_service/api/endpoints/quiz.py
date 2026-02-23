"""
legal_service/api/endpoints/quiz.py
=====================================
Endpoints Quiz phap luat.

GET  /van-ban/{vb_id}/quiz    — danh sach quiz cua VB (login)
POST /van-ban/{vb_id}/quiz    — tao quiz (BIEN_TAP, QT_NOI_DUNG)
POST /quiz/{id}/lam-bai       — CBCC nop bai (login)
GET  /quiz/{id}/ket-qua       — xem ket qua (login)
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
from legal_service.schemas.quiz import LamBaiInput, QuizCreate
from legal_service.services import quiz_service
from shared.auth import TokenPayload

router = APIRouter(tags=["Quiz"])


@router.get("/van-ban/{van_ban_id}/quiz")
async def lay_danh_sach_quiz(
    van_ban_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user),
) -> dict:
    """
    Lay danh sach quiz cua van ban.
    CBCC: an truong 'correct' trong cau hoi.
    BIEN_TAP/QT_NOI_DUNG: thay day du cau hoi voi dap an dung.
    """
    items = await quiz_service.danh_sach_quiz(
        db=db,
        user=current_user,
        van_ban_id=van_ban_id,
    )
    return {
        "success": True,
        "data": items,
        "message": "Lay danh sach quiz thanh cong",
    }


@router.post("/van-ban/{van_ban_id}/quiz")
async def tao_quiz(
    van_ban_id: UUID,
    data: QuizCreate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_platform_role("BIEN_TAP", "QT_NOI_DUNG")),
) -> dict:
    """Tao quiz moi cho van ban. Yeu cau: BIEN_TAP hoac QT_NOI_DUNG."""
    result = await quiz_service.tao_quiz(
        db=db,
        user=current_user,
        van_ban_id=van_ban_id,
        data=data,
    )
    return {
        "success": True,
        "data": result,
        "message": "Tao quiz thanh cong",
    }


@router.post("/quiz/{quiz_id}/lam-bai")
async def lam_bai_quiz(
    quiz_id: UUID,
    data: LamBaiInput,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user),
) -> dict:
    """CBCC nop bai quiz. He thong tu dong cham diem va luu ket qua."""
    result = await quiz_service.lam_bai(
        db=db,
        user_id=current_user.sub,
        quiz_id=quiz_id,
        data=data,
    )
    return {
        "success": True,
        "data": result,
        "message": "Nop bai thanh cong",
    }


@router.get("/quiz/{quiz_id}/ket-qua")
async def xem_ket_qua_quiz(
    quiz_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user),
) -> dict:
    """
    Xem ket qua quiz.
    CBCC: chi xem ket qua cua minh.
    BIEN_TAP/QT_NOI_DUNG: xem tat ca ket qua.
    """
    results = await quiz_service.ket_qua(
        db=db,
        user=current_user,
        quiz_id=quiz_id,
    )
    return {
        "success": True,
        "data": results,
        "message": "Lay ket qua quiz thanh cong",
    }
