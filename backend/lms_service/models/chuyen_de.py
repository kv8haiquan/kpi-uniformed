"""
lms_service/models/chuyen_de.py
===============================
Model chuyen de dao tao — bang lms.chuyen_de.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, Integer, String, Text, ForeignKey, DateTime, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from lms_service.models.base import Base

if TYPE_CHECKING:
    from lms_service.models.khoa_hoc import KhoaHoc
    from lms_service.models.cau_hoi import CauHoi


class ChuyenDe(Base):
    """Chuyen de dao tao — bang lms.chuyen_de."""

    __tablename__ = "chuyen_de"
    __table_args__ = {"schema": "lms"}

    # PK
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )

    # Thong tin chuyen de
    ma_chuyen_de: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    ten_chuyen_de: Mapped[str] = mapped_column(String(200), nullable=False)
    mo_ta: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    anh_dai_dien: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    thu_tu: Mapped[Optional[int]] = mapped_column(Integer, server_default="0")
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text("true"))

    # FK den public.cong_chuc — KHONG tao relationship (readonly table)
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("public.cong_chuc.id"), nullable=True
    )

    # Timestamps
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP")
    )

    # Relationships noi bo
    khoa_hoc_list: Mapped[list[KhoaHoc]] = relationship(
        back_populates="chuyen_de", lazy="selectin"
    )
    cau_hoi_list: Mapped[list[CauHoi]] = relationship(
        back_populates="chuyen_de", lazy="selectin"
    )
