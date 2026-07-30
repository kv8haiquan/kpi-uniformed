"""DGNL: them cot xac nhan ca thi tren lms.thi_sinh

Sau khi nop bai, thi sinh bam "Xac nhan ca thi" de chot ket qua (khong duoc
thi lai du con luot). Neu khong bam gi, he thong tu dong xac nhan sau 10 phut
(enforce lazy trong bat_dau_thi).

Revision ID: lms_ts_xac_nhan_20260730
Revises: lms_timestamptz_20260730
Create Date: 2026-07-30
"""
from alembic import op
import sqlalchemy as sa

revision = "lms_ts_xac_nhan_20260730"
down_revision = "lms_timestamptz_20260730"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "thi_sinh",
        sa.Column("da_xac_nhan", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        schema="lms",
    )
    op.add_column(
        "thi_sinh",
        sa.Column("thoi_gian_xac_nhan", sa.DateTime(timezone=True), nullable=True),
        schema="lms",
    )


def downgrade() -> None:
    op.drop_column("thi_sinh", "thoi_gian_xac_nhan", schema="lms")
    op.drop_column("thi_sinh", "da_xac_nhan", schema="lms")
