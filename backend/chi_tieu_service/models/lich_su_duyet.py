"""
chi_tieu_service/models/lich_su_duyet.py
========================================
Model lich su thao tac/duyet (audit) — bang chi_tieu.lich_su_duyet.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, String, Text, text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from chi_tieu_service.models.base import Base


class LichSuDuyet(Base):
    """Lich su thao tac/duyet — bang chi_tieu.lich_su_duyet."""

    __tablename__ = "lich_su_duyet"
    __table_args__ = {"schema": "chi_tieu"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    dang_ky_thang_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("chi_tieu.dang_ky_thang.id"), nullable=False
    )
    # GUI_DANG_KY | DUYET_DANG_KY | TU_CHOI_DANG_KY | GUI_SUA | DUYET_SUA |
    # TU_CHOI_SUA | GUI_KET_QUA | DUYET_KET_QUA | TU_CHOI_KET_QUA | MO_KHOA
    hanh_dong: Mapped[str] = mapped_column(String(30), nullable=False)
    nguoi_thuc_hien_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("public.cong_chuc.id"), nullable=False
    )
    noi_dung_truoc: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    noi_dung_sau: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    ghi_chu: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=text("CURRENT_TIMESTAMP")
    )
