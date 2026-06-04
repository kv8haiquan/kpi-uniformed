"""add autosave columns to lms.thi_sinh

Revision ID: add_lms_dgnl_autosave_20260527
Revises: portal_vinh_danh_thang_20260510
Create Date: 2026-05-27

Them 2 cot vao lms.thi_sinh de ho tro auto-save bai lam DGNL (giong pattern BKT):
  - chi_tiet_nhap (JSONB) — bai lam nhap, frontend gui moi 30s
  - so_lan_vi_pham (INTEGER) — dem so lan thoat tab/fullscreen

Muc tieu: tranh kep DANG_THI khong nop duoc (su co 26/05/2026 - 3 thi sinh
trong ky thi DGNL TA: 20ZZ-0066, 20ZZ-0145, 20ZZ-0109).
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


revision = 'add_lms_dgnl_autosave_20260527'
down_revision = 'portal_vinh_danh_thang_20260510'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'thi_sinh',
        sa.Column(
            'chi_tiet_nhap',
            JSONB,
            nullable=True,
            comment='Bai lam nhap auto-save (frontend gui moi 30s)',
        ),
        schema='lms',
    )
    op.add_column(
        'thi_sinh',
        sa.Column(
            'so_lan_vi_pham',
            sa.Integer(),
            server_default='0',
            comment='So lan thoat tab/fullscreen trong khi thi',
        ),
        schema='lms',
    )


def downgrade() -> None:
    op.drop_column('thi_sinh', 'so_lan_vi_pham', schema='lms')
    op.drop_column('thi_sinh', 'chi_tiet_nhap', schema='lms')
