"""
legal_service/models/loai_van_ban.py
=====================================
Model danh muc loai van ban — bang legal.loai_van_ban.

Cac gia tri ma mac dinh:
  LUAT, NGHI_DINH, THONG_TU, QUYET_DINH,
  CONG_VAN, CHI_THI, HUONG_DAN, NOI_BO
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Integer, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from legal_service.models.base import Base

if TYPE_CHECKING:
    from legal_service.models.van_ban import VanBan


class LoaiVanBan(Base):
    """Danh muc loai van ban — bang legal.loai_van_ban.

    Luu tru cac loai phan loai van ban phap luat:
    Luat, Nghi dinh, Thong tu, Quyet dinh, Cong van, Chi thi, Huong dan, Noi bo.
    """

    __tablename__ = "loai_van_ban"
    __table_args__ = {"schema": "legal"}

    # PK
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )

    # Ma loai van ban: LUAT, NGHI_DINH, THONG_TU, QUYET_DINH, ...
    ma: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    # Ten day du hien thi
    ten: Mapped[str] = mapped_column(String(200), nullable=False)

    # Thu tu hien thi trong danh sach
    thu_tu: Mapped[Optional[int]] = mapped_column(Integer, server_default="0")

    # Relationships — danh sach van ban thuoc loai nay
    # Dung lazy="noload" vi khong bao gio can load tat ca VB khi query LoaiVanBan
    # Tranh N+1 query khi lay danh sach loai van ban
    van_bans: Mapped[list[VanBan]] = relationship(
        "VanBan",
        back_populates="loai_van_ban",
        lazy="noload",
    )
