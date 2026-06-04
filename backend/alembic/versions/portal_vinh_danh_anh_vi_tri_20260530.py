"""Them cot anh_vi_tri vao portal.vinh_danh_thang — chinh vi tri anh trong khung tron

Revision ID: portal_vd_anh_vi_tri_20260530
Revises: add_lms_dgnl_autosave_20260527
Create Date: 2026-05-30

Them cot anh_vi_tri (CSS object-position, vd "50% 30%") de admin chinh vi tri
anh chan dung trong khung tron. Cot nullable, mac dinh giua "50% 50%" — an toan
voi du lieu hien co (chi 1 dong).
"""
from alembic import op
import sqlalchemy as sa

revision = 'portal_vd_anh_vi_tri_20260530'
down_revision = 'add_lms_dgnl_autosave_20260527'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'vinh_danh_thang',
        sa.Column(
            'anh_vi_tri',
            sa.String(20),
            server_default=sa.text("'50% 50%'"),
            nullable=True,
        ),
        schema='portal',
    )


def downgrade():
    op.drop_column('vinh_danh_thang', 'anh_vi_tri', schema='portal')
