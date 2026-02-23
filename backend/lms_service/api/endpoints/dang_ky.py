"""
lms_service/api/endpoints/dang_ky.py
====================================
API endpoints cho dang ky / giao khoa hoc.

Endpoints:
  POST   /khoa-hoc/{khoa_hoc_id}/dang-ky      Dang ky tu nguyen
  POST   /khoa-hoc/{khoa_hoc_id}/giao-bai      Giao bai bat buoc
  GET    /dang-ky/cua-toi                       Khoa hoc cua toi
  GET    /khoa-hoc/{khoa_hoc_id}/hoc-vien       Danh sach hoc vien
  DELETE /khoa-hoc/{khoa_hoc_id}/dang-ky        Huy dang ky
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from lms_service.dependencies import get_db, get_current_user, require_platform_role
from lms_service.schemas.dang_ky import (
    DangKyResponse,
    GiaoBaiRequest,
    GiaoBaiResponse,
    HocVienListItem,
)
from lms_service.services.dang_ky_service import DangKyService
from shared.auth import TokenPayload

router = APIRouter(tags=["Đăng ký khóa học"])


@router.post("/khoa-hoc/{khoa_hoc_id}/dang-ky", status_code=201)
async def dang_ky_tu_nguyen(
    khoa_hoc_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    """CBCC tự đăng ký khóa học. Kiểm tra điều kiện tiên quyết."""
    service = DangKyService(db)
    dk = await service.dang_ky_tu_nguyen(khoa_hoc_id, user)

    response = DangKyResponse.model_validate(dk)
    return {
        "success": True,
        "data": response.model_dump(mode="json"),
        "message": "Đăng ký khóa học thành công",
    }


@router.post("/khoa-hoc/{khoa_hoc_id}/giao-bai")
async def giao_bai(
    khoa_hoc_id: UUID,
    data: GiaoBaiRequest,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    """Giao khóa học bắt buộc cho CBCC/đơn vị.
    Auth: QT_DAO_TAO, Lãnh đạo (is_lanh_dao), SUPER_ADMIN.
    """
    # Auth check: QT_DAO_TAO hoac lanh_dao hoac SUPER_ADMIN
    is_qt = (
        user.vai_tro == "SUPER_ADMIN"
        or "QT_DAO_TAO" in (user.platform_roles or [])
    )
    if not is_qt and not user.is_lanh_dao:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "error": {"code": "PERM_001", "message": "Yêu cầu QT_DAO_TAO hoặc Lãnh đạo"},
            },
        )

    service = DangKyService(db)
    result = await service.giao_bai(khoa_hoc_id, data, user)

    return {
        "success": True,
        "data": GiaoBaiResponse(**result).model_dump(),
        "message": f"Đã giao {result['da_giao']} CBCC, bỏ qua {result['da_co']} đã có",
    }


@router.get("/dang-ky/cua-toi")
async def khoa_hoc_cua_toi(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    trang_thai: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    """Danh sách khóa học đã đăng ký của user hiện tại."""
    service = DangKyService(db)
    result = await service.khoa_hoc_cua_toi(user, page, page_size, trang_thai)

    return {
        "success": True,
        "data": [DangKyResponse(**item).model_dump(mode="json") for item in result["items"]],
        "pagination": result["pagination"],
    }


@router.get("/khoa-hoc/{khoa_hoc_id}/hoc-vien")
async def danh_sach_hoc_vien(
    khoa_hoc_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    trang_thai: Optional[str] = Query(None),
    don_vi_id: Optional[UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(require_platform_role("GIANG_VIEN", "QT_DAO_TAO")),
):
    """Danh sách học viên của khóa học."""
    service = DangKyService(db)
    result = await service.danh_sach_hoc_vien(
        khoa_hoc_id, user, page, page_size, trang_thai, don_vi_id
    )

    return {
        "success": True,
        "data": [HocVienListItem(**item).model_dump(mode="json") for item in result["items"]],
        "pagination": result["pagination"],
    }


@router.delete("/khoa-hoc/{khoa_hoc_id}/dang-ky")
async def huy_dang_ky(
    khoa_hoc_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    """Hủy đăng ký khóa học. Chỉ TU_NGUYEN + CHUA_BAT_DAU."""
    service = DangKyService(db)
    await service.huy_dang_ky(khoa_hoc_id, user)

    return {
        "success": True,
        "data": None,
        "message": "Hủy đăng ký thành công",
    }
