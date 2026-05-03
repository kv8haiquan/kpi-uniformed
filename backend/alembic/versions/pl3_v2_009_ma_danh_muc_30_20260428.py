"""PL3 V2 - 009: Tăng ma_danh_muc VARCHAR(20) → VARCHAR(30)

Revision ID: pl3_v2_009_ma_30_20260428
Revises: pl3_v2_008_drop_cham_20260428
Create Date: 2026-04-28

Phase A.9 — Hỗ trợ duplicate stt suffix.

Excel PL3 có 14 cặp duplicate stt trong cùng lĩnh vực (vd: 'PL3-I-36.2' xuất
hiện ở row 157 VÀ row 158, là 2 công việc khác nhau). Để tránh mất 18 mục
khi UPSERT, append '-r{row}' cho occurrence thứ 2 trở đi:
  - Row 157: 'PL3-I-36.2'      (giữ nguyên)
  - Row 158: 'PL3-I-36.2-r158' (suffix)

Format dài nhất khả dĩ:
  'PL3-VIII-100.1-r3455' = 20 chars vẫn dưới 30.

VARCHAR(30) đủ buffer cho mọi trường hợp.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "pl3_v2_009_ma_30_20260428"
down_revision: Union[str, None] = "pl3_v2_008_drop_cham_20260428"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


TBL = "danh_muc_sp_cong_viec"


def upgrade() -> None:
    op.alter_column(
        TBL, "ma_danh_muc",
        existing_type=sa.String(length=20),
        type_=sa.String(length=30),
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        TBL, "ma_danh_muc",
        existing_type=sa.String(length=30),
        type_=sa.String(length=20),
        existing_nullable=False,
    )
