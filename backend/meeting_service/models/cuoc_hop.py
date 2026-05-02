"""meeting.cuoc_hop — bảng trung tâm HKG."""

from __future__ import annotations

import uuid
from datetime import date, datetime, time
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, Date, ForeignKey, String, Text, Time, text
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from meeting_service.models.base import Base

if TYPE_CHECKING:
    from meeting_service.models.trang_thai_trinh_chieu import TrangThaiTrinhChieu


class CuocHop(Base):
    __tablename__ = "cuoc_hop"
    __table_args__ = {"schema": "meeting"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )

    tieu_de: Mapped[str] = mapped_column(String(500), nullable=False)
    mo_ta: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    khoi: Mapped[str] = mapped_column(String(20), nullable=False, server_default="CHUYEN_MON")
    hinh_thuc: Mapped[str] = mapped_column(String(20), nullable=False, server_default="TRUC_TIEP")

    ngay_hop: Mapped[date] = mapped_column(Date, nullable=False)
    gio_bat_dau: Mapped[time] = mapped_column(Time, nullable=False)
    gio_ket_thuc: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    dia_diem: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)

    don_vi_to_chuc_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("public.don_vi.id"), nullable=False
    )
    chu_toa_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("public.cong_chuc.id"), nullable=False
    )
    thu_ky_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("public.cong_chuc.id"), nullable=True
    )

    trang_thai: Mapped[str] = mapped_column(
        String(30), nullable=False, server_default="LEN_KE_HOACH"
    )

    la_dinh_ky: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text("FALSE"))
    chu_ky: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    chi_bo_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("NOW()"), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("NOW()"), nullable=False
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("public.cong_chuc.id"), nullable=False
    )
    is_deleted: Mapped[bool] = mapped_column(
        Boolean, server_default=text("FALSE"), nullable=False
    )

    trang_thai_trinh_chieu: Mapped[Optional["TrangThaiTrinhChieu"]] = relationship(
        "TrangThaiTrinhChieu",
        back_populates="cuoc_hop",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="select",
    )
