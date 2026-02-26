"""
forum_service/models/base.py
=============================
Base class cho tat ca SQLAlchemy models trong module Forum.
Bao gom stub READONLY cho public.cong_chuc, public.don_vi
de resolve cross-schema ForeignKey.

Quy tac bat buoc:
  - CongChucRef, DonViRef: KHONG INSERT/UPDATE/DELETE
  - KHONG map password_hash trong CongChucRef
"""

from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import Boolean, ForeignKey, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """DeclarativeBase cho Forum service."""

    pass


# ---------------------------------------------------------------------------
# READONLY stub models — public schema
# ---------------------------------------------------------------------------


class DonViRef(Base):
    """Stub READONLY model cho public.don_vi.
    Chi dung de SQLAlchemy resolve ForeignKey va JOIN lay ten_don_vi.
    KHONG INSERT/UPDATE/DELETE.
    """

    __tablename__ = "don_vi"
    __table_args__ = {"schema": "public"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    ma_don_vi: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    ten_don_vi: Mapped[str] = mapped_column(String(200), nullable=False)
    ten_viet_tat: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    loai_don_vi: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, server_default=text("true"))


class CongChucRef(Base):
    """Stub READONLY model cho public.cong_chuc.
    Chi dung de SQLAlchemy resolve ForeignKey('public.cong_chuc.id').
    KHONG INSERT/UPDATE/DELETE — chi SELECT/JOIN.

    Cac field duoc map:
      id, ma_cc, ho_ten, email, so_dien_thoai,
      don_vi_id, chuc_vu, is_lanh_dao, is_active

    KHONG map: password_hash (module Forum khong can doc)
    """

    __tablename__ = "cong_chuc"
    __table_args__ = {"schema": "public"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    ma_cc: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    ho_ten: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    so_dien_thoai: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # Quan he to chuc
    don_vi_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("public.don_vi.id"), nullable=True
    )

    # Chuc vu
    chuc_vu: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    is_lanh_dao: Mapped[bool] = mapped_column(Boolean, server_default=text("false"))
    is_active: Mapped[bool] = mapped_column(Boolean, server_default=text("true"))

    # Relationship READONLY — lay ten_don_vi khi JOIN
    don_vi: Mapped[Optional[DonViRef]] = relationship(
        "DonViRef",
        foreign_keys=[don_vi_id],
        lazy="joined",
    )
