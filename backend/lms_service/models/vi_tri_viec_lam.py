"""
lms_service/models/vi_tri_viec_lam.py
=====================================
Model vi tri viec lam — bang lms.vi_tri_viec_lam.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from lms_service.models.base import Base


class ViTriViecLam(Base):
    """Vi tri viec lam — bang lms.vi_tri_viec_lam."""

    __tablename__ = "vi_tri_viec_lam"
    __table_args__ = {"schema": "lms"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    ma_vi_tri: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    ten_vi_tri: Mapped[str] = mapped_column(String(200), nullable=False)
    mo_ta: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    linh_vuc_ids: Mapped[Optional[list]] = mapped_column(JSONB, server_default="'[]'")
    thu_tu: Mapped[Optional[int]] = mapped_column(Integer, server_default="0")
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text("true"))
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=text("CURRENT_TIMESTAMP")
    )
