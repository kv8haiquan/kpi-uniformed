"""
chi_tieu_service/models/danh_muc_chi_tieu.py
============================================
Model danh muc chi tieu — bang chi_tieu.danh_muc_chi_tieu.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from chi_tieu_service.models.base import Base


class DanhMucChiTieu(Base):
    """Danh muc chi tieu — bang chi_tieu.danh_muc_chi_tieu."""

    __tablename__ = "danh_muc_chi_tieu"
    __table_args__ = {"schema": "chi_tieu"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    linh_vuc_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("chi_tieu.linh_vuc.id"), nullable=False
    )
    ma_chi_tieu: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    ten_chi_tieu: Mapped[str] = mapped_column(String(500), nullable=False)
    don_vi_tinh: Mapped[str] = mapped_column(String(50), nullable=False)
    # SO_NGUYEN | THAP_PHAN | PHAN_TRAM
    kieu_du_lieu: Mapped[str] = mapped_column(String(20), nullable=False, server_default="THAP_PHAN")
    co_phan_dau: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text("false"))
    van_ban_giao: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    mo_ta: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    thu_tu: Mapped[Optional[int]] = mapped_column(Integer, server_default="0")
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text("true"))
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=text("CURRENT_TIMESTAMP")
    )
