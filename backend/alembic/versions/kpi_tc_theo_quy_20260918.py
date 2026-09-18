"""them cot danh_gia_thang.la_phieu_tc_quy (tieu chi chung theo quy - CV 21169)

Revision ID: kpi_tc_theo_quy_20260918
Revises: lms_reset_luot_thi_20260831
Create Date: 2026-09-18

Cong van 21169/CHQ-TCCB ngay 28/8/2026: tu quy III/2026, ky danh gia xep loai
tren phan mem duoc thiet lap theo QUY. Tieu chi chung (30 diem) chuyen tu cham
hang thang sang cham 1 lan cho ca quy.

Phieu tieu chi cua quy NEO vao ban ghi `danh_gia_thang` cua THANG CUOI QUY
(T3/T6/T9/T12); hai thang con lai doc xuyen sang ban ghi do. Cot nay danh dau
ban ghi neo — xem app/core/ky_tieu_chi.py.

Migration CHI THEM MOT COT co gia tri mac dinh false, KHONG dung toi bat ky
dong du lieu nao dang chay. Downgrade = drop cot.
"""

from alembic import op
import sqlalchemy as sa


revision = 'kpi_tc_theo_quy_20260918'
down_revision = 'lms_reset_luot_thi_20260831'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'danh_gia_thang',
        sa.Column(
            'la_phieu_tc_quy',
            sa.Boolean(),
            nullable=False,
            server_default=sa.text('false'),
            comment='Ban ghi nay chua phieu tieu chi chung cua CA QUY (CV 21169, tu Q3/2026)',
        ),
    )
    # Index rieng phan: chi vai tram dong/quy co co nay, truy van "phieu quy cho
    # duyet" loc theo co + thang/nam.
    op.create_index(
        'idx_danh_gia_phieu_tc_quy',
        'danh_gia_thang',
        ['nam', 'thang'],
        unique=False,
        postgresql_where=sa.text('la_phieu_tc_quy'),
    )


def downgrade() -> None:
    op.drop_index('idx_danh_gia_phieu_tc_quy', table_name='danh_gia_thang')
    op.drop_column('danh_gia_thang', 'la_phieu_tc_quy')
