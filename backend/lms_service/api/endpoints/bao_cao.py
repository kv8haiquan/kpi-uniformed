"""
lms_service/api/endpoints/bao_cao.py
====================================
API endpoints cho bao cao va dashboard.

Endpoints:
  GET /bao-cao/ca-nhan                   Bao cao ca nhan
  GET /bao-cao/don-vi/{don_vi_id}        Bao cao don vi
  GET /bao-cao/khoa-hoc/{khoa_hoc_id}    Bao cao khoa hoc
  GET /dashboard/summary                  Dashboard widget
"""

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from lms_service.dependencies import get_db, get_current_user, require_platform_role
from lms_service.schemas.bao_cao import (
    BaoCaoCaNhan,
    BaoCaoDonVi,
    BaoCaoKhoaHoc,
    DashboardSummary,
)
from lms_service.services.bao_cao_service import BaoCaoService
from shared.auth import TokenPayload

router = APIRouter(tags=["Báo cáo & Dashboard"])


@router.get("/bao-cao/ca-nhan")
async def bao_cao_ca_nhan(
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    """Báo cáo cá nhân: khóa đang học, hoàn thành, chứng chỉ, giờ học."""
    service = BaoCaoService(db)
    data = await service.bao_cao_ca_nhan(user)
    return {"success": True, "data": BaoCaoCaNhan(**data).model_dump(mode="json")}


@router.get("/bao-cao/don-vi/{don_vi_id}")
async def bao_cao_don_vi(
    don_vi_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    """Báo cáo đơn vị. Lãnh đạo chỉ xem đơn vị mình, QT xem tất cả."""
    service = BaoCaoService(db)
    data = await service.bao_cao_don_vi(don_vi_id, user)
    return {"success": True, "data": BaoCaoDonVi(**data).model_dump(mode="json")}


@router.get("/bao-cao/khoa-hoc/{khoa_hoc_id}")
async def bao_cao_khoa_hoc(
    khoa_hoc_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(require_platform_role("GIANG_VIEN", "QT_DAO_TAO")),
):
    """Báo cáo khóa học: số đăng ký, phân bổ trạng thái, điểm TB."""
    service = BaoCaoService(db)
    data = await service.bao_cao_khoa_hoc(khoa_hoc_id, user)
    return {"success": True, "data": BaoCaoKhoaHoc(**data).model_dump(mode="json")}


@router.get("/dashboard/summary")
async def dashboard_summary(
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    """Dashboard summary cho widget frontend."""
    service = BaoCaoService(db)
    data = await service.dashboard_summary(user)
    return {"success": True, "data": DashboardSummary(**data).model_dump(mode="json")}
