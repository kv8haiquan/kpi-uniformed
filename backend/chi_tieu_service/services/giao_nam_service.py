"""
chi_tieu_service/services/giao_nam_service.py
=============================================
Business logic giao chi tieu nam cho don vi.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from chi_tieu_service.models.giao_nam import GiaoNam
from chi_tieu_service.schemas.giao_nam import GiaoNamCreate, GiaoNamUpdate


def _err(code: str, msg: str, http=status.HTTP_400_BAD_REQUEST):
    return HTTPException(status_code=http, detail={"success": False, "error": {"code": code, "message": msg}})


class GiaoNamService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def danh_sach(
        self, nam: Optional[int] = None, don_vi_id: Optional[UUID] = None,
        page: int = 1, page_size: int = 200,
    ) -> dict:
        conds = [GiaoNam.is_deleted == False]  # noqa: E712
        if nam:
            conds.append(GiaoNam.nam == nam)
        if don_vi_id:
            conds.append(GiaoNam.don_vi_id == don_vi_id)
        total = (await self.db.execute(
            select(func.count()).select_from(GiaoNam).where(*conds)
        )).scalar() or 0
        stmt = select(GiaoNam).where(*conds) \
            .order_by(GiaoNam.created_at.asc()) \
            .offset((page - 1) * page_size).limit(page_size)
        items = (await self.db.execute(stmt)).scalars().all()
        return {
            "items": items,
            "pagination": {
                "page": page, "page_size": page_size, "total_items": total,
                "total_pages": (total + page_size - 1) // page_size if page_size > 0 else 0,
            },
        }

    async def chi_tiet(self, gn_id: UUID) -> GiaoNam:
        gn = (await self.db.execute(
            select(GiaoNam).where(GiaoNam.id == gn_id, GiaoNam.is_deleted == False)  # noqa: E712
        )).scalar_one_or_none()
        if not gn:
            raise _err("CT_ERR_404", "Ban ghi giao nam khong ton tai", status.HTTP_404_NOT_FOUND)
        return gn

    async def tao_moi(self, data: GiaoNamCreate, nguoi_giao_id: UUID) -> GiaoNam:
        # UNIQUE (don_vi, chi_tieu, nam, loai_muc)
        dup = (await self.db.execute(
            select(GiaoNam).where(
                GiaoNam.don_vi_id == data.don_vi_id,
                GiaoNam.chi_tieu_id == data.chi_tieu_id,
                GiaoNam.nam == data.nam,
                GiaoNam.loai_muc == data.loai_muc,
                GiaoNam.is_deleted == False,  # noqa: E712
            )
        )).scalar_one_or_none()
        if dup:
            raise _err("CT_ERR_DUP", "Da ton tai ban ghi giao nam cho (don vi, chi tieu, nam, muc) nay")
        gn = GiaoNam(**data.model_dump(), nguoi_giao_id=nguoi_giao_id)
        self.db.add(gn)
        await self.db.commit()
        await self.db.refresh(gn)
        return gn

    async def cap_nhat(self, gn_id: UUID, data: GiaoNamUpdate) -> GiaoNam:
        gn = await self.chi_tiet(gn_id)
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(gn, k, v)
        gn.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(gn)
        return gn

    async def xoa(self, gn_id: UUID) -> None:
        gn = await self.chi_tiet(gn_id)
        gn.is_deleted = True
        gn.updated_at = datetime.utcnow()
        await self.db.commit()
