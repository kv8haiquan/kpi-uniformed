"""meeting.y_kien — ý kiến thành viên (trước/trong/sau họp)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, ForeignKey, String, Text, text
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column

from meeting_service.models.base import Base


class YKien(Base):
    __tablename__ = "y_kien"
    __table_args__ = {"schema": "meeting"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    cuoc_hop_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("meeting.cuoc_hop.id", ondelete="CASCADE"), nullable=False
    )
    cong_chuc_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("public.cong_chuc.id"), nullable=False
    )
    noi_dung: Mapped[str] = mapped_column(Text, nullable=False)
    loai: Mapped[str] = mapped_column(String(20), server_default="TRONG_HOP", nullable=False)
    minio_key: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("NOW()"), nullable=False
    )
    is_deleted: Mapped[bool] = mapped_column(Boolean, server_default=text("FALSE"), nullable=False)
