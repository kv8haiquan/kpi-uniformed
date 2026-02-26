"""
common_service/api/internal/kpi_log.py
=======================================
Internal API cho KPI Integration Log.
Prefix: /internal/v1/kpi-log
Auth: X-Internal-Key header

Endpoints:
  POST /kpi-log        — Ghi 1 log (UPSERT)
  POST /kpi-log/bulk   — Ghi hang loat
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from common_service.dependencies import DatabaseDep, verify_internal_key
from common_service.schemas.base import SuccessResponse
from common_service.schemas.kpi_log import KpiLogCreateInternal, KpiLogResponse
from common_service.services import kpi_log_service

router = APIRouter(
    prefix="/kpi-log",
    tags=["KPI Log Internal"],
    dependencies=[Depends(verify_internal_key)],
)


@router.post("", response_model=SuccessResponse[KpiLogResponse], status_code=201)
async def ghi_log(
    data: KpiLogCreateInternal,
    db: DatabaseDep,
):
    """Ghi 1 KPI log — UPSERT.

    Neu da co (cong_chuc_id, thang, nam, module) → UPDATE metrics.
    Neu chua co → INSERT moi.
    """
    log = await kpi_log_service.ghi_log(db, data)
    return SuccessResponse(
        data=KpiLogResponse.model_validate(log),
        message="Ghi KPI log thành công",
    )


@router.post("/bulk", response_model=SuccessResponse[dict], status_code=201)
async def ghi_log_hang_loat(
    data_list: list[KpiLogCreateInternal],
    db: DatabaseDep,
):
    """Ghi KPI log hang loat — bulk UPSERT cho cron job cuoi thang."""
    count = await kpi_log_service.ghi_log_hang_loat(db, data_list)
    return SuccessResponse(
        data={"created_count": count},
        message=f"Đã ghi {count} KPI log",
    )
