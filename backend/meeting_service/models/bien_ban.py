"""meeting.bien_ban — biên bản họp + Mock CKS."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import Boolean, ForeignKey, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column

from meeting_service.models.base import Base


class BienBan(Base):
    __tablename__ = "bien_ban"
    __table_args__ = {"schema": "meeting"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    cuoc_hop_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("meeting.cuoc_hop.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )

    noi_dung_json: Mapped[Optional[Any]] = mapped_column(JSONB, nullable=True)
    noi_dung_html: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    trang_thai: Mapped[str] = mapped_column(String(30), server_default="DANG_SOAN", nullable=False)
    file_pdf_minio_key: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    file_docx_minio_key: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    is_mock_signed: Mapped[bool] = mapped_column(
        Boolean, server_default=text("FALSE"), nullable=False
    )
    qr_xac_thuc: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    hash_noi_dung: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    nguoi_soan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("public.cong_chuc.id"), nullable=False
    )
    nguoi_ky_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("public.cong_chuc.id"), nullable=True
    )
    thoi_gian_ky: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("NOW()"), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("NOW()"), nullable=False
    )
