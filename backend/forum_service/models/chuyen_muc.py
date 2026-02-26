"""
forum_service/models/chuyen_muc.py
===================================
Chuyen muc dien dan — bang forum.chuyen_muc.

Ho tro phan cap cha-con (toi da 2 cap):
  - Cap 1: Chuyen muc goc (parent_id IS NULL)
  - Cap 2: Chuyen muc con (parent_id tro den chuyen muc goc)

Cau hinh dac biet:
  - chi_doc: TRUE = chi expert/admin moi dang bai duoc
  - yeu_cau_duyet: TRUE = bai moi can duyet truoc khi hien
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from forum_service.models.base import Base

if TYPE_CHECKING:
    from forum_service.models.chu_de import ChuDe


class ChuyenMuc(Base):
    """Chuyen muc dien dan — bang forum.chuyen_muc.

    Phan cap toi da 2 cap: goc → con.
    """

    __tablename__ = "chuyen_muc"
    __table_args__ = {"schema": "forum"}

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )

    # Thong tin chuyen muc
    ten_chuyen_muc: Mapped[str] = mapped_column(String(200), nullable=False)
    mo_ta: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    icon: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    thu_tu: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Phan cap — self-reference (toi da 2 cap)
    parent_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("forum.chuyen_muc.id"),
        nullable=True,
    )

    # Cau hinh phan quyen
    chi_doc: Mapped[bool] = mapped_column(
        Boolean, server_default=text("false"), nullable=False,
    )
    yeu_cau_duyet: Mapped[bool] = mapped_column(
        Boolean, server_default=text("false"), nullable=False,
    )

    # Trang thai
    is_active: Mapped[bool] = mapped_column(
        Boolean, server_default=text("true"), nullable=False,
    )

    # Timestamp — chi co created_at (khong co updated_at theo schema)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"), nullable=False,
    )

    # --- Relationships ---

    # Self-reference: cha-con
    parent: Mapped[Optional[ChuyenMuc]] = relationship(
        "ChuyenMuc",
        remote_side="ChuyenMuc.id",
        back_populates="children",
        lazy="joined",
    )
    children: Mapped[list[ChuyenMuc]] = relationship(
        "ChuyenMuc",
        back_populates="parent",
        lazy="noload",
    )

    # Danh sach chu de trong chuyen muc
    # KHONG eager load — service su dung query rieng de dem/lay chu de
    chu_de_list: Mapped[list[ChuDe]] = relationship(
        "ChuDe",
        back_populates="chuyen_muc",
        lazy="noload",
    )
