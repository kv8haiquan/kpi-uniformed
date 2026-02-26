"""
common_service/schemas/kpi_log.py
==================================
Pydantic schemas cho KPI Integration Log.

Public:
  - KpiLogResponse: chi tiet 1 log
  - KpiLogDonViSummary: tong hop theo don vi

Internal:
  - KpiLogCreateInternal: ghi 1 log (UPSERT)
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Gia tri hop le
# ---------------------------------------------------------------------------

ALLOWED_KPI_MODULES = {"LMS", "FORUM", "LEGAL"}


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class KpiLogResponse(BaseModel):
    """Chi tiet 1 KPI integration log."""

    id: uuid.UUID
    cong_chuc_id: uuid.UUID
    thang: int
    nam: int
    module: str
    metrics: Any
    diem_quy_doi: Optional[Decimal] = None
    synced_at: datetime

    model_config = {"from_attributes": True}


class KpiLogModuleSummary(BaseModel):
    """Tong hop metrics trung binh cho 1 module trong 1 don vi."""

    module: str
    so_cbcc: int = Field(description="So CBCC co log trong module nay")
    metrics_trung_binh: dict = Field(description="Trung binh cac metrics")
    diem_quy_doi_trung_binh: Optional[float] = None


class KpiLogDonViSummary(BaseModel):
    """Tong hop KPI log theo don vi — dung cho dashboard lanh dao."""

    don_vi_id: uuid.UUID
    ten_don_vi: Optional[str] = None
    thang: int
    nam: int
    tong_cbcc: int
    modules: list[KpiLogModuleSummary] = []


# ---------------------------------------------------------------------------
# Internal API schemas
# ---------------------------------------------------------------------------


class KpiLogCreateInternal(BaseModel):
    """Ghi 1 KPI log — Internal API (UPSERT)."""

    cong_chuc_id: uuid.UUID = Field(description="UUID cong chuc")
    thang: int = Field(ge=1, le=12, description="Thang (1-12)")
    nam: int = Field(ge=2025, description="Nam (>= 2025)")
    module: str = Field(description="LMS, FORUM, LEGAL")
    metrics: dict = Field(description="Chi tiet metrics (JSONB)")
    diem_quy_doi: Optional[Decimal] = Field(default=None, description="Diem quy doi KPI (0-100)")
