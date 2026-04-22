"""Add last_recalculated_at to bao_cao_xep_loai_quy

Revision ID: add_last_recalc_quy_20260421
Revises: phieu_danh_gia_20260417
Create Date: 2026-04-21

Thêm cột `last_recalculated_at` vào bảng `bao_cao_xep_loai_quy` để debounce
việc tính lại snapshot khi GET báo cáo ở trạng thái NHAP/TU_CHOI.

Lý do: ChiTietXepLoaiQuy lưu snapshot điểm quý tại thời điểm tạo báo cáo. Nếu
dữ liệu tháng (DanhGiaThang) thay đổi sau đó, snapshot bị lệch so với bản in
(gọi tinh_diem_quy() live). Cần rebuild snapshot khi TDV mở lại báo cáo ở
trạng thái NHAP/TU_CHOI, nhưng debounce 60s để không thồi backend.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "add_last_recalc_quy_20260421"
down_revision: Union[str, None] = "phieu_danh_gia_20260417"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "bao_cao_xep_loai_quy",
        sa.Column(
            "last_recalculated_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="Thời điểm gần nhất rebuild snapshot (debounce 60s khi GET)",
        ),
    )


def downgrade() -> None:
    op.drop_column("bao_cao_xep_loai_quy", "last_recalculated_at")
