"""
chi_tieu_service/api/endpoints/danh_muc.py
==========================================
CRUD danh mục chỉ tiêu. Đọc: mọi vai trò. Ghi: QT_CHI_TIEU.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from chi_tieu_service.dependencies import get_db, get_current_user, require_platform_role
from chi_tieu_service.schemas.danh_muc import (
    DanhMucChiTieuCreate, DanhMucChiTieuUpdate, DanhMucChiTieuResponse,
)
from chi_tieu_service.services.danh_muc_service import DanhMucService
from shared.auth import TokenPayload

router = APIRouter(prefix="/danh-muc", tags=["Chỉ tiêu - Danh mục"])


@router.get("")
async def danh_sach(
    linh_vuc_id: Optional[UUID] = Query(None),
    is_active: bool = Query(True),
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    result = await DanhMucService(db).danh_sach(
        linh_vuc_id=linh_vuc_id, is_active=is_active, page=page, page_size=page_size
    )
    return {
        "success": True,
        "data": [DanhMucChiTieuResponse.model_validate(i).model_dump(mode="json") for i in result["items"]],
        "pagination": result["pagination"],
    }


@router.post("", status_code=201)
async def tao(
    data: DanhMucChiTieuCreate,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(require_platform_role("QT_CHI_TIEU")),
):
    ct = await DanhMucService(db).tao_moi(data)
    return {"success": True, "data": DanhMucChiTieuResponse.model_validate(ct).model_dump(mode="json"),
            "message": "Tạo chỉ tiêu thành công"}


@router.put("/{ct_id}")
async def cap_nhat(
    ct_id: UUID,
    data: DanhMucChiTieuUpdate,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(require_platform_role("QT_CHI_TIEU")),
):
    ct = await DanhMucService(db).cap_nhat(ct_id, data)
    return {"success": True, "data": DanhMucChiTieuResponse.model_validate(ct).model_dump(mode="json"),
            "message": "Cập nhật chỉ tiêu thành công"}


@router.delete("/{ct_id}")
async def xoa(
    ct_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(require_platform_role("QT_CHI_TIEU")),
):
    await DanhMucService(db).xoa(ct_id)
    return {"success": True, "message": "Xóa chỉ tiêu thành công"}
