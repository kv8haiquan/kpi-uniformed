"""
lms_service/models/khoa_hoc.py
==============================
Model khoa hoc — bang lms.khoa_hoc.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    Boolean, Date, DateTime, Integer, Numeric, String, Text, ForeignKey, text,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from lms_service.models.base import Base

if TYPE_CHECKING:
    from lms_service.models.chuyen_de import ChuyenDe
    from lms_service.models.bai_hoc import BaiHoc
    from lms_service.models.bai_kiem_tra import BaiKiemTra
    from lms_service.models.dang_ky_khoa_hoc import DangKyKhoaHoc
    from lms_service.models.chung_chi import ChungChi
    from lms_service.models.khao_sat import KhaoSat


class KhoaHoc(Base):
    """Khoa hoc — bang lms.khoa_hoc."""

    __tablename__ = "khoa_hoc"
    __table_args__ = {"schema": "lms"}

    # PK
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )

    # Thong tin khoa hoc
    ma_khoa_hoc: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    ten_khoa_hoc: Mapped[str] = mapped_column(String(300), nullable=False)
    mo_ta: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # FK noi bo — chuyen de
    chuyen_de_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("lms.chuyen_de.id"), nullable=True
    )

    # Loai khoa hoc: TU_HOC, BAT_BUOC, TRUC_TUYEN, KET_HOP
    loai: Mapped[str] = mapped_column(String(50), nullable=False, server_default="TU_HOC")

    # Noi dung
    anh_dai_dien: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    thoi_luong_phut: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    so_bai_hoc: Mapped[Optional[int]] = mapped_column(Integer, server_default="0")

    # Dieu kien
    dieu_kien_tien_quyet: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    diem_dat_yeu_cau: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 2), server_default="70.00"
    )

    # Thoi gian
    ngay_bat_dau: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    ngay_ket_thuc: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # FK den public.cong_chuc — KHONG tao relationship (readonly table)
    giang_vien_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("public.cong_chuc.id"), nullable=True
    )

    # Trang thai: NHAP, CHO_DUYET, DA_XUAT_BAN, TAM_DUNG, DA_DONG
    trang_thai: Mapped[Optional[str]] = mapped_column(String(50), server_default="NHAP")
    nguoi_duyet_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("public.cong_chuc.id"), nullable=True
    )
    ngay_duyet: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Flags
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text("true"))

    # Timestamps
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=text("CURRENT_TIMESTAMP")
    )

    # search_vector: tsvector — quan ly boi trigger, KHONG map trong model

    # Relationships noi bo
    chuyen_de: Mapped[Optional[ChuyenDe]] = relationship(
        back_populates="khoa_hoc_list", lazy="selectin"
    )
    bai_hoc_list: Mapped[list[BaiHoc]] = relationship(
        back_populates="khoa_hoc", lazy="selectin"
    )
    bai_kiem_tra_list: Mapped[list[BaiKiemTra]] = relationship(
        back_populates="khoa_hoc", lazy="selectin"
    )
    dang_ky_list: Mapped[list[DangKyKhoaHoc]] = relationship(
        back_populates="khoa_hoc", lazy="selectin"
    )
    chung_chi_list: Mapped[list[ChungChi]] = relationship(
        back_populates="khoa_hoc", lazy="selectin"
    )
    khao_sat_list: Mapped[list[KhaoSat]] = relationship(
        back_populates="khoa_hoc", lazy="selectin"
    )
