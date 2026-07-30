"""
lms_service/models/cau_hoi_dgnl.py
==================================
Model ngan hang cau hoi rieng cho DGNL — bang lms.cau_hoi_dgnl.
Tach biet hoan toan voi cau_hoi cua khoa hoc.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, Numeric, String, Text, ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from lms_service.models.base import Base

if TYPE_CHECKING:
    from lms_service.models.linh_vuc import LinhVuc


class CauHoiDgnl(Base):
    """Ngan hang cau hoi DGNL — bang lms.cau_hoi_dgnl."""

    __tablename__ = "cau_hoi_dgnl"
    __table_args__ = {"schema": "lms"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )

    # FK den linh_vuc — BAT BUOC
    linh_vuc_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("lms.linh_vuc.id"), nullable=False
    )

    # Noi dung
    noi_dung: Mapped[str] = mapped_column(Text, nullable=False)
    giai_thich: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Loai: TRAC_NGHIEM_1, TRAC_NGHIEM_NHIEU, DUNG_SAI, TU_LUAN
    loai: Mapped[str] = mapped_column(String(50), nullable=False)

    # Dap an (JSONB)
    dap_an: Mapped[dict] = mapped_column(JSONB, nullable=False)

    # Diem va do kho
    diem: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), server_default="1.0")
    do_kho: Mapped[Optional[str]] = mapped_column(String(20), server_default="TRUNG_BINH")

    # Nguoi tao
    nguoi_tao_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("public.cong_chuc.id"), nullable=True
    )

    # Flags
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text("true"))

    # Timestamps
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP")
    )

    # Relationships
    linh_vuc: Mapped[LinhVuc] = relationship(lazy="selectin")
