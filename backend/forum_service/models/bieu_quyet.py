"""
forum_service/models/bieu_quyet.py
===================================
Upvote / Downvote — bang forum.bieu_quyet.

Polymorphic voting:
  - doi_tuong_type: 'CHU_DE' hoac 'TRA_LOI'
  - doi_tuong_id: UUID cua chu_de hoac tra_loi
  - loai: 'UP' hoac 'DOWN'

Rang buoc: Moi nguoi chi vote 1 lan cho 1 doi tuong
  → UNIQUE(cong_chuc_id, doi_tuong_type, doi_tuong_id)
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, String, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from forum_service.models.base import Base, CongChucRef


class BieuQuyet(Base):
    """Upvote / Downvote — bang forum.bieu_quyet.

    Polymorphic: doi_tuong_type (CHU_DE|TRA_LOI) + doi_tuong_id (UUID).
    Moi nguoi chi vote 1 lan cho moi doi tuong.
    """

    __tablename__ = "bieu_quyet"
    __table_args__ = (
        UniqueConstraint(
            "cong_chuc_id", "doi_tuong_type", "doi_tuong_id",
            name="uq_forum_bq_cc_dt",
        ),
        {"schema": "forum"},
    )

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )

    # FK cross-schema — nguoi vote
    cong_chuc_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("public.cong_chuc.id"),
        nullable=False,
    )

    # Doi tuong vote (polymorphic) — 'CHU_DE' hoac 'TRA_LOI'
    doi_tuong_type: Mapped[str] = mapped_column(
        String(20), nullable=False,
    )

    # UUID cua chu_de hoac tra_loi duoc vote
    doi_tuong_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False,
    )

    # Loai vote: 'UP' hoac 'DOWN'
    loai: Mapped[str] = mapped_column(
        String(10), nullable=False,
    )

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"), nullable=False,
    )

    # --- Relationships ---

    # Nguoi vote — FK cross-schema den public.cong_chuc
    cong_chuc: Mapped[CongChucRef] = relationship(
        "CongChucRef",
        foreign_keys=[cong_chuc_id],
        lazy="joined",
    )
