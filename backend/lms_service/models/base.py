"""
lms_service/models/base.py
==========================
Base class cho tat ca SQLAlchemy models trong module LMS.
Bao gom stub READONLY cho public.cong_chuc de resolve cross-schema FK.
"""

import uuid
from typing import Optional

from sqlalchemy import String, Boolean, ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """DeclarativeBase cho LMS service."""
    pass


class CongChucRef(Base):
    """Stub READONLY model cho public.cong_chuc.
    Chi dung de SQLAlchemy resolve ForeignKey('public.cong_chuc.id').
    KHONG INSERT/UPDATE/DELETE — chi SELECT/JOIN.
    """
    __tablename__ = "cong_chuc"
    __table_args__ = {"schema": "public"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    ma_cc: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    ho_ten: Mapped[str] = mapped_column(String(100), nullable=False)
    chuc_vu: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    don_vi_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("public.don_vi.id"), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, server_default=text("true"))
    is_lanh_dao: Mapped[bool] = mapped_column(Boolean, server_default=text("false"))


class DonViRef(Base):
    """Stub READONLY model cho public.don_vi.
    Chi dung de SQLAlchemy resolve ForeignKey va JOIN lay ten_don_vi.
    """
    __tablename__ = "don_vi"
    __table_args__ = {"schema": "public"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    ma_don_vi: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    ten_don_vi: Mapped[str] = mapped_column(String(200), nullable=False)
