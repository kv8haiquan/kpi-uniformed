"""
lms_service/models/phien_thi.py
===============================
Model phien thi DGNL — bang lms.phien_thi.

Moi cong_chuc_id chi co 1 dong (UNIQUE) -> enforce 1 phien thi/tai khoan tai
1 thoi diem. bat_dau_thi sinh phien_token moi va ghi de dong cu; request tu
thiet bi cu (token khong khop) bi tu choi 409. last_seen dung cho man hinh
giam sat truc tiep (online/offline).
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, String, ForeignKey, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from lms_service.models.base import Base


class PhienThi(Base):
    """Phien thi DGNL — bang lms.phien_thi (1 phien/tai khoan)."""

    __tablename__ = "phien_thi"
    __table_args__ = (
        UniqueConstraint("cong_chuc_id", name="uq_phien_thi_cong_chuc"),
        {"schema": "lms"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    cong_chuc_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("public.cong_chuc.id"), nullable=False
    )
    phien_token: Mapped[str] = mapped_column(String(64), nullable=False)
    ky_thi_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("lms.ky_thi.id", ondelete="CASCADE"), nullable=True
    )
    thi_sinh_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("lms.thi_sinh.id", ondelete="CASCADE"), nullable=True
    )
    thiet_bi: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    last_seen: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP")
    )
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP")
    )
