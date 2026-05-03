"""meeting.nhom_thanh_phan — nhóm thành phần dùng chung cho nhiều cuộc họp."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey, String, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from meeting_service.models.base import Base

if TYPE_CHECKING:
    pass  # forward ref; chi_tiet được khai báo qua string trong relationship()


class NhomThanhPhan(Base):
    """Nhóm thành phần — danh sách thành viên dùng chung cho các cuộc họp lặp lại."""

    __tablename__ = "nhom_thanh_phan"
    __table_args__ = {"schema": "meeting"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    ten_nhom: Mapped[str] = mapped_column(String(200), nullable=False)
    mo_ta: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    loai_nhom: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    nguoi_tao_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("public.cong_chuc.id"), nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("NOW()"), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("NOW()"), nullable=False
    )

    chi_tiet: Mapped[list["NhomThanhPhanChiTiet"]] = relationship(
        "NhomThanhPhanChiTiet",
        back_populates="nhom",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class NhomThanhPhanChiTiet(Base):
    """Chi tiết thành viên trong nhóm — vai_tro + loai_tham_du."""

    __tablename__ = "nhom_thanh_phan_chi_tiet"
    __table_args__ = (
        UniqueConstraint("nhom_id", "cong_chuc_id",
                         name="uq_nhom_tp_chi_tiet_nhom_cong_chuc"),
        {"schema": "meeting"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    nhom_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("meeting.nhom_thanh_phan.id", ondelete="CASCADE"),
        nullable=False,
    )
    cong_chuc_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("public.cong_chuc.id"), nullable=False
    )

    vai_tro: Mapped[str] = mapped_column(
        String(20), server_default="THANH_VIEN", nullable=False
    )
    loai_tham_du: Mapped[str] = mapped_column(
        String(20), server_default="BAT_BUOC", nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("NOW()"), nullable=False
    )

    nhom: Mapped["NhomThanhPhan"] = relationship(
        "NhomThanhPhan", back_populates="chi_tiet", lazy="select"
    )
