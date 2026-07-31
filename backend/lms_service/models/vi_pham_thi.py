"""
lms_service/models/vi_pham_thi.py
=================================
Model log vi pham khi thi DGNL — bang lms.vi_pham_thi.

Moi lan thi sinh thoat toan man hinh / chuyen tab -> 1 row (kem thoi gian).
Thi sinh co the nhap ly do giai trinh (khong bat buoc) cho TCCB xem xet.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Integer, String, Text, ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from lms_service.models.base import Base


class ViPhamThi(Base):
    """Log 1 lan vi pham khi thi — bang lms.vi_pham_thi."""

    __tablename__ = "vi_pham_thi"
    __table_args__ = {"schema": "lms"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    thi_sinh_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("lms.thi_sinh.id", ondelete="CASCADE"), nullable=False
    )
    ky_thi_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("lms.ky_thi.id", ondelete="CASCADE"), nullable=False
    )
    lan_thi: Mapped[int] = mapped_column(Integer, nullable=False)
    # EXIT_FULLSCREEN (thoat toan man hinh) | SWITCH_TAB (chuyen tab/cua so)
    loai_vi_pham: Mapped[str] = mapped_column(String(50), nullable=False)
    thoi_gian: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False
    )
    ly_do: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP")
    )
