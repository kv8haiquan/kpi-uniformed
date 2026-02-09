"""
Add lich_su_dieu_chuyen table for Admin Module

Revision ID: admin_001_lich_su_dieu_chuyen
Revises: eb2a95925451
Create Date: 2026-01-30
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'admin_001_lich_su_dieu_chuyen'
down_revision = 'eb2a95925451'  # add_so_ngay_lam_viec_so_ngay_nghi
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Tạo bảng lich_su_dieu_chuyen để lưu lịch sử điều chuyển nhân sự.
    """
    op.create_table(
        'lich_su_dieu_chuyen',
        # Primary Key
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, 
                  server_default=sa.text('gen_random_uuid()')),
        
        # Công chức được điều chuyển
        sa.Column('cong_chuc_id', postgresql.UUID(as_uuid=True), nullable=False),
        
        # Đơn vị cũ/mới
        sa.Column('don_vi_cu_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('don_vi_moi_id', postgresql.UUID(as_uuid=True), nullable=True),
        
        # Vai trò cũ/mới
        sa.Column('vai_tro_cu_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('vai_tro_moi_id', postgresql.UUID(as_uuid=True), nullable=True),
        
        # Chức vụ cũ/mới (text)
        sa.Column('chuc_vu_cu', sa.String(100), nullable=True),
        sa.Column('chuc_vu_moi', sa.String(100), nullable=True),
        
        # Thông tin bổ sung
        sa.Column('ly_do', sa.Text(), nullable=True),
        sa.Column('ngay_hieu_luc', sa.Date(), nullable=True),
        
        # Người thực hiện (Admin)
        sa.Column('nguoi_thuc_hien_id', postgresql.UUID(as_uuid=True), nullable=True),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), 
                  server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), 
                  server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        
        # Primary Key constraint
        sa.PrimaryKeyConstraint('id'),
        
        # Foreign Keys
        sa.ForeignKeyConstraint(['cong_chuc_id'], ['cong_chuc.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['don_vi_cu_id'], ['don_vi.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['don_vi_moi_id'], ['don_vi.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['vai_tro_cu_id'], ['vai_tro.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['vai_tro_moi_id'], ['vai_tro.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['nguoi_thuc_hien_id'], ['cong_chuc.id'], ondelete='SET NULL'),
    )
    
    # Indexes
    op.create_index('idx_lich_su_dc_cong_chuc', 'lich_su_dieu_chuyen', ['cong_chuc_id'])
    op.create_index('idx_lich_su_dc_ngay', 'lich_su_dieu_chuyen', ['ngay_hieu_luc'])
    op.create_index('idx_lich_su_dc_created', 'lich_su_dieu_chuyen', ['created_at'])
    
    # Comment
    op.execute("""
        COMMENT ON TABLE lich_su_dieu_chuyen IS 
        'Lịch sử điều chuyển nhân sự - Admin Module v1.0.0 (30/01/2026)';
    """)


def downgrade() -> None:
    """
    Xóa bảng lich_su_dieu_chuyen.
    """
    op.drop_index('idx_lich_su_dc_created', table_name='lich_su_dieu_chuyen')
    op.drop_index('idx_lich_su_dc_ngay', table_name='lich_su_dieu_chuyen')
    op.drop_index('idx_lich_su_dc_cong_chuc', table_name='lich_su_dieu_chuyen')
    op.drop_table('lich_su_dieu_chuyen')