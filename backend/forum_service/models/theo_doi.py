"""
forum_service/models/theo_doi.py
=================================
Theo doi chu de — bang forum.theo_doi.

Composite primary key: (cong_chuc_id, chu_de_id) — KHONG co cot id rieng.
Moi cong chuc chi theo doi 1 lan cho moi chu de.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, text
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from forum_service.models.base import Base, CongChucRef

if TYPE_CHECKING:
    from forum_service.models.chu_de import ChuDe


class TheoDoi(Base):
    """Theo doi chu de — bang forum.theo_doi.

    Composite PK: (cong_chuc_id, chu_de_id).
    KHONG co cot id rieng.
    """

    __tablename__ = "theo_doi"
    __table_args__ = {"schema": "forum"}

    # Composite PK — phan 1: nguoi theo doi
    cong_chuc_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("public.cong_chuc.id"),
        primary_key=True,
    )

    # Composite PK — phan 2: chu de duoc theo doi
    chu_de_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("forum.chu_de.id"),
        primary_key=True,
    )

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"), nullable=False,
    )

    # --- Relationships ---

    # Nguoi theo doi — FK cross-schema den public.cong_chuc
    cong_chuc: Mapped[CongChucRef] = relationship(
        "CongChucRef",
        foreign_keys=[cong_chuc_id],
        lazy="joined",
    )

    # Chu de duoc theo doi
    chu_de: Mapped[ChuDe] = relationship(
        "ChuDe",
        foreign_keys=[chu_de_id],
        lazy="joined",
    )
