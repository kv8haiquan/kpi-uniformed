"""Meeting 003: meeting.thanh_phan

Revision ID: mt_003_thanh_phan_20260430
Revises: mt_002_cuoc_hop_20260430
Create Date: 2026-04-30

Thành phần tham dự cuộc họp. Theo HKG_DATABASE_DESIGN.md §4.2.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "mt_003_thanh_phan_20260430"
down_revision: Union[str, None] = "mt_002_cuoc_hop_20260430"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


SCHEMA = "meeting"
TBL = "thanh_phan"


def upgrade() -> None:
    op.create_table(
        TBL,
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()"), nullable=False),

        sa.Column("cuoc_hop_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("meeting.cuoc_hop.id", ondelete="CASCADE"),
                  nullable=False),
        sa.Column("cong_chuc_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("public.cong_chuc.id"), nullable=False),

        sa.Column("loai_tham_du", sa.String(20),
                  server_default="BAT_BUOC", nullable=False),

        # Xác nhận tham dự
        sa.Column("xac_nhan", sa.String(20),
                  server_default="CHUA_PHAN_HOI", nullable=True),
        sa.Column("nguoi_uy_quyen_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("public.cong_chuc.id"), nullable=True),
        sa.Column("ghi_chu_xac_nhan", sa.Text(), nullable=True),
        sa.Column("thoi_gian_xac_nhan", postgresql.TIMESTAMP(timezone=True), nullable=True),

        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),

        sa.CheckConstraint(
            "loai_tham_du IN ('BAT_BUOC', 'THAM_KHAO')",
            name="ck_thanh_phan_loai_tham_du",
        ),
        sa.CheckConstraint(
            "xac_nhan IN ('CHUA_PHAN_HOI', 'THAM_DU', 'KHONG_THAM_DU', 'UY_QUYEN')",
            name="ck_thanh_phan_xac_nhan",
        ),
        sa.UniqueConstraint("cuoc_hop_id", "cong_chuc_id",
                            name="uq_thanh_phan_cuoc_hop_cong_chuc"),

        schema=SCHEMA,
    )

    op.create_index("idx_thanh_phan_cuoc_hop", TBL, ["cuoc_hop_id"], schema=SCHEMA)
    op.create_index("idx_thanh_phan_cong_chuc", TBL, ["cong_chuc_id"], schema=SCHEMA)


def downgrade() -> None:
    op.drop_index("idx_thanh_phan_cong_chuc", table_name=TBL, schema=SCHEMA)
    op.drop_index("idx_thanh_phan_cuoc_hop", table_name=TBL, schema=SCHEMA)
    op.drop_table(TBL, schema=SCHEMA)
