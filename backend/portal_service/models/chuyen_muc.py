"""
portal_service/models/chuyen_muc.py
====================================
Model chuyen muc bai viet — bang portal.chuyen_muc.

Chuyen muc dung de phan loai bai viet:
  - Tin chi dao (loai: TIN_TUC, slug: tin-chi-dao)
  - Thong bao (loai: TIN_TUC, slug: thong-bao)
  - Tin hoat dong (loai: TIN_TUC, slug: tin-hoat-dong)
  - Cap nhat phap luat (loai: PHAP_LUAT, slug: cap-nhat-phap-luat)
  - ...

Co the them chuyen muc khac theo nhu cau.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from portal_service.models.base import Base

if TYPE_CHECKING:
    from portal_service.models.bai_viet import BaiViet


class ChuyenMuc(Base):
    """Chuyen muc bai viet — bang portal.chuyen_muc.

    Phan loai bai viet theo chu de:
      - Tin chi dao
      - Thong bao
      - Tin hoat dong
      - Cap nhat phap luat
      - ...
    """

    __tablename__ = "chuyen_muc"
    __table_args__ = {"schema": "portal"}

    # ------------------------------------------------------------------
    # Primary Key
    # ------------------------------------------------------------------
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )

    # ------------------------------------------------------------------
    # Thong tin chuyen muc
    # ------------------------------------------------------------------
    # Ten chuyen muc, VD: "Tin chi dao", "Thong bao"
    ten: Mapped[str] = mapped_column(String(200), nullable=False)

    # Slug dung cho URL, VD: "tin-chi-dao", "thong-bao"
    slug: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)

    # Mo ta chuyen muc
    mo_ta: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # ------------------------------------------------------------------
    # Thu tu hien thi va loai
    # ------------------------------------------------------------------
    # Thu tu hien thi tren menu (tang dan)
    thu_tu: Mapped[int] = mapped_column(Integer, server_default="0", nullable=False)

    # Loai chuyen muc: TIN_TUC | PHAP_LUAT | TAI_LIEU | KHAC
    loai: Mapped[str] = mapped_column(
        String(50), server_default=text("'TIN_TUC'"), nullable=False
    )

    # ------------------------------------------------------------------
    # Flags
    # ------------------------------------------------------------------
    # Hien thi hay an chuyen muc
    is_active: Mapped[bool] = mapped_column(
        Boolean, server_default=text("true"), nullable=False
    )

    # ------------------------------------------------------------------
    # Timestamps
    # ------------------------------------------------------------------
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=text("CURRENT_TIMESTAMP")
    )

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------
    # Danh sach bai viet thuoc chuyen muc nay
    bai_viets: Mapped[list[BaiViet]] = relationship(
        "BaiViet",
        back_populates="chuyen_muc",
        lazy="selectin",
    )
