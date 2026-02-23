"""
lms_service/api/endpoints/chuyen_de.py
======================================
API endpoints cho CRUD chuyen de dao tao.

Endpoints:
  GET    /chuyen-de          Danh sach chuyen de
  GET    /chuyen-de/{id}     Chi tiet chuyen de
  POST   /chuyen-de          Tao chuyen de moi
  PUT    /chuyen-de/{id}     Cap nhat chuyen de
  DELETE /chuyen-de/{id}     Xoa chuyen de (soft delete)
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from lms_service.dependencies import get_db, get_current_user, require_platform_role
from lms_service.schemas.chuyen_de import (
    ChuyenDeCreate,
    ChuyenDeResponse,
    ChuyenDeUpdate,
)
from lms_service.services.chuyen_de_service import ChuyenDeService
from shared.auth import TokenPayload

router = APIRouter(prefix="/chuyen-de", tags=["Chuyên đề"])


@router.get("")
async def danh_sach_chuyen_de(
    is_active: Optional[bool] = Query(None, description="Lọc theo trạng thái active"),
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    """Lấy danh sách chuyên đề. Tất cả CBCC đã đăng nhập đều xem được."""
    service = ChuyenDeService(db)
    items = await service.danh_sach(is_active=is_active)

    return {
        "success": True,
        "data": [ChuyenDeResponse(**item).model_dump(mode="json") for item in items],
        "message": "Lấy danh sách chuyên đề thành công",
    }


@router.get("/{id}")
async def chi_tiet_chuyen_de(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    """Chi tiết chuyên đề theo ID."""
    service = ChuyenDeService(db)
    chuyen_de = await service.chi_tiet(id)

    response = ChuyenDeResponse.model_validate(chuyen_de)
    return {
        "success": True,
        "data": response.model_dump(mode="json"),
    }


@router.post("", status_code=201)
async def tao_chuyen_de(
    data: ChuyenDeCreate,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(require_platform_role("QT_DAO_TAO")),
):
    """Tạo chuyên đề mới. Yêu cầu: QT_DAO_TAO hoặc SUPER_ADMIN."""
    service = ChuyenDeService(db)
    chuyen_de = await service.tao_moi(data, user_id=UUID(user.sub))

    response = ChuyenDeResponse.model_validate(chuyen_de)
    return {
        "success": True,
        "data": response.model_dump(mode="json"),
        "message": "Tạo chuyên đề thành công",
    }


@router.put("/{id}")
async def cap_nhat_chuyen_de(
    id: UUID,
    data: ChuyenDeUpdate,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(require_platform_role("QT_DAO_TAO")),
):
    """Cập nhật chuyên đề. Yêu cầu: QT_DAO_TAO hoặc SUPER_ADMIN."""
    service = ChuyenDeService(db)
    chuyen_de = await service.cap_nhat(id, data)

    response = ChuyenDeResponse.model_validate(chuyen_de)
    return {
        "success": True,
        "data": response.model_dump(mode="json"),
        "message": "Cập nhật chuyên đề thành công",
    }


@router.delete("/{id}")
async def xoa_chuyen_de(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(require_platform_role("QT_DAO_TAO")),
):
    """Xóa chuyên đề (soft delete). Yêu cầu: QT_DAO_TAO hoặc SUPER_ADMIN."""
    service = ChuyenDeService(db)
    await service.xoa(id)

    return {
        "success": True,
        "data": None,
        "message": "Xóa chuyên đề thành công",
    }
