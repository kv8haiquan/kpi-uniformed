"""
lms_service/services/chuyen_de_service.py
=========================================
Business logic cho CRUD chuyen de dao tao.
"""

import uuid
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from lms_service.models.chuyen_de import ChuyenDe
from lms_service.models.khoa_hoc import KhoaHoc
from lms_service.schemas.chuyen_de import ChuyenDeCreate, ChuyenDeUpdate


class ChuyenDeService:
    """Service xu ly logic chuyen de dao tao."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def danh_sach(self, is_active: Optional[bool] = None) -> list[dict]:
        """Lay danh sach chuyen de, kem so khoa hoc moi chuyen de.

        Args:
            is_active: Loc theo trang thai active (None = tat ca)

        Returns:
            list[dict]: Danh sach chuyen de voi so_khoa_hoc
        """
        # Subquery dem so khoa hoc active cho moi chuyen de
        so_kh_subq = (
            select(
                KhoaHoc.chuyen_de_id,
                func.count(KhoaHoc.id).label("so_khoa_hoc"),
            )
            .where(KhoaHoc.is_active == True)  # noqa: E712
            .group_by(KhoaHoc.chuyen_de_id)
            .subquery()
        )

        # Query chinh
        stmt = (
            select(
                ChuyenDe,
                func.coalesce(so_kh_subq.c.so_khoa_hoc, 0).label("so_khoa_hoc"),
            )
            .outerjoin(so_kh_subq, ChuyenDe.id == so_kh_subq.c.chuyen_de_id)
        )

        if is_active is not None:
            stmt = stmt.where(ChuyenDe.is_active == is_active)

        stmt = stmt.order_by(ChuyenDe.thu_tu.asc())

        result = await self.db.execute(stmt)
        rows = result.all()

        # Chuyen thanh dict de gan so_khoa_hoc
        items = []
        for chuyen_de, so_khoa_hoc in rows:
            item = {
                "id": chuyen_de.id,
                "ma_chuyen_de": chuyen_de.ma_chuyen_de,
                "ten_chuyen_de": chuyen_de.ten_chuyen_de,
                "mo_ta": chuyen_de.mo_ta,
                "anh_dai_dien": chuyen_de.anh_dai_dien,
                "thu_tu": chuyen_de.thu_tu,
                "is_active": chuyen_de.is_active,
                "created_by": chuyen_de.created_by,
                "created_at": chuyen_de.created_at,
                "so_khoa_hoc": so_khoa_hoc,
            }
            items.append(item)

        return items

    async def chi_tiet(self, id: uuid.UUID) -> ChuyenDe:
        """Lay chi tiet chuyen de theo ID.

        Raises:
            HTTPException 404: Khong tim thay chuyen de
        """
        stmt = select(ChuyenDe).where(ChuyenDe.id == id)
        result = await self.db.execute(stmt)
        chuyen_de = result.scalar_one_or_none()

        if chuyen_de is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "success": False,
                    "error": {
                        "code": "LMS_ERR_001",
                        "message": "Không tìm thấy chuyên đề",
                    },
                },
            )

        return chuyen_de

    async def tao_moi(self, data: ChuyenDeCreate, user_id: uuid.UUID) -> ChuyenDe:
        """Tao chuyen de moi.

        Args:
            data: Thong tin chuyen de
            user_id: UUID cua nguoi tao (tu JWT sub)

        Raises:
            HTTPException 409: Ma chuyen de da ton tai
        """
        # Kiem tra trung ma_chuyen_de
        stmt = select(ChuyenDe).where(ChuyenDe.ma_chuyen_de == data.ma_chuyen_de)
        result = await self.db.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "success": False,
                    "error": {
                        "code": "LMS_ERR_002",
                        "message": "Mã chuyên đề đã tồn tại",
                    },
                },
            )

        chuyen_de = ChuyenDe(
            ma_chuyen_de=data.ma_chuyen_de,
            ten_chuyen_de=data.ten_chuyen_de,
            mo_ta=data.mo_ta,
            thu_tu=data.thu_tu,
            created_by=user_id,
        )
        self.db.add(chuyen_de)
        await self.db.flush()
        await self.db.refresh(chuyen_de)
        return chuyen_de

    async def cap_nhat(self, id: uuid.UUID, data: ChuyenDeUpdate) -> ChuyenDe:
        """Cap nhat chuyen de — chi update fields khong None.

        Raises:
            HTTPException 404: Khong tim thay chuyen de
        """
        chuyen_de = await self.chi_tiet(id)

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(chuyen_de, field, value)

        await self.db.flush()
        await self.db.refresh(chuyen_de)
        return chuyen_de

    async def xoa(self, id: uuid.UUID) -> None:
        """Soft delete chuyen de — set is_active = False.

        Raises:
            HTTPException 404: Khong tim thay chuyen de
        """
        chuyen_de = await self.chi_tiet(id)
        chuyen_de.is_active = False
        await self.db.flush()
