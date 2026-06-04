"""
chi_tieu_service/models/giao_nam.py
===================================
Model chi tieu giao nam cho don vi — bang chi_tieu.giao_nam.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from chi_tieu_service.models.base import Base


class GiaoNam(Base):
    """Chi tieu giao nam cho don vi — bang chi_tieu.giao_nam."""

    __tablename__ = "giao_nam"
    __table_args__ = {"schema": "chi_tieu"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    don_vi_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("public.don_vi.id"), nullable=False
    )
    chi_tieu_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("chi_tieu.danh_muc_chi_tieu.id"), nullable=False
    )
    nam: Mapped[int] = mapped_column(Integer, nullable=False)
    # PHAP_LENH | PHAN_DAU
    loai_muc: Mapped[str] = mapped_column(String(20), nullable=False, server_default="PHAP_LENH")
    gia_tri_giao: Mapped[Decimal] = mapped_column(Numeric(18, 3), nullable=False)
    luy_ke_dau_ky: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 3), server_default="0")
    nguoi_giao_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("public.cong_chuc.id"), nullable=True
    )
    ghi_chu: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=text("CURRENT_TIMESTAMP")
    )
    is_deleted: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text("false"))
