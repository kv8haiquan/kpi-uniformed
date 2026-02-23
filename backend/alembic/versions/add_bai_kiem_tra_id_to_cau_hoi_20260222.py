"""add bai_kiem_tra_id to cau_hoi

Revision ID: add_bkt_id_cau_hoi_20260222
Revises: add_giai_thich_cau_hoi_20260221
Create Date: 2026-02-22 10:00:00.000000

Them cot bai_kiem_tra_id vao bang lms.cau_hoi de lien ket cau hoi truc tiep voi bai kiem tra.
ON DELETE SET NULL: khi xoa BKT, cau hoi van giu lai nhung bi NULL bai_kiem_tra_id.
"""

from alembic import op
import sqlalchemy as sa

revision = 'add_bkt_id_cau_hoi_20260222'
down_revision = 'add_giai_thich_cau_hoi_20260221'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'cau_hoi',
        sa.Column('bai_kiem_tra_id', sa.UUID(), nullable=True),
        schema='lms',
    )
    op.create_foreign_key(
        'fk_cau_hoi_bai_kiem_tra_id',
        'cau_hoi', 'bai_kiem_tra',
        ['bai_kiem_tra_id'], ['id'],
        source_schema='lms', referent_schema='lms',
        ondelete='SET NULL',
    )
    op.create_index(
        'ix_lms_cau_hoi_bai_kiem_tra_id',
        'cau_hoi',
        ['bai_kiem_tra_id'],
        schema='lms',
    )


def downgrade() -> None:
    op.drop_index('ix_lms_cau_hoi_bai_kiem_tra_id', table_name='cau_hoi', schema='lms')
    op.drop_constraint('fk_cau_hoi_bai_kiem_tra_id', 'cau_hoi', schema='lms', type_='foreignkey')
    op.drop_column('cau_hoi', 'bai_kiem_tra_id', schema='lms')
