"""
lms_service/services/linh_vuc_service.py
========================================
Business logic cho CRUD linh vuc nghiep vu.
"""

from datetime import datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from lms_service.models.linh_vuc import LinhVuc
from lms_service.schemas.linh_vuc import LinhVucCreate, LinhVucUpdate
from lms_service.core.timezone import now_vn


class LinhVucService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def danh_sach(self, page: int = 1, page_size: int = 20) -> dict:
        """Lay danh sach linh vuc (chi active)."""
        # Count
        count_stmt = select(func.count()).select_from(LinhVuc).where(LinhVuc.is_active == True)
        total = (await self.db.execute(count_stmt)).scalar() or 0

        # Query
        stmt = (
            select(LinhVuc)
            .where(LinhVuc.is_active == True)
            .order_by(LinhVuc.thu_tu.asc(), LinhVuc.created_at.asc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await self.db.execute(stmt)
        items = result.scalars().all()

        return {
            "items": items,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_items": total,
                "total_pages": (total + page_size - 1) // page_size if page_size > 0 else 0,
            },
        }

    async def chi_tiet(self, linh_vuc_id: UUID) -> LinhVuc:
        """Lay chi tiet 1 linh vuc."""
        stmt = select(LinhVuc).where(LinhVuc.id == linh_vuc_id, LinhVuc.is_active == True)
        result = await self.db.execute(stmt)
        lv = result.scalar_one_or_none()
        if not lv:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"success": False, "error": {"code": "DGNL_001", "message": "Lĩnh vực không tồn tại"}},
            )
        return lv

    async def tao_moi(self, data: LinhVucCreate) -> LinhVuc:
        """Tao linh vuc moi."""
        # Check ma trung
        existing = await self.db.execute(
            select(LinhVuc).where(LinhVuc.ma_linh_vuc == data.ma_linh_vuc)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"success": False, "error": {"code": "DGNL_002", "message": f"Mã lĩnh vực '{data.ma_linh_vuc}' đã tồn tại"}},
            )

        lv = LinhVuc(
            ma_linh_vuc=data.ma_linh_vuc,
            ten_linh_vuc=data.ten_linh_vuc,
            mo_ta=data.mo_ta,
            thu_tu=data.thu_tu,
        )
        self.db.add(lv)
        await self.db.commit()
        await self.db.refresh(lv)
        return lv

    async def cap_nhat(self, linh_vuc_id: UUID, data: LinhVucUpdate) -> LinhVuc:
        """Cap nhat linh vuc."""
        lv = await self.chi_tiet(linh_vuc_id)

        update_data = data.model_dump(exclude_unset=True)
        # Check ma trung neu doi ma
        if "ma_linh_vuc" in update_data:
            existing = await self.db.execute(
                select(LinhVuc).where(
                    LinhVuc.ma_linh_vuc == update_data["ma_linh_vuc"],
                    LinhVuc.id != linh_vuc_id,
                )
            )
            if existing.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"success": False, "error": {"code": "DGNL_002", "message": f"Mã lĩnh vực '{update_data['ma_linh_vuc']}' đã tồn tại"}},
                )

        for key, value in update_data.items():
            setattr(lv, key, value)
        lv.updated_at = now_vn()

        await self.db.commit()
        await self.db.refresh(lv)
        return lv

    async def xoa(self, linh_vuc_id: UUID) -> None:
        """Soft delete linh vuc."""
        lv = await self.chi_tiet(linh_vuc_id)
        lv.is_active = False
        lv.updated_at = now_vn()
        await self.db.commit()
