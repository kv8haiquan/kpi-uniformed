"""DGNL: tao bang lms.cau_truc_de_template — luu cau truc de lam mau tai su dung

QT dao tao co the luu cau truc de (so cau de/TB/kho theo vi tri x linh vuc)
cua 1 ky thi thanh mau, roi ap dung nhanh cho ky thi sau.

Revision ID: lms_ctd_template_20260730
Revises: lms_vi_pham_thi_20260730
Create Date: 2026-07-30
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "lms_ctd_template_20260730"
down_revision = "lms_vi_pham_thi_20260730"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "cau_truc_de_template",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("ten_template", sa.String(200), nullable=False),
        sa.Column("mo_ta", sa.Text(), nullable=True),
        sa.Column("nguoi_tao_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("public.cong_chuc.id"), nullable=False),
        sa.Column(
            "cau_truc", postgresql.JSONB(), server_default="[]", nullable=False,
            comment="[{vi_tri_id, linh_vuc_id, so_cau_de, so_cau_trung_binh, so_cau_kho}]",
        ),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        schema="lms",
    )
    op.create_index("idx_ctd_template_nguoi_tao", "cau_truc_de_template", ["nguoi_tao_id"], schema="lms")


def downgrade() -> None:
    op.drop_index("idx_ctd_template_nguoi_tao", table_name="cau_truc_de_template", schema="lms")
    op.drop_table("cau_truc_de_template", schema="lms")
