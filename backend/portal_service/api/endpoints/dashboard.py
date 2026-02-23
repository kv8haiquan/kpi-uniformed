"""
portal_service/api/endpoints/dashboard.py
==========================================
API endpoints cho Dashboard Portal.

Routes:
  GET /dashboard/summary     — Tổng hợp widget trang chủ (tất cả CBCC)
  GET /dashboard/lanh-dao    — Thống kê tháng dành cho Lãnh đạo
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query

from portal_service.dependencies import (
    CurrentUserDep,
    DatabaseDep,
    require_lanh_dao,
)
from portal_service.schemas.base import SuccessResponse
from portal_service.schemas.dashboard import LanhDaoDashboard, PortalDashboardSummary
from portal_service.services import dashboard_service

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get(
    "/summary",
    response_model=SuccessResponse[PortalDashboardSummary],
    summary="Dashboard trang chủ Portal",
)
async def get_summary(
    db: DatabaseDep,
    user: CurrentUserDep,
):
    """Tổng hợp dữ liệu cho widget trang chủ Portal.

    Trả về:
      - Số bài viết / tài liệu mới trong 7 ngày qua
      - Danh sách bài ghim (tối đa 3)
      - 5 bài viết mới nhất (không ghim)
    """
    summary = await dashboard_service.get_portal_summary(db, user)
    return SuccessResponse(
        data=summary,
        message="Thao tác thành công",
    )


@router.get(
    "/lanh-dao",
    response_model=SuccessResponse[LanhDaoDashboard],
    summary="Dashboard thống kê Lãnh đạo",
)
async def get_lanh_dao(
    db: DatabaseDep,
    user=Depends(require_lanh_dao()),
    thang: Optional[int] = Query(None, ge=1, le=12, description="Tháng (1-12)"),
    nam: Optional[int] = Query(None, ge=2020, le=2100, description="Năm"),
):
    """Thống kê Portal theo tháng dành cho Lãnh đạo.

    Mặc định: tháng hiện tại.
    Trả về: thống kê tin tức + tài liệu (tổng quan + trong tháng + breakdown chuyên mục).

    Lưu ý: Đây chỉ là phần Portal. Dashboard lãnh đạo tổng hợp đa module
    (LMS, Forum, Legal) sẽ được tổng hợp ở tầng frontend.
    """
    now = datetime.now()
    t = thang or now.month
    n = nam or now.year

    summary = await dashboard_service.get_lanh_dao_summary(db, thang=t, nam=n)
    return SuccessResponse(
        data=summary,
        message=f"Thống kê tháng {t}/{n}",
    )
