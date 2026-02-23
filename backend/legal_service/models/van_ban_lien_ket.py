"""
legal_service/models/van_ban_lien_ket.py
==========================================
Model lien ket giua cac van ban — bang legal.van_ban_lien_ket.

Bang nay thuc hien quan he N:N tu tham chieu (self-referential) tren
bang van_ban de mo ta cac moi quan he giua cac van ban phap luat:
  - THAY_THE: Van ban nay thay the van ban kia
  - BO_SUNG:  Van ban nay bo sung/sua doi van ban kia
  - HUONG_DAN: Van ban nay huong dan thuc hien van ban kia
  - LIEN_QUAN: Lien quan chung (khong xac dinh cu the)

Composite PK: (van_ban_id, van_ban_lien_quan_id)
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from legal_service.models.base import Base

if TYPE_CHECKING:
    from legal_service.models.van_ban import VanBan


class VanBanLienKet(Base):
    """Lien ket giua cac van ban phap luat — bang legal.van_ban_lien_ket.

    Composite PK gom (van_ban_id, van_ban_lien_quan_id).
    Loai lien ket: THAY_THE | BO_SUNG | HUONG_DAN | LIEN_QUAN
    """

    __tablename__ = "van_ban_lien_ket"
    __table_args__ = {"schema": "legal"}

    # ------------------------------------------------------------------
    # Composite Primary Key
    # ------------------------------------------------------------------
    # Van ban goc (van ban dang xem)
    van_ban_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("legal.van_ban.id"),
        primary_key=True,
        nullable=False,
    )

    # Van ban lien quan den van ban goc
    van_ban_lien_quan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("legal.van_ban.id"),
        primary_key=True,
        nullable=False,
    )

    # ------------------------------------------------------------------
    # Loai lien ket
    # ------------------------------------------------------------------
    # THAY_THE | BO_SUNG | HUONG_DAN | LIEN_QUAN
    loai_lien_ket: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------
    # Van ban chu the (foreign_keys can thiet vi co 2 FK den cung 1 bang)
    van_ban: Mapped[VanBan] = relationship(
        "VanBan",
        foreign_keys=[van_ban_id],
        back_populates="lien_kets",
        lazy="joined",
    )

    # Van ban lien quan
    van_ban_lien_quan: Mapped[VanBan] = relationship(
        "VanBan",
        foreign_keys=[van_ban_lien_quan_id],
        lazy="joined",
    )
