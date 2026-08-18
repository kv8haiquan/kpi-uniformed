"""
DeclarativeBase chung cho HKG models.

Bao gồm stub READONLY cho public.cong_chuc và public.don_vi để SQLAlchemy
resolve cross-schema ForeignKey. KHÔNG sửa/INSERT vào 2 bảng này — chỉ JOIN.
"""

import uuid
from typing import Optional

from sqlalchemy import Boolean, ForeignKey, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """DeclarativeBase cho HKG service."""
    pass


class CongChucRef(Base):
    """Stub READONLY cho public.cong_chuc — chỉ resolve FK + JOIN."""
    __tablename__ = "cong_chuc"
    __table_args__ = {"schema": "public"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    ma_cc: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    ho_ten: Mapped[str] = mapped_column(String(100), nullable=False)
    don_vi_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("public.don_vi.id"), nullable=True
    )
    # Lịch công tác hiển thị chức vụ cạnh họ tên (thẻ lịch lãnh đạo, tóm tắt
    # lịch, danh sách trực ban) nên map thêm cột này. Vẫn CHỈ ĐỌC.
    chuc_vu: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, server_default=text("true"))


class DonViRef(Base):
    """Stub READONLY cho public.don_vi — chỉ resolve FK + JOIN."""
    __tablename__ = "don_vi"
    __table_args__ = {"schema": "public"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    ma_don_vi: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    ten_don_vi: Mapped[str] = mapped_column(String(200), nullable=False)
