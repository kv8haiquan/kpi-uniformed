"""
lms_service/models/dang_ky_khoa_hoc.py
======================================
Model dang ky / giao khoa hoc — bang lms.dang_ky_khoa_hoc.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Date, DateTime, Integer, Numeric, String, ForeignKey, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from lms_service.models.base import Base

if TYPE_CHECKING:
    from lms_service.models.khoa_hoc import KhoaHoc


class DangKyKhoaHoc(Base):
    """Dang ky / Giao khoa hoc — bang lms.dang_ky_khoa_hoc."""

    __tablename__ = "dang_ky_khoa_hoc"
    __table_args__ = (
        UniqueConstraint("cong_chuc_id", "khoa_hoc_id", name="uq_lms_dkkh_cc_kh"),
        {"schema": "lms"},
    )

    # PK
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )

    # FK den public.cong_chuc — KHONG tao relationship
    cong_chuc_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("public.cong_chuc.id"), nullable=False
    )

    # FK noi bo
    khoa_hoc_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("lms.khoa_hoc.id"), nullable=False
    )

    # Loai dang ky: TU_NGUYEN, BAT_BUOC, GIAO_VIEC
    loai_dang_ky: Mapped[Optional[str]] = mapped_column(
        String(50), server_default="TU_NGUYEN"
    )

    # Nguoi giao — FK den public.cong_chuc
    nguoi_giao_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("public.cong_chuc.id"), nullable=True
    )
    han_hoan_thanh: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # Tien do: CHUA_BAT_DAU, DANG_HOC, HOAN_THANH, KHONG_DAT, QUA_HAN
    trang_thai: Mapped[Optional[str]] = mapped_column(
        String(50), server_default="CHUA_BAT_DAU"
    )
    phan_tram_hoan_thanh: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 2), server_default="0"
    )
    ngay_bat_dau_hoc: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    ngay_hoan_thanh: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Ket qua
    diem_cao_nhat: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    so_lan_lam_bai: Mapped[Optional[int]] = mapped_column(Integer, server_default="0")

    # Timestamps
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=text("CURRENT_TIMESTAMP")
    )

    # Relationships noi bo
    khoa_hoc: Mapped[KhoaHoc] = relationship(
        back_populates="dang_ky_list", lazy="selectin"
    )
