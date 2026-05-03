"""Meeting 004: meeting.tai_lieu

Revision ID: mt_004_tai_lieu_20260430
Revises: mt_003_thanh_phan_20260430
Create Date: 2026-04-30

Tài liệu họp lưu trên MinIO bucket 'meeting'.
Theo HKG_DATABASE_DESIGN.md §4.3.

MVP: phân quyền 2 cấp CONG_KHAI/HAN_CHE — KHÔNG có cấp Mật.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "mt_004_tai_lieu_20260430"
down_revision: Union[str, None] = "mt_003_thanh_phan_20260430"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


SCHEMA = "meeting"
TBL = "tai_lieu"


def upgrade() -> None:
    op.create_table(
        TBL,
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()"), nullable=False),

        sa.Column("cuoc_hop_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("meeting.cuoc_hop.id", ondelete="CASCADE"),
                  nullable=False),

        sa.Column("ten_tai_lieu", sa.String(500), nullable=False),
        sa.Column("mo_ta", sa.Text(), nullable=True),

        # File trên MinIO
        sa.Column("minio_bucket", sa.String(100),
                  server_default="meeting", nullable=False),
        sa.Column("minio_key", sa.String(500), nullable=False),
        sa.Column("file_size", sa.BigInteger(), nullable=False),
        sa.Column("mime_type", sa.String(100), nullable=True),
        sa.Column("extension", sa.String(10), nullable=True),

        # Phân quyền MVP — 2 cấp
        sa.Column("phan_quyen", sa.String(20),
                  server_default="CONG_KHAI", nullable=False),
        sa.Column("cho_phep_tai", sa.Boolean(),
                  server_default=sa.text("TRUE"), nullable=False),
        sa.Column("cho_phep_in", sa.Boolean(),
                  server_default=sa.text("TRUE"), nullable=False),

        # Audit
        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", postgresql.TIMESTAMP(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("public.cong_chuc.id"), nullable=False),
        sa.Column("is_deleted", sa.Boolean(),
                  server_default=sa.text("FALSE"), nullable=False),

        sa.CheckConstraint(
            "phan_quyen IN ('CONG_KHAI', 'HAN_CHE')",
            name="ck_tai_lieu_phan_quyen",
        ),

        schema=SCHEMA,
    )

    op.create_index(
        "idx_tai_lieu_cuoc_hop", TBL, ["cuoc_hop_id"],
        schema=SCHEMA, postgresql_where=sa.text("is_deleted = FALSE"),
    )


def downgrade() -> None:
    op.drop_index("idx_tai_lieu_cuoc_hop", table_name=TBL, schema=SCHEMA)
    op.drop_table(TBL, schema=SCHEMA)
