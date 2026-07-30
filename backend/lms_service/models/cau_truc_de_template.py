"""
lms_service/models/cau_truc_de_template.py
==========================================
Model mau cau truc de thi DGNL — bang lms.cau_truc_de_template.

Luu cau truc de (so cau de/TB/kho theo vi tri x linh vuc) lam mau de ap dung
nhanh cho cac ky thi sau.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, String, Text, ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from lms_service.models.base import Base


class CauTrucDeTemplate(Base):
    """Mau cau truc de — bang lms.cau_truc_de_template."""

    __tablename__ = "cau_truc_de_template"
    __table_args__ = {"schema": "lms"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    ten_template: Mapped[str] = mapped_column(String(200), nullable=False)
    mo_ta: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    nguoi_tao_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("public.cong_chuc.id"), nullable=False
    )
    # [{vi_tri_id, linh_vuc_id, so_cau_de, so_cau_trung_binh, so_cau_kho}]
    cau_truc: Mapped[Optional[list]] = mapped_column(JSONB, server_default="'[]'")
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text("true"))
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP")
    )
