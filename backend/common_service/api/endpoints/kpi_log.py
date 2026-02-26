"""
common_service/api/endpoints/kpi_log.py
========================================
Public API cho KPI Integration Log.
Prefix: /api/common/v1/kpi-log
Auth: JWT Bearer token

Endpoints:
  GET /kpi-log/{cong_chuc_id}        — Doc log ca nhan
  GET /kpi-log/don-vi/{don_vi_id}    — Doc log theo don vi
"""

from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Query

from common_service.dependencies import CurrentUserDep, DatabaseDep
from common_service.schemas.base import SuccessResponse
from common_service.schemas.kpi_log import KpiLogDonViSummary, KpiLogResponse
from common_service.services import kpi_log_service

router = APIRouter(prefix="/kpi-log", tags=["KPI Integration"])


@router.get(
    "/don-vi/{don_vi_id}",
    response_model=SuccessResponse[KpiLogDonViSummary],
)
async def doc_theo_don_vi(
    don_vi_id: uuid.UUID,
    db: DatabaseDep,
    user: CurrentUserDep,
    thang: int = Query(default=None, ge=1, le=12, description="Thang (1-12)"),
    nam: int = Query(default=None, ge=2025, description="Nam"),
):
    """Tong hop KPI log theo don vi — dashboard lanh dao.

    Quyen: Lanh dao (don vi minh), QT_DAO_TAO, QT_NOI_DUNG, ADMIN.
    """
    # Default thang/nam hien tai
    now = datetime.utcnow()
    if thang is None:
        thang = now.month
    if nam is None:
        nam = now.year

    # Kiem tra quyen
    is_admin = user.vai_tro == "SUPER_ADMIN" or user.is_admin
    has_role = bool(
        set(user.platform_roles or []).intersection({"QT_DAO_TAO", "QT_NOI_DUNG"})
    )
    if not is_admin and not has_role:
        if not user.is_lanh_dao:
            from fastapi import HTTPException, status
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "success": False,
                    "error": {
                        "code": "PERM_001",
                        "message": "Chỉ lãnh đạo, QT_DAO_TAO, QT_NOI_DUNG hoặc ADMIN mới có quyền xem",
                    },
                },
            )
        # Lanh dao chi xem don vi minh
        if user.don_vi_id and str(don_vi_id) != user.don_vi_id:
            from fastapi import HTTPException, status
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "success": False,
                    "error": {
                        "code": "PERM_001",
                        "message": "Bạn chỉ có thể xem KPI log đơn vị của mình",
                    },
                },
            )

    data = await kpi_log_service.doc_theo_don_vi(db, don_vi_id, thang, nam)
    return SuccessResponse(data=data)


@router.get(
    "/{cong_chuc_id}",
    response_model=SuccessResponse[list[KpiLogResponse]],
)
async def doc_kpi_log(
    cong_chuc_id: uuid.UUID,
    db: DatabaseDep,
    user: CurrentUserDep,
    thang: int = Query(default=None, ge=1, le=12, description="Thang (1-12)"),
    nam: int = Query(default=None, ge=2025, description="Nam"),
):
    """Doc KPI log ca nhan.

    Quyen: CBCC doc cua minh, Lanh dao doc CBCC don vi minh, ADMIN doc tat ca.
    """
    now = datetime.utcnow()
    if thang is None:
        thang = now.month
    if nam is None:
        nam = now.year

    is_admin = user.vai_tro == "SUPER_ADMIN" or user.is_admin
    logs = await kpi_log_service.doc_kpi_log(
        db, cong_chuc_id, thang, nam,
        user_id=user.sub,
        user_don_vi_id=user.don_vi_id,
        is_lanh_dao=user.is_lanh_dao,
        is_admin=is_admin,
    )
    return SuccessResponse(
        data=[KpiLogResponse.model_validate(log) for log in logs],
    )
