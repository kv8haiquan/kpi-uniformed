"""add bao_cao_xep_loai_quy tables

Revision ID: aad09a721c57
Revises: 20260414_173744
Create Date: 2026-04-17 00:08:14.925957

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'aad09a721c57'
down_revision: Union[str, None] = '20260414_173744'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Bảng 1: bao_cao_xep_loai_quy
    op.create_table('bao_cao_xep_loai_quy',
    sa.Column('don_vi_id', sa.UUID(), nullable=False, comment='ID đơn vị'),
    sa.Column('quy', sa.Integer(), nullable=False, comment='Quý đánh giá (1-4)'),
    sa.Column('nam', sa.Integer(), nullable=False, comment='Năm đánh giá'),
    sa.Column('nguoi_lap_id', sa.UUID(), nullable=False, comment='ID người lập báo cáo'),
    sa.Column('ngay_lap', sa.DateTime(timezone=True), nullable=True, comment='Ngày lập'),
    sa.Column('ngay_gui_duyet', sa.DateTime(timezone=True), nullable=True, comment='Ngày gửi phê duyệt'),
    sa.Column('trang_thai', sa.String(length=20), server_default='NHAP', nullable=False, comment='NHAP, CHO_PHE_DUYET, DA_PHE_DUYET, TU_CHOI'),
    sa.Column('nguoi_phe_duyet_id', sa.UUID(), nullable=True, comment='ID người phê duyệt (CCT)'),
    sa.Column('ngay_phe_duyet', sa.DateTime(timezone=True), nullable=True, comment='Ngày phê duyệt'),
    sa.Column('y_kien_phe_duyet', sa.Text(), nullable=True, comment='Ý kiến CCT'),
    sa.Column('tong_cong_chuc', sa.Integer(), server_default='0', nullable=False),
    sa.Column('so_loai_a', sa.Integer(), server_default='0', nullable=False),
    sa.Column('so_loai_b', sa.Integer(), server_default='0', nullable=False),
    sa.Column('so_loai_c', sa.Integer(), server_default='0', nullable=False),
    sa.Column('so_loai_d', sa.Integer(), server_default='0', nullable=False),
    sa.Column('so_loai_e', sa.Integer(), server_default='0', nullable=False),
    sa.Column('canh_bao_ty_le_a', sa.Boolean(), server_default='false', nullable=False),
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('is_deleted', sa.Boolean(), server_default='false', nullable=False),
    sa.CheckConstraint('nam >= 2025', name='ck_bao_cao_quy_nam'),
    sa.CheckConstraint('quy >= 1 AND quy <= 4', name='ck_bao_cao_quy_quy'),
    sa.ForeignKeyConstraint(['don_vi_id'], ['don_vi.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['nguoi_lap_id'], ['cong_chuc.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['nguoi_phe_duyet_id'], ['cong_chuc.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('don_vi_id', 'quy', 'nam', name='uq_bao_cao_quy_don_vi_quy_nam')
    )
    with op.batch_alter_table('bao_cao_xep_loai_quy', schema=None) as batch_op:
        batch_op.create_index('idx_bao_cao_quy_don_vi_quy_nam', ['don_vi_id', 'quy', 'nam'], unique=False)
        batch_op.create_index('idx_bao_cao_quy_trang_thai', ['trang_thai'], unique=False)

    # Bảng 2: chi_tiet_xep_loai_quy
    op.create_table('chi_tiet_xep_loai_quy',
    sa.Column('bao_cao_quy_id', sa.UUID(), nullable=False, comment='ID báo cáo quý'),
    sa.Column('cong_chuc_id', sa.UUID(), nullable=False, comment='ID công chức'),
    sa.Column('is_lanh_dao', sa.Boolean(), server_default='false', nullable=False),
    sa.Column('diem_tieu_chi_chung', sa.Numeric(precision=5, scale=2), server_default='0', nullable=False, comment='Điểm TC (0-30) TB 3 tháng'),
    sa.Column('diem_kpi', sa.Numeric(precision=5, scale=2), server_default='0', nullable=False, comment='Điểm KPI (0-70) TB 3 tháng'),
    sa.Column('diem_tong', sa.Numeric(precision=5, scale=2), server_default='0', nullable=False, comment='Điểm tổng (0-100) TB 3 tháng'),
    sa.Column('xep_loai_he_thong', sa.String(length=1), nullable=False, comment='A/B/C/D/E'),
    sa.Column('xep_loai_de_xuat', sa.String(length=1), nullable=True),
    sa.Column('ly_do_dieu_chinh_dt', sa.Text(), nullable=True),
    sa.Column('xep_loai_quyet_dinh', sa.String(length=1), nullable=True),
    sa.Column('ly_do_dieu_chinh_cct', sa.Text(), nullable=True),
    sa.Column('bi_tu_choi', sa.Boolean(), server_default='false', nullable=False),
    sa.Column('ly_do_tu_choi', sa.Text(), nullable=True),
    sa.Column('ghi_chu', sa.Text(), nullable=True),
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint("xep_loai_de_xuat IS NULL OR xep_loai_de_xuat IN ('A', 'B', 'C', 'D', 'E')", name='ck_ctxl_quy_xep_loai_dx'),
    sa.CheckConstraint("xep_loai_he_thong IN ('A', 'B', 'C', 'D', 'E')", name='ck_ctxl_quy_xep_loai_ht'),
    sa.CheckConstraint("xep_loai_quyet_dinh IS NULL OR xep_loai_quyet_dinh IN ('A', 'B', 'C', 'D', 'E')", name='ck_ctxl_quy_xep_loai_qd'),
    sa.ForeignKeyConstraint(['bao_cao_quy_id'], ['bao_cao_xep_loai_quy.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['cong_chuc_id'], ['cong_chuc.id'], ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('bao_cao_quy_id', 'cong_chuc_id', name='uq_ctxl_quy_bao_cao_cc')
    )
    with op.batch_alter_table('chi_tiet_xep_loai_quy', schema=None) as batch_op:
        batch_op.create_index('idx_ctxl_quy_bao_cao', ['bao_cao_quy_id'], unique=False)
        batch_op.create_index('idx_ctxl_quy_cong_chuc', ['cong_chuc_id'], unique=False)
        batch_op.create_index('idx_ctxl_quy_xep_loai_ht', ['xep_loai_he_thong'], unique=False)


def downgrade() -> None:
    op.drop_table('chi_tiet_xep_loai_quy')
    op.drop_table('bao_cao_xep_loai_quy')
