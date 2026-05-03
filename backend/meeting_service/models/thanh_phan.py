"""meeting.thanh_phan — thành phần tham dự cuộc họp."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import ForeignKey, String, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column

from meeting_service.models.base import Base


class ThanhPhan(Base):
    __tablename__ = "thanh_phan"
    __table_args__ = (
        UniqueConstraint("cuoc_hop_id", "cong_chuc_id", name="uq_thanh_phan_cuoc_hop_cong_chuc"),
        {"schema": "meeting"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    cuoc_hop_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("meeting.cuoc_hop.id", ondelete="CASCADE"),
        nullable=False,
    )
    cong_chuc_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("public.cong_chuc.id"), nullable=False
    )

    loai_tham_du: Mapped[str] = mapped_column(
        String(20), server_default="BAT_BUOC", nullable=False
    )
    xac_nhan: Mapped[Optional[str]] = mapped_column(
        String(20), server_default="CHUA_PHAN_HOI"
    )
    nguoi_uy_quyen_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("public.cong_chuc.id"), nullable=True
    )
    ghi_chu_xac_nhan: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    thoi_gian_xac_nhan: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("NOW()"), nullable=False
    )
