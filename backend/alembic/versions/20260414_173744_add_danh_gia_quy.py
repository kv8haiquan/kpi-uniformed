"""add_danh_gia_quy

Revision ID: 20260414_173744
Revises: migration_lich_su_dieu_chinh
Create Date: 2026-04-14 17:37:44.000000

Tạo bảng danh_gia_quy để lưu kết quả xếp loại quý.

Bảng này lưu điểm tổng hợp và xếp loại của công chức theo quý.
Được tính tự động từ 3 tháng trong quý, không có workflow phê duyệt.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20260414_173744'
down_revision = 'add_lms_cau_hoi_dgnl_20260406'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Tạo bảng danh_gia_quy
    op.create_table(
        'danh_gia_quy',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('cong_chuc_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('don_vi_id_snapshot', postgresql.UUID(as_uuid=True), nullable=True, comment='Snapshot đơn vị tại thời điểm tính quý'),
        sa.Column('quy', sa.Integer(), nullable=False, comment='Quý (1-4)'),
        sa.Column('nam', sa.Integer(), nullable=False, comment='Năm'),
        sa.Column('diem_kpi_quy', sa.Numeric(5, 2), nullable=True, comment='Điểm KPI quý (70đ) = TB(3 tháng × 70)'),
        sa.Column('diem_tc_quy', sa.Numeric(5, 2), nullable=True, comment='Điểm tiêu chí chung quý (max 30đ)'),
        sa.Column('diem_tong_quy', sa.Numeric(5, 2), nullable=True, comment='Điểm tổng quý (0-100)'),
        sa.Column('xep_loai_quy', sa.String(1), nullable=True, comment='Xếp loại quý (A/B/C/D)'),
        sa.Column('ghi_chu', sa.Text(), nullable=True, comment='Ghi chú (VD: CC chuyển đơn vị giữa quý)'),
        sa.Column('co_chuyen_don_vi', sa.Boolean(), server_default='false', nullable=False, comment='TRUE nếu CC chuyển đơn vị giữa quý'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['cong_chuc_id'], ['cong_chuc.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['don_vi_id_snapshot'], ['don_vi.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('cong_chuc_id', 'quy', 'nam', name='uq_danh_gia_quy_cc_quy_nam'),
        sa.CheckConstraint('quy BETWEEN 1 AND 4', name='ck_quy_range'),
        sa.CheckConstraint('nam >= 2025', name='ck_nam_min'),
        sa.CheckConstraint('diem_kpi_quy IS NULL OR diem_kpi_quy BETWEEN 0 AND 70', name='ck_diem_kpi_quy'),
        sa.CheckConstraint('diem_tc_quy IS NULL OR diem_tc_quy BETWEEN 0 AND 30', name='ck_diem_tc_quy'),
        sa.CheckConstraint('diem_tong_quy IS NULL OR diem_tong_quy BETWEEN 0 AND 100', name='ck_diem_tong_quy'),
        sa.CheckConstraint("xep_loai_quy IS NULL OR xep_loai_quy IN ('A', 'B', 'C', 'D')", name='ck_xep_loai_quy'),
    )

    # Tạo indexes
    op.create_index('idx_danh_gia_quy_cc', 'danh_gia_quy', ['cong_chuc_id'])
    op.create_index('idx_danh_gia_quy_quy_nam', 'danh_gia_quy', ['quy', 'nam'])
    op.create_index('idx_danh_gia_quy_don_vi_snapshot', 'danh_gia_quy', ['don_vi_id_snapshot', 'quy', 'nam'])
    op.create_index('idx_danh_gia_quy_xep_loai', 'danh_gia_quy', ['xep_loai_quy'])


def downgrade() -> None:
    op.drop_index('idx_danh_gia_quy_xep_loai', table_name='danh_gia_quy')
    op.drop_index('idx_danh_gia_quy_don_vi_snapshot', table_name='danh_gia_quy')
    op.drop_index('idx_danh_gia_quy_quy_nam', table_name='danh_gia_quy')
    op.drop_index('idx_danh_gia_quy_cc', table_name='danh_gia_quy')
    op.drop_table('danh_gia_quy')
