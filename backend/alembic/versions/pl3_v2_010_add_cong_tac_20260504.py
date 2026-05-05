"""PL3 V2 - 010: Thêm cột cong_tac + cong_tac_thu_tu

Revision ID: pl3_v2_010_cong_tac_20260504
Revises: mt_015_nhom_tp_chi_tiet_20260503
Create Date: 2026-05-04

Bổ sung cấp phân loại "Công tác" — sub-heading nằm giữa Lĩnh vực và Nhiệm vụ
trong file Excel PL3 (các dòng bôi đậm cột A không được đánh số, ví dụ:
"Công tác Văn thư", "Công tác Lưu trữ", ...).

- cong_tac VARCHAR(500) NULL  : tên công tác (denormalized).
- cong_tac_thu_tu SMALLINT NULL: thứ tự xuất hiện trong lĩnh vực (1, 2, ...).
  NULL khi mục thuộc lĩnh vực không phân nhóm công tác hoặc thuộc nhóm
  nhiệm vụ đứng TRƯỚC công tác đầu tiên ("(Chung)" — chưa phân công tác).

Index (linh_vuc, cong_tac_thu_tu) phục vụ ORDER BY khi list theo cây.

Backfill cho 2.812 mục đã seed do scripts/backfill_pl3_cong_tac.py xử lý
ngoài migration (parser cần đọc lại file Excel gốc).
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "pl3_v2_010_cong_tac_20260504"
down_revision: Union[str, None] = "mt_015_nhom_tp_chi_tiet_20260503"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


TBL = "danh_muc_sp_cong_viec"


def upgrade() -> None:
    op.add_column(
        TBL,
        sa.Column(
            "cong_tac",
            sa.String(length=500),
            nullable=True,
            comment="Tên công tác (sub-heading bold cột A trong Excel PL3)",
        ),
    )
    op.add_column(
        TBL,
        sa.Column(
            "cong_tac_thu_tu",
            sa.SmallInteger(),
            nullable=True,
            comment="Thứ tự công tác trong lĩnh vực (1..N), NULL nếu chưa phân công tác",
        ),
    )
    op.create_index(
        "idx_dmsp_linh_vuc_cong_tac",
        TBL,
        ["linh_vuc", "cong_tac_thu_tu"],
    )


def downgrade() -> None:
    op.drop_index("idx_dmsp_linh_vuc_cong_tac", table_name=TBL)
    op.drop_column(TBL, "cong_tac_thu_tu")
    op.drop_column(TBL, "cong_tac")
