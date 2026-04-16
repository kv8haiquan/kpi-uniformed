"""
lms_service/api/endpoints/vi_tri_viec_lam.py
=============================================
API endpoints CRUD vi tri viec lam.
4 endpoints: GET list, POST create, PUT update, DELETE soft-delete.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from lms_service.dependencies import get_db, get_current_user, require_platform_role
from lms_service.schemas.vi_tri_viec_lam import ViTriViecLamCreate, ViTriViecLamUpdate, ViTriViecLamResponse
from lms_service.services.vi_tri_viec_lam_service import ViTriViecLamService
from shared.auth import TokenPayload

router = APIRouter(prefix="/vi-tri-viec-lam", tags=["ĐGNL - Vị trí việc làm"])


@router.get("")
async def danh_sach_vi_tri(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    """Danh sach vi tri viec lam — tat ca CBCC deu xem duoc."""
    service = ViTriViecLamService(db)
    result = await service.danh_sach(page=page, page_size=page_size)
    return {
        "success": True,
        "data": [ViTriViecLamResponse.model_validate(item).model_dump(mode="json") for item in result["items"]],
        "pagination": result["pagination"],
    }


@router.post("", status_code=201)
async def tao_vi_tri(
    data: ViTriViecLamCreate,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(require_platform_role("QT_DAO_TAO")),
):
    """Tao vi tri viec lam moi — chi QT_DAO_TAO."""
    service = ViTriViecLamService(db)
    vt = await service.tao_moi(data)
    return {
        "success": True,
        "data": ViTriViecLamResponse.model_validate(vt).model_dump(mode="json"),
        "message": "Tạo vị trí việc làm thành công",
    }


@router.put("/{vi_tri_id}")
async def cap_nhat_vi_tri(
    vi_tri_id: UUID,
    data: ViTriViecLamUpdate,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(require_platform_role("QT_DAO_TAO")),
):
    """Cap nhat vi tri viec lam — chi QT_DAO_TAO."""
    service = ViTriViecLamService(db)
    vt = await service.cap_nhat(vi_tri_id, data)
    return {
        "success": True,
        "data": ViTriViecLamResponse.model_validate(vt).model_dump(mode="json"),
        "message": "Cập nhật vị trí việc làm thành công",
    }


@router.delete("/{vi_tri_id}")
async def xoa_vi_tri(
    vi_tri_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(require_platform_role("QT_DAO_TAO")),
):
    """Soft delete vi tri viec lam — chi QT_DAO_TAO."""
    service = ViTriViecLamService(db)
    await service.xoa(vi_tri_id)
    return {
        "success": True,
        "message": "Xóa vị trí việc làm thành công",
    }
