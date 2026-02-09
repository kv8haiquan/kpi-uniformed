"""
app/models/user_org.py
======================
Models cho tổ chức và nhân sự:
- DonVi: Đơn vị (Phòng/Đội/HQCK)
- VaiTro: Vai trò trong hệ thống (CCT, PCCT, TDV, PDV, CC)
- CongChuc: Công chức

Quy ước:
- Sử dụng Tiếng Việt không dấu cho tên cột (snake_case)
- Relationships với back_populates để truy vấn 2 chiều

Cập nhật v2.3 (25/01/2026):
- Thêm relationship dang_ky_nghis cho Leave Management

Cập nhật v2.5.8 (27/01/2026):
- Thêm relationship ke_khai_lanh_dao_list cho Module Lãnh đạo
- Thêm relationship danh_gia_dde_list cho Đánh giá d, đ, e
"""

import uuid
import enum
from datetime import date, datetime
from typing import Optional, List, TYPE_CHECKING

from sqlalchemy import (
    String, 
    Integer, 
    Boolean, 
    Date, 
    Text, 
    ForeignKey,
    Index,
    UniqueConstraint,
    Enum as SQLEnum,
    JSON,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel, BaseModelWithSoftDelete

# =============================================================================
# TYPE_CHECKING - Tránh circular import khi định nghĩa relationships
# =============================================================================
if TYPE_CHECKING:
    from app.models.kpi_submission import KeKhaiCongViec
    from app.models.kpi_assessment import DanhGiaThang
    from app.models.leave import DangKyNghi
    from app.models.leader_kpi import KeKhaiLanhDao, DanhGiaDDE  # v2.5.8


# =============================================================================
# ENUMS
# =============================================================================

class LoaiDonVi(str, enum.Enum):
    """
    Loại đơn vị trong Chi cục Hải quan.
    Kế thừa str để serialize dễ dàng sang JSON.
    """
    LANH_DAO_CHI_CUC = "LANH_DAO_CHI_CUC"  # Lãnh đạo Chi cục
    PHONG = "PHONG"                          # Phòng chức năng
    DOI = "DOI"                              # Đội nghiệp vụ
    HAI_QUAN_CUA_KHAU = "HAI_QUAN_CUA_KHAU"  # Hải quan cửa khẩu


class CapBacVaiTro(str, enum.Enum):
    """
    Cấp bậc vai trò - xác định thứ tự phê duyệt và quyền hạn.
    Số càng nhỏ = cấp càng cao.
    """
    SUPER_ADMIN = "SUPER_ADMIN"                # Cấp 0 - Quản trị hệ thống
    CHI_CUC_TRUONG = "CHI_CUC_TRUONG"          # Cấp 1 - Cao nhất nghiệp vụ
    PHO_CHI_CUC_TRUONG = "PHO_CHI_CUC_TRUONG"  # Cấp 2
    TRUONG_DON_VI = "TRUONG_DON_VI"            # Cấp 3
    PHO_DON_VI = "PHO_DON_VI"                  # Cấp 4
    CONG_CHUC = "CONG_CHUC"                    # Cấp 5
    TCCB = "TCCB"                              # Đặc biệt - Phòng Tổ chức cán bộ


class GioiTinh(str, enum.Enum):
    """Giới tính công chức."""
    NAM = "NAM"
    NU = "NU"


# =============================================================================
# MODELS
# =============================================================================

class DonVi(BaseModelWithSoftDelete):
    """
    Đơn vị trong Chi cục Hải quan Khu vực VIII.
    
    Relationships:
    - cong_chucs: Danh sách công chức thuộc đơn vị
    - children: Các đơn vị con
    - parent: Đơn vị cha
    """
    
    __tablename__ = "don_vi"
    
    ma_don_vi: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        nullable=False,
        index=True,
        comment="Mã đơn vị (unique)"
    )
    
    ten_don_vi: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Tên đầy đủ của đơn vị"
    )
    
    ten_viet_tat: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Tên viết tắt"
    )
    
    loai_don_vi: Mapped[LoaiDonVi] = mapped_column(
        SQLEnum(LoaiDonVi, name="loai_don_vi_enum", create_type=True),
        nullable=False,
        comment="Loại đơn vị"
    )
    
    parent_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("don_vi.id", ondelete="SET NULL"),
        nullable=True,
        comment="ID đơn vị cha"
    )
    
    thu_tu_hien_thi: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default="0",
        comment="Thứ tự hiển thị"
    )
    
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default="true",
        comment="Đơn vị còn hoạt động"
    )
    
    # -------------------------------------------------------------------------
    # RELATIONSHIPS
    # -------------------------------------------------------------------------
    
    children: Mapped[List["DonVi"]] = relationship(
        "DonVi",
        back_populates="parent",
        remote_side="DonVi.parent_id",
        lazy="selectin"
    )
    
    parent: Mapped[Optional["DonVi"]] = relationship(
        "DonVi",
        back_populates="children",
        remote_side="DonVi.id",
        lazy="joined"
    )
    
    cong_chucs: Mapped[List["CongChuc"]] = relationship(
        "CongChuc",
        back_populates="don_vi",
        lazy="selectin"
    )
    
    __table_args__ = (
        Index("idx_don_vi_ma", "ma_don_vi"),
        Index("idx_don_vi_active", "is_active", postgresql_where="is_deleted = false"),
        Index("idx_don_vi_loai", "loai_don_vi"),
    )
    
    def __repr__(self) -> str:
        return f"<DonVi(id={self.id}, ma={self.ma_don_vi}, ten='{self.ten_don_vi}')>"


class VaiTro(BaseModel):
    """
    Vai trò trong hệ thống.
    
    Relationships:
    - cong_chucs: Danh sách công chức có vai trò này
    """
    
    __tablename__ = "vai_tro"
    
    ma_vai_tro: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        comment="Mã vai trò"
    )
    
    ten_vai_tro: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Tên hiển thị"
    )
    
    cap_bac: Mapped[CapBacVaiTro] = mapped_column(
        SQLEnum(CapBacVaiTro, name="cap_bac_vai_tro_enum", create_type=True),
        nullable=False,
        comment="Cấp bậc trong hệ thống"
    )
    
    mo_ta: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Mô tả chi tiết"
    )
    
    is_lanh_dao: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="false",
        comment="Có phải lãnh đạo không"
    )
    
    is_system_admin: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="false",
        comment="Là Super Admin"
    )
    
    quyen_han: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Danh sách quyền chi tiết"
    )
    
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default="true",
        comment="Vai trò còn sử dụng"
    )
    
    # -------------------------------------------------------------------------
    # RELATIONSHIPS
    # -------------------------------------------------------------------------
    
    cong_chucs: Mapped[List["CongChuc"]] = relationship(
        "CongChuc",
        back_populates="vai_tro",
        lazy="selectin"
    )
    
    def __repr__(self) -> str:
        return f"<VaiTro(id={self.id}, ma={self.ma_vai_tro}, cap_bac={self.cap_bac.value})>"


class CongChuc(BaseModelWithSoftDelete):
    """
    Công chức Chi cục Hải quan Khu vực VIII.
    
    Relationships:
    - don_vi: Đơn vị công tác
    - vai_tro: Vai trò trong hệ thống
    - ke_khais: Các bản kê khai công việc
    - danh_gias: Các đánh giá tháng
    - dang_ky_nghis: Các đơn đăng ký nghỉ phép (v2.3)
    - ke_khai_lanh_dao_list: Kê khai công việc Lãnh đạo (v2.5.8)
    - danh_gia_dde_list: Đánh giá d, đ, e (v2.5.8)
    """
    
    __tablename__ = "cong_chuc"
    
    # -------------------------------------------------------------------------
    # THÔNG TIN CÁ NHÂN
    # -------------------------------------------------------------------------
    
    ma_cc: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        nullable=False,
        index=True,
        comment="Mã công chức"
    )
    
    ho_ten: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Họ và tên"
    )
    
    ngay_sinh: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Ngày sinh"
    )
    
    gioi_tinh: Mapped[Optional[GioiTinh]] = mapped_column(
        SQLEnum(GioiTinh, name="gioi_tinh_enum", create_type=True),
        nullable=True,
        comment="Giới tính"
    )
    
    so_dien_thoai: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="Số điện thoại"
    )
    
    email: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Email công vụ"
    )
    
    # -------------------------------------------------------------------------
    # THÔNG TIN CÔNG TÁC
    # -------------------------------------------------------------------------
    
    don_vi_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("don_vi.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="ID đơn vị công tác"
    )
    
    vai_tro_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("vai_tro.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="ID vai trò"
    )
    
    chuc_vu: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Chức vụ hiển thị"
    )
    
    ngay_vao_nganh: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Ngày vào ngành"
    )
    
    ngay_vao_chi_cuc: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Ngày về Chi cục"
    )
    
    # -------------------------------------------------------------------------
    # PHÂN LOẠI
    # -------------------------------------------------------------------------
    
    is_lanh_dao: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="false",
        comment="Có phải lãnh đạo không"
    )
    
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default="true",
        index=True,
        comment="Tài khoản còn hoạt động"
    )
    
    # -------------------------------------------------------------------------
    # ĐĂNG NHẬP
    # -------------------------------------------------------------------------
    
    username: Mapped[Optional[str]] = mapped_column(
        String(50),
        unique=True,
        nullable=True,
        index=True,
        comment="Tên đăng nhập"
    )
    
    password_hash: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Mật khẩu đã hash"
    )
    
    last_login: Mapped[Optional[datetime]] = mapped_column(
        nullable=True,
        comment="Lần đăng nhập cuối"
    )
    
    # -------------------------------------------------------------------------
    # RELATIONSHIPS - Sử dụng STRING REFERENCE để tránh circular import
    # -------------------------------------------------------------------------
    
    # Đơn vị công tác
    don_vi: Mapped["DonVi"] = relationship(
        "DonVi",
        back_populates="cong_chucs",
        lazy="joined"
    )
    
    # Vai trò
    vai_tro: Mapped["VaiTro"] = relationship(
        "VaiTro",
        back_populates="cong_chucs",
        lazy="joined"
    )
    
    # Các bản kê khai công việc (string reference)
    ke_khais: Mapped[List["KeKhaiCongViec"]] = relationship(
        "KeKhaiCongViec",
        back_populates="cong_chuc",
        foreign_keys="KeKhaiCongViec.cong_chuc_id",
        lazy="dynamic"
    )
    
    # Các đánh giá tháng (string reference)
    danh_gias: Mapped[List["DanhGiaThang"]] = relationship(
        "DanhGiaThang",
        back_populates="cong_chuc",
        foreign_keys="DanhGiaThang.cong_chuc_id",
        lazy="dynamic"
    )
    
    # =========================================================================
    # v2.3 - LEAVE MANAGEMENT: Các đơn đăng ký nghỉ phép
    # =========================================================================
    dang_ky_nghis: Mapped[List["DangKyNghi"]] = relationship(
        "DangKyNghi",
        back_populates="cong_chuc",
        foreign_keys="DangKyNghi.cong_chuc_id",
        lazy="dynamic"
    )
    
    # =========================================================================
    # v2.5.8 - LEADER KPI: Kê khai công việc Lãnh đạo
    # =========================================================================
    ke_khai_lanh_dao_list: Mapped[List["KeKhaiLanhDao"]] = relationship(
        "KeKhaiLanhDao",
        back_populates="cong_chuc",
        foreign_keys="KeKhaiLanhDao.cong_chuc_id",
        lazy="dynamic"
    )
    
    # =========================================================================
    # v2.5.8 - LEADER KPI: Đánh giá d, đ, e
    # =========================================================================
    danh_gia_dde_list: Mapped[List["DanhGiaDDE"]] = relationship(
        "DanhGiaDDE",
        back_populates="cong_chuc",
        foreign_keys="DanhGiaDDE.cong_chuc_id",
        lazy="dynamic"
    )
    
    # -------------------------------------------------------------------------
    # INDEXES & CONSTRAINTS
    # -------------------------------------------------------------------------
    __table_args__ = (
        Index("idx_cong_chuc_ma", "ma_cc"),
        Index("idx_cong_chuc_don_vi", "don_vi_id"),
        Index("idx_cong_chuc_vai_tro", "vai_tro_id"),
        Index("idx_cong_chuc_active", "is_active", postgresql_where="is_deleted = false"),
        Index("idx_cong_chuc_lanh_dao", "is_lanh_dao", postgresql_where="is_deleted = false"),
    )
    
    def __repr__(self) -> str:
        return f"<CongChuc(id={self.id}, ma_cc='{self.ma_cc}', ho_ten='{self.ho_ten}')>"
    
    # -------------------------------------------------------------------------
    # HELPER PROPERTIES
    # -------------------------------------------------------------------------
    
    @property
    def ten_hien_thi(self) -> str:
        """Tên hiển thị đầy đủ với chức vụ."""
        if self.chuc_vu:
            return f"{self.ho_ten} - {self.chuc_vu}"
        return self.ho_ten
    
    @property
    def cap_bac(self) -> Optional[CapBacVaiTro]:
        """Lấy cấp bậc từ vai trò."""
        if self.vai_tro:
            return self.vai_tro.cap_bac
        return None