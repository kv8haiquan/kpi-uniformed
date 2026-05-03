"""Meeting 006: meeting.xin_phep_vang

Revision ID: mt_006_xin_phep_20260430
Revises: mt_005_diem_danh_20260430
Create Date: 2026-04-30

Đơn xin phép vắng + auto-approve theo timeout (Celery G3).
Theo HKG_DATABASE_DESIGN.md §4.5.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "mt_006_xin_phep_20260430"
down_revision: Union[str, None] = "mt_005_diem_danh_20260430"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


SCHEMA = "meeting"
TBL = "xin_phep_vang"


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

        sa.Column("ly_do", sa.Text(), nullable=False),
        sa.Column("nguoi_du_thay_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("public.cong_chuc.id"), nullable=True),

        # File đính kèm (optional)
        sa.Column("minio_key", sa.String(500), nullable=True),

        # Trạng thái duyệt
        sa.Column("trang_thai", sa.String(30),
                  server_default="CHO_DUYET", nullable=False),
        sa.Column("auto_approved", sa.Boolean(),
                  server_default=sa.text("FALSE"), nullable=False),
        sa.Column("nguoi_duyet_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("public.cong_chuc.id"), nullable=True),
        sa.Column("thoi_gian_duyet", postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("ly_do_tu_choi", sa.Text(), nullable=True),

        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", postgresql.TIMESTAMP(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),

        sa.CheckConstraint(
            "trang_thai IN ('CHO_DUYET', 'DA_DUYET', 'TU_CHOI', 'TU_DONG_DUYET')",
            name="ck_xin_phep_trang_thai",
        ),
        sa.UniqueConstraint("cuoc_hop_id", "cong_chuc_id",
                            name="uq_xin_phep_cuoc_hop_cong_chuc"),

        schema=SCHEMA,
    )

    op.create_index("idx_xin_phep_cuoc_hop", TBL, ["cuoc_hop_id"], schema=SCHEMA)
    op.create_index("idx_xin_phep_trang_thai", TBL, ["trang_thai"], schema=SCHEMA)


def downgrade() -> None:
    op.drop_index("idx_xin_phep_trang_thai", table_name=TBL, schema=SCHEMA)
    op.drop_index("idx_xin_phep_cuoc_hop", table_name=TBL, schema=SCHEMA)
    op.drop_table(TBL, schema=SCHEMA)
