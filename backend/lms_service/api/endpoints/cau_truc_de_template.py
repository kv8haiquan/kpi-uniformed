"""
lms_service/api/endpoints/cau_truc_de_template.py
=================================================
API endpoints mau cau truc de thi DGNL — chi admin (QT_DAO_TAO/SUPER_ADMIN).

6 endpoints:
  GET    /cau-truc-de-template              Danh sach mau
  POST   /cau-truc-de-template              Luu mau moi
  GET    /cau-truc-de-template/{id}         Chi tiet mau
  PUT    /cau-truc-de-template/{id}         Sua mau truc tiep
  POST   /cau-truc-de-template/{id}/nhan-ban  Nhan ban mau
  DELETE /cau-truc-de-template/{id}         Xoa mem mau

Ap dung mau vao ky thi: POST /ky-thi/{id}/cau-truc-de/ap-dung-mau (nguyen tu).
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from lms_service.dependencies import get_db, require_platform_role
from lms_service.schemas.cau_truc_de_template import (
    CauTrucDeTemplateCreate,
    CauTrucDeTemplateNhanBan,
    CauTrucDeTemplateResponse,
    CauTrucDeTemplateUpdate,
)
from lms_service.services.cau_truc_de_template_service import CauTrucDeTemplateService
from shared.auth import TokenPayload

router = APIRouter(prefix="/cau-truc-de-template", tags=["ĐGNL - Mẫu cấu trúc đề"])


@router.get("")
async def danh_sach_template(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(require_platform_role("QT_DAO_TAO")),
):
    """Danh sach mau cau truc de."""
    service = CauTrucDeTemplateService(db)
    result = await service.danh_sach(page, page_size)
    return {
        "success": True,
        "data": [CauTrucDeTemplateResponse(**item).model_dump(mode="json") for item in result["items"]],
        "pagination": result["pagination"],
    }


@router.post("", status_code=201)
async def tao_template(
    data: CauTrucDeTemplateCreate,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(require_platform_role("QT_DAO_TAO")),
):
    """Luu mau cau truc de moi."""
    service = CauTrucDeTemplateService(db)
    tpl = await service.tao_moi(data, user)
    return {
        "success": True,
        "data": CauTrucDeTemplateResponse.model_validate(tpl).model_dump(mode="json"),
        "message": "Lưu mẫu cấu trúc đề thành công",
    }


@router.get("/{template_id}")
async def chi_tiet_template(
    template_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(require_platform_role("QT_DAO_TAO")),
):
    """Chi tiet 1 mau cau truc de."""
    service = CauTrucDeTemplateService(db)
    tpl = await service.chi_tiet(template_id)
    return {
        "success": True,
        "data": CauTrucDeTemplateResponse.model_validate(tpl).model_dump(mode="json"),
    }


@router.put("/{template_id}")
async def sua_template(
    template_id: UUID,
    data: CauTrucDeTemplateUpdate,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(require_platform_role("QT_DAO_TAO")),
):
    """Sua mau cau truc de truc tiep (ten/mo ta/cau truc)."""
    service = CauTrucDeTemplateService(db)
    tpl = await service.cap_nhat(template_id, data)
    return {
        "success": True,
        "data": CauTrucDeTemplateResponse.model_validate(tpl).model_dump(mode="json"),
        "message": "Cập nhật mẫu cấu trúc đề thành công",
    }


@router.post("/{template_id}/nhan-ban", status_code=201)
async def nhan_ban_template(
    template_id: UUID,
    data: CauTrucDeTemplateNhanBan,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(require_platform_role("QT_DAO_TAO")),
):
    """Nhan ban mau cau truc de thanh mau moi."""
    service = CauTrucDeTemplateService(db)
    tpl = await service.nhan_ban(template_id, data, user)
    return {
        "success": True,
        "data": CauTrucDeTemplateResponse.model_validate(tpl).model_dump(mode="json"),
        "message": "Nhân bản mẫu thành công",
    }


@router.delete("/{template_id}")
async def xoa_template(
    template_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(require_platform_role("QT_DAO_TAO")),
):
    """Xoa mem mau cau truc de."""
    service = CauTrucDeTemplateService(db)
    await service.xoa(template_id)
    return {"success": True, "message": "Xóa mẫu thành công"}
