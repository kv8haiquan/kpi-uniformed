"""Meeting 005: meeting.diem_danh

Revision ID: mt_005_diem_danh_20260430
Revises: mt_004_tai_lieu_20260430
Create Date: 2026-04-30

Điểm danh QR + bấm tay. Theo HKG_DATABASE_DESIGN.md §4.4.
TU_DONG (Jitsi auto-attendance) — phase sau, KHÔNG có MVP.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "mt_005_diem_danh_20260430"
down_revision: Union[str, None] = "mt_004_tai_lieu_20260430"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


SCHEMA = "meeting"
TBL = "diem_danh"


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

        sa.Column("hinh_thuc", sa.String(20), nullable=False),
        sa.Column("trang_thai", sa.String(20),
                  server_default="CO_MAT", nullable=False),

        sa.Column("gio_diem_danh", postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("ghi_chu", sa.Text(), nullable=True),

        # Người bấm điểm danh (nếu hinh_thuc=BAM_TAY)
        sa.Column("nguoi_diem_danh_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("public.cong_chuc.id"), nullable=True),

        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),

        sa.CheckConstraint(
            "hinh_thuc IN ('QR', 'BAM_TAY')",
            name="ck_diem_danh_hinh_thuc",
        ),
        sa.CheckConstraint(
            "trang_thai IN ('CO_MAT', 'DEN_MUON', 'VANG_CO_PHEP', 'VANG_KHONG_PHEP')",
            name="ck_diem_danh_trang_thai",
        ),
        sa.UniqueConstraint("cuoc_hop_id", "cong_chuc_id",
                            name="uq_diem_danh_cuoc_hop_cong_chuc"),

        schema=SCHEMA,
    )

    op.create_index("idx_diem_danh_cuoc_hop", TBL, ["cuoc_hop_id"], schema=SCHEMA)
    op.create_index("idx_diem_danh_cong_chuc", TBL, ["cong_chuc_id"], schema=SCHEMA)


def downgrade() -> None:
    op.drop_index("idx_diem_danh_cong_chuc", table_name=TBL, schema=SCHEMA)
    op.drop_index("idx_diem_danh_cuoc_hop", table_name=TBL, schema=SCHEMA)
    op.drop_table(TBL, schema=SCHEMA)
