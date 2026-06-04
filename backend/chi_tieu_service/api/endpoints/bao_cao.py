"""
chi_tieu_service/api/endpoints/bao_cao.py
=========================================
Báo cáo rà soát theo tháng + lũy kế năm. (Export Excel: TODO giai đoạn sau.)
Phạm vi xem giới hạn theo vai trò: người theo dõi/Trưởng ĐV chỉ xem đơn vị mình;
QT chỉ tiêu / LĐ Chi cục / admin xem toàn Chi cục.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from chi_tieu_service.dependencies import get_db, get_current_user
from chi_tieu_service.services.bao_cao_service import BaoCaoService
from chi_tieu_service.services.guards import allowed_view_don_vi_ids, loc_don_vi_theo_pham_vi
from shared.auth import TokenPayload

router = APIRouter(prefix="/bao-cao", tags=["Chỉ tiêu - Báo cáo"])


@router.get("/pham-vi-cua-toi")
async def pham_vi_cua_toi(
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    """Phạm vi đơn vị user được xem (FE dùng để giới hạn picker)."""
    allowed = await allowed_view_don_vi_ids(db, user)
    return {
        "success": True,
        "data": {"toan_chi_cuc": allowed is None, "don_vi_ids": allowed or []},
    }


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
    allowed = await allowed_view_don_vi_ids(db, user)
    don_vi_ids = loc_don_vi_theo_pham_vi(allowed, don_vi_id)
    data = await BaoCaoService(db).ra_soat(thang, nam, linh_vuc_id, don_vi_ids=don_vi_ids)
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
    allowed = await allowed_view_don_vi_ids(db, user)
    don_vi_ids = loc_don_vi_theo_pham_vi(allowed, don_vi_id)
    data = await BaoCaoService(db).luy_ke(nam=nam, don_vi_ids=don_vi_ids, thang=thang)
    return {"success": True, "data": data}
