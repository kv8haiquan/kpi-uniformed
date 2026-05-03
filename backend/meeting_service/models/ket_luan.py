"""meeting.ket_luan — kết luận / nhiệm vụ giao."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Optional

from sqlalchemy import Boolean, Date, ForeignKey, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column

from meeting_service.models.base import Base


class KetLuan(Base):
    __tablename__ = "ket_luan"
    __table_args__ = {"schema": "meeting"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    cuoc_hop_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("meeting.cuoc_hop.id", ondelete="CASCADE"), nullable=False
    )
    noi_dung: Mapped[str] = mapped_column(Text, nullable=False)
    nguoi_phu_trach_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("public.cong_chuc.id"), nullable=False
    )
    don_vi_phu_trach_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("public.don_vi.id"), nullable=True
    )

    han_hoan_thanh: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    muc_uu_tien: Mapped[str] = mapped_column(
        String(10), server_default="TRUNG_BINH", nullable=False
    )
    tien_do_phan_tram: Mapped[int] = mapped_column(Integer, server_default="0", nullable=False)
    trang_thai: Mapped[str] = mapped_column(
        String(30), server_default="CHUA_BAT_DAU", nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("NOW()"), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("NOW()"), nullable=False
    )
    is_deleted: Mapped[bool] = mapped_column(Boolean, server_default=text("FALSE"), nullable=False)
