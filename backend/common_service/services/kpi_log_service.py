"""
common_service/services/kpi_log_service.py
============================================
Business logic cho KPI Integration Log.

NGUYEN TAC VANG: Du lieu KPI integration = CHI THAM KHAO.
KHONG tu dong thay doi diem KPI. Hien thi de lanh dao tham khao.

Public:
  - doc_kpi_log: doc log ca nhan
  - doc_theo_don_vi: tong hop theo don vi

Internal:
  - ghi_log: UPSERT 1 record
  - ghi_log_hang_loat: bulk UPSERT
"""

from __future__ import annotations

import uuid
from collections import defaultdict
from datetime import datetime
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from common_service.models.kpi_integration_log import KpiIntegrationLog
from common_service.models.base import CongChucRef
from common_service.schemas.kpi_log import (
    ALLOWED_KPI_MODULES,
    KpiLogCreateInternal,
    KpiLogDonViSummary,
    KpiLogModuleSummary,
)


# ---------------------------------------------------------------------------
# Public methods
# ---------------------------------------------------------------------------


async def doc_kpi_log(
    db: AsyncSession,
    cong_chuc_id: uuid.UUID,
    thang: int,
    nam: int,
    *,
    user_id: str,
    user_don_vi_id: Optional[str] = None,
    is_lanh_dao: bool = False,
    is_admin: bool = False,
) -> list[KpiIntegrationLog]:
    """Doc KPI log ca nhan.

    Quyen:
      - CBCC doc cua minh
      - Lanh dao doc CBCC don vi minh
      - ADMIN doc tat ca
    """
    # Kiem tra quyen
    target_str = str(cong_chuc_id)
    if not is_admin and target_str != user_id:
        # Lanh dao chi doc CBCC trong don vi minh
        if is_lanh_dao and user_don_vi_id:
            # Kiem tra cong_chuc thuoc don vi cua lanh dao
            cc_q = select(CongChucRef.don_vi_id).where(CongChucRef.id == cong_chuc_id)
            result = await db.execute(cc_q)
            cc_don_vi = result.scalar_one_or_none()
            if cc_don_vi is None or str(cc_don_vi) != user_don_vi_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "success": False,
                        "error": {
                            "code": "PERM_001",
                            "message": "Bạn chỉ có thể xem KPI log của CBCC trong đơn vị mình",
                        },
                    },
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "success": False,
                    "error": {
                        "code": "PERM_001",
                        "message": "Bạn chỉ có thể xem KPI log của mình",
                    },
                },
            )

    q = (
        select(KpiIntegrationLog)
        .where(
            KpiIntegrationLog.cong_chuc_id == cong_chuc_id,
            KpiIntegrationLog.thang == thang,
            KpiIntegrationLog.nam == nam,
        )
        .order_by(KpiIntegrationLog.module)
    )
    result = await db.execute(q)
    return list(result.scalars().all())


async def doc_theo_don_vi(
    db: AsyncSession,
    don_vi_id: uuid.UUID,
    thang: int,
    nam: int,
) -> KpiLogDonViSummary:
    """Tong hop KPI log theo don vi — dashboard lanh dao.

    Tinh metrics trung binh cho moi module.
    """
    # Lay ten don vi
    from common_service.models.base import DonViRef
    dv_q = select(DonViRef.ten_don_vi).where(DonViRef.id == don_vi_id)
    ten_don_vi = (await db.execute(dv_q)).scalar_one_or_none()

    # Dem tong CBCC active trong don vi
    cc_count_q = (
        select(func.count())
        .select_from(CongChucRef)
        .where(CongChucRef.don_vi_id == don_vi_id, CongChucRef.is_active == True)  # noqa: E712
    )
    tong_cbcc = (await db.execute(cc_count_q)).scalar() or 0

    # Lay tat ca logs trong don vi + thang + nam
    log_q = (
        select(KpiIntegrationLog)
        .join(CongChucRef, KpiIntegrationLog.cong_chuc_id == CongChucRef.id)
        .where(
            CongChucRef.don_vi_id == don_vi_id,
            CongChucRef.is_active == True,  # noqa: E712
            KpiIntegrationLog.thang == thang,
            KpiIntegrationLog.nam == nam,
        )
    )
    result = await db.execute(log_q)
    logs = list(result.scalars().all())

    # Tong hop theo module
    module_data: dict[str, list[KpiIntegrationLog]] = defaultdict(list)
    for log in logs:
        module_data[log.module].append(log)

    modules = []
    for module_name, module_logs in sorted(module_data.items()):
        # Tinh trung binh metrics
        all_metrics = [log.metrics for log in module_logs if log.metrics]
        metrics_tb = _tinh_trung_binh_metrics(all_metrics)

        # Tinh trung binh diem_quy_doi
        diem_list = [float(log.diem_quy_doi) for log in module_logs if log.diem_quy_doi is not None]
        diem_tb = sum(diem_list) / len(diem_list) if diem_list else None

        modules.append(KpiLogModuleSummary(
            module=module_name,
            so_cbcc=len(module_logs),
            metrics_trung_binh=metrics_tb,
            diem_quy_doi_trung_binh=round(diem_tb, 2) if diem_tb is not None else None,
        ))

    return KpiLogDonViSummary(
        don_vi_id=don_vi_id,
        ten_don_vi=ten_don_vi,
        thang=thang,
        nam=nam,
        tong_cbcc=tong_cbcc,
        modules=modules,
    )


# ---------------------------------------------------------------------------
# Internal methods
# ---------------------------------------------------------------------------


async def ghi_log(
    db: AsyncSession,
    data: KpiLogCreateInternal,
) -> KpiIntegrationLog:
    """UPSERT 1 KPI log.

    Neu da co (cong_chuc_id, thang, nam, module) → UPDATE metrics.
    Neu chua co → INSERT.
    """
    _validate_module(data.module)

    # Tim record hien tai
    q = select(KpiIntegrationLog).where(
        KpiIntegrationLog.cong_chuc_id == data.cong_chuc_id,
        KpiIntegrationLog.thang == data.thang,
        KpiIntegrationLog.nam == data.nam,
        KpiIntegrationLog.module == data.module,
    )
    result = await db.execute(q)
    existing = result.scalar_one_or_none()

    if existing:
        # UPDATE
        existing.metrics = data.metrics
        if data.diem_quy_doi is not None:
            existing.diem_quy_doi = data.diem_quy_doi
        existing.synced_at = datetime.utcnow()
        await db.flush()
        await db.refresh(existing)
        return existing
    else:
        # INSERT
        log = KpiIntegrationLog(
            cong_chuc_id=data.cong_chuc_id,
            thang=data.thang,
            nam=data.nam,
            module=data.module,
            metrics=data.metrics,
            diem_quy_doi=data.diem_quy_doi,
        )
        db.add(log)
        await db.flush()
        await db.refresh(log)
        return log


async def ghi_log_hang_loat(
    db: AsyncSession,
    data_list: list[KpiLogCreateInternal],
) -> int:
    """Bulk UPSERT cho cron job cuoi thang.

    Returns:
        So luong records da ghi.
    """
    count = 0
    for data in data_list:
        await ghi_log(db, data)
        count += 1
    await db.flush()
    return count


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _validate_module(module: str) -> None:
    """Validate module KPI."""
    if module not in ALLOWED_KPI_MODULES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "error": {
                    "code": "CMN_ERR_004",
                    "message": f"Module không hợp lệ: {module}. "
                    f"Chấp nhận: {', '.join(sorted(ALLOWED_KPI_MODULES))}",
                },
            },
        )


def _tinh_trung_binh_metrics(all_metrics: list[dict]) -> dict:
    """Tinh trung binh cac metrics tu nhieu records.

    Chi tinh trung binh cho cac key co gia tri la so (int/float).
    """
    if not all_metrics:
        return {}

    totals: dict[str, float] = defaultdict(float)
    counts: dict[str, int] = defaultdict(int)

    for m in all_metrics:
        for key, val in m.items():
            if isinstance(val, (int, float)):
                totals[key] += val
                counts[key] += 1

    result = {}
    for key in totals:
        if counts[key] > 0:
            avg = totals[key] / counts[key]
            result[key] = round(avg, 2)
    return result
