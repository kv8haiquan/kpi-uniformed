"""
app/models/kpi_assessment.py
============================
Models cho đánh giá và xếp loại KPI:
- DanhGiaThang: Đánh giá tổng hợp tháng
- TieuChiChung: Master data danh mục tiêu chí chung
- TieuChiChungDanhGia: Chi tiết điểm tiêu chí chung (Binary Scoring)
- LanhDaoChiSo: Chỉ số d, đ, e cho lãnh đạo

CÔNG THỨC TÍNH ĐIỂM:
- Công chức: Điểm = A (30%) + B (70% × KPI)
  + A: Tiêu chí chung (tối đa 30 điểm)
  + B: KPI = a × b × c

- Lãnh đạo: Điểm = A (30%) + B (70% × KPI × d × đ × e)
  + d: Kết quả hoạt động đơn vị (0.5 hoặc 1)
  + đ: Khả năng tổ chức (0.5 hoặc 1)
  + e: Năng lực đoàn kết (0.5 hoặc 1)

TIÊU CHÍ CHUNG - LOGIC CHẤM ĐIỂM NHỊ PHÂN (v2.4.1):
- Nhóm 1 (1.1, 1.2): 5 điểm/tiêu chí, mặc định ĐẠT (is_achieved=True)
- Nhóm 2 (2.1-2.4): 2.5 điểm/tiêu chí, mặc định ĐẠT
- Nhóm 3 (3.1-3.4): 2.5 điểm/tiêu chí, mặc định KHÔNG ĐẠT (is_achieved=False)
- Công thức: điểm = diem_toi_da nếu is_achieved else 0

MỨC XẾP LOẠI:
- A: >= 90 điểm (Hoàn thành xuất sắc)
- B: 70-89 điểm (Hoàn thành tốt)
- C: 50-69 điểm (Hoàn thành)
- D: < 50 điểm (Không hoàn thành)

Phiên bản: 3.5.0 (02/02/2026)
- v3.5.0: Thêm CHO_CAP2, TU_CHOI vào TrangThaiTieuChi
- v3.5.0: Thêm ly_do_tu_choi_tc, nguoi_tu_choi_tc_id, ngay_tu_choi_tc
"""

import uuid
import enum
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List, TYPE_CHECKING

from sqlalchemy import (
    String, 
    Integer, 
    Boolean, 
    Date,
    Text, 
    ForeignKey,
    Index,
    Numeric,
    CheckConstraint,
    UniqueConstraint,
    Enum as SQLEnum,
    DateTime,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.models.base import BaseModel, BaseModelWithSoftDelete

if TYPE_CHECKING:
    from app.models.user_org import CongChuc


# =============================================================================
# ENUMS
# =============================================================================

class MucXepLoai(str, enum.Enum):
    """Mức xếp loại công chức."""
    A = "A"  # Hoàn thành xuất sắc (>= 90 điểm)
    B = "B"  # Hoàn thành tốt (70-89 điểm)
    C = "C"  # Hoàn thành (50-69 điểm)
    D = "D"  # Không hoàn thành (< 50 điểm)


class TrangThaiDanhGia(str, enum.Enum):
    """Trạng thái của đánh giá tháng."""
    DANG_DANH_GIA = "DANG_DANH_GIA"
    CHO_TONG_HOP = "CHO_TONG_HOP"
    DA_TONG_HOP = "DA_TONG_HOP"
    CHO_PHE_DUYET = "CHO_PHE_DUYET"
    HOAN_THANH = "HOAN_THANH"
    CO_KIEN_NGHI = "CO_KIEN_NGHI"


class TrangThaiTieuChi(str, enum.Enum):
    """
    Trạng thái của việc chấm tiêu chí chung.
    v3.5.0: Thêm CHO_CAP2 (chờ ĐT duyệt cấp 2) và TU_CHOI.
    """
    NHAP = "NHAP"
    CHO_PHE_DUYET = "CHO_PHE_DUYET"
    CHO_CAP2 = "CHO_CAP2"            # ⭐ v3.5: Phó ĐT đã duyệt, chờ ĐT
    DA_PHE_DUYET = "DA_PHE_DUYET"
    TU_CHOI = "TU_CHOI"              # ⭐ v3.5: Bị từ chối → reset về NHAP


class LoaiLogicTieuChi(str, enum.Enum):
    """Logic chấm điểm tiêu chí."""
    ALL_OR_NOTHING = "ALL_OR_NOTHING"
    BONUS = "BONUS"


# =============================================================================
# MODELS
# =============================================================================

class DanhGiaThang(BaseModelWithSoftDelete):
    """Đánh giá tổng hợp tháng của công chức."""
    
    __tablename__ = "danh_gia_thang"
    
    cong_chuc_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("cong_chuc.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="ID công chức được đánh giá"
    )
    
    thang: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Tháng đánh giá (1-12)"
    )
    
    nam: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Năm đánh giá"
    )
    
    so_sp_goc_duoc_giao: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        comment="Số SP gốc được giao"
    )
    
    so_ngay_lam_viec: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Số ngày làm việc"
    )
    
    so_ngay_nghi_phep: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default="0",
        comment="Số ngày nghỉ phép"
    )
    
    diem_tieu_chi_chung: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 2),
        nullable=True,
        comment="Tổng điểm tiêu chí chung (0-30)"
    )
    
    diem_kpi: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 4),
        nullable=True,
        comment="Điểm KPI (tỷ lệ 0-1)"
    )
    
    diem_so_luong: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 4),
        nullable=True,
        comment="Điểm số lượng (a)"
    )
    
    diem_chat_luong: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 4),
        nullable=True,
        comment="Điểm chất lượng (b)"
    )
    
    diem_tien_do: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 4),
        nullable=True,
        comment="Điểm tiến độ (c)"
    )
    
    diem_tong: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 2),
        nullable=True,
        comment="Điểm tổng (0-100)"
    )
    
    muc_xep_loai_tu_dong: Mapped[Optional[MucXepLoai]] = mapped_column(
        SQLEnum(MucXepLoai, name="muc_xep_loai_enum", create_type=True),
        nullable=True,
        comment="Xếp loại tự động"
    )
    
    muc_xep_loai_de_xuat: Mapped[Optional[MucXepLoai]] = mapped_column(
        SQLEnum(MucXepLoai, name="muc_xep_loai_enum", create_type=False),
        nullable=True,
        comment="Xếp loại đề xuất"
    )
    
    muc_xep_loai_chinh_thuc: Mapped[Optional[MucXepLoai]] = mapped_column(
        SQLEnum(MucXepLoai, name="muc_xep_loai_enum", create_type=False),
        nullable=True,
        index=True,
        comment="Xếp loại chính thức"
    )
    
    ly_do_dieu_chinh: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Lý do điều chỉnh"
    )
    
    nguoi_de_xuat_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("cong_chuc.id", ondelete="SET NULL"),
        nullable=True,
        comment="ID Trưởng ĐV đề xuất"
    )
    
    nguoi_phe_duyet_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("cong_chuc.id", ondelete="SET NULL"),
        nullable=True,
        comment="ID CCT phê duyệt"
    )
    
    trang_thai: Mapped[TrangThaiDanhGia] = mapped_column(
        SQLEnum(TrangThaiDanhGia, name="trang_thai_danh_gia_enum", create_type=True),
        nullable=False,
        server_default="DANG_DANH_GIA",
        index=True,
        comment="Trạng thái đánh giá"
    )
    
    ngay_tong_hop: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Ngày tổng hợp"
    )
    
    ngay_de_xuat: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Ngày đề xuất"
    )
    
    ngay_phe_duyet: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Ngày phê duyệt"
    )
    
    uu_diem: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    han_che: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ghi_chu: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # -------------------------------------------------------------------------
    # PHÊ DUYỆT TIÊU CHÍ CHUNG 2 CẤP (v2.5 - 29/01/2026)
    # Luồng: CC tự chấm → Phó ĐT duyệt (cấp 1) → ĐT duyệt lại (cấp 2)
    # -------------------------------------------------------------------------
    
    nguoi_phe_duyet_tc_cap1_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("cong_chuc.id", ondelete="SET NULL"),
        nullable=True,
        comment="ID Phó ĐT phê duyệt tiêu chí chung cấp 1"
    )
    
    nguoi_phe_duyet_tc_cap2_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("cong_chuc.id", ondelete="SET NULL"),
        nullable=True,
        comment="ID Đội trưởng phê duyệt tiêu chí chung cấp 2 (duyệt lại)"
    )
    
    trang_thai_tc: Mapped[Optional[TrangThaiTieuChi]] = mapped_column(
        SQLEnum(TrangThaiTieuChi, name="trang_thai_tieu_chi_enum", create_type=False),
        server_default="NHAP",
        nullable=True,
        comment="Trạng thái phê duyệt tiêu chí chung"
    )
    
    ngay_phe_duyet_tc_cap1: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Thời điểm Phó ĐT phê duyệt tiêu chí"
    )
    
    ngay_phe_duyet_tc_cap2: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Thời điểm ĐT duyệt lại tiêu chí"
    )
    
    diem_tc_cap1: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 2),
        nullable=True,
        comment="Điểm tiêu chí chung sau khi Phó ĐT duyệt (0-30)"
    )
    
    diem_tc_cap2: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 2),
        nullable=True,
        comment="Điểm tiêu chí chung sau khi ĐT duyệt lại (0-30) - Điểm cuối cùng"
    )
    
    # -------------------------------------------------------------------------
    # TỪ CHỐI TIÊU CHÍ CHUNG (v3.5.0 - 02/02/2026)
    # -------------------------------------------------------------------------
    
    ly_do_tu_choi_tc: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Lý do từ chối tiêu chí chung"
    )
    
    nguoi_tu_choi_tc_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("cong_chuc.id", ondelete="SET NULL"),
        nullable=True,
        comment="ID người từ chối tiêu chí chung"
    )
    
    ngay_tu_choi_tc: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Thời điểm từ chối tiêu chí chung"
    )
    
    # -------------------------------------------------------------------------
    # KHÓA DỮ LIỆU (v2.5 - 29/01/2026)
    # -------------------------------------------------------------------------
    
    is_khoa: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="false",
        comment="Khóa dữ liệu sau khi CCT phê duyệt báo cáo xếp loại tháng"
    )

    # Relationships
    cong_chuc: Mapped["CongChuc"] = relationship(
        "CongChuc",
        back_populates="danh_gias",
        foreign_keys=[cong_chuc_id],
        lazy="joined"
    )
    
    nguoi_de_xuat: Mapped[Optional["CongChuc"]] = relationship(
        "CongChuc",
        foreign_keys=[nguoi_de_xuat_id],
        lazy="joined"
    )
    
    nguoi_phe_duyet: Mapped[Optional["CongChuc"]] = relationship(
        "CongChuc",
        foreign_keys=[nguoi_phe_duyet_id],
        lazy="joined"
    )

    # Người phê duyệt tiêu chí cấp 1 (Phó ĐT)
    nguoi_phe_duyet_tc_cap1: Mapped[Optional["CongChuc"]] = relationship(
        "CongChuc",
        foreign_keys=[nguoi_phe_duyet_tc_cap1_id],
        lazy="joined"
    )
    
    # Người phê duyệt tiêu chí cấp 2 (ĐT)
    nguoi_phe_duyet_tc_cap2: Mapped[Optional["CongChuc"]] = relationship(
        "CongChuc",
        foreign_keys=[nguoi_phe_duyet_tc_cap2_id],
        lazy="joined"
    )
    
    # ⭐ v3.5: Người từ chối tiêu chí
    nguoi_tu_choi_tc: Mapped[Optional["CongChuc"]] = relationship(
        "CongChuc",
        foreign_keys=[nguoi_tu_choi_tc_id],
        lazy="joined"
    )
    
    tieu_chi_chungs: Mapped[List["TieuChiChungDanhGia"]] = relationship(
        "TieuChiChungDanhGia",
        back_populates="danh_gia_thang",
        lazy="selectin",
        cascade="all, delete-orphan"
    )
    
    lanh_dao_chi_so: Mapped[Optional["LanhDaoChiSo"]] = relationship(
        "LanhDaoChiSo",
        back_populates="danh_gia_thang",
        uselist=False,
        lazy="joined",
        cascade="all, delete-orphan"
    )
    
    __table_args__ = (
        CheckConstraint("thang BETWEEN 1 AND 12", name="ck_danh_gia_thang"),
        CheckConstraint("nam >= 2025", name="ck_danh_gia_nam"),
        CheckConstraint(
            "diem_tieu_chi_chung IS NULL OR diem_tieu_chi_chung BETWEEN 0 AND 30",
            name="ck_danh_gia_diem_tc"
        ),
        CheckConstraint(
            "diem_kpi IS NULL OR diem_kpi BETWEEN 0 AND 1",
            name="ck_danh_gia_diem_kpi"
        ),
        CheckConstraint(
            "diem_tong IS NULL OR diem_tong BETWEEN 0 AND 100",
            name="ck_danh_gia_diem_tong"
        ),
        UniqueConstraint("cong_chuc_id", "thang", "nam", name="uq_danh_gia_cc_thang_nam"),
        Index("idx_danh_gia_cc", "cong_chuc_id"),
        Index("idx_danh_gia_thang_nam", "thang", "nam"),
        Index("idx_danh_gia_trang_thai", "trang_thai"),
        Index("idx_danh_gia_xep_loai", "muc_xep_loai_chinh_thuc"),
    )
    
    def __repr__(self) -> str:
        return f"<DanhGiaThang(cc_id={self.cong_chuc_id}, thang={self.thang}/{self.nam})>"


class TieuChiChung(BaseModel):
    """
    Master Data: Danh mục tiêu chí chung.
    Seed 1 lần, không thay đổi. Gồm 31 tiêu chí.
    """
    
    __tablename__ = "tieu_chi_chung"
    
    ma_tieu_chi: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        unique=True,
        comment="Mã tiêu chí: 1.1, 1.2, 2.1, ..."
    )
    
    ma_tieu_chi_con: Mapped[Optional[str]] = mapped_column(
        String(10),
        nullable=True,
        comment="Mã tiêu chí con: a1, a2, b1, ..."
    )
    
    nhom_tieu_chi: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Nhóm: 1, 2, 3"
    )
    
    ten_tieu_chi: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Tên tiêu chí"
    )
    
    mo_ta: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Mô tả"
    )
    
    diem_toi_da: Mapped[Decimal] = mapped_column(
        Numeric(4, 2),
        nullable=False,
        comment="Điểm tối đa"
    )
    
    gia_tri_mac_dinh: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        comment="Giá trị mặc định: TRUE (nhóm 1,2), FALSE (nhóm 3)"
    )
    
    loai_logic: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="Logic: ALL_OR_NOTHING hoặc BONUS"
    )
    
    parent_ma_tieu_chi: Mapped[Optional[str]] = mapped_column(
        String(10),
        nullable=True,
        comment="Mã tiêu chí cha"
    )
    
    thu_tu: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Thứ tự hiển thị"
    )
    
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default="true"
    )
    
    __table_args__ = (
        CheckConstraint("nhom_tieu_chi BETWEEN 1 AND 3", name="ck_tc_nhom"),
        CheckConstraint(
            "loai_logic IN ('ALL_OR_NOTHING', 'BONUS')",
            name="ck_tc_loai_logic"
        ),
        Index("idx_tieu_chi_nhom", "nhom_tieu_chi"),
        Index("idx_tieu_chi_parent", "parent_ma_tieu_chi"),
    )
    
    def __repr__(self) -> str:
        return f"<TieuChiChung(ma={self.ma_tieu_chi}, diem_max={self.diem_toi_da})>"


class TieuChiChungDanhGia(BaseModel):
    """
    Kết quả chấm tiêu chí chung của CC trong tháng.
    
    LOGIC CHẤM ĐIỂM NHỊ PHÂN (v2.4.1):
    - is_achieved_cc: CC tự đánh giá (True/False)
    - is_achieved_ld: LĐ điều chỉnh (có thể khác CC)
    - Điểm = diem_toi_da nếu is_achieved else 0
    """
    
    __tablename__ = "tieu_chi_chung_danh_gia"
    
    danh_gia_thang_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("danh_gia_thang.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="ID đánh giá tháng"
    )
    
    tieu_chi_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tieu_chi_chung.id", ondelete="RESTRICT"),
        nullable=False,
        comment="ID tiêu chí chung"
    )
    
    # =========================================================================
    # CHẤM ĐIỂM NHỊ PHÂN - LƯU CẢ 2 BẢN TÍCH
    # =========================================================================
    
    is_achieved_cc: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        comment="BẢN TÍCH CC: TRUE=Đạt, FALSE=Không đạt"
    )
    
    is_achieved_ld: Mapped[Optional[bool]] = mapped_column(
        Boolean,
        nullable=True,
        comment="BẢN TÍCH LĐ: NULL=Chưa duyệt"
    )
    
    diem_tu_cham: Mapped[Decimal] = mapped_column(
        Numeric(4, 2),
        nullable=False,
        comment="Điểm CC = diem_toi_da if is_achieved_cc else 0"
    )
    
    diem_phe_duyet: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(4, 2),
        nullable=True,
        comment="Điểm LĐ = diem_toi_da if is_achieved_ld else 0"
    )
    
    # =========================================================================
    # LUỒNG PHÊ DUYỆT
    # =========================================================================
    
    trang_thai: Mapped[TrangThaiTieuChi] = mapped_column(
        SQLEnum(TrangThaiTieuChi, name="trang_thai_tieu_chi_enum", create_type=True),
        nullable=False,
        server_default="NHAP",
        index=True,
        comment="NHAP, CHO_PHE_DUYET, DA_PHE_DUYET"
    )
    
    nguoi_phe_duyet_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("cong_chuc.id", ondelete="SET NULL"),
        nullable=True,
        comment="ID người phê duyệt"
    )
    
    ngay_gui: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Ngày gửi phê duyệt"
    )
    
    ngay_phe_duyet: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Ngày phê duyệt"
    )
    
    ghi_chu_cc: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Ghi chú của CC"
    )
    
    ghi_chu_ld: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Ghi chú của LĐ"
    )
    
    ly_do_dieu_chinh: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Lý do LĐ điều chỉnh"
    )
    
    # Relationships
    danh_gia_thang: Mapped["DanhGiaThang"] = relationship(
        "DanhGiaThang",
        back_populates="tieu_chi_chungs",
        lazy="joined"
    )
    
    tieu_chi: Mapped["TieuChiChung"] = relationship(
        "TieuChiChung",
        lazy="joined"
    )
    
    nguoi_phe_duyet: Mapped[Optional["CongChuc"]] = relationship(
        "CongChuc",
        lazy="joined"
    )
    
    __table_args__ = (
        UniqueConstraint(
            "danh_gia_thang_id", "tieu_chi_id",
            name="uq_tc_danh_gia_tieu_chi"
        ),
        Index("idx_tc_chung_danh_gia", "danh_gia_thang_id"),
        Index("idx_tc_trang_thai", "trang_thai"),
    )
    
    def __repr__(self) -> str:
        return f"<TieuChiChungDanhGia(tc_id={self.tieu_chi_id}, cc={self.is_achieved_cc})>"
    
    @property
    def has_difference(self) -> bool:
        """Kiểm tra LĐ điều chỉnh khác CC."""
        if self.is_achieved_ld is None:
            return False
        return self.is_achieved_cc != self.is_achieved_ld


class LanhDaoChiSo(BaseModel):
    """Chỉ số d, đ, e cho lãnh đạo."""
    
    __tablename__ = "lanh_dao_chi_so"
    
    danh_gia_thang_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("danh_gia_thang.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        comment="ID đánh giá tháng (1-1)"
    )
    
    chi_so_d: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        default=Decimal("1.0"),
        server_default="1.0",
        comment="Chỉ số d (0.5 hoặc 1.0)"
    )
    
    ghi_chu_d: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    co_cc_khong_hoan_thanh: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="false"
    )
    
    chi_so_dd: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        default=Decimal("1.0"),
        server_default="1.0",
        comment="Chỉ số đ (0.5 hoặc 1.0)"
    )
    
    ghi_chu_dd: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    co_ton_tai_cham_tre: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="false"
    )
    
    chi_so_e: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        default=Decimal("1.0"),
        server_default="1.0",
        comment="Chỉ số e (0.5 hoặc 1.0)"
    )
    
    ghi_chu_e: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    co_mau_thuan_noi_bo: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="false"
    )
    
    danh_gia_thang: Mapped["DanhGiaThang"] = relationship(
        "DanhGiaThang",
        back_populates="lanh_dao_chi_so",
        lazy="joined"
    )
    
    __table_args__ = (
        CheckConstraint("chi_so_d IN (0.5, 1.0)", name="ck_ld_chi_so_d"),
        CheckConstraint("chi_so_dd IN (0.5, 1.0)", name="ck_ld_chi_so_dd"),
        CheckConstraint("chi_so_e IN (0.5, 1.0)", name="ck_ld_chi_so_e"),
    )
    
    @property
    def he_so_lanh_dao(self) -> Decimal:
        """Tính hệ số lãnh đạo = d × đ × e"""
        return self.chi_so_d * self.chi_so_dd * self.chi_so_e


# =============================================================================
# HELPER CONSTANTS - ĐIỂM TỐI ĐA THEO MÃ TIÊU CHÍ
# =============================================================================

DIEM_TOI_DA_TIEU_CHI = {
    "1.1": Decimal("5.0"),
    "1.2": Decimal("5.0"),
    "2.1": Decimal("2.5"),
    "2.2": Decimal("2.5"),
    "2.3": Decimal("2.5"),
    "2.4": Decimal("2.5"),
    "3.1": Decimal("2.5"),
    "3.2": Decimal("2.5"),
    "3.3": Decimal("2.5"),
    "3.4": Decimal("2.5"),
}


def get_diem_toi_da(ma_tieu_chi: str) -> Decimal:
    """Lấy điểm tối đa của tiêu chí."""
    return DIEM_TOI_DA_TIEU_CHI.get(ma_tieu_chi, Decimal("0"))


def tinh_diem_tu_is_achieved(ma_tieu_chi: str, is_achieved: bool) -> Decimal:
    """Tính điểm từ is_achieved (Binary Scoring)."""
    if is_achieved:
        return get_diem_toi_da(ma_tieu_chi)
    return Decimal("0")