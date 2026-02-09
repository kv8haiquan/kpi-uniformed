"""
app/models/leader_kpi.py
========================
SQLAlchemy Models cho Module Kê khai KPI Lãnh đạo.

Bao gồm:
1. KeKhaiLanhDao - Kê khai công việc của Lãnh đạo
2. DanhGiaDDE - Đánh giá d, đ, e (năng lực lãnh đạo)

Phiên bản: 2.5.8-fix (27/01/2026)
Fix: ENUM type mismatch - đổi String → SQLEnum
"""

from datetime import date, datetime
from decimal import Decimal
from enum import Enum as PyEnum
from typing import Optional, List, TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    String, Integer, Boolean, Text, Date, DateTime,
    Numeric, ForeignKey, CheckConstraint, UniqueConstraint, Index,
    Enum as SQLEnum,
    func
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.user_org import CongChuc


# =============================================================================
# ENUMS - Định nghĩa Python Enum khớp với PostgreSQL ENUM
# =============================================================================

class TrangThaiHoanThanh(str, PyEnum):
    """Trạng thái hoàn thành công việc - khớp với trang_thai_hoan_thanh_enum trong DB."""
    DA_HOAN_THANH = "DA_HOAN_THANH"
    CHUA_HOAN_THANH = "CHUA_HOAN_THANH"


class TrangThaiKeKhaiLD(str, PyEnum):
    """Trạng thái kê khai của Lãnh đạo."""
    NHAP = "NHAP"
    CHO_PHE_DUYET = "CHO_PHE_DUYET"
    DA_PHE_DUYET = "DA_PHE_DUYET"
    TU_CHOI = "TU_CHOI"


class TrangThaiDDE(str, PyEnum):
    """Trạng thái đánh giá d, đ, e."""
    NHAP = "NHAP"
    CHO_PHE_DUYET = "CHO_PHE_DUYET"
    DA_PHE_DUYET = "DA_PHE_DUYET"


# =============================================================================
# MODEL: KÊ KHAI CÔNG VIỆC LÃNH ĐẠO
# =============================================================================

class KeKhaiLanhDao(BaseModel):
    """
    Kê khai công việc của Lãnh đạo.
    
    Khác với CC thường:
    - KHÔNG có danh mục SP, cấp độ, hệ số quy đổi
    - Mỗi công việc = 1 SP
    - Đơn giản hơn: chỉ cần tên công việc, mô tả, ngày thực hiện
    
    Luồng phê duyệt:
    - Phó ĐV → Trưởng ĐV duyệt
    - Trưởng ĐV → CCT duyệt
    - Phó CCT → CCT duyệt
    - CCT → Tự phê duyệt
    """
    
    __tablename__ = "ke_khai_lanh_dao"
    
    # =========================================================================
    # FOREIGN KEYS
    # =========================================================================
    
    cong_chuc_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("cong_chuc.id", ondelete="CASCADE"),
        nullable=False,
        comment="FK → cong_chuc.id (người kê khai - phải là Lãnh đạo)"
    )
    
    nguoi_phe_duyet_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("cong_chuc.id", ondelete="SET NULL"),
        nullable=True,
        comment="FK → cong_chuc.id (người phê duyệt)"
    )
    
    # =========================================================================
    # THỜI GIAN
    # =========================================================================
    
    thang: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Tháng kê khai (1-12)"
    )
    
    nam: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Năm kê khai"
    )
    
    # =========================================================================
    # THÔNG TIN CÔNG VIỆC
    # =========================================================================
    
    ten_cong_viec: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="Tên công việc"
    )
    
    mo_ta: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Mô tả chi tiết công việc"
    )
    
    ngay_thuc_hien: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="Ngày thực hiện công việc"
    )
    
    # =========================================================================
    # TRẠNG THÁI HOÀN THÀNH - SỬ DỤNG SQLEnum
    # =========================================================================
    
    trang_thai_hoan_thanh: Mapped[TrangThaiHoanThanh] = mapped_column(
        SQLEnum(
            TrangThaiHoanThanh,
            name="trang_thai_hoan_thanh_enum",
            create_type=False  # ENUM đã tồn tại trong DB từ migration
        ),
        nullable=False,
        default=TrangThaiHoanThanh.CHUA_HOAN_THANH,
        comment="Trạng thái hoàn thành: DA_HOAN_THANH, CHUA_HOAN_THANH"
    )
    
    so_luong: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        comment="Số lượng công việc (mặc định = 1)"
    )
    
    # =========================================================================
    # TRẠNG THÁI PHÊ DUYỆT - SỬ DỤNG String (không có ENUM riêng trong DB)
    # =========================================================================
    
    trang_thai: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=TrangThaiKeKhaiLD.NHAP.value,
        comment="Trạng thái: NHAP, CHO_PHE_DUYET, DA_PHE_DUYET, TU_CHOI"
    )
    
    # =========================================================================
    # ĐÁNH GIÁ (sau phê duyệt)
    # =========================================================================
    
    so_loi_chat_luong: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Số lỗi chất lượng (LĐ cấp trên chốt)"
    )
    
    so_loi_tien_do: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Số lỗi tiến độ (LĐ cấp trên chốt)"
    )
    
    # v2.7.4: Mô tả lỗi (Lãnh đạo tự nhập khi kê khai)
    ghi_chu_loi_chat_luong: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Mô tả / giải trình lỗi chất lượng"
    )
    
    ghi_chu_loi_tien_do: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Mô tả / giải trình lỗi tiến độ"
    )
    
    y_kien_lanh_dao: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Ý kiến của người phê duyệt"
    )
    
    # =========================================================================
    # SOFT DELETE
    # =========================================================================
    
    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Soft delete flag"
    )
    
    # =========================================================================
    # RELATIONSHIPS
    # =========================================================================
    
    cong_chuc: Mapped["CongChuc"] = relationship(
        "CongChuc",
        foreign_keys=[cong_chuc_id],
        back_populates="ke_khai_lanh_dao_list",
        lazy="selectin"
    )
    
    nguoi_phe_duyet: Mapped[Optional["CongChuc"]] = relationship(
        "CongChuc",
        foreign_keys=[nguoi_phe_duyet_id],
        lazy="selectin"
    )
    
    # =========================================================================
    # TABLE ARGS
    # =========================================================================
    
    __table_args__ = (
        CheckConstraint("thang BETWEEN 1 AND 12", name="ck_kkld_thang"),
        CheckConstraint("nam >= 2025", name="ck_kkld_nam"),
        CheckConstraint("so_luong >= 1", name="ck_kkld_so_luong"),
        CheckConstraint("so_loi_chat_luong >= 0", name="ck_kkld_loi_cl"),
        CheckConstraint("so_loi_tien_do >= 0", name="ck_kkld_loi_td"),
        CheckConstraint(
            "trang_thai IN ('NHAP', 'CHO_PHE_DUYET', 'DA_PHE_DUYET', 'TU_CHOI')",
            name="ck_kkld_trang_thai"
        ),
        Index("idx_kkld_cong_chuc", "cong_chuc_id"),
        Index("idx_kkld_thang_nam", "thang", "nam"),
        Index("idx_kkld_trang_thai", "trang_thai"),
        Index("idx_kkld_nguoi_phe_duyet", "nguoi_phe_duyet_id"),
        Index("idx_kkld_deleted", "is_deleted"),
        Index("idx_kkld_cc_thang_nam", "cong_chuc_id", "thang", "nam", "is_deleted"),
        {"comment": "Kê khai công việc của Lãnh đạo (Phó ĐV, Trưởng ĐV, Phó CCT, CCT)"}
    )
    
    # =========================================================================
    # COMPUTED PROPERTIES
    # =========================================================================
    
    @property
    def is_hoan_thanh(self) -> bool:
        """Kiểm tra công việc đã hoàn thành chưa."""
        return self.trang_thai_hoan_thanh == TrangThaiHoanThanh.DA_HOAN_THANH
    
    @property
    def is_dat_chat_luong(self) -> bool:
        """Kiểm tra công việc đạt chất lượng (không có lỗi)."""
        return self.so_loi_chat_luong == 0
    
    @property
    def is_dung_tien_do(self) -> bool:
        """Kiểm tra công việc đúng tiến độ (không có lỗi)."""
        return self.so_loi_tien_do == 0


# =============================================================================
# MODEL: ĐÁNH GIÁ d, đ, e
# =============================================================================

class DanhGiaDDE(BaseModel):
    """
    Đánh giá d, đ, e của Lãnh đạo.
    
    Các chỉ số:
    - d: Kết quả đơn vị (100% hoặc 50%)
    - đ: Tổ chức triển khai (100% hoặc 50%)
    - e: Đoàn kết nội bộ (100% hoặc 50%)
    
    Mỗi LĐ chỉ có 1 bản ghi đánh giá cho mỗi tháng.
    
    Luồng phê duyệt:
    - Phó ĐV → Trưởng ĐV duyệt
    - Trưởng ĐV → CCT duyệt
    - Phó CCT → CCT duyệt
    - CCT → Tự phê duyệt
    """
    
    __tablename__ = "danh_gia_dde"
    
    # =========================================================================
    # FOREIGN KEYS
    # =========================================================================
    
    cong_chuc_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("cong_chuc.id", ondelete="CASCADE"),
        nullable=False,
        comment="FK → cong_chuc.id (người đánh giá - phải là Lãnh đạo)"
    )
    
    nguoi_phe_duyet_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("cong_chuc.id", ondelete="SET NULL"),
        nullable=True,
        comment="FK → cong_chuc.id (người phê duyệt)"
    )
    
    # =========================================================================
    # THỜI GIAN
    # =========================================================================
    
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
    
    # =========================================================================
    # CHỈ SỐ d: KẾT QUẢ ĐƠN VỊ
    # =========================================================================
    
    d_ket_qua_don_vi: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=100,
        comment="d: Kết quả đơn vị (100 hoặc 50)"
    )
    
    d_ghi_chu: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Ghi chú cho chỉ số d"
    )
    
    # =========================================================================
    # CHỈ SỐ đ: TỔ CHỨC TRIỂN KHAI
    # =========================================================================
    
    dd_to_chuc_trien_khai: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=100,
        comment="đ: Tổ chức triển khai (100 hoặc 50)"
    )
    
    dd_ghi_chu: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Ghi chú cho chỉ số đ"
    )
    
    # =========================================================================
    # CHỈ SỐ e: ĐOÀN KẾT NỘI BỘ
    # =========================================================================
    
    e_doan_ket_noi_bo: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=100,
        comment="e: Đoàn kết nội bộ (100 hoặc 50)"
    )
    
    e_ghi_chu: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Ghi chú cho chỉ số e"
    )
    
    # =========================================================================
    # TRẠNG THÁI PHÊ DUYỆT
    # =========================================================================
    
    trang_thai: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=TrangThaiDDE.NHAP.value,
        comment="Trạng thái: NHAP, CHO_PHE_DUYET, DA_PHE_DUYET"
    )
    
    y_kien_phe_duyet: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Ý kiến của người phê duyệt"
    )
    
    ngay_phe_duyet: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Ngày phê duyệt"
    )
    
    # =========================================================================
    # GIÁ TRỊ SAU PHÊ DUYỆT (LĐ cấp trên có thể điều chỉnh)
    # =========================================================================
    
    d_phe_duyet: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Giá trị d sau phê duyệt (nếu điều chỉnh)"
    )
    
    dd_phe_duyet: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Giá trị đ sau phê duyệt (nếu điều chỉnh)"
    )
    
    e_phe_duyet: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Giá trị e sau phê duyệt (nếu điều chỉnh)"
    )
    
    # =========================================================================
    # RELATIONSHIPS
    # =========================================================================
    
    cong_chuc: Mapped["CongChuc"] = relationship(
        "CongChuc",
        foreign_keys=[cong_chuc_id],
        back_populates="danh_gia_dde_list",
        lazy="selectin"
    )
    
    nguoi_phe_duyet: Mapped[Optional["CongChuc"]] = relationship(
        "CongChuc",
        foreign_keys=[nguoi_phe_duyet_id],
        lazy="selectin"
    )
    
    # =========================================================================
    # TABLE ARGS
    # =========================================================================
    
    __table_args__ = (
        UniqueConstraint("cong_chuc_id", "thang", "nam", name="uq_dde_user_month"),
        CheckConstraint("thang BETWEEN 1 AND 12", name="ck_dde_thang"),
        CheckConstraint("nam >= 2025", name="ck_dde_nam"),
        CheckConstraint("d_ket_qua_don_vi IN (50, 100)", name="ck_dde_d"),
        CheckConstraint("dd_to_chuc_trien_khai IN (50, 100)", name="ck_dde_dd"),
        CheckConstraint("e_doan_ket_noi_bo IN (50, 100)", name="ck_dde_e"),
        CheckConstraint(
            "trang_thai IN ('NHAP', 'CHO_PHE_DUYET', 'DA_PHE_DUYET')",
            name="ck_dde_trang_thai"
        ),
        Index("idx_dde_cong_chuc", "cong_chuc_id"),
        Index("idx_dde_thang_nam", "thang", "nam"),
        Index("idx_dde_trang_thai", "trang_thai"),
        Index("idx_dde_nguoi_phe_duyet", "nguoi_phe_duyet_id"),
        {"comment": "Đánh giá d, đ, e của Lãnh đạo (năng lực lãnh đạo)"}
    )
    
    # =========================================================================
    # COMPUTED PROPERTIES
    # =========================================================================
    
    @property
    def d_final(self) -> int:
        """Giá trị d cuối cùng (sau phê duyệt hoặc tự đánh giá)."""
        return self.d_phe_duyet if self.d_phe_duyet is not None else self.d_ket_qua_don_vi
    
    @property
    def dd_final(self) -> int:
        """Giá trị đ cuối cùng (sau phê duyệt hoặc tự đánh giá)."""
        return self.dd_phe_duyet if self.dd_phe_duyet is not None else self.dd_to_chuc_trien_khai
    
    @property
    def e_final(self) -> int:
        """Giá trị e cuối cùng (sau phê duyệt hoặc tự đánh giá)."""
        return self.e_phe_duyet if self.e_phe_duyet is not None else self.e_doan_ket_noi_bo
    
    @property
    def d_percent(self) -> float:
        """Giá trị d dạng phần trăm (0.5 hoặc 1.0)."""
        return self.d_final / 100.0
    
    @property
    def dd_percent(self) -> float:
        """Giá trị đ dạng phần trăm (0.5 hoặc 1.0)."""
        return self.dd_final / 100.0
    
    @property
    def e_percent(self) -> float:
        """Giá trị e dạng phần trăm (0.5 hoặc 1.0)."""
        return self.e_final / 100.0