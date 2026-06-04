"""
chi_tieu_service/api/endpoints/duyet.py
=======================================
Duyệt / từ chối của Trưởng đơn vị (TRUONG_DON_VI = vai_tro TDV).
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from chi_tieu_service.dependencies import get_db, get_current_user
from chi_tieu_service.schemas.dang_ky import DangKyResponse, TuChoiRequest
from chi_tieu_service.services.dang_ky_service import DangKyService
from chi_tieu_service.services.duyet_service import DuyetService
from chi_tieu_service.services.guards import assert_truong_don_vi, don_vi_ids_duyet
from shared.auth import TokenPayload

router = APIRouter(prefix="/duyet", tags=["Chỉ tiêu - Duyệt (Trưởng ĐV)"])


def _resp(dk) -> dict:
    return {"success": True, "data": DangKyResponse.model_validate(dk).model_dump(mode="json")}


@router.get("/cho-xu-ly")
async def cho_xu_ly(
    loai: str = Query("DANG_KY", description="DANG_KY | SUA | KET_QUA"),
    don_vi_id: UUID = Query(None, description="LĐ Chi cục/admin lọc theo đơn vị cụ thể"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    """Hàng chờ duyệt theo loại — TĐV chỉ thấy đơn vị mình; LĐ/admin truyền don_vi_id."""
    if don_vi_id:
        don_vi_ids = [don_vi_id]
    else:
        don_vi_ids = await don_vi_ids_duyet(db, user)
    result = await DuyetService(db).cho_xu_ly(loai, don_vi_ids, page=page, page_size=page_size)
    return {
        "success": True,
        "data": [DangKyResponse.model_validate(i).model_dump(mode="json") for i in result["items"]],
        "pagination": result["pagination"],
    }


@router.post("/{dk_id}/duyet")
async def duyet(
    dk_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    dk = await DangKyService(db).chi_tiet(dk_id)
    assert_truong_don_vi(user, dk.don_vi_id)
    dk = await DuyetService(db).duyet(dk_id, UUID(user.sub))
    return _resp(dk) | {"message": "Đã duyệt"}


@router.post("/{dk_id}/tu-choi")
async def tu_choi(
    dk_id: UUID,
    data: TuChoiRequest,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    dk = await DangKyService(db).chi_tiet(dk_id)
    assert_truong_don_vi(user, dk.don_vi_id)
    dk = await DuyetService(db).tu_choi(dk_id, data.ly_do_tu_choi, UUID(user.sub))
    return _resp(dk) | {"message": "Đã từ chối"}
