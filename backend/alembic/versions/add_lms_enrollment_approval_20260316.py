"""add lms enrollment approval columns

Revision ID: add_lms_enrollment_approval
Create Date: 2026-03-16
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "add_lms_enrollment_approval"
down_revision = None  # standalone — chay bang alembic upgrade head hoac manual
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Them 3 cot phe duyet vao lms.dang_ky_khoa_hoc
    op.add_column(
        "dang_ky_khoa_hoc",
        sa.Column("nguoi_phe_duyet_id", UUID(as_uuid=True), sa.ForeignKey("public.cong_chuc.id"), nullable=True),
        schema="lms",
    )
    op.add_column(
        "dang_ky_khoa_hoc",
        sa.Column("ngay_phe_duyet", sa.DateTime, nullable=True),
        schema="lms",
    )
    op.add_column(
        "dang_ky_khoa_hoc",
        sa.Column("ly_do_tu_choi", sa.Text, nullable=True),
        schema="lms",
    )

    # Index tren trang_thai de toi uu query cho_phe_duyet
    op.create_index(
        "idx_lms_dkkh_trang_thai",
        "dang_ky_khoa_hoc",
        ["trang_thai"],
        schema="lms",
    )


def downgrade() -> None:
    op.drop_index("idx_lms_dkkh_trang_thai", table_name="dang_ky_khoa_hoc", schema="lms")
    op.drop_column("dang_ky_khoa_hoc", "ly_do_tu_choi", schema="lms")
    op.drop_column("dang_ky_khoa_hoc", "ngay_phe_duyet", schema="lms")
    op.drop_column("dang_ky_khoa_hoc", "nguoi_phe_duyet_id", schema="lms")
