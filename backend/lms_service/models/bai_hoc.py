"""
lms_service/models/bai_hoc.py
=============================
Model bai hoc / noi dung khoa hoc — bang lms.bai_hoc.
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
    from lms_service.models.khoa_hoc import KhoaHoc
    from lms_service.models.tien_do_bai_hoc import TienDoBaiHoc


class BaiHoc(Base):
    """Bai hoc / noi dung khoa hoc — bang lms.bai_hoc."""

    __tablename__ = "bai_hoc"
    __table_args__ = {"schema": "lms"}

    # PK
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )

    # FK noi bo
    khoa_hoc_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("lms.khoa_hoc.id"), nullable=False
    )

    # Thong tin bai hoc
    thu_tu: Mapped[int] = mapped_column(Integer, nullable=False)
    tieu_de: Mapped[str] = mapped_column(String(300), nullable=False)

    # Loai noi dung: VIDEO, PDF, SLIDE, HTML, SCORM, QUIZ
    loai_noi_dung: Mapped[str] = mapped_column(String(50), nullable=False)

    # Noi dung
    noi_dung: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    file_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    pdf_url: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True,
        comment="URL ban PDF convert tu PPTX/DOCX, dung de xem tren web"
    )
    file_size_mb: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    thoi_luong_phut: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Dieu kien hoan thanh
    phai_xem_het: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text("true"))
    thoi_gian_toi_thieu_giay: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Flags
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text("true"))

    # Timestamps
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP")
    )

    # Relationships noi bo
    khoa_hoc: Mapped[KhoaHoc] = relationship(back_populates="bai_hoc_list", lazy="selectin")
    tien_do_list: Mapped[list[TienDoBaiHoc]] = relationship(
        back_populates="bai_hoc", lazy="selectin"
    )
