"""
forum_service/models/chu_de.py
===============================
Chu de / Thread — bang forum.chu_de.

Model phuc tap nhat cua module Forum:
  - 21 cot (bao gom search_vector tsvector)
  - FK cross-schema: tac_gia_id, nguoi_duyet_id → public.cong_chuc(id)
  - FK noi bo: chuyen_muc_id → forum.chuyen_muc(id),
               tra_loi_chuan_id → forum.tra_loi(id)
  - JSONB: tags, van_ban_lien_quan, sop_lien_quan
  - Full-text search: search_vector (trigger DB tu dong cap nhat)

Trang thai (trang_thai):
  - CHO_DUYET: Cho duyet (neu chuyen_muc.yeu_cau_duyet = TRUE)
  - MO: Dang mo, cho phep tra loi
  - DONG: Da dong (da co dap an chuan)
  - AN: An (vi pham hoac trung)
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP, TSVECTOR, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from forum_service.models.base import Base, CongChucRef

if TYPE_CHECKING:
    from forum_service.models.chuyen_muc import ChuyenMuc
    from forum_service.models.tra_loi import TraLoi


class ChuDe(Base):
    """Chu de / Thread — bang forum.chu_de.

    Trang thai: CHO_DUYET → MO → DONG | AN
    search_vector duoc cap nhat tu dong boi trigger DB:
        trg_forum_chu_de_search → forum.update_chu_de_search()
    """

    __tablename__ = "chu_de"
    __table_args__ = {"schema": "forum"}

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )

    # FK noi bo — chuyen muc
    chuyen_muc_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("forum.chuyen_muc.id"),
        nullable=False,
    )

    # Noi dung chinh
    tieu_de: Mapped[str] = mapped_column(String(500), nullable=False)
    noi_dung: Mapped[str] = mapped_column(Text, nullable=False)

    # Tag phan loai — JSONB mang chuoi, VD: ["VNACCS", "thue XNK"]
    tags: Mapped[Any] = mapped_column(
        JSONB(astext_type=Text()),
        server_default=text("'[]'::jsonb"),
        nullable=False,
    )

    # FK cross-schema — tac gia
    tac_gia_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("public.cong_chuc.id"),
        nullable=False,
    )

    # Trang thai: CHO_DUYET, MO, DONG, AN
    trang_thai: Mapped[str] = mapped_column(
        String(50), server_default="MO", nullable=False,
    )

    # Flags dieu phoi
    is_ghim: Mapped[bool] = mapped_column(
        Boolean, server_default=text("false"), nullable=False,
    )
    is_khoa: Mapped[bool] = mapped_column(
        Boolean, server_default=text("false"), nullable=False,
    )

    # Thong ke (cap nhat boi app logic)
    so_luot_xem: Mapped[int] = mapped_column(
        Integer, server_default=text("0"), nullable=False,
    )
    so_tra_loi: Mapped[int] = mapped_column(
        Integer, server_default=text("0"), nullable=False,
    )
    so_upvote: Mapped[int] = mapped_column(
        Integer, server_default=text("0"), nullable=False,
    )

    # Dap an chuan — FK den forum.tra_loi(id), set sau khi tao
    tra_loi_chuan_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("forum.tra_loi.id"),
        nullable=True,
    )

    # Lien ket cross-module (JSONB)
    van_ban_lien_quan: Mapped[Optional[Any]] = mapped_column(
        JSONB, nullable=True,
    )
    sop_lien_quan: Mapped[Optional[Any]] = mapped_column(
        JSONB, nullable=True,
    )

    # Dieu phoi — nguoi duyet FK cross-schema
    nguoi_duyet_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("public.cong_chuc.id"),
        nullable=True,
    )
    ngay_duyet: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP, nullable=True,
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"), nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"), nullable=False,
    )

    # Soft delete
    is_deleted: Mapped[bool] = mapped_column(
        Boolean, server_default=text("false"), nullable=False,
    )

    # Full-text search vector — trigger DB tu dong cap nhat
    # KHONG set gia tri thu cong, chi dung de query voi plainto_tsquery()
    search_vector: Mapped[Optional[Any]] = mapped_column(
        TSVECTOR, nullable=True,
    )

    # --- Relationships ---

    # Chuyen muc chua chu de nay
    chuyen_muc: Mapped[Optional[ChuyenMuc]] = relationship(
        "ChuyenMuc",
        back_populates="chu_de_list",
        lazy="joined",
    )

    # Tac gia — FK cross-schema den public.cong_chuc
    tac_gia: Mapped[Optional[CongChucRef]] = relationship(
        "CongChucRef",
        foreign_keys=[tac_gia_id],
        lazy="joined",
    )

    # Nguoi duyet — FK cross-schema den public.cong_chuc
    nguoi_duyet: Mapped[Optional[CongChucRef]] = relationship(
        "CongChucRef",
        foreign_keys=[nguoi_duyet_id],
        lazy="joined",
    )

    # Dap an chuan — 1 tra loi duoc chon lam chuan
    tra_loi_chuan: Mapped[Optional[TraLoi]] = relationship(
        "TraLoi",
        foreign_keys=[tra_loi_chuan_id],
        lazy="joined",
        uselist=False,
    )

    # Danh sach tat ca tra loi
    # KHONG eager load — service su dung query rieng de lay tra loi
    tra_loi_list: Mapped[list[TraLoi]] = relationship(
        "TraLoi",
        back_populates="chu_de",
        foreign_keys="TraLoi.chu_de_id",
        lazy="noload",
    )
