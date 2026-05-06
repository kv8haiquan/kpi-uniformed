"""Drop cột is_chua_hoan_thanh khỏi ke_khai_cong_viec

Revision ID: drop_chua_ht_kk_20260506
Revises: rename_chua_ht_20260506
Create Date: 2026-05-06

Theo quyết định nghiệp vụ mới (06/05/2026): điều chỉnh KQCV CHỈ ảnh hưởng
KPI của LĐ, KHÔNG đụng KPI của CC. → Cờ is_chua_hoan_thanh không cần
trong kpi_submission nữa, chỉ tồn tại trong dieu_chinh_kqcv.gia_tri_moi.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "drop_chua_ht_kk_20260506"
down_revision: Union[str, None] = "rename_chua_ht_20260506"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column("ke_khai_cong_viec", "is_chua_hoan_thanh")


def downgrade() -> None:
    op.add_column(
        "ke_khai_cong_viec",
        sa.Column(
            "is_chua_hoan_thanh",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
