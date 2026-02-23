"""
portal_service/models/bai_viet.py
==================================
Model bai viet — bang portal.bai_viet.

Bai viet portal (tin tuc, thong bao, tin hoat dong, cap nhat phap luat):
  - Co workflow duyet: NHAP → KIEM_TRA → DUYET → XUAT_BAN
  - 3 FK cross-schema den public.cong_chuc (nguoi_soan, nguoi_kiem_tra, nguoi_duyet)
  - Ghim bai viet quan trong len dau trang
  - Theo doi so luot xem

Workflow duyet:
  - NHAP: Soan nhap, chua gui duyet
  - KIEM_TRA: Gui kiem tra (nguoi_kiem_tra_id set)
  - DUYET: Duyet dang (nguoi_duyet_id set)
  - XUAT_BAN: Xuat ban ra trang chu (ngay_xuat_ban set)
  - THU_HOI: Thu hoi bai viet (khong hien thi nua)
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from portal_service.models.base import Base, CongChucRef

if TYPE_CHECKING:
    from portal_service.models.chuyen_muc import ChuyenMuc


class BaiViet(Base):
    """Bai viet portal — bang portal.bai_viet.

    Bai viet tin tuc, thong bao, tin hoat dong, cap nhat phap luat.
    Co workflow duyet 3 cap: soan → kiem tra → duyet → xuat ban.
    """

    __tablename__ = "bai_viet"
    __table_args__ = {"schema": "portal"}

    # ------------------------------------------------------------------
    # Primary Key
    # ------------------------------------------------------------------
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )

    # ------------------------------------------------------------------
    # FK chuyen muc
    # ------------------------------------------------------------------
    # FK den chuyen_muc (Tin chi dao, Thong bao, ...)
    chuyen_muc_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("portal.chuyen_muc.id"),
        nullable=True,
    )

    # ------------------------------------------------------------------
    # Thong tin bai viet
    # ------------------------------------------------------------------
    # Tieu de bai viet
    tieu_de: Mapped[str] = mapped_column(String(500), nullable=False)

    # Tom tat noi dung (hien thi trong danh sach)
    tom_tat: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Noi dung day du (HTML)
    noi_dung: Mapped[str] = mapped_column(Text, nullable=False)

    # Anh dai dien (URL MinIO hoac external)
    anh_dai_dien: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # ------------------------------------------------------------------
    # Workflow duyet: NHAP → KIEM_TRA → DUYET → XUAT_BAN → THU_HOI
    # ------------------------------------------------------------------
    # NHAP | KIEM_TRA | DUYET | XUAT_BAN | THU_HOI
    trang_thai: Mapped[str] = mapped_column(
        String(50), server_default=text("'NHAP'"), nullable=False
    )

    # FK cross-schema: nguoi soan nhap bai viet
    nguoi_soan_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("public.cong_chuc.id"),
        nullable=True,
    )

    # FK cross-schema: nguoi kiem tra noi dung
    nguoi_kiem_tra_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("public.cong_chuc.id"),
        nullable=True,
    )

    # FK cross-schema: nguoi duyet cuoi cung
    nguoi_duyet_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("public.cong_chuc.id"),
        nullable=True,
    )

    # Ngay chinh thuc xuat ban (set khi chuyen sang XUAT_BAN)
    ngay_xuat_ban: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # ------------------------------------------------------------------
    # Flags
    # ------------------------------------------------------------------
    # Ghim bai viet len dau trang (bai quan trong)
    is_ghim: Mapped[bool] = mapped_column(
        Boolean, server_default=text("false"), nullable=False
    )

    # So luot xem (tang moi lan user xem bai)
    so_luot_xem: Mapped[int] = mapped_column(
        Integer, server_default="0", nullable=False
    )

    # ------------------------------------------------------------------
    # Timestamps + soft delete
    # ------------------------------------------------------------------
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=text("CURRENT_TIMESTAMP")
    )
    is_deleted: Mapped[bool] = mapped_column(
        Boolean, server_default=text("false"), nullable=False
    )

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------

    # Chuyen muc (joined load — luon can thong tin chuyen muc)
    chuyen_muc: Mapped[Optional[ChuyenMuc]] = relationship(
        "ChuyenMuc",
        back_populates="bai_viets",
        lazy="joined",
    )

    # Nguoi soan nhap (joined load — hien thi ho ten)
    nguoi_soan: Mapped[Optional[CongChucRef]] = relationship(
        "CongChucRef",
        foreign_keys=[nguoi_soan_id],
        lazy="joined",
    )

    # Nguoi kiem tra (joined load — hien thi ho ten)
    nguoi_kiem_tra: Mapped[Optional[CongChucRef]] = relationship(
        "CongChucRef",
        foreign_keys=[nguoi_kiem_tra_id],
        lazy="joined",
    )

    # Nguoi duyet (joined load — hien thi ho ten)
    nguoi_duyet: Mapped[Optional[CongChucRef]] = relationship(
        "CongChucRef",
        foreign_keys=[nguoi_duyet_id],
        lazy="joined",
    )
