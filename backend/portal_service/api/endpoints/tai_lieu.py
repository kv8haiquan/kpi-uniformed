"""
portal_service/api/endpoints/tai_lieu.py
==========================================
API endpoints cho Tài liệu ECM.

Routes:
  GET    /tai-lieu                      — Danh sách (chỉ phiên bản mới nhất)
  POST   /tai-lieu                      — Upload tài liệu mới
  GET    /tai-lieu/{id}                 — Chi tiết
  PUT    /tai-lieu/{id}                 — Sửa metadata
  DELETE /tai-lieu/{id}                 — Xóa mềm
  POST   /tai-lieu/{id}/phien-ban-moi   — Upload phiên bản mới
  GET    /tai-lieu/{id}/lich-su         — Lịch sử tất cả phiên bản
  GET    /tai-lieu/{id}/download        — Download (redirect đến file_url)
"""

import math
import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import RedirectResponse

from portal_service.dependencies import (
    CurrentUserDep,
    DatabaseDep,
    require_platform_role,
)
from portal_service.schemas.base import PaginatedResponse, PaginationInfo, SuccessResponse
from portal_service.schemas.tai_lieu import (
    TaiLieuCreate,
    TaiLieuListResponse,
    TaiLieuResponse,
    TaiLieuUpdate,
    TaiLieuVersionResponse,
    UploadPhienBanMoiRequest,
)
from portal_service.services import tai_lieu_service

router = APIRouter(prefix="/tai-lieu", tags=["Tài liệu"])


# ---------------------------------------------------------------------------
# Danh sách
# ---------------------------------------------------------------------------


@router.get(
    "",
    response_model=PaginatedResponse[TaiLieuListResponse],
    summary="Danh sách tài liệu",
)
async def get_danh_sach(
    db: DatabaseDep,
    user: CurrentUserDep,
    thu_muc_id: Optional[uuid.UUID] = Query(None, description="Lọc theo thư mục"),
    file_type: Optional[str] = Query(None, description="Lọc theo MIME type (VD: application/pdf)"),
    tags: Optional[List[str]] = Query(None, description="Lọc theo tags (AND logic)"),
    search: Optional[str] = Query(None, description="Tìm kiếm theo tên tài liệu"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """Danh sách tài liệu — chỉ hiển thị phiên bản MỚI NHẤT.

    Phân quyền: kế thừa từ thư mục cha hoặc quyền riêng của tài liệu.
    """
    items, total = await tai_lieu_service.danh_sach(
        db,
        user=user,
        thu_muc_id=thu_muc_id,
        file_type=file_type,
        tags=tags,
        search=search,
        page=page,
        page_size=page_size,
    )
    data = [TaiLieuListResponse.model_validate(tl) for tl in items]
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
# Upload tài liệu mới
# ---------------------------------------------------------------------------


@router.post(
    "",
    response_model=SuccessResponse[TaiLieuResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Upload tài liệu mới",
)
async def upload_tai_lieu(
    payload: TaiLieuCreate,
    db: DatabaseDep,
    user=Depends(require_platform_role("BIEN_TAP", "QT_NOI_DUNG")),
):
    """Upload tài liệu mới (phiên bản 1).

    Lưu ý: file_url phải là URL đã upload sẵn qua file storage API.
    Validate file_type + file_size theo giới hạn từng loại.
    """
    tl = await tai_lieu_service.upload(db, payload, user)
    return SuccessResponse(
        data=TaiLieuResponse.model_validate(tl),
        message="Upload tài liệu thành công",
    )


# ---------------------------------------------------------------------------
# Chi tiết
# ---------------------------------------------------------------------------


@router.get(
    "/{tai_lieu_id}",
    response_model=SuccessResponse[TaiLieuResponse],
    summary="Chi tiết tài liệu",
)
async def get_chi_tiet(
    tai_lieu_id: uuid.UUID,
    db: DatabaseDep,
    user: CurrentUserDep,
):
    """Chi tiết tài liệu. Kiểm tra quyền truy cập."""
    tl = await tai_lieu_service.chi_tiet(db, tai_lieu_id, user)
    return SuccessResponse(
        data=TaiLieuResponse.model_validate(tl),
        message="Thao tác thành công",
    )


# ---------------------------------------------------------------------------
# Sửa metadata
# ---------------------------------------------------------------------------


@router.put(
    "/{tai_lieu_id}",
    response_model=SuccessResponse[TaiLieuResponse],
    summary="Sửa metadata tài liệu",
)
async def cap_nhat_tai_lieu(
    tai_lieu_id: uuid.UUID,
    payload: TaiLieuUpdate,
    db: DatabaseDep,
    user=Depends(require_platform_role("BIEN_TAP", "QT_NOI_DUNG")),
):
    """Cập nhật tên, mô tả, tags tài liệu.

    KHÔNG cho sửa file_url — upload phiên bản mới thay thế.
    """
    tl = await tai_lieu_service.cap_nhat(db, tai_lieu_id, payload, user)
    return SuccessResponse(
        data=TaiLieuResponse.model_validate(tl),
        message="Cập nhật tài liệu thành công",
    )


# ---------------------------------------------------------------------------
# Xóa mềm
# ---------------------------------------------------------------------------


@router.delete(
    "/{tai_lieu_id}",
    response_model=SuccessResponse[dict],
    summary="Xóa tài liệu",
)
async def xoa_tai_lieu(
    tai_lieu_id: uuid.UUID,
    db: DatabaseDep,
    user=Depends(require_platform_role("QT_NOI_DUNG")),
):
    """Xóa mềm tài liệu (is_deleted = True)."""
    result = await tai_lieu_service.xoa(db, tai_lieu_id, user)
    return SuccessResponse(data=result, message=result["message"])


# ---------------------------------------------------------------------------
# Upload phiên bản mới
# ---------------------------------------------------------------------------


@router.post(
    "/{tai_lieu_id}/phien-ban-moi",
    response_model=SuccessResponse[TaiLieuResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Upload phiên bản mới",
)
async def upload_phien_ban_moi(
    tai_lieu_id: uuid.UUID,
    payload: UploadPhienBanMoiRequest,
    db: DatabaseDep,
    user: CurrentUserDep,
):
    """Upload phiên bản mới của tài liệu hiện có.

    Quyền: người upload gốc, QT_NOI_DUNG, ADMIN.
    Tạo record MỚI với phien_ban += 1, phien_ban_truoc_id = id bản cũ.
    Bản cũ KHÔNG bị xóa.
    """
    tl_moi = await tai_lieu_service.upload_phien_ban_moi(db, tai_lieu_id, payload, user)
    return SuccessResponse(
        data=TaiLieuResponse.model_validate(tl_moi),
        message=f"Đã tạo phiên bản {tl_moi.phien_ban} thành công",
    )


# ---------------------------------------------------------------------------
# Lịch sử phiên bản
# ---------------------------------------------------------------------------


@router.get(
    "/{tai_lieu_id}/lich-su",
    response_model=SuccessResponse[List[TaiLieuVersionResponse]],
    summary="Lịch sử phiên bản",
)
async def lich_su_phien_ban(
    tai_lieu_id: uuid.UUID,
    db: DatabaseDep,
    user: CurrentUserDep,
):
    """Lịch sử tất cả phiên bản của tài liệu.

    Duyệt ngược theo phien_ban_truoc_id từ ID cung cấp.
    Thường gọi với ID của phiên bản MỚI NHẤT.
    Trả về danh sách sắp phien_ban DESC.
    """
    versions = await tai_lieu_service.lich_su_phien_ban(db, tai_lieu_id, user)
    data = [TaiLieuVersionResponse.model_validate(v) for v in versions]
    return SuccessResponse(
        data=data,
        message=f"Có {len(data)} phiên bản",
    )


# ---------------------------------------------------------------------------
# Download
# ---------------------------------------------------------------------------


@router.get(
    "/{tai_lieu_id}/download",
    summary="Download tài liệu",
    response_class=RedirectResponse,
)
async def download_tai_lieu(
    tai_lieu_id: uuid.UUID,
    db: DatabaseDep,
    user: CurrentUserDep,
):
    """Tải tài liệu. Redirect đến file_url (MinIO / CDN).

    Kiểm tra quyền truy cập trước khi redirect.
    """
    tl = await tai_lieu_service.chi_tiet(db, tai_lieu_id, user)
    return RedirectResponse(url=tl.file_url, status_code=status.HTTP_302_FOUND)
