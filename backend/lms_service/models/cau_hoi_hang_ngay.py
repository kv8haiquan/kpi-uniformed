"""
lms_service/models/cau_hoi_hang_ngay.py
=======================================
Model chot cau hoi DGNL phat moi ngay — bang lms.cau_hoi_hang_ngay.

VI SAO CAN BANG NAY (thay vi boc ngau nhien moi lan goi):
  - Bot Zalo co the goi lai nhieu lan trong ngay (thu lai khi mang loi, nhieu
    nguoi cung nhan). Khong chot thi moi lan ra mot cau khac nhau.
  - Chot roi thi tra dap an theo `cau_hoi_id` moi dung — nguoi dung tra loi
    luc 23h hay sang hom sau van khop cau ho da nhan.
  - Co lich su "ngay nao phat cau nao" de khong lap lai va de thong ke sau nay.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from lms_service.models.base import Base

if TYPE_CHECKING:
    from lms_service.models.cau_hoi_dgnl import CauHoiDgnl


class CauHoiHangNgay(Base):
    """Cau hoi DGNL da phat trong ngay — bang lms.cau_hoi_hang_ngay."""

    __tablename__ = "cau_hoi_hang_ngay"
    __table_args__ = {"schema": "lms"}

    # Khoa chinh la NGAY (gio VN) — moi ngay dung 1 cau, chong trung o tang DB
    ngay: Mapped[date] = mapped_column(Date, primary_key=True)

    cau_hoi_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("lms.cau_hoi_dgnl.id"), nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP")
    )

    cau_hoi: Mapped[CauHoiDgnl] = relationship(lazy="selectin")
