"""
lms_service/models/lich_su_reset_thi.py
=======================================
Model nhat ky reset luot thi DGNL — bang lms.lich_su_reset_thi.

Moi lan QT_DAO_TAO reset bai thi cua 1 thi sinh -> 1 row. Ghi lai AI reset,
reset CHO AI, LY DO, va — quan trong nhat — anh chup nguyen trang ban ghi
truoc khi reset (`du_lieu_truoc`), de con duong lui neu reset nham.

Vi sao khong FK CASCADE tu thi_sinh: nhat ky phai song lau hon doi tuong no
ghi lai. Neu ky thi hoac ban ghi thi sinh bi xoa, log van con (cac cot FK
chuyen NULL), nen `cong_chuc_id` va `ky_thi_id_snapshot` duoc luu rieng.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import DateTime, Integer, Numeric, String, Text, ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from lms_service.models.base import Base


class LichSuResetThi(Base):
    """Log 1 lan reset luot thi — bang lms.lich_su_reset_thi."""

    __tablename__ = "lich_su_reset_thi"
    __table_args__ = {"schema": "lms"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    # FK "mem": SET NULL khi doi tuong bi xoa, nhat ky van con
    thi_sinh_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("lms.thi_sinh.id", ondelete="SET NULL"), nullable=True
    )
    ky_thi_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("lms.ky_thi.id", ondelete="SET NULL"), nullable=True
    )
    # Snapshot dinh danh — khong bao gio NULL, dung de tra cuu khi FK da mat
    ky_thi_id_snapshot: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    cong_chuc_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("public.cong_chuc.id"), nullable=False
    )
    nguoi_reset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("public.cong_chuc.id"), nullable=False
    )

    # XOA_SACH (ve CHUA_THI, thi lai tu dau) | MO_KHOA_LUOT (giu ket qua, mo them luot)
    loai_reset: Mapped[str] = mapped_column(String(50), nullable=False)
    ly_do: Mapped[str] = mapped_column(Text, nullable=False)

    # Trich yeu trang thai truoc khi reset — de doc nhanh khong phai mo JSONB
    trang_thai_truoc: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    lan_thi_truoc: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    diem_truoc: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)

    # Anh chup TOAN BO ban ghi thi_sinh truoc khi reset (gom ca bai lam) —
    # day la duong lui duy nhat, khong duoc bo qua khi ghi log.
    du_lieu_truoc: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    thoi_gian: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False
    )
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP")
    )
