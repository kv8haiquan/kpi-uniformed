"""
lms_service/models/thi_sinh.py
==============================
Model thi sinh ky thi DGNL — bang lms.thi_sinh.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, Integer, Numeric, String, ForeignKey, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from lms_service.models.base import Base

if TYPE_CHECKING:
    from lms_service.models.ky_thi import KyThi
    from lms_service.models.vi_tri_viec_lam import ViTriViecLam


class ThiSinh(Base):
    """Thi sinh ky thi DGNL — bang lms.thi_sinh."""

    __tablename__ = "thi_sinh"
    __table_args__ = (
        UniqueConstraint("ky_thi_id", "cong_chuc_id", name="uq_thi_sinh_kt_cc"),
        {"schema": "lms"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    ky_thi_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("lms.ky_thi.id", ondelete="CASCADE"), nullable=False
    )
    cong_chuc_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("public.cong_chuc.id"), nullable=False
    )
    vi_tri_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("lms.vi_tri_viec_lam.id"), nullable=False
    )

    # Trang thai: CHUA_THI, DANG_THI, DA_NOP, VANG
    trang_thai: Mapped[Optional[str]] = mapped_column(String(50), server_default="CHUA_THI")
    lan_thi_hien_tai: Mapped[Optional[int]] = mapped_column(Integer, server_default="0")

    # Ket qua tot nhat
    diem_tong: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    xep_loai: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    so_cau_dung: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    so_cau_sai: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    tong_so_cau: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    diem_theo_linh_vuc: Mapped[Optional[dict]] = mapped_column(JSONB, server_default="'{}'")

    # Thoi gian
    thoi_gian_bat_dau: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    thoi_gian_nop: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    thoi_gian_lam_giay: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # De thi random
    de_thi_ids: Mapped[Optional[list]] = mapped_column(JSONB, server_default="'[]'")
    chi_tiet_tra_loi: Mapped[Optional[list]] = mapped_column(JSONB, server_default="'[]'")
    lich_su_thi: Mapped[Optional[list]] = mapped_column(JSONB, server_default="'[]'")

    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=text("CURRENT_TIMESTAMP")
    )

    # Relationships
    ky_thi: Mapped[KyThi] = relationship(back_populates="thi_sinh_list", lazy="selectin")
    vi_tri: Mapped[ViTriViecLam] = relationship(lazy="selectin")
