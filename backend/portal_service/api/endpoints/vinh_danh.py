"""
portal_service/api/endpoints/vinh_danh.py
==========================================
API endpoints cho Vinh danh cong chuc tieu bieu thang.

Routes:
  GET    /vinh-danh                  — Danh sach (phan trang, filter thang/nam/trang_thai)
  GET    /vinh-danh/current          — Vinh danh PUBLISHED cua thang hien tai (widget)
  GET    /vinh-danh/{id}             — Chi tiet
  POST   /vinh-danh                  — Tao moi (DRAFT) — admin only
  PUT    /vinh-danh/{id}             — Cap nhat — admin only
  POST   /vinh-danh/{id}/cong-bo     — DRAFT -> PUBLISHED — admin only
  POST   /vinh-danh/{id}/go-cong-bo  — PUBLISHED -> DRAFT — admin only
  DELETE /vinh-danh/{id}             — Xoa (chi DRAFT) — admin only
  POST   /vinh-danh/upload-anh       — Upload anh chan dung — admin only

Phan quyen: SUPER_ADMIN va platform role QT_NOI_DUNG co full quyen.
"""

import math
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, File, Query, UploadFile, status

from portal_service.dependencies import (
    CurrentUserDep,
    DatabaseDep,
    require_platform_role,
)
from portal_service.schemas.base import (
    PaginatedResponse,
    PaginationInfo,
    SuccessResponse,
)
from portal_service.schemas.vinh_danh_thang import (
    UploadAnhResponse,
    VinhDanhThangCreate,
    VinhDanhThangResponse,
    VinhDanhThangUpdate,
)
from portal_service.services import vinh_danh_service
from portal_service.services.file_service import PortalFileService

router = APIRouter(prefix="/vinh-danh", tags=["Vinh danh"])


# ---------------------------------------------------------------------------
# Danh sach (cong khai cho moi user da dang nhap)
# ---------------------------------------------------------------------------


@router.get(
    "",
    response_model=PaginatedResponse[VinhDanhThangResponse],
    summary="Danh sach vinh danh",
)
async def get_danh_sach(
    db: DatabaseDep,
    _user: CurrentUserDep,
    nam: Optional[int] = Query(None, ge=2020, le=2100),
    thang: Optional[int] = Query(None, ge=1, le=12),
    trang_thai: Optional[str] = Query(None, description="DRAFT | PUBLISHED"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """Danh sach vinh danh — sap xep moi nhat truoc.

    Moi cong chuc da dang nhap deu xem duoc.
    """
    items, total = await vinh_danh_service.danh_sach(
        db, nam=nam, thang=thang, trang_thai=trang_thai, page=page, page_size=page_size
    )
    data = [VinhDanhThangResponse.model_validate(it) for it in items]
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
# Vinh danh thang hien tai (widget dashboard)
# ---------------------------------------------------------------------------


@router.get(
    "/current",
    response_model=SuccessResponse[Optional[VinhDanhThangResponse]],
    summary="Vinh danh PUBLISHED cua thang hien tai",
)
async def get_current(db: DatabaseDep, _user: CurrentUserDep):
    """Tra ve ban ghi vinh danh PUBLISHED cua thang hien tai (None neu chua co)."""
    vd = await vinh_danh_service.lay_vinh_danh_thang_hien_tai(db)
    data = VinhDanhThangResponse.model_validate(vd) if vd else None
    return SuccessResponse(data=data, message="OK")


# ---------------------------------------------------------------------------
# Upload anh chan dung — admin only
# ---------------------------------------------------------------------------


@router.post(
    "/upload-anh",
    response_model=SuccessResponse[UploadAnhResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Upload anh chan dung",
)
async def upload_anh(
    file: UploadFile = File(..., description="File anh (.jpg, .png, .webp, max 5MB)"),
    _user=Depends(require_platform_role("QT_NOI_DUNG")),
):
    """Upload anh chan dung cho ban ghi vinh danh. Tra ve URL de paste vao form."""
    fs = PortalFileService()
    result = await fs.save_image(file, sub_folder="vinh-danh")
    return SuccessResponse(
        data=UploadAnhResponse(url=result["file_url"]),
        message="Upload anh thanh cong",
    )


# ---------------------------------------------------------------------------
# Chi tiet
# ---------------------------------------------------------------------------


@router.get(
    "/{vd_id}",
    response_model=SuccessResponse[VinhDanhThangResponse],
    summary="Chi tiet ban ghi vinh danh",
)
async def get_chi_tiet(
    vd_id: uuid.UUID,
    db: DatabaseDep,
    _user: CurrentUserDep,
):
    """Lay chi tiet ban ghi vinh danh."""
    vd = await vinh_danh_service.chi_tiet(db, vd_id)
    return SuccessResponse(
        data=VinhDanhThangResponse.model_validate(vd),
        message="OK",
    )


# ---------------------------------------------------------------------------
# Tao moi (admin only)
# ---------------------------------------------------------------------------


@router.post(
    "",
    response_model=SuccessResponse[VinhDanhThangResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Tao moi vinh danh (DRAFT)",
)
async def post_tao_moi(
    data: VinhDanhThangCreate,
    db: DatabaseDep,
    user=Depends(require_platform_role("QT_NOI_DUNG")),
):
    """Tao ban ghi vinh danh moi o trang thai DRAFT."""
    vd = await vinh_danh_service.tao_moi(db, data, nguoi_tao_id=uuid.UUID(user.sub))
    return SuccessResponse(
        data=VinhDanhThangResponse.model_validate(vd),
        message="Da tao ban ghi vinh danh (DRAFT)",
    )


# ---------------------------------------------------------------------------
# Cap nhat (admin only)
# ---------------------------------------------------------------------------


@router.put(
    "/{vd_id}",
    response_model=SuccessResponse[VinhDanhThangResponse],
    summary="Cap nhat vinh danh",
)
async def put_cap_nhat(
    vd_id: uuid.UUID,
    data: VinhDanhThangUpdate,
    db: DatabaseDep,
    _user=Depends(require_platform_role("QT_NOI_DUNG")),
):
    """Cap nhat noi dung ban ghi vinh danh."""
    vd = await vinh_danh_service.cap_nhat(db, vd_id, data)
    return SuccessResponse(
        data=VinhDanhThangResponse.model_validate(vd),
        message="Da cap nhat ban ghi vinh danh",
    )


# ---------------------------------------------------------------------------
# Cong bo / Go cong bo (admin only)
# ---------------------------------------------------------------------------


@router.post(
    "/{vd_id}/cong-bo",
    response_model=SuccessResponse[VinhDanhThangResponse],
    summary="Cong bo (DRAFT -> PUBLISHED)",
)
async def post_cong_bo(
    vd_id: uuid.UUID,
    db: DatabaseDep,
    _user=Depends(require_platform_role("QT_NOI_DUNG")),
):
    """Chuyen ban ghi tu DRAFT sang PUBLISHED, set ngay_cong_bo."""
    vd = await vinh_danh_service.cong_bo(db, vd_id)
    return SuccessResponse(
        data=VinhDanhThangResponse.model_validate(vd),
        message="Da cong bo vinh danh",
    )


@router.post(
    "/{vd_id}/go-cong-bo",
    response_model=SuccessResponse[VinhDanhThangResponse],
    summary="Go cong bo (PUBLISHED -> DRAFT)",
)
async def post_go_cong_bo(
    vd_id: uuid.UUID,
    db: DatabaseDep,
    _user=Depends(require_platform_role("QT_NOI_DUNG")),
):
    """Chuyen ban ghi tu PUBLISHED ve DRAFT (an khoi widget dashboard)."""
    vd = await vinh_danh_service.go_cong_bo(db, vd_id)
    return SuccessResponse(
        data=VinhDanhThangResponse.model_validate(vd),
        message="Da go cong bo",
    )


# ---------------------------------------------------------------------------
# Xoa (chi DRAFT, admin only)
# ---------------------------------------------------------------------------


@router.delete(
    "/{vd_id}",
    response_model=SuccessResponse[dict],
    summary="Xoa ban ghi vinh danh (chi DRAFT)",
)
async def delete_vinh_danh(
    vd_id: uuid.UUID,
    db: DatabaseDep,
    _user=Depends(require_platform_role("QT_NOI_DUNG")),
):
    """Xoa ban ghi DRAFT. Khong xoa duoc PUBLISHED (phai go cong bo truoc)."""
    result = await vinh_danh_service.xoa(db, vd_id)
    return SuccessResponse(data=result, message="Da xoa")
