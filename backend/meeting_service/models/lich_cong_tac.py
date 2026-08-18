"""Models cho nghiệp vụ Lịch công tác (di trú từ lichkv8).

Cuộc họp KHÔNG có model riêng — dùng chung `meeting.cuoc_hop` với HKG, phân
biệt bằng cột `nguon` ('HKG' | 'LICH_CONG_TAC'). Xem migration meeting_016.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Optional

from sqlalchemy import Boolean, Date, ForeignKey, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column

from meeting_service.models.base import Base


class LanhDaoLienQuan(Base):
    """Lãnh đạo liên quan tới cuộc họp.

    Trục của Lịch lãnh đạo, Dashboard theo lãnh đạo và Tóm tắt lịch.
    Khác `thanh_phan` (người dự thật): bảng này chỉ ghi cuộc họp thuộc chương
    trình công tác của lãnh đạo nào.
    """

    __tablename__ = "lanh_dao_lien_quan"
    __table_args__ = {"schema": "meeting"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True,
        server_default=text("gen_random_uuid()"))
    cuoc_hop_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("meeting.cuoc_hop.id", ondelete="CASCADE"), nullable=False)
    cong_chuc_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("public.cong_chuc.id"), nullable=False)
    thu_tu: Mapped[int] = mapped_column(Integer, server_default="1", nullable=False)
    # Nguyên văn token trước khi khớp — để truy vết khi đối soát.
    ten_goc: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("NOW()"), nullable=False)


class TruSo(Base):
    """Trụ sở trực ban — 9 địa điểm.

    KHÔNG phải đơn vị: KSHQ_HL và KSHQ_MC là hai trụ sở của cùng đơn vị KSHQ,
    còn CHICUC là trụ sở dùng chung của 7 phòng/đội nên `don_vi_id` để trống.
    """

    __tablename__ = "tru_so"
    __table_args__ = {"schema": "meeting"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True,
        server_default=text("gen_random_uuid()"))
    ma_tru_so: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    ten_tru_so: Mapped[str] = mapped_column(String(200), nullable=False)
    don_vi_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("public.don_vi.id"), nullable=True)
    thu_tu: Mapped[int] = mapped_column(Integer, server_default="1", nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean, server_default=text("TRUE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("NOW()"), nullable=False)


class TrucBan(Base):
    """Một người trực tại một trụ sở trong một ngày.

    Số điện thoại là trường cốt lõi — nghiệp vụ này thực chất là danh bạ lãnh
    đạo trực cuối tuần để liên lạc khi có việc.
    """

    __tablename__ = "truc_ban"
    __table_args__ = {"schema": "meeting"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True,
        server_default=text("gen_random_uuid()"))
    ngay_truc: Mapped[date] = mapped_column(Date, nullable=False)
    tru_so_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("meeting.tru_so.id"), nullable=False)
    # Mã đơn vị cũ của lichkv8 — chỉ để đối soát, không dùng cho nghiệp vụ.
    unit_code_cu: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    cong_chuc_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("public.cong_chuc.id"), nullable=True)
    ho_ten: Mapped[str] = mapped_column(String(100), nullable=False)
    chuc_vu: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    so_dien_thoai: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    loai_truc: Mapped[str] = mapped_column(
        String(20), server_default="CUOI_TUAN", nullable=False)
    ca_truc: Mapped[str] = mapped_column(
        String(20), server_default="CA_NGAY", nullable=False)
    ghi_chu: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    trang_thai: Mapped[str] = mapped_column(
        String(20), server_default="NHAP", nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("NOW()"), nullable=False)
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("public.cong_chuc.id"), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("NOW()"), nullable=False)
    updated_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("public.cong_chuc.id"), nullable=True)
    is_deleted: Mapped[bool] = mapped_column(
        Boolean, server_default=text("FALSE"), nullable=False)


class TrucBanTruSo(Base):
    """Trạng thái nộp lịch trực của một trụ sở trong một ngày."""

    __tablename__ = "truc_ban_tru_so"
    __table_args__ = {"schema": "meeting"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True,
        server_default=text("gen_random_uuid()"))
    ngay_truc: Mapped[date] = mapped_column(Date, nullable=False)
    tru_so_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("meeting.tru_so.id"), nullable=False)
    trang_thai: Mapped[str] = mapped_column(
        String(20), server_default="NHAP", nullable=False)
    nguoi_nop_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("public.cong_chuc.id"), nullable=True)
    thoi_diem_nop: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True)
    is_locked: Mapped[bool] = mapped_column(
        Boolean, server_default=text("FALSE"), nullable=False)
    ghi_chu: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("NOW()"), nullable=False)
    updated_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("public.cong_chuc.id"), nullable=True)


class DiTruDoiSoat(Base):
    """Hàng đợi đối soát thư mục tài liệu chưa gắn được cuộc họp.

    Chỉ dùng trong giai đoạn chuyển đổi. Xuất bảng này ra Excel chính là biên
    bản đối chiếu phải nộp khi nghiệm thu.
    """

    __tablename__ = "di_tru_doi_soat"
    __table_args__ = {"schema": "meeting"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True,
        server_default=text("gen_random_uuid()"))
    drive_folder_id: Mapped[str] = mapped_column(
        String(60), nullable=False, unique=True)
    duong_dan_thu_muc: Mapped[str] = mapped_column(Text, nullable=False)
    so_file: Mapped[int] = mapped_column(Integer, server_default="0", nullable=False)
    ngay_suy_ra: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    so_gm_suy_ra: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    nhom: Mapped[str] = mapped_column(String(2), nullable=False)

    quyet_dinh: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    cuoc_hop_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("meeting.cuoc_hop.id", ondelete="SET NULL"), nullable=True)
    nguoi_quyet_dinh_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("public.cong_chuc.id"), nullable=True)
    thoi_diem_quyet_dinh: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True)
    ghi_chu: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("NOW()"), nullable=False)
