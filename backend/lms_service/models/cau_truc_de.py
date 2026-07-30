"""
lms_service/models/cau_truc_de.py
=================================
Model cau truc de thi theo vi tri — bang lms.cau_truc_de.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, Integer, ForeignKey, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from lms_service.models.base import Base

if TYPE_CHECKING:
    from lms_service.models.ky_thi import KyThi
    from lms_service.models.vi_tri_viec_lam import ViTriViecLam
    from lms_service.models.linh_vuc import LinhVuc


class CauTrucDe(Base):
    """Cau truc de thi theo vi tri — bang lms.cau_truc_de."""

    __tablename__ = "cau_truc_de"
    __table_args__ = (
        UniqueConstraint("ky_thi_id", "vi_tri_id", "linh_vuc_id", name="uq_cau_truc_de_kt_vt_lv"),
        {"schema": "lms"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    ky_thi_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("lms.ky_thi.id", ondelete="CASCADE"), nullable=False
    )
    vi_tri_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("lms.vi_tri_viec_lam.id"), nullable=False
    )
    linh_vuc_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("lms.linh_vuc.id"), nullable=False
    )

    so_cau_de: Mapped[Optional[int]] = mapped_column(Integer, server_default="0")
    so_cau_trung_binh: Mapped[Optional[int]] = mapped_column(Integer, server_default="0")
    so_cau_kho: Mapped[Optional[int]] = mapped_column(Integer, server_default="0")

    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP")
    )

    # Relationships
    ky_thi: Mapped[KyThi] = relationship(back_populates="cau_truc_de_list", lazy="selectin")
    vi_tri: Mapped[ViTriViecLam] = relationship(lazy="selectin")
    linh_vuc: Mapped[LinhVuc] = relationship(lazy="selectin")
