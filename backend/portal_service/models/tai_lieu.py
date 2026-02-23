"""
portal_service/models/tai_lieu.py
==================================
Model tai lieu — bang portal.tai_lieu.

Tai lieu luu tru file (PDF, Word, Excel, ...) tren MinIO:
  - Versioning: phien_ban, phien_ban_truoc_id (self-reference)
  - JSONB: tags (array), metadata (dict)
  - Quyen truy cap: TAT_CA | THEO_DON_VI
  - Theo doi file_size_bytes, file_type

Phan quyen:
  - TAT_CA: Moi nguoi tai duoc
  - THEO_DON_VI: Chi don vi duoc chi dinh (don_vi_ids JSONB array)
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from portal_service.models.base import Base, CongChucRef

if TYPE_CHECKING:
    from portal_service.models.thu_muc import ThuMuc


class TaiLieu(Base):
    """Tai lieu — bang portal.tai_lieu.

    Luu tru file tai lieu (PDF, Word, Excel, ...) tren MinIO.
    Ho tro versioning va phan quyen theo don vi.
    """

    __tablename__ = "tai_lieu"
    __table_args__ = {"schema": "portal"}

    # ------------------------------------------------------------------
    # Primary Key
    # ------------------------------------------------------------------
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )

    # ------------------------------------------------------------------
    # Thong tin tai lieu
    # ------------------------------------------------------------------
    # Ten tai lieu, VD: "Quy dinh noi bo ve quan ly KPI 2026"
    ten_tai_lieu: Mapped[str] = mapped_column(String(300), nullable=False)

    # Mo ta tai lieu
    mo_ta: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # ------------------------------------------------------------------
    # FK thu muc
    # ------------------------------------------------------------------
    # FK den thu_muc (Van ban noi bo, Tai lieu dao tao, ...)
    thu_muc_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("portal.thu_muc.id"),
        nullable=True,
    )

    # ------------------------------------------------------------------
    # Thong tin file
    # ------------------------------------------------------------------
    # URL file tren MinIO
    file_url: Mapped[str] = mapped_column(Text, nullable=False)

    # Ten file goc (khi user upload), VD: "quy_dinh_2026.pdf"
    file_name: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Dung luong file (bytes) — dung BigInteger cho file lon
    file_size_bytes: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)

    # Loai file (MIME type), VD: "application/pdf", "application/vnd.ms-excel"
    file_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # ------------------------------------------------------------------
    # Versioning (self-reference)
    # ------------------------------------------------------------------
    # Phien ban hien tai (tang dan: 1, 2, 3, ...)
    phien_ban: Mapped[int] = mapped_column(Integer, server_default="1", nullable=False)

    # FK den phien ban truoc (NULL = phien ban dau tien)
    phien_ban_truoc_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("portal.tai_lieu.id"),
        nullable=True,
    )

    # ------------------------------------------------------------------
    # Tags va metadata (JSONB)
    # ------------------------------------------------------------------
    # Tags tu do, VD: ["2026", "KPI", "quan-ly"]
    tags: Mapped[Optional[list]] = mapped_column(
        JSONB, server_default=text("'[]'"), nullable=True
    )

    # Metadata mo rong (custom fields), VD: {"author": "Nguyen Van A", "year": 2026}
    # Luu y: 'metadata' la reserved attribute cua SQLAlchemy Base
    # → Map thanh column name "metadata" nhung attribute name la file_metadata
    file_metadata: Mapped[Optional[dict]] = mapped_column(
        "metadata", JSONB, server_default=text("'{}'"), nullable=True
    )

    # ------------------------------------------------------------------
    # Phan quyen truy cap
    # ------------------------------------------------------------------
    # Quyen truy cap: TAT_CA | THEO_DON_VI
    quyen_truy_cap: Mapped[str] = mapped_column(
        String(50), server_default=text("'TAT_CA'"), nullable=False
    )

    # Danh sach don_vi_id duoc phep tai (JSONB array)
    # VD: ["uuid1", "uuid2"]
    don_vi_ids: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # ------------------------------------------------------------------
    # Nguoi tai len
    # ------------------------------------------------------------------
    # FK cross-schema den public.cong_chuc
    nguoi_tai_len_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("public.cong_chuc.id"),
        nullable=True,
    )

    # ------------------------------------------------------------------
    # Timestamps + soft delete
    # ------------------------------------------------------------------
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=text("CURRENT_TIMESTAMP")
    )
    is_deleted: Mapped[bool] = mapped_column(
        Boolean, server_default=text("false"), nullable=False
    )

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------

    # Thu muc chua tai lieu (joined load — can thong tin thu muc)
    thu_muc: Mapped[Optional[ThuMuc]] = relationship(
        "ThuMuc",
        back_populates="tai_lieus",
        lazy="joined",
    )

    # Self-reference: phien ban truoc
    phien_ban_truoc: Mapped[Optional[TaiLieu]] = relationship(
        "TaiLieu",
        foreign_keys=[phien_ban_truoc_id],
        remote_side="TaiLieu.id",  # type: ignore[assignment]
        lazy="select",
    )

    # Nguoi tai len file (joined load — hien thi ho ten)
    nguoi_tai_len: Mapped[Optional[CongChucRef]] = relationship(
        "CongChucRef",
        foreign_keys=[nguoi_tai_len_id],
        lazy="joined",
    )
