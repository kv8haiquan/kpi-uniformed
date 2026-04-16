"""
lms_service/services/vi_tri_viec_lam_service.py
================================================
Business logic cho CRUD vi tri viec lam.
"""

from datetime import datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from lms_service.models.vi_tri_viec_lam import ViTriViecLam
from lms_service.schemas.vi_tri_viec_lam import ViTriViecLamCreate, ViTriViecLamUpdate


class ViTriViecLamService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def danh_sach(self, page: int = 1, page_size: int = 20) -> dict:
        """Lay danh sach vi tri viec lam (chi active)."""
        count_stmt = select(func.count()).select_from(ViTriViecLam).where(ViTriViecLam.is_active == True)
        total = (await self.db.execute(count_stmt)).scalar() or 0

        stmt = (
            select(ViTriViecLam)
            .where(ViTriViecLam.is_active == True)
            .order_by(ViTriViecLam.thu_tu.asc(), ViTriViecLam.created_at.asc())
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

    async def chi_tiet(self, vi_tri_id: UUID) -> ViTriViecLam:
        """Lay chi tiet 1 vi tri."""
        stmt = select(ViTriViecLam).where(ViTriViecLam.id == vi_tri_id, ViTriViecLam.is_active == True)
        result = await self.db.execute(stmt)
        vt = result.scalar_one_or_none()
        if not vt:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"success": False, "error": {"code": "DGNL_003", "message": "Vị trí việc làm không tồn tại"}},
            )
        return vt

    async def tao_moi(self, data: ViTriViecLamCreate) -> ViTriViecLam:
        """Tao vi tri viec lam moi."""
        # Check ma trung
        existing = await self.db.execute(
            select(ViTriViecLam).where(ViTriViecLam.ma_vi_tri == data.ma_vi_tri)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"success": False, "error": {"code": "DGNL_004", "message": f"Mã vị trí '{data.ma_vi_tri}' đã tồn tại"}},
            )

        vt = ViTriViecLam(
            ma_vi_tri=data.ma_vi_tri,
            ten_vi_tri=data.ten_vi_tri,
            mo_ta=data.mo_ta,
            linh_vuc_ids=[str(uid) for uid in (data.linh_vuc_ids or [])],
            thu_tu=data.thu_tu,
        )
        self.db.add(vt)
        await self.db.commit()
        await self.db.refresh(vt)
        return vt

    async def cap_nhat(self, vi_tri_id: UUID, data: ViTriViecLamUpdate) -> ViTriViecLam:
        """Cap nhat vi tri viec lam."""
        vt = await self.chi_tiet(vi_tri_id)

        update_data = data.model_dump(exclude_unset=True)
        # Check ma trung neu doi ma
        if "ma_vi_tri" in update_data:
            existing = await self.db.execute(
                select(ViTriViecLam).where(
                    ViTriViecLam.ma_vi_tri == update_data["ma_vi_tri"],
                    ViTriViecLam.id != vi_tri_id,
                )
            )
            if existing.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"success": False, "error": {"code": "DGNL_004", "message": f"Mã vị trí '{update_data['ma_vi_tri']}' đã tồn tại"}},
                )

        # Convert linh_vuc_ids UUID -> str
        if "linh_vuc_ids" in update_data and update_data["linh_vuc_ids"] is not None:
            update_data["linh_vuc_ids"] = [str(uid) for uid in update_data["linh_vuc_ids"]]

        for key, value in update_data.items():
            setattr(vt, key, value)
        vt.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(vt)
        return vt

    async def xoa(self, vi_tri_id: UUID) -> None:
        """Soft delete vi tri viec lam."""
        vt = await self.chi_tiet(vi_tri_id)
        vt.is_active = False
        vt.updated_at = datetime.utcnow()
        await self.db.commit()
