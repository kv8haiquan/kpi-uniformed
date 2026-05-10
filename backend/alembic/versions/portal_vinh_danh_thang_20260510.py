"""Create portal.vinh_danh_thang — Module vinh danh công chức tiêu biểu tháng

Revision ID: portal_vinh_danh_thang_20260510
Revises: phieu_danh_gia_t_20260508
Create Date: 2026-05-10

Tao bang portal.vinh_danh_thang phuc vu tinh nang vinh danh:
  - 1 cong chuc tieu bieu / thang (UNIQUE partial index khi PUBLISHED)
  - Workflow don gian: DRAFT -> PUBLISHED
  - Admin (SUPER_ADMIN / QT_NOI_DUNG) tu chon nguoi vinh danh thu cong
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'portal_vinh_danh_thang_20260510'
down_revision = 'phieu_danh_gia_t_20260508'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'vinh_danh_thang',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column('thang', sa.Integer(), nullable=False),
        sa.Column('nam', sa.Integer(), nullable=False),
        sa.Column(
            'cong_chuc_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('public.cong_chuc.id'),
            nullable=False,
        ),
        sa.Column('tieu_de', sa.String(200), nullable=False),
        sa.Column('ly_do', sa.Text(), nullable=False),
        sa.Column('anh_chan_dung', sa.String(500), nullable=True),
        sa.Column('loi_tuyen_duong', sa.Text(), nullable=True),
        sa.Column(
            'trang_thai',
            sa.String(50),
            server_default='DRAFT',
            nullable=False,
        ),
        sa.Column(
            'nguoi_tao_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('public.cong_chuc.id'),
            nullable=True,
        ),
        sa.Column('ngay_cong_bo', sa.TIMESTAMP(), nullable=True),
        sa.Column(
            'created_at',
            sa.TIMESTAMP(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            'updated_at',
            sa.TIMESTAMP(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.CheckConstraint('thang >= 1 AND thang <= 12', name='ck_vinh_danh_thang_range'),
        sa.CheckConstraint('nam >= 2020 AND nam <= 2100', name='ck_vinh_danh_nam_range'),
        sa.CheckConstraint(
            "trang_thai IN ('DRAFT', 'PUBLISHED')",
            name='ck_vinh_danh_trang_thai',
        ),
        schema='portal',
    )

    # Index tra cuu theo thang/nam
    op.create_index(
        'idx_portal_vd_thang_nam',
        'vinh_danh_thang',
        ['nam', 'thang'],
        schema='portal',
    )

    # UNIQUE partial: chi 1 ban ghi PUBLISHED cho moi thang/nam
    op.execute("""
        CREATE UNIQUE INDEX uq_portal_vd_published_per_month
        ON portal.vinh_danh_thang (nam, thang)
        WHERE trang_thai = 'PUBLISHED'
    """)


def downgrade():
    op.execute("DROP INDEX IF EXISTS portal.uq_portal_vd_published_per_month")
    op.drop_index('idx_portal_vd_thang_nam', table_name='vinh_danh_thang', schema='portal')
    op.drop_table('vinh_danh_thang', schema='portal')
