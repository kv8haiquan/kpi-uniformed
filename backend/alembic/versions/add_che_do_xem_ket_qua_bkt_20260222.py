"""add che_do_xem_ket_qua and hien_giai_thich to bai_kiem_tra

Revision ID: add_che_do_xem_bkt_20260222
Revises: add_bkt_id_cau_hoi_20260222
Create Date: 2026-02-22 11:00:00.000000

Them 2 cot vao bang lms.bai_kiem_tra:
  - che_do_xem_ket_qua: che do hien thi ket qua sau khi nop bai
  - hien_giai_thich: co hien giai thich dap an hay khong
"""

from alembic import op
import sqlalchemy as sa

revision = 'add_che_do_xem_bkt_20260222'
down_revision = 'add_bkt_id_cau_hoi_20260222'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'bai_kiem_tra',
        sa.Column(
            'che_do_xem_ket_qua',
            sa.String(50),
            server_default='XEM_DIEM_VA_DAP_AN',
            nullable=False,
        ),
        schema='lms',
    )
    op.add_column(
        'bai_kiem_tra',
        sa.Column(
            'hien_giai_thich',
            sa.Boolean(),
            server_default=sa.text('true'),
            nullable=False,
        ),
        schema='lms',
    )


def downgrade() -> None:
    op.drop_column('bai_kiem_tra', 'hien_giai_thich', schema='lms')
    op.drop_column('bai_kiem_tra', 'che_do_xem_ket_qua', schema='lms')
