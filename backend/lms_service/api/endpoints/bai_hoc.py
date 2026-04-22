"""
lms_service/api/endpoints/bai_hoc.py
====================================
API endpoints cho CRUD bai hoc + cap nhat tien do.

Endpoints:
  GET    /khoa-hoc/{khoa_hoc_id}/bai-hoc              Danh sach bai hoc
  GET    /bai-hoc/{id}                                  Chi tiet bai hoc
  POST   /khoa-hoc/{khoa_hoc_id}/bai-hoc              Tao bai hoc moi
  PUT    /bai-hoc/{id}                                  Cap nhat bai hoc
  PATCH  /bai-hoc/{id}/tien-do                          Cap nhat tien do
  PATCH  /khoa-hoc/{khoa_hoc_id}/bai-hoc/sap-xep      Sap xep lai bai hoc
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from lms_service.dependencies import get_db, get_current_user, require_platform_role
from lms_service.schemas.bai_hoc import (
    BaiHocCreate,
    BaiHocResponse,
    BaiHocUpdate,
    SapXepRequest,
    TienDoUpdate,
)
from lms_service.services.bai_hoc_service import BaiHocService
from shared.auth import TokenPayload

router = APIRouter(tags=["Bài học"])


# =========================================================================
# ENDPOINTS DUNG PATH /khoa-hoc/{khoa_hoc_id}/bai-hoc
# =========================================================================

@router.get("/khoa-hoc/{khoa_hoc_id}/bai-hoc")
async def danh_sach_bai_hoc(
    khoa_hoc_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    """Danh sách bài học của khóa học, kèm tiến độ cá nhân."""
    service = BaiHocService(db)
    items = await service.danh_sach(khoa_hoc_id, user)

    return {
        "success": True,
        "data": [BaiHocResponse(**item).model_dump(mode="json") for item in items],
    }


@router.post("/khoa-hoc/{khoa_hoc_id}/bai-hoc", status_code=201)
async def tao_bai_hoc(
    khoa_hoc_id: UUID,
    data: BaiHocCreate,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(require_platform_role("GIANG_VIEN", "QT_DAO_TAO")),
):
    """Tạo bài học mới cho khóa học. Yêu cầu: GIANG_VIEN hoặc QT_DAO_TAO."""
    service = BaiHocService(db)
    bh = await service.tao_moi(khoa_hoc_id, data, user)

    response = BaiHocResponse.model_validate(bh)
    return {
        "success": True,
        "data": response.model_dump(mode="json"),
        "message": "Tạo bài học thành công",
    }


@router.patch("/khoa-hoc/{khoa_hoc_id}/bai-hoc/sap-xep")
async def sap_xep_bai_hoc(
    khoa_hoc_id: UUID,
    data: SapXepRequest,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(require_platform_role("GIANG_VIEN", "QT_DAO_TAO")),
):
    """Sắp xếp lại thứ tự bài học."""
    service = BaiHocService(db)
    await service.sap_xep(khoa_hoc_id, data.thu_tu, user)

    return {
        "success": True,
        "data": None,
        "message": "Sắp xếp bài học thành công",
    }


# =========================================================================
# ENDPOINTS DUNG PATH /bai-hoc/{id}
# =========================================================================

@router.get("/bai-hoc/{id}")
async def chi_tiet_bai_hoc(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    """Chi tiết bài học, kèm tiến độ cá nhân."""
    service = BaiHocService(db)
    data = await service.chi_tiet(id, user)

    return {
        "success": True,
        "data": BaiHocResponse(**data).model_dump(mode="json"),
    }


@router.put("/bai-hoc/{id}")
async def cap_nhat_bai_hoc(
    id: UUID,
    data: BaiHocUpdate,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(require_platform_role("GIANG_VIEN", "QT_DAO_TAO")),
):
    """Cập nhật bài học. Yêu cầu: GIANG_VIEN hoặc QT_DAO_TAO."""
    service = BaiHocService(db)
    bh = await service.cap_nhat(id, data, user)

    response = BaiHocResponse.model_validate(bh)
    return {
        "success": True,
        "data": response.model_dump(mode="json"),
        "message": "Cập nhật bài học thành công",
    }


@router.patch("/bai-hoc/{id}/tien-do")
async def cap_nhat_tien_do(
    id: UUID,
    data: TienDoUpdate,
    preview: bool = Query(False, description="True: GV/QT xem thử, không ghi tiến độ"),
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    """Cập nhật tiến độ học bài. Tất cả CBCC đã đăng ký khóa.

    preview=True + user là GV/QT/ADMIN → trả về bài học với tien_do_ca_nhan=None,
    KHÔNG UPSERT tien_do_bai_hoc và KHÔNG tính phần trăm hoàn thành.
    """
    service = BaiHocService(db)

    if preview:
        is_manager = user.vai_tro == "SUPER_ADMIN" or "QT_DAO_TAO" in (user.platform_roles or [])
        is_gv = "GIANG_VIEN" in (user.platform_roles or [])
        if is_manager or is_gv:
            bh = await service._get_bai_hoc(id)
            # Chi tra du lieu bai hoc, khong cap nhat tien do
            return {
                "success": True,
                "data": BaiHocResponse(**service._bai_hoc_to_dict(bh, None)).model_dump(mode="json"),
                "message": "Chế độ xem thử — không lưu tiến độ",
            }

    result = await service.cap_nhat_tien_do(id, data, user)

    return {
        "success": True,
        "data": BaiHocResponse(**result).model_dump(mode="json"),
        "message": "Cập nhật tiến độ thành công",
    }
