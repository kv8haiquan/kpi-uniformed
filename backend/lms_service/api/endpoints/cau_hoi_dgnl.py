"""
lms_service/api/endpoints/cau_hoi_dgnl.py
==========================================
API endpoints ngan hang cau hoi DGNL.
8 endpoints:
  GET    /dgnl/ngan-hang              Danh sach cau hoi
  POST   /dgnl/ngan-hang              Tao cau hoi
  GET    /dgnl/ngan-hang/thong-ke     Thong ke theo linh vuc
  GET    /dgnl/ngan-hang/import/mau   Download template Excel
  POST   /dgnl/ngan-hang/import       Import tu Excel/CSV
  GET    /dgnl/ngan-hang/{id}         Chi tiet
  PUT    /dgnl/ngan-hang/{id}         Cap nhat
  DELETE /dgnl/ngan-hang/{id}         Soft delete
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, Query, Response, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from lms_service.dependencies import get_db, require_platform_role
from lms_service.schemas.cau_hoi_dgnl import CauHoiDgnlCreate, CauHoiDgnlUpdate, CauHoiDgnlResponse
from lms_service.services.cau_hoi_dgnl_service import CauHoiDgnlService
from shared.auth import TokenPayload

router = APIRouter(prefix="/dgnl/ngan-hang", tags=["ĐGNL - Ngân hàng câu hỏi"])


@router.get("")
async def danh_sach(
    linh_vuc_id: Optional[UUID] = Query(None),
    do_kho: Optional[str] = Query(None),
    loai: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(require_platform_role("QT_DAO_TAO", "GIANG_VIEN")),
):
    """Danh sach cau hoi DGNL."""
    service = CauHoiDgnlService(db)
    result = await service.danh_sach(linh_vuc_id, do_kho, loai, search, page, page_size)
    return {
        "success": True,
        "data": [CauHoiDgnlResponse(**item).model_dump(mode="json") for item in result["items"]],
        "pagination": result["pagination"],
    }


@router.post("", status_code=201)
async def tao_cau_hoi(
    data: CauHoiDgnlCreate,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(require_platform_role("QT_DAO_TAO", "GIANG_VIEN")),
):
    """Tao cau hoi DGNL."""
    service = CauHoiDgnlService(db)
    ch = await service.tao_moi(data, user)
    return {
        "success": True,
        "data": CauHoiDgnlResponse.model_validate(ch).model_dump(mode="json"),
        "message": "Tạo câu hỏi thành công",
    }


@router.get("/thong-ke")
async def thong_ke_ngan_hang(
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(require_platform_role("QT_DAO_TAO")),
):
    """Thong ke ngan hang cau hoi theo linh vuc + do kho."""
    service = CauHoiDgnlService(db)
    data = await service.thong_ke()
    return {
        "success": True,
        "data": [item.model_dump(mode="json") for item in data],
    }


@router.get("/import/mau")
async def download_template(
    user: TokenPayload = Depends(require_platform_role("QT_DAO_TAO", "GIANG_VIEN")),
):
    """Download file Excel mau import cau hoi DGNL."""
    service = CauHoiDgnlService.__new__(CauHoiDgnlService)
    xlsx_bytes = service.generate_template()
    return Response(
        content=xlsx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=mau_import_cau_hoi_dgnl.xlsx"},
    )


@router.post("/import", status_code=201)
async def import_cau_hoi(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(require_platform_role("QT_DAO_TAO", "GIANG_VIEN")),
):
    """Import cau hoi DGNL tu file Excel/CSV."""
    service = CauHoiDgnlService(db)
    result = await service.import_from_file(file, db, user.sub)
    return {
        "success": True,
        "data": result,
        "message": f"Import hoàn tất: {result['thanh_cong']}/{result['tong']} câu thành công",
    }


@router.get("/{id}")
async def chi_tiet(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(require_platform_role("QT_DAO_TAO", "GIANG_VIEN")),
):
    """Chi tiet cau hoi DGNL."""
    service = CauHoiDgnlService(db)
    ch = await service.chi_tiet(id)
    return {"success": True, "data": CauHoiDgnlResponse.model_validate(ch).model_dump(mode="json")}


@router.put("/{id}")
async def cap_nhat(
    id: UUID,
    data: CauHoiDgnlUpdate,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(require_platform_role("QT_DAO_TAO", "GIANG_VIEN")),
):
    """Cap nhat cau hoi DGNL."""
    service = CauHoiDgnlService(db)
    ch = await service.cap_nhat(id, data, user)
    return {
        "success": True,
        "data": CauHoiDgnlResponse.model_validate(ch).model_dump(mode="json"),
        "message": "Cập nhật câu hỏi thành công",
    }


@router.delete("/{id}")
async def xoa(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(require_platform_role("QT_DAO_TAO", "GIANG_VIEN")),
):
    """Soft delete cau hoi DGNL."""
    service = CauHoiDgnlService(db)
    await service.xoa(id, user)
    return {"success": True, "message": "Xóa câu hỏi thành công"}
