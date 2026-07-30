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

from sqlalchemy import BigInteger, Boolean, DateTime, Integer, Numeric, String, Text, ForeignKey, text
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

    # Bai lam nhap (auto-save)
    chi_tiet_nhap: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True, comment="Bai lam nhap (auto-save)")

    # So lan vi pham (thoat tab/fullscreen)
    so_lan_vi_pham: Mapped[Optional[int]] = mapped_column(Integer, server_default="0", comment="So lan thoat tab/fullscreen")

    # Dat yeu cau
    dat_yeu_cau: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)

    # =====================================================================
    # BKT THUC HANH — bai nop + cham tay (NULL khi BKT trac nghiem)
    # =====================================================================
    bai_nop_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    bai_nop_ten_file: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    bai_nop_size_bytes: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    bai_nop_content_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    ngay_nop: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Cham tay
    nguoi_cham_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("public.cong_chuc.id"), nullable=True
    )
    diem_cham_tay: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    nhan_xet: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    trang_thai_cham: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="CHO_CHAM | DA_CHAM (NULL khi BKT trac nghiem)",
    )
    ngay_cham: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Timestamps
    ngay_lam: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP")
    )

    # Relationships noi bo
    bai_kiem_tra: Mapped[BaiKiemTra] = relationship(
        back_populates="ket_qua_list", lazy="selectin"
    )
