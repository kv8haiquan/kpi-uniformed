"""meeting.tai_lieu — tài liệu họp (file MinIO)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, Boolean, ForeignKey, String, Text, text
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column

from meeting_service.models.base import Base


class TaiLieu(Base):
    __tablename__ = "tai_lieu"
    __table_args__ = {"schema": "meeting"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    # Một tài liệu thuộc ĐÚNG MỘT chủ thể: cuộc họp hoặc ghi chú cá nhân
    # (CHECK `ck_tai_lieu_chu_the` trong CSDL). Trước G5.2 chỉ có cuộc họp nên
    # model để nullable=False, lệch với CSDL — nay khai đúng cả hai cột.
    cuoc_hop_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("meeting.cuoc_hop.id", ondelete="CASCADE"), nullable=True
    )
    ghi_chu_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("meeting.ghi_chu.id", ondelete="CASCADE"), nullable=True
    )
    ten_tai_lieu: Mapped[str] = mapped_column(String(500), nullable=False)
    mo_ta: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    minio_bucket: Mapped[str] = mapped_column(String(100), server_default="meeting", nullable=False)
    minio_key: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    mime_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    extension: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)

    phan_quyen: Mapped[str] = mapped_column(String(20), server_default="CONG_KHAI", nullable=False)
    cho_phep_tai: Mapped[bool] = mapped_column(Boolean, server_default=text("TRUE"), nullable=False)
    cho_phep_in: Mapped[bool] = mapped_column(Boolean, server_default=text("TRUE"), nullable=False)

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
