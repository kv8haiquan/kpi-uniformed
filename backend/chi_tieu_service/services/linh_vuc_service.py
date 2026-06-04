"""
chi_tieu_service/services/linh_vuc_service.py
=============================================
Business logic CRUD linh vuc cong tac.
"""

from datetime import datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from chi_tieu_service.models.linh_vuc import LinhVuc
from chi_tieu_service.schemas.linh_vuc import LinhVucCreate, LinhVucUpdate


def _err(code: str, msg: str, http=status.HTTP_400_BAD_REQUEST):
    return HTTPException(status_code=http, detail={"success": False, "error": {"code": code, "message": msg}})


class LinhVucService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def danh_sach(self, page: int = 1, page_size: int = 100) -> dict:
        base = select(LinhVuc).where(LinhVuc.is_active == True)  # noqa: E712
        total = (await self.db.execute(
            select(func.count()).select_from(LinhVuc).where(LinhVuc.is_active == True)  # noqa: E712
        )).scalar() or 0
        stmt = base.order_by(LinhVuc.thu_tu.asc(), LinhVuc.created_at.asc()) \
            .offset((page - 1) * page_size).limit(page_size)
        items = (await self.db.execute(stmt)).scalars().all()
        return {
            "items": items,
            "pagination": {
                "page": page, "page_size": page_size, "total_items": total,
                "total_pages": (total + page_size - 1) // page_size if page_size > 0 else 0,
            },
        }

    async def chi_tiet(self, linh_vuc_id: UUID) -> LinhVuc:
        lv = (await self.db.execute(
            select(LinhVuc).where(LinhVuc.id == linh_vuc_id, LinhVuc.is_active == True)  # noqa: E712
        )).scalar_one_or_none()
        if not lv:
            raise _err("CT_ERR_404", "Linh vuc khong ton tai", status.HTTP_404_NOT_FOUND)
        return lv

    async def tao_moi(self, data: LinhVucCreate) -> LinhVuc:
        dup = (await self.db.execute(
            select(LinhVuc).where(LinhVuc.ma_linh_vuc == data.ma_linh_vuc)
        )).scalar_one_or_none()
        if dup:
            raise _err("CT_ERR_DUP", f"Ma linh vuc '{data.ma_linh_vuc}' da ton tai")
        lv = LinhVuc(**data.model_dump())
        self.db.add(lv)
        await self.db.commit()
        await self.db.refresh(lv)
        return lv

    async def cap_nhat(self, linh_vuc_id: UUID, data: LinhVucUpdate) -> LinhVuc:
        lv = await self.chi_tiet(linh_vuc_id)
        upd = data.model_dump(exclude_unset=True)
        if "ma_linh_vuc" in upd:
            dup = (await self.db.execute(
                select(LinhVuc).where(LinhVuc.ma_linh_vuc == upd["ma_linh_vuc"], LinhVuc.id != linh_vuc_id)
            )).scalar_one_or_none()
            if dup:
                raise _err("CT_ERR_DUP", f"Ma linh vuc '{upd['ma_linh_vuc']}' da ton tai")
        for k, v in upd.items():
            setattr(lv, k, v)
        lv.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(lv)
        return lv

    async def xoa(self, linh_vuc_id: UUID) -> None:
        lv = await self.chi_tiet(linh_vuc_id)
        lv.is_active = False
        lv.updated_at = datetime.utcnow()
        await self.db.commit()
