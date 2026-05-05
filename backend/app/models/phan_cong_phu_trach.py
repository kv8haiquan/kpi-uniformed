"""
app/models/phan_cong_phu_trach.py
=================================
Model PhanCongPhuTrach — phân công CCT/PCCT phụ trách đơn vị.

Versioned theo thời gian:
- Một bản ghi = (LĐ, đơn vị, hiệu lực từ ngày, hiệu lực đến ngày).
- hieu_luc_den NULL = vẫn còn hiệu lực.

Mục đích:
- Phục vụ tính KPI lãnh đạo công thức mới (từ tháng 4/2026):
  + PCCT = gộp SP các đơn vị mình phụ trách
  + CCT  = gộp SP các đơn vị mình trực tiếp phụ trách + các PCCT phụ trách
- Một đơn vị tại 1 thời điểm CHỈ thuộc đúng 1 LĐ cấp Chi cục
  (kiểm tra ở service layer khi tạo/sửa).

Phiên bản: 1.0 (05/05/2026)
"""

from datetime import date
from typing import Optional, TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    Date,
    Text,
    ForeignKey,
    Index,
    CheckConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModelWithSoftDelete

if TYPE_CHECKING:
    from app.models.user_org import CongChuc, DonVi


class PhanCongPhuTrach(BaseModelWithSoftDelete):
    """
    Phân công CCT/PCCT phụ trách 1 đơn vị trong khoảng thời gian.

    Lưu ý:
    - lanh_dao_id PHẢI là CongChuc có cap_bac IN (CHI_CUC_TRUONG, PHO_CHI_CUC_TRUONG).
      Validate ở service layer (DB không check vai trò).
    - don_vi_id PHẢI là đơn vị có TDV (loại trừ LDCC, DEPT-ADMIN). Validate ở service.
    - Không cho overlap cho cùng (don_vi_id) — validate ở service.
    """

    __tablename__ = "phan_cong_phu_trach"

    lanh_dao_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("cong_chuc.id", ondelete="RESTRICT"),
        nullable=False,
        comment="FK → cong_chuc.id (LĐ phụ trách — CCT hoặc PCCT)",
    )

    don_vi_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("don_vi.id", ondelete="RESTRICT"),
        nullable=False,
        comment="FK → don_vi.id (đơn vị được phụ trách)",
    )

    hieu_luc_tu: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="Ngày bắt đầu hiệu lực phân công",
    )

    hieu_luc_den: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Ngày kết thúc hiệu lực (NULL = vẫn còn hiệu lực)",
    )

    ghi_chu: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Ghi chú phân công",
    )

    # Relationships
    lanh_dao: Mapped["CongChuc"] = relationship(
        "CongChuc",
        foreign_keys=[lanh_dao_id],
        lazy="joined",
    )

    don_vi: Mapped["DonVi"] = relationship(
        "DonVi",
        foreign_keys=[don_vi_id],
        lazy="joined",
    )

    __table_args__ = (
        CheckConstraint(
            "hieu_luc_den IS NULL OR hieu_luc_den >= hieu_luc_tu",
            name="ck_pcpt_hieu_luc_range",
        ),
        Index("idx_pcpt_don_vi", "don_vi_id"),
        Index("idx_pcpt_lanh_dao", "lanh_dao_id"),
        Index("idx_pcpt_hieu_luc_tu", "hieu_luc_tu"),
        Index("idx_pcpt_hieu_luc_den", "hieu_luc_den"),
        {"comment": "Phân công CCT/PCCT phụ trách đơn vị (versioned theo thời gian)"},
    )

    def is_active_at(self, ngay: date) -> bool:
        """Kiểm tra phân công có hiệu lực tại ngày `ngay` không."""
        if self.is_deleted:
            return False
        if self.hieu_luc_tu > ngay:
            return False
        if self.hieu_luc_den is not None and self.hieu_luc_den < ngay:
            return False
        return True

    def __repr__(self) -> str:
        return (
            f"<PhanCongPhuTrach(id={self.id}, ld={self.lanh_dao_id}, "
            f"dv={self.don_vi_id}, từ={self.hieu_luc_tu}, đến={self.hieu_luc_den})>"
        )
