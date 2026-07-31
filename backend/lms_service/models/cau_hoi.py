"""
lms_service/models/cau_hoi.py
=============================
Model ngan hang cau hoi — bang lms.cau_hoi.
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
    from lms_service.models.khoa_hoc import KhoaHoc
    from lms_service.models.chuyen_de import ChuyenDe
    from lms_service.models.bai_kiem_tra import BaiKiemTra
    from lms_service.models.linh_vuc import LinhVuc


class CauHoi(Base):
    """Ngan hang cau hoi — bang lms.cau_hoi."""

    __tablename__ = "cau_hoi"
    __table_args__ = {"schema": "lms"}

    # PK
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )

    # FK noi bo
    khoa_hoc_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("lms.khoa_hoc.id"), nullable=True
    )
    chuyen_de_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("lms.chuyen_de.id"), nullable=True
    )
    # FK den bai_kiem_tra — SET NULL khi xoa BKT
    bai_kiem_tra_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("lms.bai_kiem_tra.id", ondelete="SET NULL"), nullable=True
    )

    # Noi dung cau hoi
    noi_dung: Mapped[str] = mapped_column(Text, nullable=False)

    # Giai thich dap an (hien thi sau khi lam bai)
    giai_thich: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Loai: TRAC_NGHIEM_1, TRAC_NGHIEM_NHIEU, DUNG_SAI, TU_LUAN, GHEP_DOI
    loai: Mapped[str] = mapped_column(String(50), nullable=False)

    # Dap an (JSONB)
    dap_an: Mapped[dict] = mapped_column(JSONB, nullable=False)

    # Diem va do kho
    diem: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), server_default="1.0")
    do_kho: Mapped[Optional[str]] = mapped_column(String(20), server_default="TRUNG_BINH")

    # FK den linh_vuc — dung cho ky thi DGNL (nullable, cau hoi cu khong co)
    linh_vuc_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("lms.linh_vuc.id"), nullable=True
    )

    # Cross-module reference den legal.van_ban
    van_ban_lien_quan_ids: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # FK den public.cong_chuc — KHONG tao relationship
    nguoi_tao_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("public.cong_chuc.id"), nullable=True
    )

    # Flags
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text("true"))

    # Timestamps
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP")
    )

    # Relationships noi bo
    khoa_hoc: Mapped[Optional[KhoaHoc]] = relationship(lazy="selectin")
    chuyen_de: Mapped[Optional[ChuyenDe]] = relationship(
        back_populates="cau_hoi_list", lazy="selectin"
    )
    bai_kiem_tra: Mapped[Optional[BaiKiemTra]] = relationship(
        foreign_keys=[bai_kiem_tra_id], lazy="selectin"
    )
    linh_vuc: Mapped[Optional[LinhVuc]] = relationship(lazy="selectin")
