"""
common_service/models/zalo.py
==============================
Models cho hạ tầng gửi thông báo qua Zalo OA.

Bảng: common.zalo_lien_ket, common.zalo_outbox, common.zalo_token
Migration: alembic/versions/zalo_oa_20260731.py

Lưu ý: KHÔNG có model nào sửa common.thong_bao — quan hệ là một chiều
(outbox tham chiếu tới thong_bao), nên bật/tắt Zalo không ảnh hưởng
đường ghi thông báo của KPI / LMS / HKG.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


# ---------------------------------------------------------------------------
# Hằng số trạng thái — dùng chung giữa worker, script import và test
# ---------------------------------------------------------------------------

# zalo_lien_ket.trang_thai
LK_CHUA_XAC_MINH = "CHUA_XAC_MINH"  # mới import, chưa gửi thử lần nào
LK_HOAT_DONG = "HOAT_DONG"  # đã gửi thành công ít nhất 1 lần
LK_SO_LOI = "SO_LOI"  # Zalo báo số không hợp lệ / không có Zalo
LK_TU_CHOI_NHAN = "TU_CHOI_NHAN"  # người dùng yêu cầu ngừng nhận

# zalo_outbox.trang_thai
OB_CHO_GUI = "CHO_GUI"
OB_DANG_GUI = "DANG_GUI"
OB_DA_GUI = "DA_GUI"
OB_THAT_BAI = "THAT_BAI"
OB_BO_QUA = "BO_QUA"

# zalo_outbox.ly_do_bo_qua
BQ_KHONG_CO_SDT = "KHONG_CO_SDT"
BQ_DA_TU_CHOI = "DA_TU_CHOI"
BQ_KHONG_CO_TEMPLATE = "KHONG_CO_TEMPLATE"
BQ_TAT_TINH_NANG = "TAT_TINH_NANG"
# Template khai `ma_hop` là tham số BẮT BUỘC nhưng thông báo không có
# doi_tuong_id — gửi đi chắc chắn bị Zalo từ chối nên chặn từ đầu.
BQ_THIEU_MA_HOP = "THIEU_MA_HOP"
# Nằm chờ quá `zalo_han_gui_gio` — thường do trần chi tiêu chặn. Nội dung
# (giấy mời, nhắc họp) đã lỗi thời nên gửi muộn còn tệ hơn không gửi.
BQ_QUA_HAN = "QUA_HAN"


class ZaloLienKet(Base):
    """Ánh xạ công chức ↔ kênh Zalo.

    Có hai cách nhận tin và bảng này phục vụ cả hai:
      - `so_dien_thoai` → gửi qua ZNS (không cần người dùng follow OA)
      - `zalo_user_id`  → gửi qua OA message API (bắt buộc đã follow OA)

    `zalo_user_id` KHÔNG suy ra được từ số điện thoại: Zalo cố tình không
    cung cấp API tra cứu chiều đó. Nó chỉ xuất hiện khi người dùng chủ động
    follow OA hoặc ủy quyền qua Zalo Login (giai đoạn 2).
    """

    __tablename__ = "zalo_lien_ket"
    __table_args__ = {"schema": "common"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    cong_chuc_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("public.cong_chuc.id"), nullable=False
    )

    # Số đã chuẩn hóa dạng 84xxxxxxxxx; so_goc giữ nguyên bản để đối chiếu
    so_dien_thoai: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    so_goc: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)

    zalo_user_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    trang_thai: Mapped[str] = mapped_column(
        String(50), server_default=LK_CHUA_XAC_MINH, nullable=False
    )
    # Cờ opt-out theo Nghị định 13/2023/NĐ-CP
    da_dong_y: Mapped[bool] = mapped_column(
        Boolean, server_default=text("true"), nullable=False
    )
    nguon: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    ghi_chu: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("NOW()"), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("NOW()"), nullable=False
    )


class ZaloOutbox(Base):
    """Hàng đợi gửi Zalo (outbox pattern).

    Vì sao cần hàng đợi thay vì gọi API Zalo ngay lúc tạo thông báo:
      - Zalo lỗi/chậm không được phép làm treo thao tác tạo cuộc họp
      - Cần retry có backoff khi mạng chập chờn
      - Cần dấu vết đối soát khi có người báo "tôi không nhận được tin"

    `thong_bao_id` là UNIQUE → chống gửi trùng ở mức database, kể cả khi
    worker bị chạy chồng hai tiến trình.
    """

    __tablename__ = "zalo_outbox"
    __table_args__ = {"schema": "common"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    thong_bao_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("common.thong_bao.id", ondelete="CASCADE"),
        nullable=False,
    )
    cong_chuc_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("public.cong_chuc.id"), nullable=False
    )
    so_dien_thoai: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    template_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    template_data: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSONB, nullable=True
    )

    trang_thai: Mapped[str] = mapped_column(
        String(50), server_default=OB_CHO_GUI, nullable=False
    )
    ly_do_bo_qua: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    so_lan_thu: Mapped[int] = mapped_column(
        Integer, server_default=text("0"), nullable=False
    )
    gui_sau: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("NOW()"), nullable=False
    )

    ma_loi: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    mo_ta_loi: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    zns_message_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    ngay_gui: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("NOW()"), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("NOW()"), nullable=False
    )


class ZaloToken(Base):
    """Lưu OAuth token của Official Account.

    ⚠️ refresh_token của Zalo XOAY VÒNG: mỗi lần gọi refresh, Zalo trả về
    refresh_token MỚI và vô hiệu hóa cái cũ. Vì vậy token bắt buộc nằm ở
    database (ghi đè được) chứ không phải trong .env — để trong .env thì
    sau lần refresh đầu tiên giá trị trong file đã chết, và lần restart kế
    tiếp service sẽ không lấy được token nào dùng được nữa.
    """

    __tablename__ = "zalo_token"
    __table_args__ = {"schema": "common"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    ten: Mapped[str] = mapped_column(String(50), server_default="OA", nullable=False)

    access_token: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    refresh_token: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    het_han_luc: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
    lan_refresh_cuoi: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("NOW()"), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("NOW()"), nullable=False
    )
