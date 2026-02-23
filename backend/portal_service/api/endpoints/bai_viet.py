"""
portal_service/api/endpoints/bai_viet.py
=========================================
API endpoints cho Bài viết portal (CMS tin tức nội bộ).

Routes:
  GET    /bai-viet                     — Danh sách công khai (XUAT_BAN, tất cả CBCC)
  GET    /bai-viet/quan-ly             — Danh sách quản lý (BIEN_TAP+)
  POST   /bai-viet                     — Tạo bài viết (BIEN_TAP, QT_NOI_DUNG, ADMIN)
  GET    /bai-viet/{id}                — Chi tiết + tăng lượt xem
  PUT    /bai-viet/{id}                — Sửa (chỉ khi NHAP)
  DELETE /bai-viet/{id}                — Xóa mềm (chỉ khi NHAP)
  PATCH  /bai-viet/{id}/trang-thai     — Đổi trạng thái workflow
  PATCH  /bai-viet/{id}/ghim           — Ghim/bỏ ghim (QT_NOI_DUNG, ADMIN)
"""

import math
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query, status

from portal_service.dependencies import (
    CurrentUserDep,
    DatabaseDep,
    require_platform_role,
)
from portal_service.schemas.base import PaginatedResponse, PaginationInfo, SuccessResponse
from portal_service.schemas.bai_viet import (
    BaiVietCreate,
    BaiVietListResponse,
    BaiVietResponse,
    BaiVietUpdate,
    DoiTrangThaiRequest,
    GhimRequest,
)
from portal_service.services import bai_viet_service

router = APIRouter(prefix="/bai-viet", tags=["Bài viết"])


# ---------------------------------------------------------------------------
# Danh sách công khai — bài XUAT_BAN, tất cả CBCC đã xác thực
# ---------------------------------------------------------------------------


@router.get(
    "",
    response_model=PaginatedResponse[BaiVietListResponse],
    summary="Danh sách bài viết công khai",
)
async def get_danh_sach_cong_khai(
    db: DatabaseDep,
    _user: CurrentUserDep,
    chuyen_muc_id: Optional[uuid.UUID] = Query(None, description="Lọc theo chuyên mục"),
    search: Optional[str] = Query(None, description="Tìm kiếm theo tiêu đề / tóm tắt"),
    page: int = Query(1, ge=1, description="Trang hiện tại"),
    page_size: int = Query(20, ge=1, le=100, description="Số bài mỗi trang"),
):
    """Danh sách bài viết đã xuất bản.

    - Chỉ trả bài XUAT_BAN
    - Bài ghim (is_ghim=True) luôn đứng đầu
    - Hỗ trợ lọc theo chuyên mục và tìm kiếm ILIKE
    """
    items, total = await bai_viet_service.danh_sach_cong_khai(
        db,
        chuyen_muc_id=chuyen_muc_id,
        search=search,
        page=page,
        page_size=page_size,
    )
    data = [BaiVietListResponse.model_validate(bv) for bv in items]
    total_pages = math.ceil(total / page_size) if page_size else 1
    return PaginatedResponse(
        data=data,
        pagination=PaginationInfo(
            page=page,
            page_size=page_size,
            total_items=total,
            total_pages=total_pages,
        ),
    )


# ---------------------------------------------------------------------------
# Danh sách quản lý — BIEN_TAP+
# ---------------------------------------------------------------------------


@router.get(
    "/quan-ly",
    response_model=PaginatedResponse[BaiVietListResponse],
    summary="Danh sách bài viết quản lý",
)
async def get_danh_sach_quan_ly(
    db: DatabaseDep,
    user=Depends(require_platform_role("BIEN_TAP", "QT_NOI_DUNG")),
    trang_thai: Optional[str] = Query(None, description="Lọc theo trạng thái workflow"),
    chuyen_muc_id: Optional[uuid.UUID] = Query(None, description="Lọc theo chuyên mục"),
    search: Optional[str] = Query(None, description="Tìm kiếm theo tiêu đề / tóm tắt"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """Danh sách bài viết dành cho quản trị.

    Phân quyền xem:
      - BIEN_TAP: chỉ thấy bài mình soạn
      - QT_NOI_DUNG / ADMIN: thấy tất cả bài
    """
    items, total = await bai_viet_service.danh_sach_quan_ly(
        db,
        user=user,
        trang_thai=trang_thai,
        chuyen_muc_id=chuyen_muc_id,
        search=search,
        page=page,
        page_size=page_size,
    )
    data = [BaiVietListResponse.model_validate(bv) for bv in items]
    total_pages = math.ceil(total / page_size) if page_size else 1
    return PaginatedResponse(
        data=data,
        pagination=PaginationInfo(
            page=page,
            page_size=page_size,
            total_items=total,
            total_pages=total_pages,
        ),
    )


# ---------------------------------------------------------------------------
# Tạo bài viết
# ---------------------------------------------------------------------------


@router.post(
    "",
    response_model=SuccessResponse[BaiVietResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Tạo bài viết",
)
async def tao_bai_viet(
    payload: BaiVietCreate,
    db: DatabaseDep,
    user=Depends(require_platform_role("BIEN_TAP", "QT_NOI_DUNG")),
):
    """Tạo bài viết mới ở trạng thái NHAP."""
    bv = await bai_viet_service.tao_bai_viet(db, payload, user)
    return SuccessResponse(
        data=BaiVietResponse.model_validate(bv),
        message="Tạo bài viết thành công",
    )


# ---------------------------------------------------------------------------
# Chi tiết bài viết
# ---------------------------------------------------------------------------


@router.get(
    "/{bai_viet_id}",
    response_model=SuccessResponse[BaiVietResponse],
    summary="Chi tiết bài viết",
)
async def get_chi_tiet(
    bai_viet_id: uuid.UUID,
    db: DatabaseDep,
    _user: CurrentUserDep,
):
    """Lấy chi tiết bài viết. Mỗi lần xem tăng lượt xem lên 1."""
    bv = await bai_viet_service.chi_tiet(db, bai_viet_id)
    return SuccessResponse(
        data=BaiVietResponse.model_validate(bv),
        message="Thao tác thành công",
    )


# ---------------------------------------------------------------------------
# Sửa bài viết
# ---------------------------------------------------------------------------


@router.put(
    "/{bai_viet_id}",
    response_model=SuccessResponse[BaiVietResponse],
    summary="Sửa bài viết",
)
async def sua_bai_viet(
    bai_viet_id: uuid.UUID,
    payload: BaiVietUpdate,
    db: DatabaseDep,
    user=Depends(require_platform_role("BIEN_TAP", "QT_NOI_DUNG")),
):
    """Cập nhật nội dung bài viết (chỉ khi trạng thái NHAP).

    - BIEN_TAP: chỉ sửa bài mình soạn
    - QT_NOI_DUNG / ADMIN: sửa tất cả
    """
    bv = await bai_viet_service.sua_bai_viet(db, bai_viet_id, payload, user)
    return SuccessResponse(
        data=BaiVietResponse.model_validate(bv),
        message="Cập nhật bài viết thành công",
    )


# ---------------------------------------------------------------------------
# Xóa mềm bài viết
# ---------------------------------------------------------------------------


@router.delete(
    "/{bai_viet_id}",
    response_model=SuccessResponse[dict],
    summary="Xóa bài viết",
)
async def xoa_bai_viet(
    bai_viet_id: uuid.UUID,
    db: DatabaseDep,
    user=Depends(require_platform_role("BIEN_TAP", "QT_NOI_DUNG")),
):
    """Xóa mềm bài viết (chỉ khi trạng thái NHAP).

    - BIEN_TAP: chỉ xóa bài mình soạn
    - QT_NOI_DUNG / ADMIN: xóa tất cả
    """
    result = await bai_viet_service.xoa_bai_viet(db, bai_viet_id, user)
    return SuccessResponse(data=result, message=result["message"])


# ---------------------------------------------------------------------------
# Đổi trạng thái workflow
# ---------------------------------------------------------------------------


@router.patch(
    "/{bai_viet_id}/trang-thai",
    response_model=SuccessResponse[BaiVietResponse],
    summary="Đổi trạng thái workflow",
)
async def doi_trang_thai(
    bai_viet_id: uuid.UUID,
    payload: DoiTrangThaiRequest,
    db: DatabaseDep,
    user: CurrentUserDep,
):
    """Đổi trạng thái workflow bài viết.

    Các chuyển đổi hợp lệ:
    ```
    NHAP      → KIEM_TRA   (BIEN_TAP người soạn)
    KIEM_TRA  → DUYET      (QT_NOI_DUNG)
    KIEM_TRA  → NHAP       (QT_NOI_DUNG — từ chối)
    DUYET     → XUAT_BAN   (Lãnh đạo is_lanh_dao=True)
    DUYET     → NHAP       (Lãnh đạo — từ chối)
    XUAT_BAN  → THU_HOI    (QT_NOI_DUNG, ADMIN)
    THU_HOI   → NHAP       (BIEN_TAP người soạn)
    ```
    """
    bv = await bai_viet_service.doi_trang_thai(
        db,
        bai_viet_id,
        trang_thai_moi=payload.trang_thai_moi,
        user=user,
        ly_do=payload.ly_do,
    )
    return SuccessResponse(
        data=BaiVietResponse.model_validate(bv),
        message=f"Chuyển trạng thái sang '{payload.trang_thai_moi}' thành công",
    )


# ---------------------------------------------------------------------------
# Ghim / bỏ ghim bài viết
# ---------------------------------------------------------------------------


@router.patch(
    "/{bai_viet_id}/ghim",
    response_model=SuccessResponse[BaiVietResponse],
    summary="Ghim/bỏ ghim bài viết",
)
async def ghim_bai_viet(
    bai_viet_id: uuid.UUID,
    payload: GhimRequest,
    db: DatabaseDep,
    user=Depends(require_platform_role("QT_NOI_DUNG")),
):
    """Ghim hoặc bỏ ghim bài viết.

    - Tối đa 3 bài ghim cùng lúc
    - Chỉ QT_NOI_DUNG / ADMIN có quyền ghim
    """
    bv = await bai_viet_service.ghim_bai_viet(db, bai_viet_id, payload.is_ghim, user)
    action = "Ghim" if payload.is_ghim else "Bỏ ghim"
    return SuccessResponse(
        data=BaiVietResponse.model_validate(bv),
        message=f"{action} bài viết thành công",
    )
