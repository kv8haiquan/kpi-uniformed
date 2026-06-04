"""
chi_tieu_service/models/dang_ky_thang.py
========================================
Model dang ky + ket qua theo thang (BANG LOI) — bang chi_tieu.dang_ky_thang.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from chi_tieu_service.models.base import Base


class DangKyThang(Base):
    """Dang ky + ket qua theo thang — bang chi_tieu.dang_ky_thang (bang loi)."""

    __tablename__ = "dang_ky_thang"
    __table_args__ = {"schema": "chi_tieu"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    don_vi_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("public.don_vi.id"), nullable=False
    )
    chi_tieu_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("chi_tieu.danh_muc_chi_tieu.id"), nullable=False
    )
    thang: Mapped[int] = mapped_column(Integer, nullable=False)
    nam: Mapped[int] = mapped_column(Integer, nullable=False)

    # Dang ky dau thang
    khong_dang_ky: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text("false"))
    gia_tri_dang_ky: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 3), nullable=True)

    # Ket qua cuoi thang
    gia_tri_ket_qua: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 3), nullable=True)

    # Danh gia
    danh_gia_tu_dong: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    danh_gia_ghi_chu: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    # Trang thai vong doi
    trang_thai: Mapped[str] = mapped_column(String(30), nullable=False, server_default="NHAP")

    # Nguoi lien quan
    nguoi_theo_doi_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("public.cong_chuc.id"), nullable=False
    )
    nguoi_duyet_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("public.cong_chuc.id"), nullable=True
    )

    # Moc thoi gian quy trinh
    ngay_gui_dang_ky: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    ngay_duyet_dang_ky: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    ngay_gui_ket_qua: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    ngay_duyet_ket_qua: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    ly_do_tu_choi: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Khoa sau khi chot
    is_khoa: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text("false"))

    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=text("CURRENT_TIMESTAMP")
    )
    is_deleted: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text("false"))
