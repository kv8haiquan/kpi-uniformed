"""
legal_service/models/xac_nhan_doc.py
======================================
Model xac nhan da doc van ban — bang legal.xac_nhan_doc.

Theo doi viec CBCC xac nhan da doc van ban phap luat.
Tinh nang:
  - da_doc: CBCC co mo/doc van ban khong
  - da_xac_nhan: CBCC bam nut xac nhan "da doc va hieu"
  - thoi_gian_doc_giay: thoi gian thuc te CBCC mo van ban (tracking)

UNIQUE constraint: (van_ban_id, cong_chuc_id)
— moi CBCC chi co 1 ban ghi xac nhan cho moi van ban.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from legal_service.models.base import Base, CongChucRef

if TYPE_CHECKING:
    from legal_service.models.van_ban import VanBan


class XacNhanDoc(Base):
    """Xac nhan da doc van ban phap luat — bang legal.xac_nhan_doc.

    Moi CBCC co mot ban ghi duy nhat cho moi van ban (UNIQUE van_ban_id + cong_chuc_id).
    He thong tu dong tao ban ghi khi CBCC lan dau mo van ban.
    """

    __tablename__ = "xac_nhan_doc"
    __table_args__ = (
        # Moi CBCC chi xac nhan 1 lan cho 1 van ban
        UniqueConstraint("van_ban_id", "cong_chuc_id", name="uq_xnd_van_ban_cong_chuc"),
        {"schema": "legal"},
    )

    # ------------------------------------------------------------------
    # Primary Key
    # ------------------------------------------------------------------
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )

    # ------------------------------------------------------------------
    # Foreign Keys
    # ------------------------------------------------------------------
    # Van ban duoc xac nhan
    van_ban_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("legal.van_ban.id"),
        nullable=False,
    )

    # Cong chuc xac nhan (FK cross-schema)
    cong_chuc_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("public.cong_chuc.id"),
        nullable=False,
    )

    # ------------------------------------------------------------------
    # Trang thai doc
    # ------------------------------------------------------------------
    # CBCC co mo/doc van ban khong (auto set khi mo van ban)
    da_doc: Mapped[bool] = mapped_column(Boolean, server_default=text("false"), nullable=False)

    # Thoi diem CBCC lan dau mo doc van ban
    ngay_doc: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Thoi gian doc thuc te (tinh bang giay — tracking behavioral)
    thoi_gian_doc_giay: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # ------------------------------------------------------------------
    # Xac nhan chinh thuc
    # ------------------------------------------------------------------
    # CBCC bam nut "Toi da doc va hieu noi dung nay"
    da_xac_nhan: Mapped[bool] = mapped_column(Boolean, server_default=text("false"), nullable=False)

    # Thoi diem CBCC bam nut xac nhan
    ngay_xac_nhan: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Ghi chu them (CBCC co the ghi chu khi xac nhan)
    ghi_chu: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # ------------------------------------------------------------------
    # Timestamp
    # ------------------------------------------------------------------
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=text("CURRENT_TIMESTAMP")
    )

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------
    # Van ban duoc xac nhan (joined — luon can thong tin van ban)
    van_ban: Mapped[VanBan] = relationship(
        "VanBan",
        back_populates="xac_nhan_docs",
        lazy="joined",
    )

    # Cong chuc xac nhan (joined — can ho ten de hien thi)
    cong_chuc: Mapped[CongChucRef] = relationship(
        "CongChucRef",
        foreign_keys=[cong_chuc_id],
        lazy="joined",
    )
