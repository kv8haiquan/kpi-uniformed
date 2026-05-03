"""meeting.mau_bieu — template biên bản (DOCX)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column

from meeting_service.models.base import Base


class MauBieu(Base):
    __tablename__ = "mau_bieu"
    __table_args__ = {"schema": "meeting"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    loai: Mapped[str] = mapped_column(String(30), nullable=False)
    ten_mau: Mapped[str] = mapped_column(String(200), nullable=False)
    mo_ta: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    ap_dung_cho: Mapped[str] = mapped_column(String(50), server_default="TAT_CA", nullable=False)
    minio_key: Mapped[str] = mapped_column(String(500), nullable=False)
    phien_ban: Mapped[int] = mapped_column(Integer, server_default="1", nullable=False)
    la_mac_dinh: Mapped[bool] = mapped_column(Boolean, server_default=text("FALSE"), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("NOW()"), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("NOW()"), nullable=False
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("public.cong_chuc.id"), nullable=False
    )
    is_deleted: Mapped[bool] = mapped_column(Boolean, server_default=text("FALSE"), nullable=False)
