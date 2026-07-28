"""add lms.phien_thi + ky_thi.yeu_cau_toan_man_hinh (DGNL exam hardening)

Revision ID: lms_phien_giamsat_20260622
Revises: create_chi_tieu_schema_20260604
Create Date: 2026-06-22

Phuc vu 3 tinh nang siet ky luat phong thi DGNL:
  1. lms.phien_thi — 1 phien thi/tai khoan tai 1 thoi diem (chong dung chung
     tai khoan). Moi cong_chuc_id chi co 1 dong (UNIQUE). bat_dau_thi sinh
     token moi -> thiet bi cu bi 409 khi luu-nhap/nop-bai.
  2. last_seen cua phien_thi dung luon cho man hinh giam sat truc tiep (online).
  3. lms.ky_thi.yeu_cau_toan_man_hinh — bat/tat ep toan man hinh + canh bao
     vi pham theo tung ky thi (mac dinh true).

Chi dong cham schema `lms`. KHONG dung public / KPI production.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


revision = 'lms_phien_giamsat_20260622'
down_revision = 'create_chi_tieu_schema_20260604'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Cot ep toan man hinh tren ky thi
    op.add_column(
        'ky_thi',
        sa.Column(
            'yeu_cau_toan_man_hinh',
            sa.Boolean(),
            server_default=sa.text('true'),
            nullable=False,
            comment='Ep toan man hinh + canh bao vi pham khi thi',
        ),
        schema='lms',
    )

    # 2. Bang phien thi — 1 phien/tai khoan
    op.create_table(
        'phien_thi',
        sa.Column('id', UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('cong_chuc_id', UUID(as_uuid=True), sa.ForeignKey('public.cong_chuc.id'), nullable=False),
        sa.Column('phien_token', sa.String(64), nullable=False),
        sa.Column('ky_thi_id', UUID(as_uuid=True), sa.ForeignKey('lms.ky_thi.id', ondelete='CASCADE'), nullable=True),
        sa.Column('thi_sinh_id', UUID(as_uuid=True), sa.ForeignKey('lms.thi_sinh.id', ondelete='CASCADE'), nullable=True),
        sa.Column('thiet_bi', sa.String(255), nullable=True, comment='User-Agent rut gon'),
        sa.Column('last_seen', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.UniqueConstraint('cong_chuc_id', name='uq_phien_thi_cong_chuc'),
        schema='lms',
    )


def downgrade() -> None:
    op.drop_table('phien_thi', schema='lms')
    op.drop_column('ky_thi', 'yeu_cau_toan_man_hinh', schema='lms')
