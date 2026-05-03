"""meeting.diem_danh — điểm danh QR/bấm tay."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import ForeignKey, String, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column

from meeting_service.models.base import Base


class DiemDanh(Base):
    __tablename__ = "diem_danh"
    __table_args__ = (
        UniqueConstraint("cuoc_hop_id", "cong_chuc_id", name="uq_diem_danh_cuoc_hop_cong_chuc"),
        {"schema": "meeting"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    cuoc_hop_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("meeting.cuoc_hop.id", ondelete="CASCADE"), nullable=False
    )
    cong_chuc_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("public.cong_chuc.id"), nullable=False
    )

    hinh_thuc: Mapped[str] = mapped_column(String(20), nullable=False)
    trang_thai: Mapped[str] = mapped_column(String(20), server_default="CO_MAT", nullable=False)

    gio_diem_danh: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
    ghi_chu: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    nguoi_diem_danh_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("public.cong_chuc.id"), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("NOW()"), nullable=False
    )
