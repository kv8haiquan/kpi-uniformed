"""
common_service/models/thong_bao.py
===================================
Notification Center — Thong bao da module.
Bang: common.thong_bao

Loai thong bao: KPI, LMS, FORUM, LEGAL, PORTAL, HE_THONG
Muc do: KHAN, QUAN_TRONG, BINH_THUONG
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, ForeignKey, String, Text, text
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, CongChucRef


class ThongBao(Base):
    """Notification Center — Thong bao da module.

    Luu thong bao cho tat ca module (KPI, LMS, Forum, Legal, Portal).
    Moi thong bao gan voi 1 nguoi nhan (cong_chuc) va co the link den
    1 doi tuong cu the (khoa_hoc, van_ban, chu_de...).
    """

    __tablename__ = "thong_bao"
    __table_args__ = {"schema": "common"}

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )

    # Nguoi nhan — FK cross-schema den public.cong_chuc
    nguoi_nhan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("public.cong_chuc.id"),
        nullable=False,
    )

    # Noi dung thong bao
    tieu_de: Mapped[str] = mapped_column(String(300), nullable=False)
    noi_dung: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Phan loai: KPI, LMS, FORUM, LEGAL, PORTAL, HE_THONG
    loai: Mapped[str] = mapped_column(String(50), nullable=False)

    # Link den doi tuong cu the
    link_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    doi_tuong_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    doi_tuong_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )

    # Trang thai doc
    da_doc: Mapped[bool] = mapped_column(
        Boolean, server_default=text("false"), nullable=False
    )
    ngay_doc: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP, nullable=True)

    # Muc do: KHAN, QUAN_TRONG, BINH_THUONG
    muc_do: Mapped[str] = mapped_column(
        String(20), server_default="BINH_THUONG", nullable=False
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"), nullable=False
    )

    # --- Relationships ---
    nguoi_nhan: Mapped[Optional[CongChucRef]] = relationship(
        "CongChucRef",
        foreign_keys=[nguoi_nhan_id],
        lazy="joined",
    )
