"""
lms_service/models/chung_chi.py
===============================
Model chung chi / chung nhan hoan thanh — bang lms.chung_chi.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, Numeric, String, Text, ForeignKey, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from lms_service.models.base import Base

if TYPE_CHECKING:
    from lms_service.models.khoa_hoc import KhoaHoc


class ChungChi(Base):
    """Chung chi / Chung nhan hoan thanh — bang lms.chung_chi."""

    __tablename__ = "chung_chi"
    __table_args__ = (
        UniqueConstraint("cong_chuc_id", "khoa_hoc_id", name="uq_lms_cc_kh"),
        {"schema": "lms"},
    )

    # PK
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )

    # FK den public.cong_chuc — KHONG tao relationship
    cong_chuc_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("public.cong_chuc.id"), nullable=False
    )

    # FK noi bo
    khoa_hoc_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("lms.khoa_hoc.id"), nullable=False
    )

    # Thong tin chung chi
    ma_chung_chi: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    ten_chung_chi: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    diem_dat: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    ngay_cap: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=text("CURRENT_TIMESTAMP")
    )

    # Nguoi cap — FK den public.cong_chuc
    nguoi_cap_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("public.cong_chuc.id"), nullable=True
    )

    # File chung chi
    file_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships noi bo
    khoa_hoc: Mapped[KhoaHoc] = relationship(
        back_populates="chung_chi_list", lazy="selectin"
    )
