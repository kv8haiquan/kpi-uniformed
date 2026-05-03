"""
app/models/task_catalog.py
==========================
Models cho danh mục sản phẩm/công việc:
- SpCongViecChuan: Sản phẩm chuẩn V1 (SP1, SP2, SP3, SP4) — giữ làm fallback
- CapDoPhucTap: Cấp độ phức tạp V1 (C1-C5) — giữ làm fallback (LOCKED 6)
- DanhMucSpCongViec: Danh mục công việc — đã MỞ RỘNG cho V2_PL3 (LOCKED 7)
- NhomCongViecPL3 (V2): 5 nhóm thay thế C1-C5 trong V2_PL3

V1 — Quy tắc quy đổi:
- SP1 = 5 phút = 1 SP gốc (chuẩn)
- SP2 = 60 phút = 12 SP gốc
- SP3 = 60 phút = 12 SP gốc (giờ trực)
- SP4 = 60 phút = 12 SP gốc (giờ tuần tra)

V1 — Cấp độ phức tạp (hệ số nhân):
- C1: Dễ (x1 cho SP1, x1 cho SP2)
- C2: Trung bình (x4 cho SP1, x2 cho SP2)
- C3: Khó (x12 cho SP1, x4 cho SP2)
- C4: Rất khó (x24 cho SP1, x8 cho SP2)
- C5: Theo thực tế (do lãnh đạo xác định)

V2_PL3 (28/04/2026):
- 2.812 mục từ Phụ lục III Sổ tay Bộ Nội vụ
- 15 lĩnh vực (I-XV) × 5 nhóm × 4 tiêu chí chấm điểm
- he_so_quy_doi = diem_cham / 25 (1 SP1 = 25 điểm cơ sở)
"""

import uuid
from decimal import Decimal
from typing import Optional, List, TYPE_CHECKING

from sqlalchemy import (
    String,
    Integer,
    SmallInteger,
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
    Danh mục sản phẩm/công việc cụ thể.

    PHÂN BIỆT V1 vs V2 bằng cột `nguon_du_lieu`:
    - 'V1': 46 mục cũ (Chi cục), bắt buộc map sp_chuan + cap_do.
    - 'PL3': 2.812 mục mới, có he_so_quy_doi sẵn, sp_chuan_id có thể NULL.

    V1 ví dụ:
    - "Tờ khai xuất khẩu loại A" → SP1
    - "Công văn trả lời DN" → SP2
    - "Trực cổng Container" → SP3
    - "Tuần tra biên giới" → SP4

    V2_PL3 ví dụ:
    - linh_vuc='I' (Quản lý điều hành)
      nhom_pl3=2 → he_so_quy_doi=6.8 → 1 mục = 6.8 SP1

    Relationships:
    - sp_chuan: V1 only (V2 NULL).
    - don_vi_ap_dung: Đơn vị áp dụng (NULL = toàn Chi cục).
    - ke_khais: Các bản kê khai công việc này.
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
    # V2_PL3: nullable (LOCKED 7 — V2 không bắt buộc map về SP1-SP4)
    sp_chuan_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("sp_cong_viec_chuan.id", ondelete="RESTRICT"),
        nullable=True,
        comment="V1: ID loại SP chuẩn (SP1-SP4). V2_PL3: NULL"
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

    # =========================================================================
    # PL3 V2 FIELDS (28/04/2026) — chỉ dùng khi nguon_du_lieu='PL3'
    # =========================================================================

    nguon_du_lieu: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default="V1",
        comment="V1 = 46 mục cũ; PL3 = 2.812 mục mới"
    )

    linh_vuc: Mapped[Optional[str]] = mapped_column(
        String(10),
        nullable=True,
        comment="Mã lĩnh vực La Mã: I-XV (chỉ V2_PL3)"
    )

    ten_linh_vuc: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        comment="Tên đầy đủ lĩnh vực"
    )

    nhiem_vu: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="Cột B Excel PL3"
    )

    cong_viec_chi_tiet: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Cột C Excel PL3"
    )

    san_pham_dau_ra: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Cột D Excel PL3"
    )

    nhom_pl3: Mapped[Optional[int]] = mapped_column(
        SmallInteger,
        nullable=True,
        comment="Phân nhóm 1-5 (chỉ V2_PL3)"
    )

    khung_diem_toi_da: Mapped[Optional[int]] = mapped_column(
        SmallInteger,
        nullable=True,
        comment="100/200/300/400/500 tương ứng nhóm 1-5 (derive từ nhom_pl3)"
    )

    # 28/04/2026: Bỏ 4 cột chấm chi tiết theo quyết định nghiệp vụ.
    # Nghiệp vụ chỉ cần diem_cham + he_so_quy_doi.

    diem_cham: Mapped[Optional[int]] = mapped_column(
        SmallInteger,
        nullable=True,
        comment="Cột K Excel PL3 (giá trị do người soạn Excel quyết định)"
    )

    he_so_quy_doi: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(8, 4),
        nullable=True,
        comment="Cột L Excel PL3 = diem_cham / 25 (chỉ V2_PL3)"
    )

    # -------------------------------------------------------------------------
    # RELATIONSHIPS
    # -------------------------------------------------------------------------

    # Loại SP chuẩn — V1 only
    sp_chuan: Mapped[Optional["SpCongViecChuan"]] = relationship(
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
    # CONSTRAINTS & INDEXES
    # -------------------------------------------------------------------------
    __table_args__ = (
        CheckConstraint(
            "nhom_pl3 IS NULL OR nhom_pl3 BETWEEN 1 AND 5",
            name="ck_dmsp_nhom_pl3",
        ),
        CheckConstraint(
            "he_so_quy_doi IS NULL OR he_so_quy_doi > 0",
            name="ck_dmsp_he_so_pos",
        ),
        CheckConstraint(
            "nguon_du_lieu IN ('V1', 'PL3')",
            name="ck_dmsp_nguon_du_lieu",
        ),
        Index("idx_danh_muc_sp_ma", "ma_danh_muc"),
        Index("idx_danh_muc_sp_chuan", "sp_chuan_id"),
        Index("idx_danh_muc_don_vi", "don_vi_ap_dung_id"),
        Index("idx_danh_muc_nhom", "nhom_cong_viec"),
        Index("idx_dmsp_linh_vuc", "linh_vuc"),
        Index("idx_dmsp_nhom_pl3", "nhom_pl3"),
        Index("idx_dmsp_nguon_du_lieu", "nguon_du_lieu"),
    )
    
    def __repr__(self) -> str:
        return f"<DanhMucSpCongViec(ma={self.ma_danh_muc}, ten='{self.ten_cong_viec[:50]}...')>"


# =============================================================================
# PL3 V2 — Bảng phân nhóm (28/04/2026)
# =============================================================================

class NhomCongViecPL3(BaseModel):
    """
    5 nhóm phân loại trong V2_PL3, thay thế C1-C5 của V1.

    Seed sẵn 5 nhóm với điểm tối đa: 100/200/300/400/500.
    Read-only sau khi seed; admin chỉ chỉnh `ten_nhom`/`mo_ta`.
    """

    __tablename__ = "nhom_cong_viec_pl3"

    nhom: Mapped[int] = mapped_column(
        SmallInteger,
        unique=True,
        nullable=False,
        comment="1-5",
    )

    ten_nhom: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Tên hiển thị nhóm",
    )

    diem_toi_da: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        comment="100/200/300/400/500",
    )

    mo_ta: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Mô tả nhóm",
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default="true",
        comment="Còn dùng",
    )

    __table_args__ = (
        CheckConstraint("nhom BETWEEN 1 AND 5", name="ck_nhom_pl3_range"),
        CheckConstraint("diem_toi_da > 0", name="ck_nhom_pl3_diem_pos"),
    )

    def __repr__(self) -> str:
        return f"<NhomCongViecPL3(nhom={self.nhom}, ten='{self.ten_nhom}')>"
