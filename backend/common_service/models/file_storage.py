"""
common_service/models/file_storage.py
======================================
File metadata tren MinIO.
Bang: common.file_storage

Module: LMS, FORUM, LEGAL, PORTAL
Soft delete: is_deleted flag
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, Boolean, ForeignKey, String, Text, text
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, CongChucRef


class FileStorage(Base):
    """File metadata tren MinIO.

    Luu thong tin file (ten, duong dan, kich thuoc, MIME type) cho
    tat ca module. File thuc te luu tren MinIO, bang nay chi luu metadata.

    file_path theo cau truc: "{module}/{loai}/{uuid}.{ext}"
    Vi du: "lms/videos/abc-123.mp4"
    """

    __tablename__ = "file_storage"
    __table_args__ = {"schema": "common"}

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )

    # Thong tin file
    file_name: Mapped[str] = mapped_column(String(500), nullable=False)
    file_path: Mapped[str] = mapped_column(Text, nullable=False)
    file_size_bytes: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    mime_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Phan loai module: LMS, FORUM, LEGAL, PORTAL
    module: Mapped[str] = mapped_column(String(50), nullable=False)

    # Link den doi tuong cha (BAI_HOC, CHU_DE, VAN_BAN, BAI_VIET...)
    doi_tuong_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    doi_tuong_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )

    # Nguoi tai len — FK cross-schema den public.cong_chuc
    nguoi_tai_len_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("public.cong_chuc.id"),
        nullable=True,
    )

    # Timestamps + soft delete
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"), nullable=False
    )
    is_deleted: Mapped[bool] = mapped_column(
        Boolean, server_default=text("false"), nullable=False
    )

    # --- Relationships ---
    nguoi_tai_len: Mapped[Optional[CongChucRef]] = relationship(
        "CongChucRef",
        foreign_keys=[nguoi_tai_len_id],
        lazy="joined",
    )

    # --- Property helpers ---
    @property
    def file_url(self) -> str:
        """Tao full URL tu file_path."""
        return f"/files/{self.file_path}"
