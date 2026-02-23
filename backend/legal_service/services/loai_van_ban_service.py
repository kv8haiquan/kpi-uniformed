"""
legal_service/services/loai_van_ban_service.py
================================================
Business logic cho danh muc Loai Van Ban.

Cac ham:
  danh_sach  — lay danh sach tat ca loai van ban (theo thu_tu ASC)
  tao        — tao loai van ban moi (check trung ma)
  cap_nhat   — cap nhat ten/thu_tu
  xoa        — xoa that (check con FK truoc)
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from legal_service.models.loai_van_ban import LoaiVanBan
from legal_service.models.van_ban import VanBan
from legal_service.schemas.loai_van_ban import LoaiVanBanCreate, LoaiVanBanUpdate


async def danh_sach(db: AsyncSession) -> list[LoaiVanBan]:
    """
    Lay tat ca loai van ban, sap xep theo thu_tu ASC.
    Khong phan trang vi so luong it (< 20 loai).
    """
    result = await db.execute(
        select(LoaiVanBan).order_by(LoaiVanBan.thu_tu.asc(), LoaiVanBan.ten.asc())
    )
    return list(result.scalars().all())


async def tao(db: AsyncSession, data: LoaiVanBanCreate) -> LoaiVanBan:
    """
    Tao loai van ban moi.
    Check trung ma truoc khi insert.
    """
    # Kiem tra trung ma
    ket_qua = await db.execute(select(LoaiVanBan).where(LoaiVanBan.ma == data.ma.upper()))
    if ket_qua.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "error": {
                    "code": "LEGAL_LVB_001",
                    "message": f"Ma loai van ban '{data.ma}' da ton tai",
                },
            },
        )

    loai_vb = LoaiVanBan(
        ma=data.ma.upper(),
        ten=data.ten,
        thu_tu=data.thu_tu,
    )
    db.add(loai_vb)
    await db.commit()
    await db.refresh(loai_vb)
    return loai_vb


async def cap_nhat(
    db: AsyncSession,
    loai_vb_id: UUID,
    data: LoaiVanBanUpdate,
) -> LoaiVanBan:
    """Cap nhat thong tin loai van ban."""
    # Tim loai van ban
    ket_qua = await db.execute(select(LoaiVanBan).where(LoaiVanBan.id == loai_vb_id))
    loai_vb = ket_qua.scalar_one_or_none()
    if not loai_vb:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": {
                    "code": "LEGAL_LVB_002",
                    "message": "Khong tim thay loai van ban",
                },
            },
        )

    # Cap nhat cac truong co gia tri
    if data.ten is not None:
        loai_vb.ten = data.ten
    if data.thu_tu is not None:
        loai_vb.thu_tu = data.thu_tu

    await db.commit()
    await db.refresh(loai_vb)
    return loai_vb


async def xoa(db: AsyncSession, loai_vb_id: UUID) -> None:
    """
    Xoa that loai van ban.
    Kiem tra con van ban nao FK khong truoc khi xoa.
    """
    # Tim loai van ban
    ket_qua = await db.execute(select(LoaiVanBan).where(LoaiVanBan.id == loai_vb_id))
    loai_vb = ket_qua.scalar_one_or_none()
    if not loai_vb:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": {
                    "code": "LEGAL_LVB_002",
                    "message": "Khong tim thay loai van ban",
                },
            },
        )

    # Kiem tra con van ban nao FK den loai nay khong
    ket_qua_vb = await db.execute(
        select(VanBan.id)
        .where(VanBan.loai_van_ban_id == loai_vb_id)
        .where(VanBan.is_deleted == False)
        .limit(1)
    )
    if ket_qua_vb.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "error": {
                    "code": "LEGAL_LVB_003",
                    "message": "Khong the xoa loai van ban dang duoc su dung",
                },
            },
        )

    await db.delete(loai_vb)
    await db.commit()
