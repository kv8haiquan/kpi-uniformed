"""
chi_tieu_service/services/danh_muc_service.py
=============================================
Business logic CRUD danh muc chi tieu.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from chi_tieu_service.models.danh_muc_chi_tieu import DanhMucChiTieu
from chi_tieu_service.schemas.danh_muc import DanhMucChiTieuCreate, DanhMucChiTieuUpdate


def _err(code: str, msg: str, http=status.HTTP_400_BAD_REQUEST):
    return HTTPException(status_code=http, detail={"success": False, "error": {"code": code, "message": msg}})


class DanhMucService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def danh_sach(
        self, linh_vuc_id: Optional[UUID] = None, is_active: bool = True,
        page: int = 1, page_size: int = 100,
    ) -> dict:
        conds = [DanhMucChiTieu.is_active == is_active]
        if linh_vuc_id:
            conds.append(DanhMucChiTieu.linh_vuc_id == linh_vuc_id)
        total = (await self.db.execute(
            select(func.count()).select_from(DanhMucChiTieu).where(*conds)
        )).scalar() or 0
        stmt = select(DanhMucChiTieu).where(*conds) \
            .order_by(DanhMucChiTieu.thu_tu.asc(), DanhMucChiTieu.created_at.asc()) \
            .offset((page - 1) * page_size).limit(page_size)
        items = (await self.db.execute(stmt)).scalars().all()
        return {
            "items": items,
            "pagination": {
                "page": page, "page_size": page_size, "total_items": total,
                "total_pages": (total + page_size - 1) // page_size if page_size > 0 else 0,
            },
        }

    async def chi_tiet(self, ct_id: UUID) -> DanhMucChiTieu:
        ct = (await self.db.execute(
            select(DanhMucChiTieu).where(DanhMucChiTieu.id == ct_id)
        )).scalar_one_or_none()
        if not ct:
            raise _err("CT_ERR_404", "Chi tieu khong ton tai", status.HTTP_404_NOT_FOUND)
        return ct

    async def tao_moi(self, data: DanhMucChiTieuCreate) -> DanhMucChiTieu:
        dup = (await self.db.execute(
            select(DanhMucChiTieu).where(DanhMucChiTieu.ma_chi_tieu == data.ma_chi_tieu)
        )).scalar_one_or_none()
        if dup:
            raise _err("CT_ERR_DUP", f"Ma chi tieu '{data.ma_chi_tieu}' da ton tai")
        ct = DanhMucChiTieu(**data.model_dump())
        self.db.add(ct)
        await self.db.commit()
        await self.db.refresh(ct)
        return ct

    async def cap_nhat(self, ct_id: UUID, data: DanhMucChiTieuUpdate) -> DanhMucChiTieu:
        ct = await self.chi_tiet(ct_id)
        upd = data.model_dump(exclude_unset=True)
        if "ma_chi_tieu" in upd:
            dup = (await self.db.execute(
                select(DanhMucChiTieu).where(
                    DanhMucChiTieu.ma_chi_tieu == upd["ma_chi_tieu"], DanhMucChiTieu.id != ct_id
                )
            )).scalar_one_or_none()
            if dup:
                raise _err("CT_ERR_DUP", f"Ma chi tieu '{upd['ma_chi_tieu']}' da ton tai")
        for k, v in upd.items():
            setattr(ct, k, v)
        ct.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(ct)
        return ct

    async def xoa(self, ct_id: UUID) -> None:
        ct = await self.chi_tiet(ct_id)
        ct.is_active = False
        ct.updated_at = datetime.utcnow()
        await self.db.commit()
