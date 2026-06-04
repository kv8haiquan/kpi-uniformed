"""
chi_tieu_service/api/endpoints/giao_nam.py
==========================================
Giao chỉ tiêu năm cho đơn vị. Ghi: QT_CHI_TIEU.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from chi_tieu_service.dependencies import get_db, get_current_user, require_platform_role
from chi_tieu_service.schemas.giao_nam import GiaoNamCreate, GiaoNamUpdate, GiaoNamResponse
from chi_tieu_service.services.giao_nam_service import GiaoNamService
from shared.auth import TokenPayload

router = APIRouter(prefix="/giao-nam", tags=["Chỉ tiêu - Giao năm"])


@router.get("")
async def danh_sach(
    nam: Optional[int] = Query(None),
    don_vi_id: Optional[UUID] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(200, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    result = await GiaoNamService(db).danh_sach(nam=nam, don_vi_id=don_vi_id, page=page, page_size=page_size)
    return {
        "success": True,
        "data": [GiaoNamResponse.model_validate(i).model_dump(mode="json") for i in result["items"]],
        "pagination": result["pagination"],
    }


@router.post("", status_code=201)
async def tao(
    data: GiaoNamCreate,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(require_platform_role("QT_CHI_TIEU")),
):
    gn = await GiaoNamService(db).tao_moi(data, nguoi_giao_id=UUID(user.sub))
    return {"success": True, "data": GiaoNamResponse.model_validate(gn).model_dump(mode="json"),
            "message": "Giao chỉ tiêu năm thành công"}


@router.put("/{gn_id}")
async def cap_nhat(
    gn_id: UUID,
    data: GiaoNamUpdate,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(require_platform_role("QT_CHI_TIEU")),
):
    gn = await GiaoNamService(db).cap_nhat(gn_id, data)
    return {"success": True, "data": GiaoNamResponse.model_validate(gn).model_dump(mode="json"),
            "message": "Cập nhật giao năm thành công"}


@router.delete("/{gn_id}")
async def xoa(
    gn_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(require_platform_role("QT_CHI_TIEU")),
):
    await GiaoNamService(db).xoa(gn_id)
    return {"success": True, "message": "Xóa giao năm thành công"}
