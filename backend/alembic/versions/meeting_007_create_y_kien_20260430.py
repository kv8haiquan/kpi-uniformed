"""Meeting 007: meeting.y_kien

Revision ID: mt_007_y_kien_20260430
Revises: mt_006_xin_phep_20260430
Create Date: 2026-04-30

Ý kiến của thành viên (trước/trong/sau họp).
Theo HKG_DATABASE_DESIGN.md §4.6.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "mt_007_y_kien_20260430"
down_revision: Union[str, None] = "mt_006_xin_phep_20260430"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


SCHEMA = "meeting"
TBL = "y_kien"


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

        sa.Column("noi_dung", sa.Text(), nullable=False),
        sa.Column("loai", sa.String(20),
                  server_default="TRONG_HOP", nullable=False),

        sa.Column("minio_key", sa.String(500), nullable=True),

        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
        sa.Column("is_deleted", sa.Boolean(),
                  server_default=sa.text("FALSE"), nullable=False),

        sa.CheckConstraint(
            "loai IN ('TRUOC_HOP', 'TRONG_HOP', 'SAU_HOP')",
            name="ck_y_kien_loai",
        ),

        schema=SCHEMA,
    )

    op.create_index(
        "idx_y_kien_cuoc_hop", TBL, ["cuoc_hop_id"],
        schema=SCHEMA, postgresql_where=sa.text("is_deleted = FALSE"),
    )
    op.create_index("idx_y_kien_loai", TBL, ["loai"], schema=SCHEMA)


def downgrade() -> None:
    op.drop_index("idx_y_kien_loai", table_name=TBL, schema=SCHEMA)
    op.drop_index("idx_y_kien_cuoc_hop", table_name=TBL, schema=SCHEMA)
    op.drop_table(TBL, schema=SCHEMA)
