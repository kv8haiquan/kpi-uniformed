"""
legal_service/models/ket_qua_quiz.py
=======================================
Model ket qua quiz phap luat — bang legal.ket_qua_quiz.

Luu ket qua moi lan CBCC lam quiz. CBCC co the lam lai nhieu lan
(khong co UniqueConstraint — khac voi xac_nhan_doc).

Cau truc JSONB chi_tiet:
  [
    {"cau": 0, "tra_loi": 2, "dung": false},
    {"cau": 1, "tra_loi": 1, "dung": true},
    ...
  ]
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from legal_service.models.base import Base, CongChucRef

if TYPE_CHECKING:
    from legal_service.models.quiz_van_ban import QuizVanBan


class KetQuaQuiz(Base):
    """Ket qua quiz van ban — bang legal.ket_qua_quiz.

    Moi ban ghi la 1 lan lam quiz cua 1 CBCC.
    CBCC co the lam lai nhieu lan (cac lan sau ghi de ban ghi moi).
    chi_tiet JSONB chua lich su tra loi tung cau.
    """

    __tablename__ = "ket_qua_quiz"
    __table_args__ = {"schema": "legal"}

    # ------------------------------------------------------------------
    # Primary Key
    # ------------------------------------------------------------------
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )

    # ------------------------------------------------------------------
    # Foreign Keys
    # ------------------------------------------------------------------
    # Quiz duoc lam
    quiz_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("legal.quiz_van_ban.id"),
        nullable=False,
    )

    # Cong chuc lam quiz (FK cross-schema)
    cong_chuc_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("public.cong_chuc.id"),
        nullable=False,
    )

    # ------------------------------------------------------------------
    # Ket qua
    # ------------------------------------------------------------------
    # Diem so (0-100, tinh theo % cau dung)
    diem: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)

    # So cau tra loi dung
    so_cau_dung: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Co dat yeu cau hay khong (diem >= diem_dat cua quiz)
    dat_yeu_cau: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)

    # Chi tiet tung cau tra loi: [{"cau": 0, "tra_loi": 2, "dung": false}, ...]
    chi_tiet: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)

    # ------------------------------------------------------------------
    # Timestamp
    # ------------------------------------------------------------------
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=text("CURRENT_TIMESTAMP")
    )

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------
    # Quiz duoc lam (joined — can thong tin quiz: diem_dat, so_cau_hoi)
    quiz: Mapped[QuizVanBan] = relationship(
        "QuizVanBan",
        back_populates="ket_quas",
        lazy="joined",
    )

    # Cong chuc lam quiz (joined — hien thi ho ten)
    cong_chuc: Mapped[CongChucRef] = relationship(
        "CongChucRef",
        foreign_keys=[cong_chuc_id],
        lazy="joined",
    )
