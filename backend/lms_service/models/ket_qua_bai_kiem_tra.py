"""
lms_service/models/ket_qua_bai_kiem_tra.py
==========================================
Model ket qua lam bai kiem tra — bang lms.ket_qua_bai_kiem_tra.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, Integer, Numeric, ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from lms_service.models.base import Base

if TYPE_CHECKING:
    from lms_service.models.bai_kiem_tra import BaiKiemTra


class KetQuaBaiKiemTra(Base):
    """Ket qua lam bai kiem tra — bang lms.ket_qua_bai_kiem_tra."""

    __tablename__ = "ket_qua_bai_kiem_tra"
    __table_args__ = {"schema": "lms"}

    # PK
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )

    # FK den public.cong_chuc — KHONG tao relationship
    cong_chuc_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("public.cong_chuc.id"), nullable=False
    )

    # FK noi bo
    bai_kiem_tra_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("lms.bai_kiem_tra.id"), nullable=False
    )

    # Lan thu
    lan_thu: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1")

    # Ket qua
    diem: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    so_cau_dung: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    so_cau_sai: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    thoi_gian_lam_giay: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Chi tiet tra loi (JSONB)
    chi_tiet_tra_loi: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Dat yeu cau
    dat_yeu_cau: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)

    # Timestamps
    ngay_lam: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=text("CURRENT_TIMESTAMP")
    )

    # Relationships noi bo
    bai_kiem_tra: Mapped[BaiKiemTra] = relationship(
        back_populates="ket_qua_list", lazy="selectin"
    )
