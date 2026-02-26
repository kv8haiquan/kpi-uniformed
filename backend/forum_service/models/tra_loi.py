"""
forum_service/models/tra_loi.py
================================
Tra loi / Binh luan — bang forum.tra_loi.

Ho tro threaded reply (reply long nhau, toi da 2 cap):
  - Cap 1: Tra loi truc tiep cho chu de (parent_id IS NULL)
  - Cap 2: Tra loi cho tra loi (parent_id tro den cap 1)

Dac biet:
  - is_dap_an_chuan: duoc chuyen gia/dieu phoi chon lam dap an chuan
  - can_cu_phap_ly: JSONB dinh kem van ban, SOP lien quan
    Format: [{"loai": "VAN_BAN"|"SOP", "id": "uuid", "trich_dan": "..."}]
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import Boolean, ForeignKey, Integer, Text, text
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from forum_service.models.base import Base, CongChucRef

if TYPE_CHECKING:
    from forum_service.models.chu_de import ChuDe


class TraLoi(Base):
    """Tra loi / Binh luan — bang forum.tra_loi.

    Threaded reply: parent_id tro den tra loi cha (toi da 2 cap).
    """

    __tablename__ = "tra_loi"
    __table_args__ = {"schema": "forum"}

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )

    # FK noi bo — chu de chua tra loi nay
    chu_de_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("forum.chu_de.id"),
        nullable=False,
    )

    # Self-reference — reply long nhau (toi da 2 cap)
    parent_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("forum.tra_loi.id"),
        nullable=True,
    )

    # Noi dung (Markdown/HTML)
    noi_dung: Mapped[str] = mapped_column(Text, nullable=False)

    # FK cross-schema — tac gia
    tac_gia_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("public.cong_chuc.id"),
        nullable=False,
    )

    # Trang thai dap an chuan — chuyen gia/dieu phoi chon
    is_dap_an_chuan: Mapped[bool] = mapped_column(
        Boolean, server_default=text("false"), nullable=False,
    )

    # An bai (vi pham noi quy)
    is_an: Mapped[bool] = mapped_column(
        Boolean, server_default=text("false"), nullable=False,
    )

    # Thong ke upvote
    so_upvote: Mapped[int] = mapped_column(
        Integer, server_default=text("0"), nullable=False,
    )

    # Can cu phap ly dinh kem
    # Format: [{"loai": "VAN_BAN"|"SOP", "id": "uuid", "trich_dan": "..."}]
    can_cu_phap_ly: Mapped[Optional[Any]] = mapped_column(
        JSONB, nullable=True,
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"), nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"), nullable=False,
    )

    # Soft delete
    is_deleted: Mapped[bool] = mapped_column(
        Boolean, server_default=text("false"), nullable=False,
    )

    # --- Relationships ---

    # Chu de chua tra loi nay
    chu_de: Mapped[Optional[ChuDe]] = relationship(
        "ChuDe",
        back_populates="tra_loi_list",
        foreign_keys=[chu_de_id],
        lazy="joined",
    )

    # Tac gia — FK cross-schema den public.cong_chuc
    tac_gia: Mapped[Optional[CongChucRef]] = relationship(
        "CongChucRef",
        foreign_keys=[tac_gia_id],
        lazy="joined",
    )

    # Self-reference: cha-con (threaded reply)
    parent: Mapped[Optional[TraLoi]] = relationship(
        "TraLoi",
        remote_side="TraLoi.id",
        back_populates="children",
        foreign_keys=[parent_id],
        lazy="joined",
    )
    children: Mapped[list[TraLoi]] = relationship(
        "TraLoi",
        back_populates="parent",
        foreign_keys="TraLoi.parent_id",
        lazy="selectin",
    )
