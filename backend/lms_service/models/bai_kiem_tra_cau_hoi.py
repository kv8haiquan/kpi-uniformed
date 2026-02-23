"""
lms_service/models/bai_kiem_tra_cau_hoi.py
==========================================
Model lien ket bai kiem tra va cau hoi — bang lms.bai_kiem_tra_cau_hoi.
Composite PK: (bai_kiem_tra_id, cau_hoi_id) — KHONG co cot id.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from lms_service.models.base import Base

if TYPE_CHECKING:
    from lms_service.models.bai_kiem_tra import BaiKiemTra
    from lms_service.models.cau_hoi import CauHoi


class BaiKiemTraCauHoi(Base):
    """Lien ket bai kiem tra <-> cau hoi — bang lms.bai_kiem_tra_cau_hoi.
    Composite PK, khong co cot id rieng.
    """

    __tablename__ = "bai_kiem_tra_cau_hoi"
    __table_args__ = {"schema": "lms"}

    # Composite PK
    bai_kiem_tra_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("lms.bai_kiem_tra.id"), primary_key=True
    )
    cau_hoi_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("lms.cau_hoi.id"), primary_key=True
    )

    # Thu tu cau hoi trong bai kiem tra
    thu_tu: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Relationships
    bai_kiem_tra: Mapped[BaiKiemTra] = relationship(
        back_populates="cau_hoi_links", lazy="selectin"
    )
    cau_hoi: Mapped[CauHoi] = relationship(lazy="selectin")
