"""
Migration: Them cot giai_thich vao bang lms.cau_hoi
Author: Platform Team
Date: 2026-02-21

Ly do: Frontend da co truong giai_thich trong ICauHoi va form UI,
       nhung backend chua co column -> truong bi mat khi luu.
"""

from alembic import op
import sqlalchemy as sa


# Revision identifiers
revision = 'add_giai_thich_cau_hoi_20260221'
down_revision = 'create_lms_schema_20260220'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'cau_hoi',
        sa.Column('giai_thich', sa.Text(), nullable=True),
        schema='lms',
    )


def downgrade():
    op.drop_column('cau_hoi', 'giai_thich', schema='lms')
