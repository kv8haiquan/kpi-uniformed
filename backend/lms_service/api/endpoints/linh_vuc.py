"""
lms_service/api/endpoints/linh_vuc.py
=====================================
API endpoints CRUD linh vuc nghiep vu.
4 endpoints: GET list, POST create, PUT update, DELETE soft-delete.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from lms_service.dependencies import get_db, get_current_user, require_platform_role
from lms_service.schemas.linh_vuc import LinhVucCreate, LinhVucUpdate, LinhVucResponse
from lms_service.services.linh_vuc_service import LinhVucService
from shared.auth import TokenPayload

router = APIRouter(prefix="/linh-vuc", tags=["ĐGNL - Lĩnh vực"])


@router.get("")
async def danh_sach_linh_vuc(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    """Danh sach linh vuc nghiep vu — tat ca CBCC deu xem duoc."""
    service = LinhVucService(db)
    result = await service.danh_sach(page=page, page_size=page_size)
    return {
        "success": True,
        "data": [LinhVucResponse.model_validate(item).model_dump(mode="json") for item in result["items"]],
        "pagination": result["pagination"],
    }


@router.post("", status_code=201)
async def tao_linh_vuc(
    data: LinhVucCreate,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(require_platform_role("QT_DAO_TAO")),
):
    """Tao linh vuc moi — chi QT_DAO_TAO."""
    service = LinhVucService(db)
    lv = await service.tao_moi(data)
    return {
        "success": True,
        "data": LinhVucResponse.model_validate(lv).model_dump(mode="json"),
        "message": "Tạo lĩnh vực thành công",
    }


@router.put("/{linh_vuc_id}")
async def cap_nhat_linh_vuc(
    linh_vuc_id: UUID,
    data: LinhVucUpdate,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(require_platform_role("QT_DAO_TAO")),
):
    """Cap nhat linh vuc — chi QT_DAO_TAO."""
    service = LinhVucService(db)
    lv = await service.cap_nhat(linh_vuc_id, data)
    return {
        "success": True,
        "data": LinhVucResponse.model_validate(lv).model_dump(mode="json"),
        "message": "Cập nhật lĩnh vực thành công",
    }


@router.delete("/{linh_vuc_id}")
async def xoa_linh_vuc(
    linh_vuc_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(require_platform_role("QT_DAO_TAO")),
):
    """Soft delete linh vuc — chi QT_DAO_TAO."""
    service = LinhVucService(db)
    await service.xoa(linh_vuc_id)
    return {
        "success": True,
        "message": "Xóa lĩnh vực thành công",
    }
