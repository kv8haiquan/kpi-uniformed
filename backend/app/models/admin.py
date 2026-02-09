"""
app/models/admin.py
===================
Models cho Admin Module - Quản lý lịch sử điều chuyển nhân sự.

Phiên bản: 1.0.0 (30/01/2026)
Tác giả: Claude AI

Bảng mới:
- LichSuDieuChuyen: Lưu lịch sử điều chuyển nhân sự giữa các đơn vị
"""

import uuid
from datetime import date, datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import (
    String,
    Date,
    Text,
    ForeignKey,
    Index,
    DateTime,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.user_org import CongChuc, DonVi, VaiTro


class LichSuDieuChuyen(BaseModel):
    """
    Lịch sử điều chuyển nhân sự.
    
    Ghi lại mỗi lần Admin điều chuyển nhân sự:
    - Đổi đơn vị
    - Đổi vai trò
    - Đổi chức vụ
    
    Attributes:
        cong_chuc_id: ID công chức được điều chuyển
        don_vi_cu_id: Đơn vị cũ
        don_vi_moi_id: Đơn vị mới
        vai_tro_cu_id: Vai trò cũ
        vai_tro_moi_id: Vai trò mới
        chuc_vu_cu: Chức vụ cũ (text)
        chuc_vu_moi: Chức vụ mới (text)
        ly_do: Lý do điều chuyển (VD: "Theo QĐ số 123/QĐ-HQKV8")
        ngay_hieu_luc: Ngày có hiệu lực
        nguoi_thuc_hien_id: Admin thực hiện điều chuyển
    """
    
    __tablename__ = "lich_su_dieu_chuyen"
    
    # -------------------------------------------------------------------------
    # CÔNG CHỨC ĐƯỢC ĐIỀU CHUYỂN
    # -------------------------------------------------------------------------
    cong_chuc_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("cong_chuc.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="ID công chức được điều chuyển"
    )
    
    # -------------------------------------------------------------------------
    # ĐƠN VỊ CŨ / MỚI
    # -------------------------------------------------------------------------
    don_vi_cu_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("don_vi.id", ondelete="SET NULL"),
        nullable=True,
        comment="ID đơn vị cũ"
    )
    
    don_vi_moi_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("don_vi.id", ondelete="SET NULL"),
        nullable=True,
        comment="ID đơn vị mới"
    )
    
    # -------------------------------------------------------------------------
    # VAI TRÒ CŨ / MỚI
    # -------------------------------------------------------------------------
    vai_tro_cu_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("vai_tro.id", ondelete="SET NULL"),
        nullable=True,
        comment="ID vai trò cũ"
    )
    
    vai_tro_moi_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("vai_tro.id", ondelete="SET NULL"),
        nullable=True,
        comment="ID vai trò mới"
    )
    
    # -------------------------------------------------------------------------
    # CHỨC VỤ CŨ / MỚI (Text - không FK)
    # -------------------------------------------------------------------------
    chuc_vu_cu: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Chức vụ cũ"
    )
    
    chuc_vu_moi: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Chức vụ mới"
    )
    
    # -------------------------------------------------------------------------
    # THÔNG TIN BỔ SUNG
    # -------------------------------------------------------------------------
    ly_do: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Lý do điều chuyển"
    )
    
    ngay_hieu_luc: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Ngày có hiệu lực"
    )
    
    # -------------------------------------------------------------------------
    # NGƯỜI THỰC HIỆN (Admin)
    # -------------------------------------------------------------------------
    nguoi_thuc_hien_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("cong_chuc.id", ondelete="SET NULL"),
        nullable=True,
        comment="ID Admin thực hiện điều chuyển"
    )
    
    # -------------------------------------------------------------------------
    # RELATIONSHIPS
    # -------------------------------------------------------------------------
    cong_chuc: Mapped["CongChuc"] = relationship(
        "CongChuc",
        foreign_keys=[cong_chuc_id],
        lazy="joined"
    )
    
    don_vi_cu: Mapped[Optional["DonVi"]] = relationship(
        "DonVi",
        foreign_keys=[don_vi_cu_id],
        lazy="joined"
    )
    
    don_vi_moi: Mapped[Optional["DonVi"]] = relationship(
        "DonVi",
        foreign_keys=[don_vi_moi_id],
        lazy="joined"
    )
    
    vai_tro_cu: Mapped[Optional["VaiTro"]] = relationship(
        "VaiTro",
        foreign_keys=[vai_tro_cu_id],
        lazy="joined"
    )
    
    vai_tro_moi: Mapped[Optional["VaiTro"]] = relationship(
        "VaiTro",
        foreign_keys=[vai_tro_moi_id],
        lazy="joined"
    )
    
    nguoi_thuc_hien: Mapped[Optional["CongChuc"]] = relationship(
        "CongChuc",
        foreign_keys=[nguoi_thuc_hien_id],
        lazy="joined"
    )
    
    # -------------------------------------------------------------------------
    # INDEXES
    # -------------------------------------------------------------------------
    __table_args__ = (
        Index("idx_lich_su_dc_cong_chuc", "cong_chuc_id"),
        Index("idx_lich_su_dc_ngay", "ngay_hieu_luc"),
        Index("idx_lich_su_dc_created", "created_at"),
    )
    
    def __repr__(self) -> str:
        return f"<LichSuDieuChuyen(id={self.id}, cc={self.cong_chuc_id}, ngay={self.ngay_hieu_luc})>"
