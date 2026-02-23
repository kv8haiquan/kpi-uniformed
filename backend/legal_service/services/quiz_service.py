"""
legal_service/services/quiz_service.py
=======================================
Business logic cho Quiz phap luat.

Cau hoi duoc nhung truc tiep vao JSONB quiz_van_ban.cau_hoi.
CBCC lam quiz → ket qua luu vao legal.ket_qua_quiz.

Cac ham:
  danh_sach_quiz — lay quiz cua van ban (an 'correct' khi CBCC xem)
  tao_quiz       — tao quiz moi (BIEN_TAP, QT_NOI_DUNG)
  lam_bai        — CBCC nop bai, cham diem tu dong
  ket_qua        — xem ket qua quiz
"""

import os
import sys
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from legal_service.models.ket_qua_quiz import KetQuaQuiz
from legal_service.models.quiz_van_ban import QuizVanBan
from legal_service.models.van_ban import VanBan
from legal_service.schemas.quiz import LamBaiInput, QuizCreate
from shared.auth import TokenPayload


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _is_quan_ly(user: TokenPayload) -> bool:
    if user.vai_tro == "SUPER_ADMIN" or user.is_admin:
        return True
    return "QT_NOI_DUNG" in (user.platform_roles or [])


def _is_bien_tap_hoac_quan_ly(user: TokenPayload) -> bool:
    if _is_quan_ly(user):
        return True
    return "BIEN_TAP" in (user.platform_roles or [])


def _an_correct(cau_hoi_list: list) -> list:
    """An truong 'correct' trong danh sach cau hoi (dung cho CBCC)."""
    result = []
    for ch in cau_hoi_list:
        ch_copy = dict(ch)
        ch_copy.pop("correct", None)
        result.append(ch_copy)
    return result


async def danh_sach_quiz(
    db: AsyncSession,
    user: TokenPayload,
    van_ban_id: UUID,
) -> list[dict]:
    """
    Lay danh sach quiz cua 1 van ban.
    BIEN_TAP/QT_NOI_DUNG: thay 'correct' trong cau_hoi.
    CBCC: an 'correct' (chi thay dap an, khong thay dap an dung).
    """
    result = await db.execute(
        select(QuizVanBan)
        .where(QuizVanBan.van_ban_id == van_ban_id)
        .where(QuizVanBan.is_active == True)
        .order_by(QuizVanBan.created_at.asc())
    )
    quizzes = list(result.scalars().all())

    co_quyen_xem_dap_an = _is_bien_tap_hoac_quan_ly(user)

    items = []
    for q in quizzes:
        cau_hoi = q.cau_hoi or []
        if not co_quyen_xem_dap_an:
            # An dap an dung khi CBCC xem
            cau_hoi = _an_correct(cau_hoi)

        items.append(
            {
                "id": q.id,
                "van_ban_id": q.van_ban_id,
                "tieu_de": q.tieu_de,
                "so_cau_hoi": q.so_cau_hoi,
                "thoi_gian_phut": q.thoi_gian_phut,
                "diem_dat": float(q.diem_dat),
                "cau_hoi": cau_hoi,
                "is_active": q.is_active,
                "created_at": q.created_at,
            }
        )

    return items


async def tao_quiz(
    db: AsyncSession,
    user: TokenPayload,
    van_ban_id: UUID,
    data: QuizCreate,
) -> dict:
    """
    Tao quiz moi cho van ban.

    Dieu kien:
      - Van ban phai ton tai va DA_XUAT_BAN
      - So cau hoi: 5-20
      - correct index hop le (0 <= correct < len(dap_an))
    """
    # Kiem tra van ban ton tai
    vb_result = await db.execute(
        select(VanBan.id, VanBan.trang_thai_duyet)
        .where(VanBan.id == van_ban_id)
        .where(VanBan.is_deleted == False)
    )
    vb_row = vb_result.first()
    if not vb_row:
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

    if vb_row[1] != "DA_XUAT_BAN":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "error": {
                    "code": "LEGAL_ERR_007",
                    "message": "Chi co the them quiz cho van ban da xuat ban",
                },
            },
        )

    # Validate cau hoi
    for i, cau in enumerate(data.cau_hoi):
        if not (0 <= cau.correct < len(cau.dap_an)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "success": False,
                    "error": {
                        "code": "LEGAL_ERR_008",
                        "message": f"Cau {i+1}: index 'correct' ({cau.correct}) khong hop le (co {len(cau.dap_an)} dap an)",
                    },
                },
            )

    # Chuyen cau hoi sang dict de luu JSONB
    cau_hoi_jsonb = [
        {
            "noi_dung": ch.noi_dung,
            "dap_an": ch.dap_an,
            "correct": ch.correct,
            "giai_thich": ch.giai_thich,
        }
        for ch in data.cau_hoi
    ]

    quiz = QuizVanBan(
        van_ban_id=van_ban_id,
        tieu_de=data.tieu_de,
        so_cau_hoi=len(data.cau_hoi),
        thoi_gian_phut=data.thoi_gian_phut,
        diem_dat=data.diem_dat,
        cau_hoi=cau_hoi_jsonb,
        nguoi_tao_id=UUID(user.sub),
        is_active=True,
        created_at=_now(),
    )
    db.add(quiz)
    await db.commit()
    await db.refresh(quiz)

    # BIEN_TAP/QT_NOI_DUNG thay dap an dung
    return {
        "id": quiz.id,
        "van_ban_id": quiz.van_ban_id,
        "tieu_de": quiz.tieu_de,
        "so_cau_hoi": quiz.so_cau_hoi,
        "thoi_gian_phut": quiz.thoi_gian_phut,
        "diem_dat": float(quiz.diem_dat),
        "cau_hoi": quiz.cau_hoi,
        "is_active": quiz.is_active,
        "created_at": quiz.created_at,
    }


async def lam_bai(
    db: AsyncSession,
    user_id: str,
    quiz_id: UUID,
    data: LamBaiInput,
) -> dict:
    """
    CBCC nop bai quiz — tu dong cham diem.

    Tinh diem:
      diem = (so_cau_dung / so_cau_hoi) * 100
      dat_yeu_cau = diem >= quiz.diem_dat

    chi_tiet: [{"cau": i, "tra_loi": x, "dung": bool, "giai_thich": str}]
    """
    user_uuid = UUID(user_id)

    # Load quiz
    result = await db.execute(select(QuizVanBan).where(QuizVanBan.id == quiz_id))
    quiz = result.scalar_one_or_none()
    if not quiz or not quiz.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": {
                    # LEGAL_ERR_006: Quiz khong ton tai (dung theo LEGAL_API_SPECS)
                    "code": "LEGAL_ERR_006",
                    "message": "Khong tim thay quiz hoac quiz da bi tat",
                },
            },
        )

    cau_hoi = quiz.cau_hoi or []
    so_cau_hoi = len(cau_hoi)

    # Cham diem
    so_cau_dung = 0
    chi_tiet = []

    # Tao map tra loi theo index cau
    tra_loi_map = {tl.cau: tl.dap_an for tl in data.tra_loi}

    for i, ch in enumerate(cau_hoi):
        tra_loi = tra_loi_map.get(i)
        dung = (tra_loi == ch.get("correct")) if tra_loi is not None else False
        if dung:
            so_cau_dung += 1

        chi_tiet.append(
            {
                "cau": i,
                "tra_loi": tra_loi,
                "dung": dung,
                "giai_thich": ch.get("giai_thich", ""),
            }
        )

    diem = (so_cau_dung / so_cau_hoi * 100) if so_cau_hoi > 0 else 0.0
    dat_yeu_cau = diem >= float(quiz.diem_dat)

    # Luu ket qua
    ket_qua = KetQuaQuiz(
        quiz_id=quiz_id,
        cong_chuc_id=user_uuid,
        diem=round(diem, 2),
        so_cau_dung=so_cau_dung,
        dat_yeu_cau=dat_yeu_cau,
        chi_tiet=chi_tiet,
        created_at=_now(),
    )
    db.add(ket_qua)
    await db.commit()
    await db.refresh(ket_qua)

    return {
        "id": ket_qua.id,
        "quiz_id": quiz_id,
        "diem": float(ket_qua.diem),
        "so_cau_dung": ket_qua.so_cau_dung,
        "dat_yeu_cau": ket_qua.dat_yeu_cau,
        "chi_tiet": ket_qua.chi_tiet,
        "created_at": ket_qua.created_at,
    }


async def ket_qua(
    db: AsyncSession,
    user: TokenPayload,
    quiz_id: UUID,
) -> list[dict]:
    """
    Xem ket qua quiz.

    CBCC: chi xem ket qua cua minh.
    BIEN_TAP/QT_NOI_DUNG: xem tat ca ket qua cua quiz.
    """
    user_uuid = UUID(user.sub)
    is_quan_ly = _is_quan_ly(user)
    is_bt = "BIEN_TAP" in (user.platform_roles or [])

    # Build query
    query = select(KetQuaQuiz).where(KetQuaQuiz.quiz_id == quiz_id)

    # CBCC chi xem ket qua cua minh
    if not is_quan_ly and not is_bt:
        query = query.where(KetQuaQuiz.cong_chuc_id == user_uuid)

    query = query.order_by(KetQuaQuiz.created_at.desc())
    result = await db.execute(query)
    ket_quas = list(result.scalars().all())

    return [
        {
            "id": kq.id,
            "quiz_id": kq.quiz_id,
            "diem": float(kq.diem) if kq.diem else None,
            "so_cau_dung": kq.so_cau_dung,
            "dat_yeu_cau": kq.dat_yeu_cau,
            "chi_tiet": kq.chi_tiet,
            "created_at": kq.created_at,
        }
        for kq in ket_quas
    ]
