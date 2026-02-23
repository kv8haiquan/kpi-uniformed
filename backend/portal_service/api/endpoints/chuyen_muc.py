"""
portal_service/api/endpoints/chuyen_muc.py
===========================================
API endpoints cho Chuyên mục bài viết.

Routes:
  GET    /chuyen-muc         — Danh sách (tất cả CBCC đã xác thực)
  POST   /chuyen-muc         — Tạo (BIEN_TAP, QT_NOI_DUNG, ADMIN)
  PUT    /chuyen-muc/{id}    — Sửa (BIEN_TAP, QT_NOI_DUNG, ADMIN)
  DELETE /chuyen-muc/{id}    — Xóa (QT_NOI_DUNG, ADMIN)
"""

import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status

from portal_service.dependencies import (
    CurrentUserDep,
    DatabaseDep,
    require_platform_role,
)
from portal_service.schemas.base import SuccessResponse
from portal_service.schemas.chuyen_muc import (
    ChuyenMucCreate,
    ChuyenMucResponse,
    ChuyenMucUpdate,
)
from portal_service.services import chuyen_muc_service

router = APIRouter(prefix="/chuyen-muc", tags=["Chuyên mục"])


@router.get(
    "",
    response_model=SuccessResponse[List[ChuyenMucResponse]],
    summary="Danh sách chuyên mục",
)
async def get_danh_sach(
    db: DatabaseDep,
    _user: CurrentUserDep,
    chi_active: bool = Query(True, description="Chỉ trả về chuyên mục đang hoạt động"),
):
    """Lấy danh sách chuyên mục, sắp theo thứ tự tăng dần."""
    items = await chuyen_muc_service.danh_sach(db, chi_active=chi_active)
    data = [ChuyenMucResponse.model_validate(cm) for cm in items]
    return SuccessResponse(data=data, message=f"Có {len(data)} chuyên mục")


@router.post(
    "",
    response_model=SuccessResponse[ChuyenMucResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Tạo chuyên mục",
)
async def tao_chuyen_muc(
    payload: ChuyenMucCreate,
    db: DatabaseDep,
    user=Depends(require_platform_role("BIEN_TAP", "QT_NOI_DUNG")),
):
    """Tạo chuyên mục mới. Tự sinh slug từ tên nếu không cung cấp."""
    cm = await chuyen_muc_service.tao(db, payload)
    return SuccessResponse(
        data=ChuyenMucResponse.model_validate(cm),
        message="Tạo chuyên mục thành công",
    )


@router.put(
    "/{chuyen_muc_id}",
    response_model=SuccessResponse[ChuyenMucResponse],
    summary="Sửa chuyên mục",
)
async def sua_chuyen_muc(
    chuyen_muc_id: uuid.UUID,
    payload: ChuyenMucUpdate,
    db: DatabaseDep,
    user=Depends(require_platform_role("BIEN_TAP", "QT_NOI_DUNG")),
):
    """Cập nhật thông tin chuyên mục."""
    cm = await chuyen_muc_service.sua(db, chuyen_muc_id, payload)
    return SuccessResponse(
        data=ChuyenMucResponse.model_validate(cm),
        message="Cập nhật chuyên mục thành công",
    )


@router.delete(
    "/{chuyen_muc_id}",
    response_model=SuccessResponse[dict],
    summary="Xóa chuyên mục",
)
async def xoa_chuyen_muc(
    chuyen_muc_id: uuid.UUID,
    db: DatabaseDep,
    user=Depends(require_platform_role("QT_NOI_DUNG")),
):
    """Xóa chuyên mục.

    - Nếu còn bài viết: ẩn (is_active=False)
    - Nếu không có bài viết: xóa hẳn
    """
    result = await chuyen_muc_service.xoa(db, chuyen_muc_id)
    return SuccessResponse(data=result, message=result["message"])
