"""
Tạo bảng bao_cao_xep_loai và chi_tiet_xep_loai

Module: Báo cáo Xếp loại Chất lượng Công chức
Tham chiếu: Điều 17 - Quy chế đánh giá KPI Chi cục Hải quan KV8

Revision ID: 20260128_001
Revises: 20260125_005
Create Date: 2026-01-28
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '20260128_001'
down_revision = '005_leader_kpi'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # =========================================================================
    # BẢNG 1: bao_cao_xep_loai - Báo cáo xếp loại theo đơn vị/tháng
    # =========================================================================
    op.create_table(
        'bao_cao_xep_loai',
        
        # Primary Key
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, 
                  server_default=sa.text('gen_random_uuid()'), nullable=False),
        
        # Thông tin báo cáo
        sa.Column('don_vi_id', postgresql.UUID(as_uuid=True), 
                  sa.ForeignKey('don_vi.id', ondelete='RESTRICT'), nullable=False,
                  comment='ID đơn vị'),
        sa.Column('thang', sa.Integer(), nullable=False, comment='Tháng (1-12)'),
        sa.Column('nam', sa.Integer(), nullable=False, comment='Năm (>= 2025)'),
        
        # Người lập (Đội trưởng hoặc CCT cho đơn vị Lãnh đạo Chi cục)
        sa.Column('nguoi_lap_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('cong_chuc.id', ondelete='RESTRICT'), nullable=False,
                  comment='ID người lập báo cáo'),
        sa.Column('ngay_lap', sa.DateTime(timezone=True), nullable=True,
                  comment='Ngày lập (khi gửi duyệt)'),
        
        # Trạng thái
        sa.Column('trang_thai', sa.String(20), nullable=False, server_default='NHAP',
                  comment='NHAP, CHO_PHE_DUYET, DA_PHE_DUYET, TU_CHOI'),
        
        # Phê duyệt (CCT)
        sa.Column('nguoi_phe_duyet_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('cong_chuc.id', ondelete='SET NULL'), nullable=True,
                  comment='ID người phê duyệt (CCT)'),
        sa.Column('ngay_phe_duyet', sa.DateTime(timezone=True), nullable=True,
                  comment='Ngày phê duyệt'),
        sa.Column('y_kien_phe_duyet', sa.Text(), nullable=True,
                  comment='Ý kiến của CCT'),
        
        # Thống kê (computed khi gửi duyệt)
        sa.Column('tong_cong_chuc', sa.Integer(), server_default='0',
                  comment='Tổng số CC trong báo cáo'),
        sa.Column('so_loai_a', sa.Integer(), server_default='0', comment='Số CC loại A'),
        sa.Column('so_loai_b', sa.Integer(), server_default='0', comment='Số CC loại B'),
        sa.Column('so_loai_c', sa.Integer(), server_default='0', comment='Số CC loại C'),
        sa.Column('so_loai_d', sa.Integer(), server_default='0', comment='Số CC loại D'),
        sa.Column('so_loai_e', sa.Integer(), server_default='0', comment='Số CC loại E'),
        
        # Cảnh báo tỷ lệ A
        sa.Column('canh_bao_ty_le_a', sa.Boolean(), server_default='false',
                  comment='Cảnh báo nếu loại A > 20% loại B'),
        
        # Metadata
        sa.Column('created_at', sa.DateTime(timezone=True), 
                  server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), 
                  server_default=sa.text('NOW()'), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), server_default='false', nullable=False),
        
        # Constraints
        sa.CheckConstraint('thang BETWEEN 1 AND 12', name='ck_bcxl_thang'),
        sa.CheckConstraint('nam >= 2025', name='ck_bcxl_nam'),
        sa.CheckConstraint(
            "trang_thai IN ('NHAP', 'CHO_PHE_DUYET', 'DA_PHE_DUYET', 'TU_CHOI')",
            name='ck_bcxl_trang_thai'
        ),
        sa.UniqueConstraint('don_vi_id', 'thang', 'nam', name='uq_bcxl_don_vi_thang_nam'),
    )
    
    # Indexes cho bao_cao_xep_loai
    op.create_index('idx_bcxl_don_vi', 'bao_cao_xep_loai', ['don_vi_id'])
    op.create_index('idx_bcxl_thang_nam', 'bao_cao_xep_loai', ['thang', 'nam'])
    op.create_index('idx_bcxl_trang_thai', 'bao_cao_xep_loai', ['trang_thai'])
    op.create_index('idx_bcxl_nguoi_lap', 'bao_cao_xep_loai', ['nguoi_lap_id'])
    
    # =========================================================================
    # BẢNG 2: chi_tiet_xep_loai - Chi tiết xếp loại từng công chức
    # =========================================================================
    op.create_table(
        'chi_tiet_xep_loai',
        
        # Primary Key
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()'), nullable=False),
        
        # Foreign Keys
        sa.Column('bao_cao_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('bao_cao_xep_loai.id', ondelete='CASCADE'), nullable=False,
                  comment='ID báo cáo'),
        sa.Column('cong_chuc_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('cong_chuc.id', ondelete='RESTRICT'), nullable=False,
                  comment='ID công chức'),
        
        # Phân loại đối tượng
        sa.Column('is_lanh_dao', sa.Boolean(), server_default='false', nullable=False,
                  comment='Có phải lãnh đạo không (phân biệt nguồn tính điểm)'),
        
        # Điểm từ hệ thống (snapshot tại thời điểm tạo báo cáo)
        sa.Column('diem_tieu_chi_chung', sa.Numeric(5, 2), server_default='0',
                  comment='Điểm tiêu chí chung (0-30)'),
        sa.Column('diem_kpi', sa.Numeric(5, 2), server_default='0',
                  comment='Điểm KPI đã nhân 70 (0-70)'),
        sa.Column('diem_tong', sa.Numeric(5, 2), server_default='0',
                  comment='Điểm tổng = tiêu chí chung + KPI (0-100)'),
        sa.Column('xep_loai_he_thong', sa.String(1), nullable=False,
                  comment='Xếp loại hệ thống tự tính (A/B/C/D/E)'),
        
        # Đề xuất của Đội trưởng
        sa.Column('xep_loai_de_xuat', sa.String(1), nullable=True,
                  comment='Xếp loại Đội trưởng đề xuất'),
        sa.Column('ly_do_dieu_chinh_dt', sa.Text(), nullable=True,
                  comment='Lý do điều chỉnh của Đội trưởng (bắt buộc nếu khác hệ thống)'),
        
        # Quyết định của CCT
        sa.Column('xep_loai_quyet_dinh', sa.String(1), nullable=True,
                  comment='Xếp loại CCT quyết định'),
        sa.Column('ly_do_dieu_chinh_cct', sa.Text(), nullable=True,
                  comment='Lý do điều chỉnh của CCT (bắt buộc nếu khác đề xuất)'),
        
        # Trạng thái từ chối riêng (cho việc sửa từng CC)
        sa.Column('bi_tu_choi', sa.Boolean(), server_default='false',
                  comment='CC này bị CCT từ chối'),
        sa.Column('ly_do_tu_choi', sa.Text(), nullable=True,
                  comment='Lý do từ chối cụ thể'),
        
        # Ghi chú
        sa.Column('ghi_chu', sa.Text(), nullable=True, comment='Ghi chú bổ sung'),
        
        # Metadata
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True),
                  server_default=sa.text('NOW()'), nullable=False),
        
        # Constraints
        sa.CheckConstraint(
            "xep_loai_he_thong IN ('A', 'B', 'C', 'D', 'E')",
            name='ck_ctxl_xep_loai_ht'
        ),
        sa.CheckConstraint(
            "xep_loai_de_xuat IS NULL OR xep_loai_de_xuat IN ('A', 'B', 'C', 'D', 'E')",
            name='ck_ctxl_xep_loai_dx'
        ),
        sa.CheckConstraint(
            "xep_loai_quyet_dinh IS NULL OR xep_loai_quyet_dinh IN ('A', 'B', 'C', 'D', 'E')",
            name='ck_ctxl_xep_loai_qd'
        ),
        sa.UniqueConstraint('bao_cao_id', 'cong_chuc_id', name='uq_ctxl_bao_cao_cc'),
    )
    
    # Indexes cho chi_tiet_xep_loai
    op.create_index('idx_ctxl_bao_cao', 'chi_tiet_xep_loai', ['bao_cao_id'])
    op.create_index('idx_ctxl_cong_chuc', 'chi_tiet_xep_loai', ['cong_chuc_id'])
    op.create_index('idx_ctxl_xep_loai_ht', 'chi_tiet_xep_loai', ['xep_loai_he_thong'])
    op.create_index('idx_ctxl_is_lanh_dao', 'chi_tiet_xep_loai', ['is_lanh_dao'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_ctxl_is_lanh_dao', table_name='chi_tiet_xep_loai')
    op.drop_index('idx_ctxl_xep_loai_ht', table_name='chi_tiet_xep_loai')
    op.drop_index('idx_ctxl_cong_chuc', table_name='chi_tiet_xep_loai')
    op.drop_index('idx_ctxl_bao_cao', table_name='chi_tiet_xep_loai')
    
    op.drop_index('idx_bcxl_nguoi_lap', table_name='bao_cao_xep_loai')
    op.drop_index('idx_bcxl_trang_thai', table_name='bao_cao_xep_loai')
    op.drop_index('idx_bcxl_thang_nam', table_name='bao_cao_xep_loai')
    op.drop_index('idx_bcxl_don_vi', table_name='bao_cao_xep_loai')
    
    # Drop tables
    op.drop_table('chi_tiet_xep_loai')
    op.drop_table('bao_cao_xep_loai')
