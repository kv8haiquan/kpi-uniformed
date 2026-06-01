"""
app/models/hdld.py
==================
SQLAlchemy Models cho Bộ tiêu chí đánh giá HĐLĐ 111 theo QĐ 714/QĐ-CHQ (08/5/2026).

Mô hình VB714:
- 6 nhóm nghề (I..VI), mỗi nhóm 3 tiêu chí cố định (Chất lượng / Tuân thủ / Hiệu quả).
- Mỗi tiêu chí thang 0-100. 2 cột chấm: Tự đánh giá (HĐLĐ) + Cấp quản lý đánh giá.
- Điểm chính thức = TB 3 tiêu chí (cột cấp quản lý) → KPI-70 = TB / 100 * 70.
- Cộng tiêu chí chung 30 như công chức → xếp loại A/B/C/D.

Áp dụng từ tháng 5/2026 (xem app.core.hdld_vb714). Tháng ≤ 4/2026 giữ form cũ.

Luồng 1 cấp: NHAP → CHO_DUYET → DA_DUYET / TRA_LAI.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum as PyEnum
from typing import Optional, List, TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    String, Integer, Boolean, Text, Numeric, DateTime,
    ForeignKey, CheckConstraint, UniqueConstraint, Index, func,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.user_org import CongChuc


class TrangThaiHdldDanhGia(str, PyEnum):
    """Trạng thái đánh giá HĐLĐ 111 theo VB714."""
    NHAP = "NHAP"
    CHO_DUYET = "CHO_DUYET"
    DA_DUYET = "DA_DUYET"
    TRA_LAI = "TRA_LAI"


# Tên 6 nhóm nghề (đồng bộ với seed trong migration)
TEN_NHOM_HDLD = {
    'I': 'Nhân viên lái xe',
    'II': 'Nhân viên bảo vệ',
    'III': 'Nhân viên lễ tân, phục vụ',
    'IV': 'Nhân viên tạp vụ',
    'V': 'Nhân viên bảo trì, bảo dưỡng, vận hành trụ sở, trang thiết bị, máy móc (nhân viên kỹ thuật)',
    'VI': 'Nhân viên hợp đồng lao động làm các công việc khác',
}


class HdldTieuChi(BaseModel):
    """Danh mục tiêu chí cố định theo VB714 (seed 18 dòng: 6 nhóm × 3 tiêu chí)."""

    __tablename__ = "hdld_tieu_chi"

    nhom: Mapped[str] = mapped_column(String(5), nullable=False)
    ten_nhom: Mapped[str] = mapped_column(String(200), nullable=False)
    so_tt: Mapped[int] = mapped_column(Integer, nullable=False)
    ten_tieu_chi: Mapped[str] = mapped_column(String(200), nullable=False)
    mo_ta_chi_tiet: Mapped[str] = mapped_column(Text, nullable=False)
    diem_toi_da: Mapped[int] = mapped_column(Integer, nullable=False, server_default="100")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")

    __table_args__ = (
        UniqueConstraint('nhom', 'so_tt', name='uq_hdld_tieu_chi_nhom_sott'),
        CheckConstraint("nhom IN ('I','II','III','IV','V','VI')", name='ck_hdld_tieu_chi_nhom'),
        CheckConstraint('so_tt >= 1 AND so_tt <= 3', name='ck_hdld_tieu_chi_sott'),
    )


class HdldDanhGia(BaseModel):
    """Header đánh giá HĐLĐ theo tháng — 1 bản/người/tháng."""

    __tablename__ = "hdld_danh_gia"

    cong_chuc_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey('public.cong_chuc.id'), nullable=False
    )
    thang: Mapped[int] = mapped_column(Integer, nullable=False)
    nam: Mapped[int] = mapped_column(Integer, nullable=False)
    nhom_nghe: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)
    trang_thai: Mapped[str] = mapped_column(String(50), nullable=False, server_default="NHAP")
    nguoi_duyet_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey('public.cong_chuc.id'), nullable=True
    )
    diem_tc_tb_tu: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2), nullable=True)
    diem_tc_tb_ql: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2), nullable=True)
    diem_kpi_70: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2), nullable=True)
    ghi_chu: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ly_do_tra_lai: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ngay_nop: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    ngay_duyet: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    cong_chuc: Mapped["CongChuc"] = relationship(
        "CongChuc", foreign_keys=[cong_chuc_id], lazy="selectin"
    )
    nguoi_duyet: Mapped[Optional["CongChuc"]] = relationship(
        "CongChuc", foreign_keys=[nguoi_duyet_id], lazy="selectin"
    )
    chi_tiets: Mapped[List["HdldDanhGiaChiTiet"]] = relationship(
        "HdldDanhGiaChiTiet",
        back_populates="danh_gia",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="HdldDanhGiaChiTiet.so_tt",
    )

    __table_args__ = (
        UniqueConstraint('cong_chuc_id', 'thang', 'nam', name='uq_hdld_danh_gia_cc_thang_nam'),
        CheckConstraint('thang >= 1 AND thang <= 12', name='ck_hdld_danh_gia_thang'),
        CheckConstraint('nam >= 2020 AND nam <= 2100', name='ck_hdld_danh_gia_nam'),
        CheckConstraint("nhom_nghe IS NULL OR nhom_nghe IN ('I','II','III','IV','V','VI')",
                        name='ck_hdld_danh_gia_nhom'),
        Index('idx_hdld_danh_gia_thang_nam', 'thang', 'nam'),
        Index('idx_hdld_danh_gia_trang_thai', 'trang_thai'),
        Index('idx_hdld_danh_gia_nguoi_duyet', 'nguoi_duyet_id'),
    )


class HdldDanhGiaChiTiet(BaseModel):
    """Chi tiết điểm 3 tiêu chí của 1 header — 2 cột: tự đánh giá + cấp quản lý."""

    __tablename__ = "hdld_danh_gia_chi_tiet"

    danh_gia_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey('hdld_danh_gia.id', ondelete='CASCADE'), nullable=False
    )
    so_tt: Mapped[int] = mapped_column(Integer, nullable=False)
    diem_tu: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    ghi_chu_tu: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    diem_ql: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    ghi_chu_ql: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ly_do_sua: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    danh_gia: Mapped["HdldDanhGia"] = relationship("HdldDanhGia", back_populates="chi_tiets")

    __table_args__ = (
        UniqueConstraint('danh_gia_id', 'so_tt', name='uq_hdld_ct_danhgia_sott'),
        CheckConstraint('so_tt >= 1 AND so_tt <= 3', name='ck_hdld_ct_sott'),
        CheckConstraint('diem_tu IS NULL OR (diem_tu >= 0 AND diem_tu <= 100)', name='ck_hdld_ct_diem_tu'),
        CheckConstraint('diem_ql IS NULL OR (diem_ql >= 0 AND diem_ql <= 100)', name='ck_hdld_ct_diem_ql'),
    )
