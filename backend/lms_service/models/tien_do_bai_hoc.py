"""
lms_service/models/tien_do_bai_hoc.py
=====================================
Model tien do hoc tung bai — bang lms.tien_do_bai_hoc.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, Integer, String, ForeignKey, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from lms_service.models.base import Base

if TYPE_CHECKING:
    from lms_service.models.bai_hoc import BaiHoc


class TienDoBaiHoc(Base):
    """Tien do hoc tung bai — bang lms.tien_do_bai_hoc."""

    __tablename__ = "tien_do_bai_hoc"
    __table_args__ = (
        UniqueConstraint("cong_chuc_id", "bai_hoc_id", name="uq_lms_tdbh_cc_bh"),
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
    bai_hoc_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("lms.bai_hoc.id"), nullable=False
    )

    # Trang thai: CHUA_XEM, DANG_XEM, DA_HOAN_THANH
    trang_thai: Mapped[Optional[str]] = mapped_column(String(50), server_default="CHUA_XEM")
    thoi_gian_xem_giay: Mapped[Optional[int]] = mapped_column(Integer, server_default="0")
    lan_xem_cuoi: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    ngay_hoan_thanh: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships noi bo
    bai_hoc: Mapped[BaiHoc] = relationship(
        back_populates="tien_do_list", lazy="selectin"
    )
