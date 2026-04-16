"""add anti-cheat columns to lms.bai_kiem_tra and lms.ket_qua_bai_kiem_tra

Revision ID: add_lms_anti_cheat_20260316
Revises: add_don_vi_snapshot_20260227
Create Date: 2026-03-16

Them 4 cot moi:
  - lms.bai_kiem_tra: gio_mo (VARCHAR 5), gio_dong (VARCHAR 5) — khung gio lam bai
  - lms.ket_qua_bai_kiem_tra: chi_tiet_nhap (JSONB) — auto-save bai lam nhap
  - lms.ket_qua_bai_kiem_tra: so_lan_vi_pham (INTEGER) — dem so lan thoat tab/fullscreen
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = 'add_lms_anti_cheat_20260316'
down_revision = 'add_don_vi_snapshot_20260227'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # lms.bai_kiem_tra — khung gio lam bai
    op.add_column(
        'bai_kiem_tra',
        sa.Column('gio_mo', sa.String(5), nullable=True, comment='Gio bat dau cho phep thi (HH:MM)'),
        schema='lms',
    )
    op.add_column(
        'bai_kiem_tra',
        sa.Column('gio_dong', sa.String(5), nullable=True, comment='Gio ket thuc cho phep thi (HH:MM)'),
        schema='lms',
    )

    # lms.ket_qua_bai_kiem_tra — auto-save + violation tracking
    op.add_column(
        'ket_qua_bai_kiem_tra',
        sa.Column('chi_tiet_nhap', JSONB, nullable=True, comment='Bai lam nhap (auto-save)'),
        schema='lms',
    )
    op.add_column(
        'ket_qua_bai_kiem_tra',
        sa.Column('so_lan_vi_pham', sa.Integer(), server_default='0', comment='So lan thoat tab/fullscreen'),
        schema='lms',
    )


def downgrade() -> None:
    op.drop_column('ket_qua_bai_kiem_tra', 'so_lan_vi_pham', schema='lms')
    op.drop_column('ket_qua_bai_kiem_tra', 'chi_tiet_nhap', schema='lms')
    op.drop_column('bai_kiem_tra', 'gio_dong', schema='lms')
    op.drop_column('bai_kiem_tra', 'gio_mo', schema='lms')
