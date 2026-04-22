"""
lms_service/models/bai_kiem_tra.py
==================================
Model bai kiem tra — bang lms.bai_kiem_tra.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, Date, DateTime, Integer, Numeric, String, Text, ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from lms_service.models.base import Base

if TYPE_CHECKING:
    from lms_service.models.khoa_hoc import KhoaHoc
    from lms_service.models.bai_kiem_tra_cau_hoi import BaiKiemTraCauHoi
    from lms_service.models.ket_qua_bai_kiem_tra import KetQuaBaiKiemTra


class BaiKiemTra(Base):
    """Bai kiem tra — bang lms.bai_kiem_tra."""

    __tablename__ = "bai_kiem_tra"
    __table_args__ = {"schema": "lms"}

    # PK
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )

    # FK noi bo
    khoa_hoc_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("lms.khoa_hoc.id"), nullable=True
    )

    # Thong tin bai kiem tra
    tieu_de: Mapped[str] = mapped_column(String(300), nullable=False)
    mo_ta: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Loai BKT: TRAC_NGHIEM (mac dinh) | THUC_HANH (hoc vien upload video)
    loai_bai_kiem_tra: Mapped[str] = mapped_column(
        String(50),
        server_default="TRAC_NGHIEM",
        nullable=False,
        comment="TRAC_NGHIEM | THUC_HANH",
    )

    # Thuc hanh: huong dan bai lam + giới hạn upload
    yeu_cau_bai_lam: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    dung_luong_toi_da_mb: Mapped[Optional[int]] = mapped_column(Integer, server_default="500")
    dinh_dang_cho_phep: Mapped[Optional[str]] = mapped_column(
        String(200),
        server_default="mp4,mov,webm",
        comment="CSV extension (khong dau cham)",
    )

    # Cau hinh de thi
    so_cau_hoi: Mapped[int] = mapped_column(Integer, nullable=False)
    thoi_gian_lam_bai_phut: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    so_lan_lam_toi_da: Mapped[Optional[int]] = mapped_column(Integer, server_default="3")
    diem_dat: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), server_default="70.00")
    tron_de: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text("true"))
    tron_dap_an: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text("true"))

    # Thoi gian mo
    ngay_mo: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    ngay_dong: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    gio_mo: Mapped[Optional[str]] = mapped_column(String(5), nullable=True, comment="Gio bat dau cho phep thi (HH:MM)")
    gio_dong: Mapped[Optional[str]] = mapped_column(String(5), nullable=True, comment="Gio ket thuc cho phep thi (HH:MM)")

    # FK den public.cong_chuc — KHONG tao relationship
    nguoi_tao_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("public.cong_chuc.id"), nullable=True
    )

    # Cau hinh hien thi ket qua sau khi nop bai
    che_do_xem_ket_qua: Mapped[str] = mapped_column(
        String(50),
        server_default="XEM_DIEM_VA_DAP_AN",
        nullable=False,
        comment="XEM_DIEM_VA_DAP_AN | CHI_XEM_DIEM | CHI_XEM_CAU_SAI | XEM_KHI_LAN_CUOI | KHONG_CHO_XEM",
    )
    hien_giai_thich: Mapped[bool] = mapped_column(
        Boolean,
        server_default=text("true"),
        nullable=False,
        comment="Hien giai thich dap an sau khi nop bai",
    )

    # Flags
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text("true"))

    # Timestamps
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=text("CURRENT_TIMESTAMP")
    )

    # Relationships noi bo
    khoa_hoc: Mapped[Optional[KhoaHoc]] = relationship(
        back_populates="bai_kiem_tra_list", lazy="selectin"
    )
    cau_hoi_links: Mapped[list[BaiKiemTraCauHoi]] = relationship(
        back_populates="bai_kiem_tra", lazy="selectin"
    )
    ket_qua_list: Mapped[list[KetQuaBaiKiemTra]] = relationship(
        back_populates="bai_kiem_tra", lazy="selectin"
    )
