"""
lms_service/models/khao_sat.py
==============================
Model khao sat sau khoa hoc — bang lms.khao_sat.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from lms_service.models.base import Base

if TYPE_CHECKING:
    from lms_service.models.khoa_hoc import KhoaHoc


class KhaoSat(Base):
    """Khao sat sau khoa hoc — bang lms.khao_sat."""

    __tablename__ = "khao_sat"
    __table_args__ = (
        UniqueConstraint("cong_chuc_id", "khoa_hoc_id", name="uq_lms_ks_cc_kh"),
        {"schema": "lms"},
    )

    # PK
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )

    # FK noi bo
    khoa_hoc_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("lms.khoa_hoc.id"), nullable=False
    )

    # FK den public.cong_chuc — KHONG tao relationship
    cong_chuc_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("public.cong_chuc.id"), nullable=False
    )

    # Noi dung khao sat (JSONB)
    noi_dung: Mapped[dict] = mapped_column(JSONB, nullable=False)

    # Timestamps
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP")
    )

    # Relationships noi bo
    khoa_hoc: Mapped[KhoaHoc] = relationship(
        back_populates="khao_sat_list", lazy="selectin"
    )
