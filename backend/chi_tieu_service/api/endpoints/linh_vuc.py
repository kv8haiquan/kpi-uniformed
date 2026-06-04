"""
chi_tieu_service/api/endpoints/linh_vuc.py
==========================================
CRUD lĩnh vực công tác. Đọc: mọi vai trò. Ghi: QT_CHI_TIEU.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from chi_tieu_service.dependencies import get_db, get_current_user, require_platform_role
from chi_tieu_service.schemas.linh_vuc import LinhVucCreate, LinhVucUpdate, LinhVucResponse
from chi_tieu_service.services.linh_vuc_service import LinhVucService
from shared.auth import TokenPayload

router = APIRouter(prefix="/linh-vuc", tags=["Chỉ tiêu - Lĩnh vực"])


@router.get("")
async def danh_sach(
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    result = await LinhVucService(db).danh_sach(page=page, page_size=page_size)
    return {
        "success": True,
        "data": [LinhVucResponse.model_validate(i).model_dump(mode="json") for i in result["items"]],
        "pagination": result["pagination"],
    }


@router.post("", status_code=201)
async def tao(
    data: LinhVucCreate,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(require_platform_role("QT_CHI_TIEU")),
):
    lv = await LinhVucService(db).tao_moi(data)
    return {"success": True, "data": LinhVucResponse.model_validate(lv).model_dump(mode="json"),
            "message": "Tạo lĩnh vực thành công"}


@router.put("/{linh_vuc_id}")
async def cap_nhat(
    linh_vuc_id: UUID,
    data: LinhVucUpdate,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(require_platform_role("QT_CHI_TIEU")),
):
    lv = await LinhVucService(db).cap_nhat(linh_vuc_id, data)
    return {"success": True, "data": LinhVucResponse.model_validate(lv).model_dump(mode="json"),
            "message": "Cập nhật lĩnh vực thành công"}


@router.delete("/{linh_vuc_id}")
async def xoa(
    linh_vuc_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(require_platform_role("QT_CHI_TIEU")),
):
    await LinhVucService(db).xoa(linh_vuc_id)
    return {"success": True, "message": "Xóa lĩnh vực thành công"}
