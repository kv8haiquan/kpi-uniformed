"""
portal_service/models/vinh_danh_thang.py
=========================================
Model VinhDanhThang — bang portal.vinh_danh_thang.

Vinh danh cong chuc tieu bieu thang:
  - 1 cong chuc / thang (UNIQUE partial WHERE PUBLISHED)
  - Workflow: DRAFT -> PUBLISHED
  - 2 FK cross-schema den public.cong_chuc (cong_chuc_id, nguoi_tao_id)
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from portal_service.models.base import Base, CongChucRef


class VinhDanhThang(Base):
    """Vinh danh cong chuc tieu bieu thang — bang portal.vinh_danh_thang."""

    __tablename__ = "vinh_danh_thang"
    __table_args__ = {"schema": "portal"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )

    # Thang/nam vinh danh
    thang: Mapped[int] = mapped_column(Integer, nullable=False)
    nam: Mapped[int] = mapped_column(Integer, nullable=False)

    # FK cross-schema: cong chuc duoc vinh danh
    cong_chuc_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("public.cong_chuc.id"),
        nullable=False,
    )

    # Tieu de + noi dung vinh danh
    tieu_de: Mapped[str] = mapped_column(String(200), nullable=False)
    ly_do: Mapped[str] = mapped_column(Text, nullable=False)
    anh_chan_dung: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    # Vi tri anh trong khung tron (CSS object-position), vd "50% 30%"
    anh_vi_tri: Mapped[Optional[str]] = mapped_column(
        String(20), server_default=text("'50% 50%'"), nullable=True
    )
    loi_tuyen_duong: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Workflow: DRAFT | PUBLISHED
    trang_thai: Mapped[str] = mapped_column(
        String(50), server_default=text("'DRAFT'"), nullable=False
    )

    # Admin tao ban ghi
    nguoi_tao_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("public.cong_chuc.id"),
        nullable=True,
    )

    # Ngay cong bo (set khi PUBLISHED)
    ngay_cong_bo: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=text("CURRENT_TIMESTAMP")
    )

    # Relationships
    cong_chuc: Mapped[Optional[CongChucRef]] = relationship(
        "CongChucRef",
        foreign_keys=[cong_chuc_id],
        lazy="joined",
    )
    nguoi_tao: Mapped[Optional[CongChucRef]] = relationship(
        "CongChucRef",
        foreign_keys=[nguoi_tao_id],
        lazy="joined",
    )
