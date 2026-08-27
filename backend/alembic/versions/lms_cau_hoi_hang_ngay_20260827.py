"""them bang lms.cau_hoi_hang_ngay

Revision ID: lms_cau_hoi_hang_ngay_20260827
Revises: mt_025_loai_tai_lieu_20260822
Create Date: 2026-08-27

Chot moi ngay dung 1 cau hoi DGNL de phat qua chatbot Zalo.

Khoa chinh la cot `ngay` (khong phai id UUID) — co y: rang buoc "moi ngay dung
mot cau" duoc bao dam o tang co so du lieu, nen hai tien trinh goi cung luc
khong the tao ra hai cau khac nhau cho cung mot ngay (INSERT ... ON CONFLICT).

Bang nay CHI THEM MOI, khong sua bang nao dang chay.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


revision = 'lms_cau_hoi_hang_ngay_20260827'
down_revision = 'mt_025_loai_tai_lieu_20260822'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'cau_hoi_hang_ngay',
        sa.Column(
            'ngay',
            sa.Date(),
            primary_key=True,
            comment='Ngay phat cau hoi (gio Viet Nam)',
        ),
        sa.Column(
            'cau_hoi_id',
            UUID(as_uuid=True),
            sa.ForeignKey('lms.cau_hoi_dgnl.id'),
            nullable=False,
            comment='Cau hoi da phat trong ngay do',
        ),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('CURRENT_TIMESTAMP'),
        ),
        schema='lms',
    )
    # Tra "cau nay da phat chua" khi boc cau moi — tranh lap lai
    op.create_index(
        'ix_cau_hoi_hang_ngay_cau_hoi_id',
        'cau_hoi_hang_ngay',
        ['cau_hoi_id'],
        schema='lms',
    )


def downgrade() -> None:
    op.drop_index(
        'ix_cau_hoi_hang_ngay_cau_hoi_id',
        table_name='cau_hoi_hang_ngay',
        schema='lms',
    )
    op.drop_table('cau_hoi_hang_ngay', schema='lms')
