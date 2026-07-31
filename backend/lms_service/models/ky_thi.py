"""
lms_service/models/ky_thi.py
============================
Model ky thi danh gia nang luc — bang lms.ky_thi.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, Integer, Numeric, String, Text, ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from lms_service.models.base import Base

if TYPE_CHECKING:
    from lms_service.models.cau_truc_de import CauTrucDe
    from lms_service.models.thi_sinh import ThiSinh


class KyThi(Base):
    """Ky thi danh gia nang luc — bang lms.ky_thi."""

    __tablename__ = "ky_thi"
    __table_args__ = {"schema": "lms"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    ma_ky_thi: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    ten_ky_thi: Mapped[str] = mapped_column(String(300), nullable=False)
    mo_ta: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Thoi gian
    ngay_bat_dau: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ngay_ket_thuc: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    thoi_gian_lam_bai_phut: Mapped[int] = mapped_column(Integer, nullable=False, server_default="60")

    # Cau hinh
    diem_dat: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), server_default="50.00")
    so_lan_thi_toi_da: Mapped[Optional[int]] = mapped_column(Integer, server_default="1")
    tron_cau_hoi: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text("true"))
    tron_dap_an: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text("true"))
    hien_ket_qua: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text("true"))
    hien_dap_an: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text("false"))
    # Ep toan man hinh + canh bao vi pham khi thi (anti-cheat)
    yeu_cau_toan_man_hinh: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text("true"))

    # Trang thai: NHAP, CHO_DUYET, DANG_MO, DA_DONG
    trang_thai: Mapped[Optional[str]] = mapped_column(String(50), server_default="NHAP")

    # Nguoi tao / nguoi duyet
    nguoi_tao_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("public.cong_chuc.id"), nullable=False
    )
    nguoi_duyet_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("public.cong_chuc.id"), nullable=True
    )
    ngay_duyet: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text("true"))
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP")
    )

    # Relationships
    cau_truc_de_list: Mapped[list[CauTrucDe]] = relationship(
        back_populates="ky_thi", lazy="selectin", cascade="all, delete-orphan"
    )
    thi_sinh_list: Mapped[list[ThiSinh]] = relationship(
        back_populates="ky_thi", lazy="selectin", cascade="all, delete-orphan"
    )
