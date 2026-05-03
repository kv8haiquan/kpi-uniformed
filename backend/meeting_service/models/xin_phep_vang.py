"""meeting.xin_phep_vang — đơn xin vắng họp."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, ForeignKey, String, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column

from meeting_service.models.base import Base


class XinPhepVang(Base):
    __tablename__ = "xin_phep_vang"
    __table_args__ = (
        UniqueConstraint("cuoc_hop_id", "cong_chuc_id", name="uq_xin_phep_cuoc_hop_cong_chuc"),
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

    ly_do: Mapped[str] = mapped_column(Text, nullable=False)
    nguoi_du_thay_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("public.cong_chuc.id"), nullable=True
    )
    minio_key: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    trang_thai: Mapped[str] = mapped_column(String(30), server_default="CHO_DUYET", nullable=False)
    auto_approved: Mapped[bool] = mapped_column(
        Boolean, server_default=text("FALSE"), nullable=False
    )
    nguoi_duyet_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("public.cong_chuc.id"), nullable=True
    )
    thoi_gian_duyet: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
    ly_do_tu_choi: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("NOW()"), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("NOW()"), nullable=False
    )
