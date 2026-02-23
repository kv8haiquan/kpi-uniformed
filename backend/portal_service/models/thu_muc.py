"""
portal_service/models/thu_muc.py
=================================
Model thu muc tai lieu — bang portal.thu_muc.

Thu muc co cau truc cay (tree structure):
  - Van ban noi bo (parent_id: NULL)
    - Quy dinh noi bo (parent_id: uuid-van-ban-noi-bo)
    - Huong dan noi bo (parent_id: uuid-van-ban-noi-bo)
  - Tai lieu dao tao (parent_id: NULL)
  - Bieu mau (parent_id: NULL)
  - ...

Quyen truy cap:
  - TAT_CA: Moi nguoi xem duoc
  - THEO_DON_VI: Chi don vi duoc chi dinh (don_vi_ids JSONB)
  - THEO_VAI_TRO: Chi vai tro duoc chi dinh (vai_tro_ids JSONB)
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from portal_service.models.base import Base, CongChucRef

if TYPE_CHECKING:
    from portal_service.models.tai_lieu import TaiLieu


class ThuMuc(Base):
    """Thu muc tai lieu — bang portal.thu_muc.

    Cau truc cay (tree structure) voi parent_id self-reference.
    Quan ly phan quyen theo don vi hoac vai tro.
    """

    __tablename__ = "thu_muc"
    __table_args__ = {"schema": "portal"}

    # ------------------------------------------------------------------
    # Primary Key
    # ------------------------------------------------------------------
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )

    # ------------------------------------------------------------------
    # Thong tin thu muc
    # ------------------------------------------------------------------
    # Ten thu muc, VD: "Van ban noi bo", "Tai lieu dao tao"
    ten: Mapped[str] = mapped_column(String(200), nullable=False)

    # ------------------------------------------------------------------
    # Tree structure (self-reference)
    # ------------------------------------------------------------------
    # FK den thu muc cha (NULL = thu muc goc)
    parent_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("portal.thu_muc.id"),
        nullable=True,
    )

    # ------------------------------------------------------------------
    # Thu tu hien thi
    # ------------------------------------------------------------------
    # Thu tu hien thi trong danh sach (tang dan)
    thu_tu: Mapped[int] = mapped_column(Integer, server_default="0", nullable=False)

    # ------------------------------------------------------------------
    # Phan quyen truy cap
    # ------------------------------------------------------------------
    # Quyen truy cap: TAT_CA | THEO_DON_VI | THEO_VAI_TRO
    quyen_truy_cap: Mapped[str] = mapped_column(
        String(50), server_default=text("'TAT_CA'"), nullable=False
    )

    # Danh sach don_vi_id duoc phep xem (JSONB array)
    # VD: ["uuid1", "uuid2"]
    don_vi_ids: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # ------------------------------------------------------------------
    # Nguoi tao
    # ------------------------------------------------------------------
    # FK cross-schema den public.cong_chuc
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("public.cong_chuc.id"),
        nullable=True,
    )

    # ------------------------------------------------------------------
    # Timestamps
    # ------------------------------------------------------------------
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=text("CURRENT_TIMESTAMP")
    )

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------

    # Self-reference: thu muc cha
    parent: Mapped[Optional[ThuMuc]] = relationship(
        "ThuMuc",
        foreign_keys=[parent_id],
        remote_side="ThuMuc.id",  # type: ignore[assignment]
        back_populates="children",
        lazy="select",
    )

    # Self-reference: danh sach thu muc con
    children: Mapped[list[ThuMuc]] = relationship(
        "ThuMuc",
        back_populates="parent",
        lazy="selectin",
    )

    # Nguoi tao thu muc (joined load — hien thi ho ten)
    created_by_user: Mapped[Optional[CongChucRef]] = relationship(
        "CongChucRef",
        foreign_keys=[created_by],
        lazy="joined",
    )

    # Danh sach tai lieu trong thu muc nay
    tai_lieus: Mapped[list[TaiLieu]] = relationship(
        "TaiLieu",
        back_populates="thu_muc",
        lazy="selectin",
    )
