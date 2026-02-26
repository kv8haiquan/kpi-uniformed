"""
common_service/models/knowledge_base.py
========================================
Kho SOP / FAQ voi Full-text Search.
Bang: common.knowledge_base

Loai: SOP, FAQ
Trang thai: NHAP, CHO_DUYET, DA_XUAT_BAN, CAN_CAP_NHAT
search_vector: tsvector — trigger DB tu dong cap nhat (trg_common_kb_search)
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP, TSVECTOR, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, CongChucRef


class KnowledgeBase(Base):
    """Kho SOP / FAQ voi Full-text Search.

    Luu tru cac tai lieu SOP (Standard Operating Procedure) va FAQ
    cho toan bo he thong. Ho tro full-text search qua tsvector.

    search_vector duoc cap nhat tu dong boi trigger DB:
        trg_common_kb_search → common.update_kb_search()
    KHONG can set gia tri thu cong khi INSERT/UPDATE.
    """

    __tablename__ = "knowledge_base"
    __table_args__ = {"schema": "common"}

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )

    # Phan loai: SOP, FAQ
    loai: Mapped[str] = mapped_column(String(20), nullable=False)

    # Noi dung chinh (HTML/Markdown)
    tieu_de: Mapped[str] = mapped_column(String(500), nullable=False)
    noi_dung: Mapped[str] = mapped_column(Text, nullable=False)

    # Phan loai JSONB
    chuyen_de: Mapped[Any] = mapped_column(
        JSONB(astext_type=Text()),
        server_default=text("'[]'::jsonb"),
        nullable=False,
    )
    tags: Mapped[Any] = mapped_column(
        JSONB(astext_type=Text()),
        server_default=text("'[]'::jsonb"),
        nullable=False,
    )

    # Chu so huu — FK cross-schema den public.cong_chuc
    chu_so_huu_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("public.cong_chuc.id"),
        nullable=True,
    )

    # Trang thai: NHAP, CHO_DUYET, DA_XUAT_BAN, CAN_CAP_NHAT
    trang_thai: Mapped[str] = mapped_column(
        String(50), server_default="NHAP", nullable=False
    )

    # Lien ket cross-module (JSONB array cac UUID)
    van_ban_lien_quan: Mapped[Optional[Any]] = mapped_column(JSONB, nullable=True)
    chu_de_forum_lien_quan: Mapped[Optional[Any]] = mapped_column(JSONB, nullable=True)

    # Phien ban
    phien_ban: Mapped[int] = mapped_column(
        Integer, server_default=text("1"), nullable=False
    )
    ngay_cap_nhat_cuoi: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP, nullable=True
    )

    # Full-text search vector — trigger DB tu dong cap nhat
    # KHONG set gia tri thu cong, chi dung de query
    search_vector: Mapped[Optional[Any]] = mapped_column(TSVECTOR, nullable=True)

    # Timestamps + soft delete
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"), nullable=False
    )
    is_deleted: Mapped[bool] = mapped_column(
        Boolean, server_default=text("false"), nullable=False
    )

    # --- Relationships ---
    chu_so_huu: Mapped[Optional[CongChucRef]] = relationship(
        "CongChucRef",
        foreign_keys=[chu_so_huu_id],
        lazy="joined",
    )
