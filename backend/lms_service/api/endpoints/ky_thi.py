"""
lms_service/api/endpoints/ky_thi.py
====================================
API endpoints ky thi DGNL + cau truc de + validate + thong ke.

11 endpoints:
  GET    /ky-thi                            Danh sach ky thi
  POST   /ky-thi                            Tao ky thi moi
  GET    /ky-thi/{id}                       Chi tiet ky thi
  PUT    /ky-thi/{id}                       Cap nhat (chi NHAP)
  PATCH  /ky-thi/{id}/trang-thai            Chuyen trang thai
  DELETE /ky-thi/{id}                       Soft delete (chi NHAP)
  POST   /ky-thi/{id}/validate              Validate ngan hang cau hoi
  GET    /ky-thi/{id}/thong-ke              Thong ke ket qua
  GET    /ky-thi/{id}/cau-truc-de           Lay cau truc de
  POST   /ky-thi/{id}/cau-truc-de           Upsert cau truc de 1 vi tri
  POST   /ky-thi/{id}/cau-truc-de/ap-dung-mau  Ap dung mau (nguyen tu)
  DELETE /ky-thi/{id}/cau-truc-de/{vi_tri_id}  Xoa cau truc de 1 vi tri
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from lms_service.dependencies import get_db, get_current_user, require_platform_role
from lms_service.schemas.ky_thi import (
    KyThiCreate, KyThiUpdate, KyThiTrangThaiUpdate, KyThiResponse,
    CauTrucDeCreate, CauTrucDeByViTri, ApDungMauRequest,
    ValidateResponse, ThongKeKyThi,
)
from lms_service.services.ky_thi_service import KyThiService
from shared.auth import TokenPayload

router = APIRouter(prefix="/ky-thi", tags=["ĐGNL - Kỳ thi"])


# ================================================================
# KY THI CRUD
# ================================================================

@router.get("")
async def danh_sach_ky_thi(
    trang_thai: Optional[str] = Query(None, description="Filter theo trang thai: NHAP, CHO_DUYET, DANG_MO, DA_DONG"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    """Danh sach ky thi. CBCC chi thay ky thi DANG_MO/DA_DONG ma minh duoc giao."""
    service = KyThiService(db)
    result = await service.danh_sach(user, trang_thai=trang_thai, page=page, page_size=page_size)
    return {
        "success": True,
        "data": [KyThiResponse(**item).model_dump(mode="json") for item in result["items"]],
        "pagination": result["pagination"],
    }


@router.post("", status_code=201)
async def tao_ky_thi(
    data: KyThiCreate,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(require_platform_role("QT_DAO_TAO")),
):
    """Tao ky thi DGNL moi — chi QT_DAO_TAO."""
    service = KyThiService(db)
    kt = await service.tao_moi(data, user)
    return {
        "success": True,
        "data": KyThiResponse.model_validate(kt).model_dump(mode="json"),
        "message": "Tạo kỳ thi thành công",
    }


@router.get("/{ky_thi_id}")
async def chi_tiet_ky_thi(
    ky_thi_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    """Chi tiet ky thi (kem thong ke nhanh)."""
    service = KyThiService(db)
    data = await service.chi_tiet_full(ky_thi_id, user)
    return {
        "success": True,
        "data": KyThiResponse(**data).model_dump(mode="json"),
    }


@router.put("/{ky_thi_id}")
async def cap_nhat_ky_thi(
    ky_thi_id: UUID,
    data: KyThiUpdate,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(require_platform_role("QT_DAO_TAO")),
):
    """Cap nhat ky thi — chi khi NHAP."""
    service = KyThiService(db)
    kt = await service.cap_nhat(ky_thi_id, data, user)
    return {
        "success": True,
        "data": KyThiResponse.model_validate(kt).model_dump(mode="json"),
        "message": "Cập nhật kỳ thi thành công",
    }


@router.patch("/{ky_thi_id}/trang-thai")
async def chuyen_trang_thai_ky_thi(
    ky_thi_id: UUID,
    data: KyThiTrangThaiUpdate,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    """Chuyen trang thai ky thi: NHAP -> CHO_DUYET -> DANG_MO -> DA_DONG."""
    service = KyThiService(db)
    kt = await service.chuyen_trang_thai(ky_thi_id, data, user)
    return {
        "success": True,
        "data": KyThiResponse.model_validate(kt).model_dump(mode="json"),
        "message": f"Chuyển trạng thái thành {kt.trang_thai} thành công",
    }


@router.delete("/{ky_thi_id}")
async def xoa_ky_thi(
    ky_thi_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(require_platform_role("QT_DAO_TAO")),
):
    """Soft delete ky thi — chi khi NHAP va chua co thi sinh."""
    service = KyThiService(db)
    await service.xoa(ky_thi_id, user)
    return {
        "success": True,
        "message": "Xóa kỳ thi thành công",
    }


# ================================================================
# VALIDATE
# ================================================================

@router.post("/{ky_thi_id}/validate")
async def validate_ngan_hang(
    ky_thi_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(require_platform_role("QT_DAO_TAO")),
):
    """Kiem tra ngan hang cau hoi co du cho cau truc de cua ky thi."""
    service = KyThiService(db)
    result = await service.validate_ngan_hang(ky_thi_id)
    return {
        "success": True,
        "data": result.model_dump(mode="json"),
    }


# ================================================================
# THONG KE
# ================================================================

@router.get("/{ky_thi_id}/thong-ke")
async def thong_ke_ky_thi(
    ky_thi_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(require_platform_role("QT_DAO_TAO")),
):
    """Thong ke ket qua ky thi. Chi admin (QT_DAO_TAO/SUPER_ADMIN)."""
    service = KyThiService(db)
    data = await service.thong_ke(ky_thi_id, user)
    return {
        "success": True,
        "data": data,
    }


# ================================================================
# CAU TRUC DE
# ================================================================

@router.get("/{ky_thi_id}/cau-truc-de")
async def lay_cau_truc_de(
    ky_thi_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(require_platform_role("QT_DAO_TAO")),
):
    """Lay cau truc de thi nhom theo vi tri."""
    service = KyThiService(db)
    data = await service.lay_cau_truc_de(ky_thi_id)
    return {
        "success": True,
        "data": [item.model_dump(mode="json") for item in data],
    }


@router.post("/{ky_thi_id}/cau-truc-de", status_code=201)
async def upsert_cau_truc_de(
    ky_thi_id: UUID,
    data: CauTrucDeCreate,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(require_platform_role("QT_DAO_TAO")),
):
    """Tao hoac cap nhat cau truc de cho 1 vi tri (bulk upsert)."""
    service = KyThiService(db)
    result = await service.upsert_cau_truc_de(ky_thi_id, data, user)
    return {
        "success": True,
        "data": [item.model_dump(mode="json") for item in result],
        "message": "Cập nhật cấu trúc đề thành công",
    }


@router.post("/{ky_thi_id}/cau-truc-de/ap-dung-mau", status_code=201)
async def ap_dung_mau_cau_truc(
    ky_thi_id: UUID,
    data: ApDungMauRequest,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(require_platform_role("QT_DAO_TAO")),
):
    """Ap dung mau cau truc de vao ky thi — validate het roi ghi 1 transaction."""
    service = KyThiService(db)
    result = await service.ap_dung_mau_cau_truc(ky_thi_id, data, user)
    return {
        "success": True,
        "data": [item.model_dump(mode="json") for item in result],
        "message": "Áp dụng mẫu cấu trúc đề thành công",
    }


@router.delete("/{ky_thi_id}/cau-truc-de/{vi_tri_id}")
async def xoa_cau_truc_de_vi_tri(
    ky_thi_id: UUID,
    vi_tri_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(require_platform_role("QT_DAO_TAO")),
):
    """Xoa cau truc de cua 1 vi tri."""
    service = KyThiService(db)
    await service.xoa_cau_truc_de_vi_tri(ky_thi_id, vi_tri_id, user)
    return {
        "success": True,
        "message": "Xóa cấu trúc đề thành công",
    }
