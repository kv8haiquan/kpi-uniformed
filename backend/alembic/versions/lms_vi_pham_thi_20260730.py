"""DGNL: tao bang lms.vi_pham_thi — log chi tiet tung lan vi pham khi thi

Moi lan thi sinh thoat toan man hinh / chuyen tab, FE goi API ghi ngay 1 row
(kem thoi gian). Thi sinh co the nhap ly do giai trinh (khong bat buoc) de
TCCB/QT dao tao xem xet.

Revision ID: lms_vi_pham_thi_20260730
Revises: lms_ts_xac_nhan_20260730
Create Date: 2026-07-30
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "lms_vi_pham_thi_20260730"
down_revision = "lms_ts_xac_nhan_20260730"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "vi_pham_thi",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("thi_sinh_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("lms.thi_sinh.id", ondelete="CASCADE"), nullable=False),
        sa.Column("ky_thi_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("lms.ky_thi.id", ondelete="CASCADE"), nullable=False),
        sa.Column("lan_thi", sa.Integer(), nullable=False, comment="Lan thi xay ra vi pham"),
        sa.Column("loai_vi_pham", sa.String(50), nullable=False, comment="EXIT_FULLSCREEN | SWITCH_TAB"),
        sa.Column("thoi_gian", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("ly_do", sa.Text(), nullable=True, comment="Ly do giai trinh (thi sinh nhap, khong bat buoc)"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        schema="lms",
    )
    op.create_index("idx_vi_pham_thi_thi_sinh", "vi_pham_thi", ["thi_sinh_id"], schema="lms")
    op.create_index("idx_vi_pham_thi_ky_thi", "vi_pham_thi", ["ky_thi_id"], schema="lms")


def downgrade() -> None:
    op.drop_index("idx_vi_pham_thi_ky_thi", table_name="vi_pham_thi", schema="lms")
    op.drop_index("idx_vi_pham_thi_thi_sinh", table_name="vi_pham_thi", schema="lms")
    op.drop_table("vi_pham_thi", schema="lms")
