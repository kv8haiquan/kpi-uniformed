"""
lms_service/api/endpoints/khoa_hoc.py
=====================================
API endpoints cho CRUD + workflow khoa hoc.

Endpoints:
  GET    /khoa-hoc                  Danh sach khoa hoc (hoc vien)
  GET    /khoa-hoc/quan-ly          Danh sach quan ly (giang vien/QT)
  GET    /khoa-hoc/{id}             Chi tiet khoa hoc
  POST   /khoa-hoc                  Tao khoa hoc moi
  PUT    /khoa-hoc/{id}             Cap nhat khoa hoc
  PATCH  /khoa-hoc/{id}/trang-thai  Chuyen trang thai (workflow)
  DELETE /khoa-hoc/{id}             Xoa khoa hoc (soft delete)
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from lms_service.dependencies import get_db, get_current_user, require_platform_role
from lms_service.schemas.khoa_hoc import (
    KhoaHocCreate,
    KhoaHocListItem,
    KhoaHocResponse,
    KhoaHocUpdate,
    TrangThaiUpdate,
)
from lms_service.services.khoa_hoc_service import KhoaHocService
from shared.auth import TokenPayload

router = APIRouter(prefix="/khoa-hoc", tags=["Khóa học"])


@router.get("")
async def danh_sach_khoa_hoc(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    trang_thai: Optional[str] = Query(None),
    chuyen_de_id: Optional[UUID] = Query(None),
    loai: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    """Danh sách khóa học. CBCC thường chỉ thấy DA_XUAT_BAN."""
    service = KhoaHocService(db)
    result = await service.danh_sach(
        page=page,
        page_size=page_size,
        trang_thai=trang_thai,
        chuyen_de_id=chuyen_de_id,
        loai=loai,
        search=search,
        user=user,
    )

    return {
        "success": True,
        "data": [KhoaHocListItem(**item).model_dump(mode="json") for item in result["items"]],
        "pagination": result["pagination"],
    }


@router.get("/quan-ly")
async def danh_sach_quan_ly(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    trang_thai: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(require_platform_role("GIANG_VIEN", "QT_DAO_TAO")),
):
    """Danh sách quản lý. GIANG_VIEN: khóa của mình. QT_DAO_TAO: tất cả."""
    service = KhoaHocService(db)
    result = await service.danh_sach_quan_ly(
        page=page,
        page_size=page_size,
        trang_thai=trang_thai,
        search=search,
        user=user,
    )

    return {
        "success": True,
        "data": [KhoaHocListItem(**item).model_dump(mode="json") for item in result["items"]],
        "pagination": result["pagination"],
    }


@router.get("/{id}")
async def chi_tiet_khoa_hoc(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    """Chi tiết khóa học. Bao gồm trạng thái đăng ký của user hiện tại."""
    service = KhoaHocService(db)
    # Truyền user_id để query thêm trạng thái đăng ký cá nhân
    data = await service.chi_tiet(id, user_id=UUID(user.sub))

    return {
        "success": True,
        "data": KhoaHocResponse(**data).model_dump(mode="json"),
    }


@router.post("", status_code=201)
async def tao_khoa_hoc(
    data: KhoaHocCreate,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(require_platform_role("GIANG_VIEN", "QT_DAO_TAO")),
):
    """Tạo khóa học mới. Yêu cầu: GIANG_VIEN hoặc QT_DAO_TAO."""
    service = KhoaHocService(db)
    kh = await service.tao_moi(data, user)

    response = KhoaHocResponse.model_validate(kh)
    return {
        "success": True,
        "data": response.model_dump(mode="json"),
        "message": "Tạo khóa học thành công",
    }


@router.put("/{id}")
async def cap_nhat_khoa_hoc(
    id: UUID,
    data: KhoaHocUpdate,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(require_platform_role("GIANG_VIEN", "QT_DAO_TAO")),
):
    """Cập nhật khóa học. GIANG_VIEN: khóa mình + NHÁP. QT_DAO_TAO: tất cả."""
    service = KhoaHocService(db)
    kh = await service.cap_nhat(id, data, user)

    response = KhoaHocResponse.model_validate(kh)
    return {
        "success": True,
        "data": response.model_dump(mode="json"),
        "message": "Cập nhật khóa học thành công",
    }


@router.patch("/{id}/trang-thai")
async def chuyen_trang_thai(
    id: UUID,
    data: TrangThaiUpdate,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(require_platform_role("GIANG_VIEN", "QT_DAO_TAO")),
):
    """Chuyển trạng thái khóa học (workflow).
    NHAP → CHO_DUYET → DA_XUAT_BAN → TAM_DUNG/DA_DONG.
    """
    service = KhoaHocService(db)
    kh = await service.chuyen_trang_thai(id, data.trang_thai, data.ghi_chu, user)

    response = KhoaHocResponse.model_validate(kh)
    return {
        "success": True,
        "data": response.model_dump(mode="json"),
        "message": f"Chuyển trạng thái thành {data.trang_thai} thành công",
    }


@router.delete("/{id}")
async def xoa_khoa_hoc(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(require_platform_role("QT_DAO_TAO")),
):
    """Xóa khóa học (soft delete). Chỉ NHÁP + chưa có học viên."""
    service = KhoaHocService(db)
    await service.xoa(id, user)

    return {
        "success": True,
        "data": None,
        "message": "Xóa khóa học thành công",
    }
