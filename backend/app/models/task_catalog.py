"""
app/models/task_catalog.py
==========================
Models cho danh mục sản phẩm/công việc:
- SpCongViecChuan: Sản phẩm chuẩn (SP1, SP2, SP3, SP4)
- CapDoPhucTap: Cấp độ phức tạp (C1-C5)
- DanhMucSpCongViec: Danh mục công việc cụ thể của Chi cục

Quy tắc quy đổi:
- SP1 = 5 phút = 1 SP gốc (chuẩn)
- SP2 = 60 phút = 12 SP gốc
- SP3 = 60 phút = 12 SP gốc (giờ trực)
- SP4 = 60 phút = 12 SP gốc (giờ tuần tra)

Cấp độ phức tạp (hệ số nhân):
- C1: Dễ (x1 cho SP1, x1 cho SP2)
- C2: Trung bình (x4 cho SP1, x2 cho SP2)
- C3: Khó (x12 cho SP1, x4 cho SP2)
- C4: Rất khó (x24 cho SP1, x8 cho SP2)
- C5: Theo thực tế (do lãnh đạo xác định)
"""

import uuid
from decimal import Decimal
from typing import Optional, List, TYPE_CHECKING

from sqlalchemy import (
    String, 
    Integer, 
    Boolean, 
    Text, 
    ForeignKey,
    Index,
    Numeric,
    CheckConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel, BaseModelWithSoftDelete

if TYPE_CHECKING:
    from app.models.user_org import DonVi
    from app.models.kpi_submission import KeKhaiCongViec


class SpCongViecChuan(BaseModel):
    """
    Sản phẩm công việc chuẩn (SP1-SP4).
    
    Đây là 4 loại sản phẩm gốc theo Quy chế KPI:
    - SP1: Tờ khai HQ được kiểm tra chi tiết hồ sơ (5 phút = 1 SP gốc)
    - SP2: Văn bản hành chính (60 phút = 12 SP gốc)
    - SP3: Giờ trực làm việc (60 phút = 12 SP gốc)
    - SP4: Giờ tuần tra kiểm soát (60 phút = 12 SP gốc)
    
    Relationships:
    - danh_muc_items: Các công việc cụ thể thuộc loại SP này
    """
    
    __tablename__ = "sp_cong_viec_chuan"
    
    ma_sp: Mapped[str] = mapped_column(
        String(10),
        unique=True,
        nullable=False,
        comment="Mã sản phẩm: SP1, SP2, SP3, SP4"
    )
    
    ten_sp: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Tên sản phẩm chuẩn"
    )
    
    mo_ta: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Mô tả chi tiết"
    )
    
    thoi_gian_phut: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Thời gian thực hiện (phút)"
    )
    
    he_so_quy_doi_sp1: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        server_default="1",
        comment="Hệ số quy đổi về SP gốc (SP1=1, SP2/3/4=12)"
    )
    
    is_sp_goc: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="false",
        comment="Là SP gốc (chỉ SP1 = TRUE)"
    )
    
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default="true",
        comment="Còn sử dụng"
    )
    
    # -------------------------------------------------------------------------
    # RELATIONSHIPS
    # -------------------------------------------------------------------------
    
    # Danh mục công việc sử dụng SP này
    danh_muc_items: Mapped[List["DanhMucSpCongViec"]] = relationship(
        "DanhMucSpCongViec",
        back_populates="sp_chuan",
        lazy="dynamic"
    )
    
    # -------------------------------------------------------------------------
    # CONSTRAINTS
    # -------------------------------------------------------------------------
    __table_args__ = (
        CheckConstraint("thoi_gian_phut > 0", name="ck_sp_thoi_gian_positive"),
        CheckConstraint("he_so_quy_doi_sp1 > 0", name="ck_sp_he_so_positive"),
        Index("idx_sp_chuan_ma", "ma_sp"),
    )
    
    def __repr__(self) -> str:
        return f"<SpCongViecChuan(ma={self.ma_sp}, ten='{self.ten_sp}')>"


class CapDoPhucTap(BaseModel):
    """
    Cấp độ phức tạp của công việc (C1-C5).
    
    Hệ số nhân với sản phẩm:
    - C1 (Dễ): SP1 x1, SP2 x1
    - C2 (Trung bình): SP1 x4, SP2 x2
    - C3 (Khó): SP1 x12, SP2 x4
    - C4 (Rất khó): SP1 x24, SP2 x8
    - C5 (Theo thực tế): Do lãnh đạo xác định khi phê duyệt
    
    Relationships:
    - ke_khais: Các bản kê khai sử dụng cấp độ này
    """
    
    __tablename__ = "cap_do_phuc_tap"
    
    ma_cap_do: Mapped[str] = mapped_column(
        String(10),
        unique=True,
        nullable=False,
        comment="Mã cấp độ: C1, C2, C3, C4, C5"
    )
    
    ten_cap_do: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Tên cấp độ (VD: Dễ - Đơn giản)"
    )
    
    mo_ta: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Mô tả tiêu chí phân loại"
    )
    
    # Hệ số quy đổi
    he_so_sp1: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        comment="Hệ số nhân khi áp dụng cho SP1"
    )
    
    he_so_sp2: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        comment="Hệ số nhân khi áp dụng cho SP2/SP3/SP4"
    )
    
    is_theo_thuc_te: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="false",
        comment="C5 = TRUE (hệ số do lãnh đạo nhập)"
    )
    
    thu_tu: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Thứ tự sắp xếp (1-5)"
    )
    
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default="true",
        comment="Còn sử dụng"
    )
    
    # -------------------------------------------------------------------------
    # RELATIONSHIPS
    # -------------------------------------------------------------------------
    
    # Các bản kê khai sử dụng cấp độ này
    ke_khais: Mapped[List["KeKhaiCongViec"]] = relationship(
        "KeKhaiCongViec",
        back_populates="cap_do",
        lazy="dynamic"
    )
    
    # -------------------------------------------------------------------------
    # CONSTRAINTS
    # -------------------------------------------------------------------------
    __table_args__ = (
        CheckConstraint("thu_tu BETWEEN 1 AND 5", name="ck_cap_do_thu_tu"),
        CheckConstraint("he_so_sp1 >= 0", name="ck_cap_do_he_so_sp1"),
        CheckConstraint("he_so_sp2 >= 0", name="ck_cap_do_he_so_sp2"),
        Index("idx_cap_do_ma", "ma_cap_do"),
        Index("idx_cap_do_thu_tu", "thu_tu"),
    )
    
    def __repr__(self) -> str:
        return f"<CapDoPhucTap(ma={self.ma_cap_do}, ten='{self.ten_cap_do}')>"


class DanhMucSpCongViec(BaseModelWithSoftDelete):
    """
    Danh mục sản phẩm/công việc cụ thể của Chi cục.
    
    Mỗi công việc được map với 1 loại SP chuẩn (SP1-SP4).
    Có thể áp dụng cho toàn Chi cục hoặc chỉ 1 đơn vị cụ thể.
    
    VD:
    - "Tờ khai xuất khẩu loại A" -> SP1
    - "Công văn trả lời DN" -> SP2
    - "Trực cổng Container" -> SP3
    - "Tuần tra biên giới" -> SP4
    
    Relationships:
    - sp_chuan: Loại SP chuẩn (SP1-SP4)
    - don_vi_ap_dung: Đơn vị áp dụng (NULL = toàn Chi cục)
    - ke_khais: Các bản kê khai công việc này
    """
    
    __tablename__ = "danh_muc_sp_cong_viec"
    
    ma_danh_muc: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        nullable=False,
        comment="Mã danh mục công việc"
    )
    
    ten_cong_viec: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="Tên công việc chi tiết"
    )
    
    mo_ta: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Mô tả chi tiết công việc"
    )
    
    # Foreign keys
    sp_chuan_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("sp_cong_viec_chuan.id", ondelete="RESTRICT"),
        nullable=False,
        comment="ID loại SP chuẩn (SP1-SP4)"
    )
    
    don_vi_ap_dung_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("don_vi.id", ondelete="SET NULL"),
        nullable=True,
        comment="ID đơn vị áp dụng (NULL = toàn Chi cục)"
    )
    
    # Phân nhóm
    nhom_cong_viec: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        comment="Nhóm công việc (để filter)"
    )
    
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default="true",
        comment="Còn sử dụng"
    )
    
    # -------------------------------------------------------------------------
    # RELATIONSHIPS
    # -------------------------------------------------------------------------
    
    # Loại SP chuẩn
    sp_chuan: Mapped["SpCongViecChuan"] = relationship(
        "SpCongViecChuan",
        back_populates="danh_muc_items",
        lazy="joined"
    )
    
    # Đơn vị áp dụng
    don_vi_ap_dung: Mapped[Optional["DonVi"]] = relationship(
        "DonVi",
        lazy="joined"
    )
    
    # Các bản kê khai
    ke_khais: Mapped[List["KeKhaiCongViec"]] = relationship(
        "KeKhaiCongViec",
        back_populates="danh_muc_sp",
        lazy="dynamic"
    )
    
    # -------------------------------------------------------------------------
    # INDEXES
    # -------------------------------------------------------------------------
    __table_args__ = (
        Index("idx_danh_muc_sp_ma", "ma_danh_muc"),
        Index("idx_danh_muc_sp_chuan", "sp_chuan_id"),
        Index("idx_danh_muc_don_vi", "don_vi_ap_dung_id"),
        Index("idx_danh_muc_nhom", "nhom_cong_viec"),
    )
    
    def __repr__(self) -> str:
        return f"<DanhMucSpCongViec(ma={self.ma_danh_muc}, ten='{self.ten_cong_viec[:50]}...')>"
