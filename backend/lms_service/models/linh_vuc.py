"""
lms_service/models/linh_vuc.py
==============================
Model linh vuc nghiep vu — bang lms.linh_vuc.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from lms_service.models.base import Base


class LinhVuc(Base):
    """Linh vuc nghiep vu — bang lms.linh_vuc."""

    __tablename__ = "linh_vuc"
    __table_args__ = {"schema": "lms"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    ma_linh_vuc: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    ten_linh_vuc: Mapped[str] = mapped_column(String(200), nullable=False)
    mo_ta: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    thu_tu: Mapped[Optional[int]] = mapped_column(Integer, server_default="0")
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text("true"))
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP")
    )
