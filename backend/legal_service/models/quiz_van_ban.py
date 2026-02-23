"""
legal_service/models/quiz_van_ban.py
======================================
Model quiz kiem tra kien thuc phap luat — bang legal.quiz_van_ban.

Quiz nhe, cau hoi duoc nhung truc tiep vao cot JSONB (khong dung ngan
hang cau hoi rieng biet nhu LMS).

Cau truc JSONB cau_hoi:
  [
    {
      "noi_dung": "Nghi dinh 335 co hieu luc tu ngay nao?",
      "dap_an": ["01/01/2025", "01/03/2025", "01/06/2025", "01/09/2025"],
      "correct": 1,
      "giai_thich": "Theo Dieu 45..."
    },
    ...
  ]
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from legal_service.models.base import Base, CongChucRef

if TYPE_CHECKING:
    from legal_service.models.ket_qua_quiz import KetQuaQuiz
    from legal_service.models.van_ban import VanBan


class QuizVanBan(Base):
    """Quiz kiem tra kien thuc van ban phap luat — bang legal.quiz_van_ban.

    Quiz nhe duoc nhung truc tiep vao van ban:
    moi van ban co the co nhieu quiz, moi quiz la tap hop cau hoi JSONB.
    Diem dat yeu cau (%) de xac dinh CBCC da nam duoc noi dung.
    """

    __tablename__ = "quiz_van_ban"
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
    # Van ban ma quiz nay kiem tra kien thuc
    van_ban_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("legal.van_ban.id"),
        nullable=False,
    )

    # ------------------------------------------------------------------
    # Thong tin quiz
    # ------------------------------------------------------------------
    # Tieu de quiz
    tieu_de: Mapped[str] = mapped_column(String(300), nullable=False)

    # Tong so cau hoi trong quiz
    so_cau_hoi: Mapped[int] = mapped_column(Integer, nullable=False)

    # Thoi gian lam bai (phut) — NULL = khong gioi han
    thoi_gian_phut: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Diem dat yeu cau (%) de coi la qua
    diem_dat: Mapped[Decimal] = mapped_column(Numeric(5, 2), server_default="70.00", nullable=False)

    # ------------------------------------------------------------------
    # Cau hoi (JSONB — nhung truc tiep, khong dung ngan hang rieng)
    # ------------------------------------------------------------------
    # [{"noi_dung": "...", "dap_an": [...], "correct": 0, "giai_thich": "..."}, ...]
    cau_hoi: Mapped[list] = mapped_column(JSONB, nullable=False)

    # ------------------------------------------------------------------
    # Tac gia + trang thai
    # ------------------------------------------------------------------
    # Nguoi tao quiz (FK cross-schema)
    nguoi_tao_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("public.cong_chuc.id"),
        nullable=True,
    )

    # Quiz dang active (CBCC co the thi)
    is_active: Mapped[bool] = mapped_column(Boolean, server_default=text("true"), nullable=False)

    # ------------------------------------------------------------------
    # Timestamp
    # ------------------------------------------------------------------
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=text("CURRENT_TIMESTAMP")
    )

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------
    # Van ban chua quiz nay
    van_ban: Mapped[VanBan] = relationship(
        "VanBan",
        back_populates="quizzes",
        lazy="joined",
    )

    # Nguoi tao quiz (joined — hien thi ho ten)
    nguoi_tao: Mapped[Optional[CongChucRef]] = relationship(
        "CongChucRef",
        foreign_keys=[nguoi_tao_id],
        lazy="joined",
    )

    # Ket qua quiz cua tat ca CBCC
    ket_quas: Mapped[list[KetQuaQuiz]] = relationship(
        "KetQuaQuiz",
        back_populates="quiz",
        lazy="selectin",
    )
