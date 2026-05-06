"""Đổi tên is_loai_tru_kpi → is_chua_hoan_thanh

Revision ID: rename_loai_tru_to_chua_ht_20260506
Revises: dieu_chinh_kqcv_20260506
Create Date: 2026-05-06

User chốt lại nghĩa: cờ này là "CV chưa hoàn thành" thay vì "loại trừ KPI".
- CV bị đánh dấu vẫn vào MẪU SỐ tổng SP kê khai.
- Nhưng đóng 0 vào tử số a/b/c → cả 3 chỉ số đều giảm.
"""

from typing import Sequence, Union

from alembic import op


revision: str = "rename_chua_ht_20260506"
down_revision: Union[str, None] = "dieu_chinh_kqcv_20260506"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "ke_khai_cong_viec",
        "is_loai_tru_kpi",
        new_column_name="is_chua_hoan_thanh",
    )


def downgrade() -> None:
    op.alter_column(
        "ke_khai_cong_viec",
        "is_chua_hoan_thanh",
        new_column_name="is_loai_tru_kpi",
    )
