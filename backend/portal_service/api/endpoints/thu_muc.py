"""
portal_service/api/endpoints/thu_muc.py
=========================================
API endpoints cho Thư mục tài liệu ECM.

Routes:
  GET    /thu-muc          — Danh sách (query: parent_id)
  GET    /thu-muc/tree     — Cây thư mục đầy đủ (nested)
  POST   /thu-muc          — Tạo (Auth: QT_NOI_DUNG, ADMIN)
  PUT    /thu-muc/{id}     — Sửa (Auth: QT_NOI_DUNG, ADMIN)
  DELETE /thu-muc/{id}     — Xóa (chỉ thư mục rỗng)
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
from portal_service.schemas.thu_muc import (
    ThuMucCreate,
    ThuMucResponse,
    ThuMucTreeResponse,
    ThuMucUpdate,
)
from portal_service.services import thu_muc_service

router = APIRouter(prefix="/thu-muc", tags=["Thư mục"])


@router.get(
    "",
    response_model=SuccessResponse[List[ThuMucResponse]],
    summary="Danh sách thư mục",
)
async def get_danh_sach(
    db: DatabaseDep,
    user: CurrentUserDep,
    parent_id: Optional[uuid.UUID] = Query(
        None,
        description="UUID thư mục cha (None = thư mục gốc)",
    ),
):
    """Lấy danh sách thư mục theo parent_id, lọc theo quyền truy cập của user."""
    folders = await thu_muc_service.danh_sach(db, user, parent_id=parent_id)

    data = []
    for tm in folders:
        so_con, so_tl = await thu_muc_service.enrichment_counts(db, tm.id)
        r = ThuMucResponse.model_validate(tm)
        r.so_thu_muc_con = so_con
        r.so_tai_lieu = so_tl
        data.append(r)

    return SuccessResponse(data=data, message=f"Có {len(data)} thư mục")


@router.get(
    "/tree",
    response_model=SuccessResponse[List[ThuMucTreeResponse]],
    summary="Cây thư mục đầy đủ",
)
async def get_tree(
    db: DatabaseDep,
    user: CurrentUserDep,
):
    """Lấy toàn bộ cây thư mục dưới dạng nested structure.

    Kết quả đã lọc theo quyền truy cập của user.
    """
    tree = await thu_muc_service.lay_cay_thu_muc(db, user)
    return SuccessResponse(
        data=tree,
        message=f"Cây thư mục ({len(tree)} node gốc)",
    )


@router.post(
    "",
    response_model=SuccessResponse[ThuMucResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Tạo thư mục",
)
async def tao_thu_muc(
    payload: ThuMucCreate,
    db: DatabaseDep,
    user=Depends(require_platform_role("QT_NOI_DUNG")),
):
    """Tạo thư mục mới.

    - parent_id = None → thư mục gốc
    - parent_id = uuid → thư mục con (kiểm tra parent tồn tại)
    """
    tm = await thu_muc_service.tao(db, payload, user)
    so_con, so_tl = await thu_muc_service.enrichment_counts(db, tm.id)
    r = ThuMucResponse.model_validate(tm)
    r.so_thu_muc_con = so_con
    r.so_tai_lieu = so_tl
    return SuccessResponse(data=r, message="Tạo thư mục thành công")


@router.put(
    "/{thu_muc_id}",
    response_model=SuccessResponse[ThuMucResponse],
    summary="Sửa thư mục",
)
async def sua_thu_muc(
    thu_muc_id: uuid.UUID,
    payload: ThuMucUpdate,
    db: DatabaseDep,
    user=Depends(require_platform_role("QT_NOI_DUNG")),
):
    """Cập nhật thông tin thư mục.

    Không cho đặt parent_id thành chính mình hoặc thư mục con (tránh vòng lặp).
    """
    tm = await thu_muc_service.sua(db, thu_muc_id, payload, user)
    so_con, so_tl = await thu_muc_service.enrichment_counts(db, tm.id)
    r = ThuMucResponse.model_validate(tm)
    r.so_thu_muc_con = so_con
    r.so_tai_lieu = so_tl
    return SuccessResponse(data=r, message="Cập nhật thư mục thành công")


@router.delete(
    "/{thu_muc_id}",
    response_model=SuccessResponse[dict],
    summary="Xóa thư mục",
)
async def xoa_thu_muc(
    thu_muc_id: uuid.UUID,
    db: DatabaseDep,
    user=Depends(require_platform_role("QT_NOI_DUNG")),
):
    """Xóa thư mục.

    Điều kiện: thư mục phải RỖNG (không có thư mục con, không có tài liệu).
    Nếu còn nội dung → 400 PORTAL_ERR_004.
    """
    result = await thu_muc_service.xoa(db, thu_muc_id, user)
    return SuccessResponse(data=result, message=result["message"])
