"""Meeting 014: meeting.nhom_thanh_phan

Revision ID: mt_014_nhom_tp_20260503
Revises: mt_013_ttc_20260502
Create Date: 2026-05-03

Bảng "Nhóm thành phần" — danh sách thành viên dùng chung cho nhiều cuộc họp.
Mọi công chức đều có thể tạo/sửa/xoá. Hard delete (cascade chi_tiet).
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "mt_014_nhom_tp_20260503"
down_revision: Union[str, None] = "mt_013_ttc_20260502"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


SCHEMA = "meeting"
TBL = "nhom_thanh_phan"


def upgrade() -> None:
    op.create_table(
        TBL,
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()"), nullable=False),

        sa.Column("ten_nhom", sa.String(200), nullable=False),
        sa.Column("mo_ta", sa.Text(), nullable=True),
        sa.Column("loai_nhom", sa.String(100), nullable=True),

        sa.Column("nguoi_tao_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("public.cong_chuc.id"), nullable=False),

        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", postgresql.TIMESTAMP(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),

        schema=SCHEMA,
    )

    op.create_index("idx_nhom_thanh_phan_ten", TBL, ["ten_nhom"], schema=SCHEMA)
    op.create_index("idx_nhom_thanh_phan_loai", TBL, ["loai_nhom"], schema=SCHEMA)
    op.create_index("idx_nhom_thanh_phan_nguoi_tao", TBL, ["nguoi_tao_id"], schema=SCHEMA)


def downgrade() -> None:
    op.drop_index("idx_nhom_thanh_phan_nguoi_tao", table_name=TBL, schema=SCHEMA)
    op.drop_index("idx_nhom_thanh_phan_loai", table_name=TBL, schema=SCHEMA)
    op.drop_index("idx_nhom_thanh_phan_ten", table_name=TBL, schema=SCHEMA)
    op.drop_table(TBL, schema=SCHEMA)
