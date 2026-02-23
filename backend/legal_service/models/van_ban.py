"""
legal_service/models/van_ban.py
================================
Model kho van ban phap luat — bang legal.van_ban.

Day la model PHUC TAP NHAT trong module Legal:
  - 2 FK cross-schema den public.cong_chuc (nguoi_nhap, nguoi_duyet)
  - 1 self-reference FK (van_ban_thay_the_id)
  - 3 cot JSONB (chuyen_de, doi_tuong_ap_dung, tags)
  - 1 cot TSVECTOR (search_vector — quan ly boi PostgreSQL trigger)
  - 5 relationships (loai_van_ban, nguoi_nhap, nguoi_duyet, van_ban_thay_the, lien_kets, ...)

Workflow duyet: NHAP → CHO_DUYET → DA_DUYET → DA_XUAT_BAN

Trang thai hieu luc:
  CON_HIEU_LUC | HET_HIEU_LUC | BI_THAY_THE | DANG_SUA_DOI

Muc do:
  KHAN (doc trong 24h) | QUAN_TRONG (3 ngay) | BINH_THUONG
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from legal_service.models.base import Base, CongChucRef

if TYPE_CHECKING:
    from legal_service.models.loai_van_ban import LoaiVanBan
    from legal_service.models.quiz_van_ban import QuizVanBan
    from legal_service.models.van_ban_lien_ket import VanBanLienKet
    from legal_service.models.xac_nhan_doc import XacNhanDoc


class VanBan(Base):
    """Kho van ban phap luat — bang legal.van_ban.

    Luu tru toan bo van ban phap luat: luat, nghi dinh, thong tu,
    quyet dinh, cong van, chi thi, huong dan, van ban noi bo.

    Tinh nang dac thu:
      - Diem moi quy dinh: mo ta diem moi so voi VB cu
      - Viec can lam: huong dan CBCC sau khi doc
      - Bat buoc doc + han xac nhan: theo doi tuan thu
      - Full-text search: tsvector tu dong cap nhat qua trigger
    """

    __tablename__ = "van_ban"
    __table_args__ = {"schema": "legal"}

    # ------------------------------------------------------------------
    # Primary Key
    # ------------------------------------------------------------------
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )

    # ------------------------------------------------------------------
    # Thong tin co ban van ban
    # ------------------------------------------------------------------
    # So hieu van ban, VD: "335/2025/ND-CP"
    so_hieu: Mapped[str] = mapped_column(String(100), nullable=False)

    # Trich yeu noi dung
    trich_yeu: Mapped[str] = mapped_column(String(500), nullable=False)

    # FK den loai van ban (LUAT, NGHI_DINH, ...)
    loai_van_ban_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("legal.loai_van_ban.id"),
        nullable=True,
    )

    # Co quan ban hanh, VD: "Chinh phu", "Bo Tai chinh"
    co_quan_ban_hanh: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    # Cac moc thoi gian hieu luc
    ngay_ban_hanh: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    ngay_hieu_luc: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    ngay_het_hieu_luc: Mapped[Optional[date]] = mapped_column(
        Date, nullable=True
    )  # NULL = con hieu luc

    # ------------------------------------------------------------------
    # Trang thai hieu luc
    # ------------------------------------------------------------------
    # CON_HIEU_LUC | HET_HIEU_LUC | BI_THAY_THE | DANG_SUA_DOI
    trang_thai_hieu_luc: Mapped[str] = mapped_column(
        String(50), server_default=text("'CON_HIEU_LUC'"), nullable=False
    )

    # Self-reference: van ban nao da thay the van ban nay
    van_ban_thay_the_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("legal.van_ban.id"),
        nullable=True,
    )

    # ------------------------------------------------------------------
    # Noi dung van ban
    # ------------------------------------------------------------------
    # Tom tat noi dung chinh (markdown/text)
    tom_tat: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Noi dung day du (HTML — render trong browser)
    noi_dung_html: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Duong dan file goc tren MinIO (PDF/Word)
    file_goc_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # ------------------------------------------------------------------
    # Phan loai linh hoat (JSONB)
    # ------------------------------------------------------------------
    # Chuyen de phap luat, VD: ["thue XNK", "giam sat", "KTSTQ"]
    chuyen_de: Mapped[Optional[list]] = mapped_column(
        JSONB, server_default=text("'[]'"), nullable=True
    )

    # Doi tuong ap dung, VD: ["Doi thu tuc", "Doi KTSTQ"] hoac ["TAT_CA"]
    doi_tuong_ap_dung: Mapped[Optional[list]] = mapped_column(
        JSONB, server_default=text("'[]'"), nullable=True
    )

    # Tags tu do, VD: ["2025", "moi", "uu_tien"]
    tags: Mapped[Optional[list]] = mapped_column(JSONB, server_default=text("'[]'"), nullable=True)

    # ------------------------------------------------------------------
    # Diem moi quy dinh (tinh nang dac thu cua HQKV8)
    # ------------------------------------------------------------------
    # Mo ta nhung diem moi so voi van ban cu
    diem_moi: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Nhung viec CBCC can lam sau khi doc
    viec_can_lam: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # ------------------------------------------------------------------
    # Muc do quan trong + rang buoc doc
    # ------------------------------------------------------------------
    # KHAN | QUAN_TRONG | BINH_THUONG
    muc_do: Mapped[str] = mapped_column(
        String(50), server_default=text("'BINH_THUONG'"), nullable=False
    )

    # CBCC bat buoc phai xac nhan da doc van ban nay
    bat_buoc_doc: Mapped[bool] = mapped_column(
        Boolean, server_default=text("false"), nullable=False
    )

    # Han cuoi CBCC phai xac nhan da doc (NULL = khong gioi han)
    han_xac_nhan: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # ------------------------------------------------------------------
    # Workflow duyet dang: NHAP → CHO_DUYET → DA_DUYET → DA_XUAT_BAN
    # ------------------------------------------------------------------
    # FK cross-schema: nguoi nhap lieu
    nguoi_nhap_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("public.cong_chuc.id"),
        nullable=True,
    )

    # FK cross-schema: nguoi duyet dang
    nguoi_duyet_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("public.cong_chuc.id"),
        nullable=True,
    )

    # NHAP | CHO_DUYET | DA_DUYET | DA_XUAT_BAN
    trang_thai_duyet: Mapped[str] = mapped_column(
        String(50), server_default=text("'NHAP'"), nullable=False
    )

    # Ngay chinh thuc xuat ban (set khi chuyen sang DA_XUAT_BAN)
    ngay_xuat_ban: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # ------------------------------------------------------------------
    # Versioning
    # ------------------------------------------------------------------
    phien_ban: Mapped[int] = mapped_column(Integer, server_default="1", nullable=False)

    # ------------------------------------------------------------------
    # Timestamps + soft delete
    # ------------------------------------------------------------------
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=text("CURRENT_TIMESTAMP")
    )
    is_deleted: Mapped[bool] = mapped_column(Boolean, server_default=text("false"), nullable=False)

    # ------------------------------------------------------------------
    # Full-text search vector (quan ly boi PostgreSQL trigger)
    # Trigger: legal.trg_legal_van_ban_search
    # to_tsvector('simple', so_hieu || trich_yeu || tom_tat || diem_moi)
    # ------------------------------------------------------------------
    search_vector: Mapped[Optional[str]] = mapped_column(TSVECTOR, nullable=True)

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------

    # Loai van ban (joined load — luon can thong tin loai)
    loai_van_ban: Mapped[Optional[LoaiVanBan]] = relationship(
        "LoaiVanBan",
        back_populates="van_bans",
        lazy="joined",
    )

    # Nguoi nhap lieu (joined load — hien thi ho ten)
    nguoi_nhap: Mapped[Optional[CongChucRef]] = relationship(
        "CongChucRef",
        foreign_keys=[nguoi_nhap_id],
        lazy="joined",
    )

    # Nguoi duyet dang (joined load — hien thi ho ten)
    nguoi_duyet: Mapped[Optional[CongChucRef]] = relationship(
        "CongChucRef",
        foreign_keys=[nguoi_duyet_id],
        lazy="joined",
    )

    # Van ban thay the (self-reference — phan cap)
    van_ban_thay_the: Mapped[Optional[VanBan]] = relationship(
        "VanBan",
        foreign_keys=[van_ban_thay_the_id],
        remote_side="VanBan.id",  # type: ignore[assignment]
        lazy="joined",
    )

    # Danh sach lien ket voi van ban khac (selectin — load khi can)
    lien_kets: Mapped[list[VanBanLienKet]] = relationship(
        "VanBanLienKet",
        foreign_keys="VanBanLienKet.van_ban_id",
        back_populates="van_ban",
        lazy="selectin",
    )

    # Danh sach xac nhan da doc cua CBCC
    xac_nhan_docs: Mapped[list[XacNhanDoc]] = relationship(
        "XacNhanDoc",
        back_populates="van_ban",
        lazy="selectin",
    )

    # Danh sach quiz kiem tra kien thuc phap luat
    quizzes: Mapped[list[QuizVanBan]] = relationship(
        "QuizVanBan",
        back_populates="van_ban",
        lazy="selectin",
    )
