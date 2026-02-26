"""
common_service/models/kpi_integration_log.py
=============================================
Tich hop diem KPI tu cac module (LMS, Forum, Legal).
Bang: common.kpi_integration_log

UniqueConstraint: (cong_chuc_id, thang, nam, module)
CheckConstraint: thang BETWEEN 1 AND 12, nam >= 2025
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, Optional

from sqlalchemy import CheckConstraint, ForeignKey, Integer, Numeric, String, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, CongChucRef


class KpiIntegrationLog(Base):
    """Tich hop diem KPI tu cac module.

    Moi record la diem KPI cua 1 cong_chuc trong 1 thang/nam tu 1 module.
    Composite unique: (cong_chuc_id, thang, nam, module) — moi module chi co
    1 record/thang/nguoi.

    metrics la JSONB chua chi tiet tu module:
      LMS: {"khoa_hoc_hoan_thanh": 2, "gio_hoc": 15.5, "diem_tb_bkt": 85}
      Forum: {"chu_de_tao": 3, "tra_loi": 12, "upvote_nhan": 8}
      Legal: {"van_ban_doc": 10, "quiz_dat": 5, "diem_tb": 90}
    """

    __tablename__ = "kpi_integration_log"
    __table_args__ = (
        UniqueConstraint(
            "cong_chuc_id", "thang", "nam", "module",
            name="uq_common_kpi_cc_thang_nam_module",
        ),
        CheckConstraint("thang BETWEEN 1 AND 12", name="ck_common_kpi_thang"),
        CheckConstraint("nam >= 2025", name="ck_common_kpi_nam"),
        {"schema": "common"},
    )

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )

    # Cong chuc — FK cross-schema den public.cong_chuc
    cong_chuc_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("public.cong_chuc.id"),
        nullable=False,
    )

    # Thoi gian: thang (1-12), nam (>= 2025)
    thang: Mapped[int] = mapped_column(Integer, nullable=False)
    nam: Mapped[int] = mapped_column(Integer, nullable=False)

    # Module: LMS, FORUM, LEGAL
    module: Mapped[str] = mapped_column(String(50), nullable=False)

    # Chi tiet metrics tu module (JSONB)
    metrics: Mapped[Any] = mapped_column(JSONB, nullable=False)

    # Diem quy doi KPI (NUMERIC 5,2)
    diem_quy_doi: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 2), nullable=True
    )

    # Thoi diem dong bo
    synced_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"), nullable=False
    )

    # --- Relationships ---
    cong_chuc: Mapped[Optional[CongChucRef]] = relationship(
        "CongChucRef",
        foreign_keys=[cong_chuc_id],
        lazy="joined",
    )
