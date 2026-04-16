"""
lms_service/api/endpoints/chung_chi.py
======================================
API endpoints cho chung chi va khao sat.

Endpoints:
  GET    /chung-chi/cua-toi                       Danh sach chung chi cua toi
  GET    /chung-chi/xac-minh/{ma_chung_chi}       Xac minh chung chi (PUBLIC)
  GET    /chung-chi/{id}/tai                       Tai chung chi (PDF placeholder)
  POST   /khao-sat                                 Gui khao sat
  GET    /khoa-hoc/{khoa_hoc_id}/khao-sat/thong-ke Thong ke khao sat
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from lms_service.dependencies import get_db, get_current_user, require_platform_role
from lms_service.schemas.chung_chi import (
    ChungChiResponse,
    KhaoSatCreate,
    KhaoSatResponse,
    ThongKeKhaoSat,
)
from lms_service.services.chung_chi_service import ChungChiService
from shared.auth import TokenPayload

router = APIRouter(tags=["Chứng chỉ & Khảo sát"])


@router.get("/chung-chi/cua-toi")
async def chung_chi_cua_toi(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    """Danh sách chứng chỉ của user hiện tại."""
    service = ChungChiService(db)
    result = await service.chung_chi_cua_toi(user, page, page_size)
    return {
        "success": True,
        "data": [ChungChiResponse(**item).model_dump(mode="json") for item in result["items"]],
        "pagination": result["pagination"],
    }


@router.get("/chung-chi/xac-minh/{ma_chung_chi}")
async def xac_minh_chung_chi(
    ma_chung_chi: str,
    db: AsyncSession = Depends(get_db),
):
    """Xác minh chứng chỉ bằng mã. KHÔNG yêu cầu đăng nhập (public)."""
    service = ChungChiService(db)
    data = await service.xac_minh(ma_chung_chi)
    return {"success": True, "data": ChungChiResponse(**data).model_dump(mode="json")}


@router.get("/chung-chi/{id}/tai")
async def tai_chung_chi(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    """Tải chứng chỉ PDF."""
    service = ChungChiService(db)
    pdf_bytes, filename = await service.tai_chung_chi(id, user)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{filename}"'},
    )


@router.post("/khao-sat", status_code=201)
async def gui_khao_sat(
    data: KhaoSatCreate,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    """Gửi khảo sát sau khi hoàn thành khóa học."""
    service = ChungChiService(db)
    ks = await service.gui_khao_sat(data, user)
    return {
        "success": True,
        "data": KhaoSatResponse.model_validate(ks).model_dump(mode="json"),
        "message": "Gửi khảo sát thành công",
    }


@router.get("/khoa-hoc/{khoa_hoc_id}/khao-sat/thong-ke")
async def thong_ke_khao_sat(
    khoa_hoc_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(require_platform_role("GIANG_VIEN", "QT_DAO_TAO")),
):
    """Thống kê khảo sát của khóa học."""
    service = ChungChiService(db)
    data = await service.thong_ke_khao_sat(khoa_hoc_id, user)
    return {"success": True, "data": ThongKeKhaoSat(**data).model_dump(mode="json")}
