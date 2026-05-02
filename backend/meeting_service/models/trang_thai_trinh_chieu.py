"""meeting.trang_thai_trinh_chieu — state phiên trình chiếu (Phase 4.1).

Threat model + design notes:
- 1 cuộc họp = 1 row (UNIQUE cuoc_hop_id) → UPSERT pattern.
- KHÔNG có cột `is_deleted` (khác với các model nghiệp vụ): bảng state UPSERT
  1-1, soft-delete vô nghĩa và sẽ chặn re-create. Cleanup thông qua
  `ON DELETE CASCADE` từ `meeting.cuoc_hop`.
- `is_active` đại diện cho phiên trình chiếu đang chạy hay không. Cho phép
  start/end nhiều lần, ghi đè timestamp lần cuối (D8 plan v3.1).
- 4 CHECK constraint reflect trong `__table_args__` để ORM-level validation.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    Integer,
    Numeric,
    text,
)
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from meeting_service.models.base import Base

if TYPE_CHECKING:
    from meeting_service.models.cuoc_hop import CuocHop
    from meeting_service.models.tai_lieu import TaiLieu


class TrangThaiTrinhChieu(Base):
    """State realtime của phiên trình chiếu trong cuộc họp.

    1 row / 1 cuộc họp (UNIQUE cuoc_hop_id). Lifecycle: chu_toa bấm Bắt đầu
    trình chiếu → is_active=TRUE, bat_dau_luc=NOW; bấm Kết thúc → is_active=FALSE,
    ket_thuc_luc=NOW. Cho phép start/end nhiều lần (timestamp lần cuối).
    """

    __tablename__ = "trang_thai_trinh_chieu"
    __table_args__ = (
        CheckConstraint("trang_hien_tai > 0", name="chk_ttc_trang_positive"),
        CheckConstraint(
            "zoom_level >= 0.5 AND zoom_level <= 4.0",
            name="chk_ttc_zoom_range",
        ),
        CheckConstraint(
            "NOT is_active OR tai_lieu_hien_tai_id IS NOT NULL",
            name="chk_ttc_active_has_doc",
        ),
        CheckConstraint(
            "bat_dau_luc IS NULL OR ket_thuc_luc IS NULL OR bat_dau_luc <= ket_thuc_luc",
            name="chk_ttc_thoi_gian_hop_le",
        ),
        {"schema": "meeting"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

    cuoc_hop_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("meeting.cuoc_hop.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )

    tai_lieu_hien_tai_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("meeting.tai_lieu.id", ondelete="SET NULL"),
        nullable=True,
    )

    trang_hien_tai: Mapped[int] = mapped_column(
        Integer, server_default=text("1"), nullable=False
    )
    zoom_level: Mapped[Decimal] = mapped_column(
        Numeric(4, 2), server_default=text("1.0"), nullable=False
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean, server_default=text("FALSE"), nullable=False
    )
    bat_dau_luc: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
    ket_thuc_luc: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )

    cap_nhat_luc: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=text("NOW()"),
        nullable=False,
    )
    cap_nhat_boi_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("public.cong_chuc.id", ondelete="SET NULL"),
        nullable=True,
    )

    cuoc_hop: Mapped["CuocHop"] = relationship(
        "CuocHop",
        back_populates="trang_thai_trinh_chieu",
        lazy="select",
    )
    tai_lieu_hien_tai: Mapped[Optional["TaiLieu"]] = relationship(
        "TaiLieu",
        foreign_keys=[tai_lieu_hien_tai_id],
        lazy="select",
    )

    def __repr__(self) -> str:
        return (
            f"<TrangThaiTrinhChieu cuoc_hop_id={self.cuoc_hop_id} "
            f"page={self.trang_hien_tai} zoom={self.zoom_level} "
            f"active={self.is_active}>"
        )
