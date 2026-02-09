"""
app/models/lich_su_dieu_chinh.py
================================
Model cho Lịch sử điều chỉnh.

Ghi nhận mọi thay đổi của lãnh đạo (Phó ĐT, ĐT) khi phê duyệt:
- Kê khai công việc: chỉnh cấp độ, số lỗi CL/TĐ
- Tiêu chí chung: chỉnh điểm đạt/không đạt
- Đánh giá tháng: chỉnh xếp loại đề xuất

Phiên bản: 1.0 (29/01/2026)
"""

import uuid
import enum
from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import (
    String,
    Text,
    ForeignKey,
    Index,
    Enum as SQLEnum,
    DateTime,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.user_org import CongChuc


# =============================================================================
# ENUMS
# =============================================================================

class LoaiDoiTuongDieuChinh(str, enum.Enum):
    """Loại đối tượng được điều chỉnh."""
    KE_KHAI_CONG_VIEC = "KE_KHAI_CONG_VIEC"   # Kê khai công việc
    TIEU_CHI_CHUNG = "TIEU_CHI_CHUNG"         # Tiêu chí chung (trong tieu_chi_chung_danh_gia)
    DANG_KY_NGHI = "DANG_KY_NGHI"             # Đăng ký nghỉ
    DANH_GIA_THANG = "DANH_GIA_THANG"         # Đánh giá tháng (xếp loại)


# =============================================================================
# MODELS
# =============================================================================

class LichSuDieuChinh(Base):
    """
    Lịch sử điều chỉnh của lãnh đạo.
    
    Mỗi lần Phó ĐT hoặc ĐT chỉnh sửa dữ liệu của CC khi phê duyệt,
    hệ thống tự động ghi nhận:
    - Đối tượng nào bị chỉnh (kê khai, tiêu chí, nghỉ phép, đánh giá)
    - Ai chỉnh
    - Chỉnh trường nào
    - Giá trị cũ → Giá trị mới
    - Lý do chỉnh
    - Thời điểm chỉnh
    
    Mục đích:
    - Minh bạch: CC biết ai đã chỉnh gì
    - Kiểm tra: CCT có thể review các điều chỉnh
    - Audit: Lưu vết để giải quyết tranh chấp
    """
    
    __tablename__ = "lich_su_dieu_chinh"
    
    # -------------------------------------------------------------------------
    # PRIMARY KEY
    # -------------------------------------------------------------------------
    
    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="ID lịch sử"
    )
    
    # -------------------------------------------------------------------------
    # ĐỐI TƯỢNG ĐƯỢC ĐIỀU CHỈNH
    # -------------------------------------------------------------------------
    
    loai_doi_tuong: Mapped[LoaiDoiTuongDieuChinh] = mapped_column(
        SQLEnum(LoaiDoiTuongDieuChinh, name="loai_doi_tuong_dieu_chinh_enum", create_type=False),
        nullable=False,
        index=True,
        comment="Loại đối tượng: KE_KHAI_CONG_VIEC, TIEU_CHI_CHUNG, DANG_KY_NGHI, DANH_GIA_THANG"
    )
    
    doi_tuong_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=False,
        index=True,
        comment="ID của đối tượng bị điều chỉnh"
    )
    
    # -------------------------------------------------------------------------
    # NGƯỜI ĐIỀU CHỈNH
    # -------------------------------------------------------------------------
    
    nguoi_dieu_chinh_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("cong_chuc.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="ID người thực hiện điều chỉnh (Phó ĐT/ĐT)"
    )
    
    # -------------------------------------------------------------------------
    # CHI TIẾT ĐIỀU CHỈNH
    # -------------------------------------------------------------------------
    
    truong_du_lieu: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Tên trường bị chỉnh: cap_do_id, so_loi_chat_luong, is_achieved, ..."
    )
    
    gia_tri_cu: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Giá trị cũ trước khi chỉnh (JSON string nếu phức tạp)"
    )
    
    gia_tri_moi: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Giá trị mới sau khi chỉnh"
    )
    
    ly_do: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Lý do điều chỉnh (bắt buộc nhập trên UI)"
    )
    
    # -------------------------------------------------------------------------
    # THỜI GIAN
    # -------------------------------------------------------------------------
    
    ngay_dieu_chinh: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Thời điểm điều chỉnh"
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    
    # -------------------------------------------------------------------------
    # RELATIONSHIPS
    # -------------------------------------------------------------------------
    
    nguoi_dieu_chinh: Mapped["CongChuc"] = relationship(
        "CongChuc",
        foreign_keys=[nguoi_dieu_chinh_id],
        lazy="joined"
    )
    
    # -------------------------------------------------------------------------
    # INDEXES
    # -------------------------------------------------------------------------
    
    __table_args__ = (
        Index("idx_lich_su_doi_tuong", "loai_doi_tuong", "doi_tuong_id"),
        Index("idx_lich_su_nguoi", "nguoi_dieu_chinh_id"),
        Index("idx_lich_su_ngay", "ngay_dieu_chinh"),
    )
    
    def __repr__(self) -> str:
        return (
            f"<LichSuDieuChinh("
            f"loai={self.loai_doi_tuong.value}, "
            f"truong={self.truong_du_lieu}, "
            f"cu={self.gia_tri_cu}, moi={self.gia_tri_moi})>"
        )