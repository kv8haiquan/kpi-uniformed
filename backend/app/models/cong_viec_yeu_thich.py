"""
app/models/cong_viec_yeu_thich.py
==================================
Model "Công việc yêu thích" — bookmark của công chức cho các mục PL3 hay dùng.

Bảng public.cong_viec_yeu_thich (tạo bởi migration fav_001_*).

Nghiệp vụ:
- Mỗi công chức tự mark các danh_muc_sp_cong_viec hay dùng.
- Modal /ke-khai-v2 hiển thị tab "⭐ Yêu thích" để pick nhanh.
- Idempotent: UNIQUE(cong_chuc_id, danh_muc_sp_id).
- ON DELETE CASCADE: tự dọn khi danh mục PL3 bị xoá hoặc CC bị xoá.
"""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.user_org import CongChuc
    from app.models.task_catalog import DanhMucSpCongViec


class CongViecYeuThich(BaseModel):
    """Bookmark danh mục công việc yêu thích của 1 công chức."""

    __tablename__ = "cong_viec_yeu_thich"

    cong_chuc_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("cong_chuc.id", ondelete="CASCADE"),
        nullable=False,
    )

    danh_muc_sp_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("danh_muc_sp_cong_viec.id", ondelete="CASCADE"),
        nullable=False,
    )

    cong_chuc: Mapped["CongChuc"] = relationship(
        "CongChuc",
        lazy="select",
    )

    danh_muc_sp: Mapped["DanhMucSpCongViec"] = relationship(
        "DanhMucSpCongViec",
        lazy="joined",
    )

    __table_args__ = (
        UniqueConstraint(
            "cong_chuc_id",
            "danh_muc_sp_id",
            name="uq_cvyt_cc_dm",
        ),
    )

    def __repr__(self) -> str:
        return f"<CongViecYeuThich(cc={self.cong_chuc_id}, dm={self.danh_muc_sp_id})>"
