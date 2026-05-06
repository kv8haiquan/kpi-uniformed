"""
app/models/dieu_chinh_kqcv.py
=============================
Model DieuChinhKqcv — lịch sử + workflow LĐ điều chỉnh KQCV của CC/cấp dưới.

Yêu cầu 2 — 06/05/2026.
"""

from datetime import datetime
from typing import Optional, TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    String,
    Text,
    DateTime,
    ForeignKey,
    Index,
    CheckConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModelWithSoftDelete

if TYPE_CHECKING:
    from app.models.kpi_submission import KeKhaiCongViec
    from app.models.user_org import CongChuc


class DieuChinhKqcv(BaseModelWithSoftDelete):
    """Mỗi bản ghi = 1 lần LĐ đề xuất sửa 1 CV."""

    __tablename__ = "dieu_chinh_kqcv"

    ke_khai_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("ke_khai_cong_viec.id", ondelete="RESTRICT"),
        nullable=False,
    )

    nguoi_dieu_chinh_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("cong_chuc.id", ondelete="RESTRICT"),
        nullable=False,
    )

    nguoi_phe_duyet_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("cong_chuc.id", ondelete="RESTRICT"),
        nullable=False,
    )

    gia_tri_cu: Mapped[dict] = mapped_column(JSONB, nullable=False)
    gia_tri_moi: Mapped[dict] = mapped_column(JSONB, nullable=False)

    ly_do: Mapped[str] = mapped_column(Text, nullable=False)

    trang_thai: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="NHAP",
        server_default="NHAP",
    )

    y_kien_phe_duyet: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ngay_phe_duyet: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    ke_khai: Mapped["KeKhaiCongViec"] = relationship(
        "KeKhaiCongViec",
        foreign_keys=[ke_khai_id],
        lazy="joined",
    )

    nguoi_dieu_chinh: Mapped["CongChuc"] = relationship(
        "CongChuc",
        foreign_keys=[nguoi_dieu_chinh_id],
        lazy="joined",
    )

    nguoi_phe_duyet: Mapped["CongChuc"] = relationship(
        "CongChuc",
        foreign_keys=[nguoi_phe_duyet_id],
        lazy="joined",
    )

    __table_args__ = (
        CheckConstraint(
            "trang_thai IN ('NHAP', 'CHO_PHE_DUYET', 'DA_PHE_DUYET', 'TU_CHOI')",
            name="ck_dieu_chinh_kqcv_trang_thai",
        ),
        Index("idx_dckqcv_ke_khai", "ke_khai_id"),
        Index("idx_dckqcv_nguoi_dc", "nguoi_dieu_chinh_id"),
        Index("idx_dckqcv_nguoi_pd", "nguoi_phe_duyet_id"),
        Index("idx_dckqcv_trang_thai", "trang_thai"),
        {"comment": "Lịch sử + workflow LĐ điều chỉnh KQCV (Yêu cầu 2)"},
    )
