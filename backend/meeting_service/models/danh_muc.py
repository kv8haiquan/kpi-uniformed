"""Model danh mục dùng chung của Lịch công tác (G4.11).

Thay chỗ sheet `SETUP` của lichkv8. Xem migration meeting_024 để biết vì sao
chỉ mang 4 trong 12 nhóm của hệ cũ và cờ `he_thong` dùng để làm gì.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column

from meeting_service.models.base import Base


# Bốn nhóm danh mục. Khớp CHECK `ck_danh_muc_nhom` trong meeting_024.
NHOM_LOAI_LICH = "LOAI_LICH"
NHOM_TRANG_THAI = "TRANG_THAI_LICH"
NHOM_LOAI_TAI_LIEU = "LOAI_TAI_LIEU"
NHOM_PHONG_HOP = "PHONG_HOP"

NHOM_HOP_LE = (
    NHOM_LOAI_LICH,
    NHOM_TRANG_THAI,
    NHOM_LOAI_TAI_LIEU,
    NHOM_PHONG_HOP,
)

# Nhãn hiển thị của từng nhóm trên màn hình quản trị.
NHAN_NHOM = {
    NHOM_LOAI_LICH: "Loại lịch",
    NHOM_TRANG_THAI: "Trạng thái lịch",
    NHOM_LOAI_TAI_LIEU: "Loại tài liệu",
    NHOM_PHONG_HOP: "Phòng họp / địa điểm",
}

# Cột của `meeting.cuoc_hop` mà mỗi nhóm điều khiển — dùng để đếm "đang dùng
# bao nhiêu" trước khi cho xoá. None nghĩa là nhóm chưa gắn vào cột nào.
COT_SU_DUNG = {
    NHOM_LOAI_LICH: "loai_lich",
    NHOM_TRANG_THAI: "trang_thai",
    NHOM_PHONG_HOP: None,      # địa điểm là chuỗi tự do, đối chiếu theo nhãn
    NHOM_LOAI_TAI_LIEU: None,  # nằm ở meeting.tai_lieu.mo_ta, không phải cuoc_hop
}


class DanhMuc(Base):
    """Một mục trong danh mục dùng chung.

    Khoá nghiệp vụ là cặp (`nhom`, `ma`) — `ma` là thứ dữ liệu tham chiếu tới
    nên không cho đổi sau khi tạo; muốn đổi cách gọi thì sửa `nhan`.
    """

    __tablename__ = "danh_muc"
    __table_args__ = {"schema": "meeting"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True,
        server_default=text("gen_random_uuid()"))
    nhom: Mapped[str] = mapped_column(String(30), nullable=False)
    ma: Mapped[str] = mapped_column(String(50), nullable=False)
    nhan: Mapped[str] = mapped_column(String(150), nullable=False)
    thu_tu: Mapped[int] = mapped_column(Integer, server_default="0", nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean, server_default=text("true"), nullable=False)
    # Mã bị mã nguồn rẽ nhánh theo: sửa được nhãn, không đổi mã / xoá / tắt.
    he_thong: Mapped[bool] = mapped_column(
        Boolean, server_default=text("false"), nullable=False)
    mo_ta: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("NOW()"), nullable=False)
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True)
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True)
    updated_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True)
