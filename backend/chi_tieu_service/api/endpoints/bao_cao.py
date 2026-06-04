"""
chi_tieu_service/api/endpoints/bao_cao.py
=========================================
Báo cáo rà soát theo tháng + lũy kế năm. (Export Excel: TODO giai đoạn sau.)
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from chi_tieu_service.dependencies import get_db, get_current_user
from chi_tieu_service.services.bao_cao_service import BaoCaoService
from shared.auth import TokenPayload

router = APIRouter(prefix="/bao-cao", tags=["Chỉ tiêu - Báo cáo"])


@router.get("/ra-soat")
async def ra_soat(
    thang: int = Query(..., ge=1, le=12),
    nam: int = Query(..., ge=2025),
    linh_vuc_id: Optional[UUID] = Query(None),
    don_vi_id: Optional[UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    """Rà soát theo tháng — cấu trúc lồng linh_vuc → chi_tieu → dong_don_vi (lũy kế cắt theo tháng)."""
    data = await BaoCaoService(db).ra_soat(thang, nam, linh_vuc_id, don_vi_id)
    return {"success": True, "data": data}


@router.get("/luy-ke")
async def luy_ke(
    nam: int = Query(..., ge=2025),
    don_vi_id: Optional[UUID] = Query(None),
    thang: Optional[int] = Query(None, ge=1, le=12),
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    """Lũy kế năm theo đơn vị (Đạt% năm từng chỉ tiêu/mức). Cắt đến `thang` nếu truyền."""
    data = await BaoCaoService(db).luy_ke(nam=nam, don_vi_id=don_vi_id, thang=thang)
    return {"success": True, "data": data}
