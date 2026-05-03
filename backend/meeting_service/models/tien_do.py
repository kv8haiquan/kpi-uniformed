"""meeting.tien_do — cập nhật tiến độ kết luận."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import ForeignKey, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column

from meeting_service.models.base import Base


class TienDo(Base):
    __tablename__ = "tien_do"
    __table_args__ = {"schema": "meeting"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    ket_luan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("meeting.ket_luan.id", ondelete="CASCADE"), nullable=False
    )

    mo_ta: Mapped[str] = mapped_column(Text, nullable=False)
    phan_tram_truoc: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    phan_tram_sau: Mapped[int] = mapped_column(Integer, nullable=False)
    file_minh_chung_minio_key: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    nguoi_cap_nhat_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("public.cong_chuc.id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("NOW()"), nullable=False
    )
