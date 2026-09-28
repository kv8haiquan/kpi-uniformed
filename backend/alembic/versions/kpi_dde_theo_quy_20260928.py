"""them cot danh_gia_dde.la_phieu_dde_quy (d/d/e theo quy - CV 21169)

Revision ID: kpi_dde_theo_quy_20260928
Revises: kpi_tc_theo_quy_20260918
Create Date: 2026-09-28

Mau 02B kem CV 21169 chi co MOT o cho moi chi so d/d/e trong ca quy. Truoc day
phan mem bat lanh dao ke ba lan moi quy roi lay MIN ba thang — quy uoc noi bo,
khong co trong cong van.

Tu Q3/2026, phieu d/d/e cua quy NEO vao ban ghi `danh_gia_dde` cua THANG CUOI QUY
(T3/T6/T9/T12); hai thang con lai doc xuyen sang. Cot nay danh dau ban ghi neo —
xem app/core/ky_tieu_chi.py.

Migration CHI THEM MOT COT mac dinh false, KHONG dung toi dong du lieu nao dang
chay (70-90 ban moi quy van nguyen ven de tra cuu). Downgrade = drop cot.
"""

from alembic import op
import sqlalchemy as sa


revision = 'kpi_dde_theo_quy_20260928'
down_revision = 'kpi_tc_theo_quy_20260918'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'danh_gia_dde',
        sa.Column(
            'la_phieu_dde_quy',
            sa.Boolean(),
            nullable=False,
            server_default=sa.text('false'),
            comment='Ban ghi nay la phieu d/d/e cua CA QUY (CV 21169, tu Q3/2026)',
        ),
    )
    op.create_index(
        'idx_dde_phieu_quy',
        'danh_gia_dde',
        ['nam', 'thang'],
        unique=False,
        postgresql_where=sa.text('la_phieu_dde_quy'),
    )


def downgrade() -> None:
    op.drop_index('idx_dde_phieu_quy', table_name='danh_gia_dde')
    op.drop_column('danh_gia_dde', 'la_phieu_dde_quy')
