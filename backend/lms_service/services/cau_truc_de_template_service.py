"""
lms_service/services/cau_truc_de_template_service.py
====================================================
Business logic CRUD mau cau truc de thi DGNL.

Ap dung template vao ky thi: FE lay `cau_truc` tu template roi goi endpoint
upsert san co POST /ky-thi/{id}/cau-truc-de (validate vi_tri/linh_vuc o do).
"""

import uuid

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from lms_service.core.timezone import now_vn
from lms_service.models.base import CongChucRef
from lms_service.models.cau_truc_de_template import CauTrucDeTemplate
from lms_service.schemas.cau_truc_de_template import CauTrucDeTemplateCreate
from shared.auth import TokenPayload


class CauTrucDeTemplateService:
    """Service mau cau truc de."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def danh_sach(self, page: int = 1, page_size: int = 50) -> dict:
        """Danh sach template dang hoat dong (kem ten nguoi tao)."""
        base_where = [CauTrucDeTemplate.is_active == True]  # noqa: E712

        count_r = await self.db.execute(
            select(func.count(CauTrucDeTemplate.id)).where(*base_where)
        )
        total = count_r.scalar() or 0

        cc = CongChucRef.__table__.alias("cc")
        stmt = (
            select(CauTrucDeTemplate, cc.c.ho_ten.label("nguoi_tao_ho_ten"))
            .outerjoin(cc, CauTrucDeTemplate.nguoi_tao_id == cc.c.id)
            .where(*base_where)
            .order_by(CauTrucDeTemplate.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await self.db.execute(stmt)

        items = []
        for tpl, nguoi_tao_ho_ten in result.all():
            items.append({
                "id": tpl.id,
                "ten_template": tpl.ten_template,
                "mo_ta": tpl.mo_ta,
                "nguoi_tao_id": tpl.nguoi_tao_id,
                "nguoi_tao_ho_ten": nguoi_tao_ho_ten,
                "cau_truc": tpl.cau_truc or [],
                "created_at": tpl.created_at,
                "updated_at": tpl.updated_at,
            })

        return {
            "items": items,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_items": total,
                "total_pages": (total + page_size - 1) // page_size if page_size else 0,
            },
        }

    async def tao_moi(self, data: CauTrucDeTemplateCreate, user: TokenPayload) -> CauTrucDeTemplate:
        """Tao template moi tu cau truc de dang soan."""
        tpl = CauTrucDeTemplate(
            ten_template=data.ten_template,
            mo_ta=data.mo_ta,
            nguoi_tao_id=uuid.UUID(user.sub),
            cau_truc=[item.model_dump(mode="json") for item in data.cau_truc],
        )
        self.db.add(tpl)
        await self.db.commit()
        await self.db.refresh(tpl)
        return tpl

    async def chi_tiet(self, template_id: uuid.UUID) -> CauTrucDeTemplate:
        """Chi tiet 1 template."""
        r = await self.db.execute(
            select(CauTrucDeTemplate).where(
                CauTrucDeTemplate.id == template_id,
                CauTrucDeTemplate.is_active == True,  # noqa: E712
            )
        )
        tpl = r.scalar_one_or_none()
        if not tpl:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"success": False, "error": {"code": "DGNL_070", "message": "Mẫu cấu trúc đề không tồn tại"}},
            )
        return tpl

    async def xoa(self, template_id: uuid.UUID) -> None:
        """Xoa mem template."""
        tpl = await self.chi_tiet(template_id)
        tpl.is_active = False
        tpl.updated_at = now_vn()
        await self.db.commit()
