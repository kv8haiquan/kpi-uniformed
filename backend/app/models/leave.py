"""
app/models/leave.py
===================
Models cho Quản lý Nghỉ phép (Leave Management).

Module này hỗ trợ đặc thù nghiệp vụ Hải quan:
- Công chức làm việc theo CA/KÍP, không nghỉ cố định T7/CN
- CC phải đăng ký NGHI_TUAN trên hệ thống cho ngày nghỉ tuần
- Công thức KPI: SP_được_giao = (Ngày_dương_lịch - Ngày_nghỉ_đã_duyệt) × 96

Luồng phê duyệt nghỉ phép:
1. CC đăng ký nghỉ → chọn Phó ĐV để phê duyệt
2. Phó ĐV phê duyệt → Trưởng ĐV phê duyệt Phó ĐV
3. Trưởng ĐV đăng ký → CCT phê duyệt
4. CCT tự phê duyệt

Phiên bản: 1.0 (25/01/2026)
"""

import uuid
import enum
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, TYPE_CHECKING

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
    Enum as SQLEnum,
    DateTime,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModelWithSoftDelete

# =============================================================================
# TYPE_CHECKING - Tránh circular import
# =============================================================================
if TYPE_CHECKING:
    from app.models.user_org import CongChuc


# =============================================================================
# ENUMS
# =============================================================================

class LoaiNghi(str, enum.Enum):
    """
    Loại nghỉ phép - 9 loại.
    
    ĐẶC THÙ HẢI QUAN:
    - NGHI_TUAN: Thay thế T7/CN - HQ làm ca/kíp, linh hoạt trong tháng
    - Tất cả loại nghỉ đều cần phê duyệt (kể cả NGHI_TUAN)
    - NGHI_TUAN ≠ PHEP_NAM (hai loại này tách biệt)
    """
    NGHI_TUAN = "NGHI_TUAN"         # Nghỉ tuần (thay thế T7/CN)
    PHEP_NAM = "PHEP_NAM"           # Phép năm (12-14 ngày/năm)
    NGHI_LE = "NGHI_LE"             # Nghỉ các ngày lễ
    NGHI_TET = "NGHI_TET"
    NGHI_OM = "NGHI_OM"             # Ốm đau
    THAI_SAN = "THAI_SAN"           # Thai sản
    VIEC_RIENG = "VIEC_RIENG"       # Việc riêng có lương
    KHONG_LUONG = "KHONG_LUONG"     # Nghỉ không lương
    NGHI_BU = "NGHI_BU"             # Nghỉ bù
    KHAC = "KHAC"                   # Các trường hợp khác


class TrangThaiNghi(str, enum.Enum):
    """Trạng thái của đơn nghỉ phép."""
    CHO_PHE_DUYET = "CHO_PHE_DUYET"  # Đang chờ phê duyệt
    DA_PHE_DUYET = "DA_PHE_DUYET"    # Đã được phê duyệt
    TU_CHOI = "TU_CHOI"              # Bị từ chối
    HUY = "HUY"                      # Đã hủy


# =============================================================================
# MODELS
# =============================================================================

class DangKyNghi(BaseModelWithSoftDelete):
    """
    Đăng ký nghỉ phép của công chức.
    
    Mỗi đơn nghỉ ghi nhận:
    - Ai đăng ký (cong_chuc_id)
    - Loại nghỉ (NGHI_TUAN, PHEP_NAM, NGHI_LE, ...)
    - Thời gian nghỉ (tu_ngay, den_ngay, so_ngay)
    - Ai phê duyệt (nguoi_phe_duyet_id)
    - Áp dụng cho tháng/năm nào (thang_ap_dung, nam_ap_dung)
    
    Công thức KPI (v2.3):
    SP_được_giao = (Ngày_dương_lịch - Tổng_ngày_nghỉ_đã_duyệt) × 96
    
    Relationships:
    - cong_chuc: Người đăng ký nghỉ (back_populates với CongChuc.dang_ky_nghis)
    - nguoi_phe_duyet: Người phê duyệt đơn
    """
    
    __tablename__ = "dang_ky_nghi"
    
    # -------------------------------------------------------------------------
    # NGƯỜI ĐĂNG KÝ
    # -------------------------------------------------------------------------
    
    cong_chuc_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("cong_chuc.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="ID công chức đăng ký nghỉ"
    )
    
    # -------------------------------------------------------------------------
    # THÔNG TIN NGHỈ
    # -------------------------------------------------------------------------
    
    loai_nghi: Mapped[LoaiNghi] = mapped_column(
        SQLEnum(LoaiNghi, name="loai_nghi_enum", create_type=True),
        nullable=False,
        index=True,
        comment="Loại nghỉ phép"
    )
    
    tu_ngay: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="Ngày bắt đầu nghỉ"
    )
    
    den_ngay: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="Ngày kết thúc nghỉ"
    )
    
    so_ngay: Mapped[Decimal] = mapped_column(
        Numeric(4, 1),
        nullable=False,
        comment="Số ngày nghỉ thực tế (cho phép 0.5)"
    )
    
    ly_do: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Lý do xin nghỉ"
    )
    
    tai_lieu_dinh_kem: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="Đường dẫn file đính kèm"
    )
    
    # -------------------------------------------------------------------------
    # PHÊ DUYỆT
    # -------------------------------------------------------------------------
    
    nguoi_phe_duyet_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("cong_chuc.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="ID người phê duyệt"
    )
    
    trang_thai: Mapped[TrangThaiNghi] = mapped_column(
        SQLEnum(TrangThaiNghi, name="trang_thai_nghi_enum", create_type=True),
        nullable=False,
        server_default="CHO_PHE_DUYET",
        index=True,
        comment="Trạng thái đơn nghỉ"
    )
    
    ly_do_tu_choi: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Lý do từ chối"
    )
    
    ngay_phe_duyet: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Thời điểm phê duyệt/từ chối"
    )
    
    ghi_chu_phe_duyet: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Ghi chú của người phê duyệt"
    )

    # -------------------------------------------------------------------------
    # PHÊ DUYỆT CẤP 2 - ĐỘI TRƯỞNG (v2.5 - 29/01/2026)
    # Luồng: CC → Phó ĐT (cấp 1) → ĐT (cấp 2)
    # -------------------------------------------------------------------------
    
    nguoi_phe_duyet_cap2_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("cong_chuc.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="ID Đội trưởng phê duyệt cấp 2"
    )
    
    trang_thai_cap1: Mapped[Optional[TrangThaiNghi]] = mapped_column(
        SQLEnum(TrangThaiNghi, name="trang_thai_nghi_enum", create_type=False),
        nullable=True,
        comment="Trạng thái phê duyệt cấp 1 (Phó ĐT)"
    )
    
    ngay_phe_duyet_cap1: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Thời điểm Phó ĐT phê duyệt cấp 1"
    )
    
    ly_do_tu_choi_cap1: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Lý do Phó ĐT từ chối (nếu có)"
    )
    # -------------------------------------------------------------------------
    # LIÊN KẾT KPI
    # -------------------------------------------------------------------------
    
    thang_ap_dung: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Tháng áp dụng cho tính KPI (1-12)"
    )
    
    nam_ap_dung: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Năm áp dụng cho tính KPI"
    )
    
    da_tinh_kpi: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="false",
        comment="Đánh dấu đã được tính vào KPI chưa"
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

    # =========================================================================
    # RELATIONSHIPS - Sử dụng STRING REFERENCE để SQLAlchemy resolve sau
    # =========================================================================
    
    # Người đăng ký nghỉ - QUAN TRỌNG: back_populates phải khớp với CongChuc.dang_ky_nghis
    cong_chuc: Mapped["CongChuc"] = relationship(
        "CongChuc",
        back_populates="dang_ky_nghis",
        foreign_keys=[cong_chuc_id],
        lazy="joined"
    )
    
    # Người phê duyệt - Không cần back_populates vì không query ngược từ approver
    nguoi_phe_duyet: Mapped[Optional["CongChuc"]] = relationship(
        "CongChuc",
        foreign_keys=[nguoi_phe_duyet_id],
        lazy="joined"
    )
    # Người phê duyệt cấp 2 (ĐT)
    nguoi_phe_duyet_cap2: Mapped[Optional["CongChuc"]] = relationship(
        "CongChuc",
        foreign_keys=[nguoi_phe_duyet_cap2_id],
        lazy="joined"
    )
    
    # -------------------------------------------------------------------------
    # INDEXES & CONSTRAINTS
    # -------------------------------------------------------------------------
    __table_args__ = (
        # Constraints
        CheckConstraint("den_ngay >= tu_ngay", name="ck_dang_ky_nghi_ngay"),
        CheckConstraint("so_ngay > 0 AND so_ngay <= 365", name="ck_dang_ky_nghi_so_ngay"),
        CheckConstraint(
            "thang_ap_dung IS NULL OR (thang_ap_dung BETWEEN 1 AND 12)",
            name="ck_dang_ky_nghi_thang"
        ),
        CheckConstraint(
            "nam_ap_dung IS NULL OR nam_ap_dung >= 2025",
            name="ck_dang_ky_nghi_nam"
        ),
        
        # Indexes
        Index("idx_dang_ky_nghi_cc", "cong_chuc_id"),
        Index("idx_dang_ky_nghi_trang_thai", "trang_thai"),
        Index("idx_dang_ky_nghi_loai", "loai_nghi"),
        Index("idx_dang_ky_nghi_ngay", "tu_ngay", "den_ngay"),
        Index("idx_dang_ky_nghi_thang_nam", "thang_ap_dung", "nam_ap_dung"),
        Index("idx_dang_ky_nghi_phe_duyet", "nguoi_phe_duyet_id"),
        
        # Composite index cho query tính KPI
        Index(
            "idx_dang_ky_nghi_kpi",
            "cong_chuc_id", "thang_ap_dung", "nam_ap_dung", "trang_thai",
            postgresql_where="trang_thai = 'DA_PHE_DUYET' AND is_deleted = FALSE"
        ),
    )
    
    def __repr__(self) -> str:
        return (
            f"<DangKyNghi(id={self.id}, "
            f"cc_id={self.cong_chuc_id}, "
            f"loai={self.loai_nghi.value}, "
            f"tu={self.tu_ngay}, den={self.den_ngay}, "
            f"trang_thai={self.trang_thai.value})>"
        )
    
    @property
    def loai_nghi_ten(self) -> str:
        """Trả về tên tiếng Việt của loại nghỉ."""
        mapping = {
            LoaiNghi.NGHI_TUAN: "Nghỉ tuần",
            LoaiNghi.PHEP_NAM: "Phép năm",
            LoaiNghi.NGHI_LE: "Nghỉ lễ",
            LoaiNghi.NGHI_OM: "Ốm đau",
            LoaiNghi.THAI_SAN: "Thai sản",
            LoaiNghi.VIEC_RIENG: "Việc riêng có lương",
            LoaiNghi.KHONG_LUONG: "Nghỉ không lương",
            LoaiNghi.NGHI_BU: "Nghỉ bù",
            LoaiNghi.KHAC: "Khác",
        }
        return mapping.get(self.loai_nghi, "Không xác định")
    
    @property
    def trang_thai_ten(self) -> str:
        """Trả về tên tiếng Việt của trạng thái."""
        mapping = {
            TrangThaiNghi.CHO_PHE_DUYET: "Chờ phê duyệt",
            TrangThaiNghi.DA_PHE_DUYET: "Đã phê duyệt",
            TrangThaiNghi.TU_CHOI: "Từ chối",
            TrangThaiNghi.HUY: "Đã hủy",
        }
        return mapping.get(self.trang_thai, "Không xác định")
