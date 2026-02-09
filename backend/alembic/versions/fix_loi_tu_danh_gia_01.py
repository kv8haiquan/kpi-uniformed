"""
Fix: Dùng số lỗi tự đánh giá CC làm mặc định nếu lãnh đạo chưa nhập

Revision ID: fix_loi_tu_danh_gia_01
Revises: fix_sp_cl_td_20260131
Create Date: 2026-01-31

Mô tả:
- Business Rule: Số lỗi chốt = Số lỗi LĐ nhập (nếu có) HOẶC Số lỗi tự đánh giá CC
- Bước 1: Cập nhật so_loi_chat_luong/tien_do từ tu_danh_gia nếu = 0
- Bước 2: Tính lại so_sp_chat_luong/tien_do với công thức đúng
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'fix_loi_tu_danh_gia_01'
down_revision = 'fix_sp_cl_td_20260131'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Bước 1: Cập nhật số lỗi chốt = số lỗi tự đánh giá nếu lãnh đạo chưa nhập (= 0)
    Bước 2: Tính lại so_sp_chat_luong và so_sp_tien_do
    """
    
    # =========================================================================
    # BƯỚC 1: Cập nhật số lỗi chốt từ tự đánh giá
    # =========================================================================
    op.execute("""
        UPDATE ke_khai_cong_viec
        SET 
            so_loi_chat_luong = COALESCE(NULLIF(so_loi_chat_luong, 0), tu_danh_gia_chat_luong, 0),
            so_loi_tien_do = COALESCE(NULLIF(so_loi_tien_do, 0), tu_danh_gia_tien_do, 0),
            updated_at = CURRENT_TIMESTAMP
        WHERE 
            trang_thai = 'DA_PHE_DUYET'
            AND is_deleted = FALSE;
    """)
    
    # =========================================================================
    # BƯỚC 2: Tính lại SP chất lượng và tiến độ với công thức đúng
    # Công thức: SP_đạt = SP_gốc - (0.25 × min(Lỗi, SL×4) × SP_per_unit)
    # =========================================================================
    op.execute("""
        UPDATE ke_khai_cong_viec
        SET 
            so_sp_chat_luong = GREATEST(
                so_sp_goc_quy_doi - (
                    0.25 
                    * LEAST(COALESCE(so_loi_chat_luong, 0), so_luong * 4)
                    * (so_sp_goc_quy_doi / NULLIF(so_luong, 0))
                ),
                0
            ),
            so_sp_tien_do = GREATEST(
                so_sp_goc_quy_doi - (
                    0.25 
                    * LEAST(COALESCE(so_loi_tien_do, 0), so_luong * 4)
                    * (so_sp_goc_quy_doi / NULLIF(so_luong, 0))
                ),
                0
            ),
            updated_at = CURRENT_TIMESTAMP
        WHERE 
            trang_thai = 'DA_PHE_DUYET'
            AND is_deleted = FALSE
            AND so_sp_goc_quy_doi IS NOT NULL
            AND so_luong > 0;
    """)


def downgrade() -> None:
    """
    Rollback: Reset số lỗi chốt về 0 và tính lại SP = SP gốc
    """
    op.execute("""
        UPDATE ke_khai_cong_viec
        SET 
            so_loi_chat_luong = 0,
            so_loi_tien_do = 0,
            so_sp_chat_luong = so_sp_goc_quy_doi,
            so_sp_tien_do = so_sp_goc_quy_doi,
            updated_at = CURRENT_TIMESTAMP
        WHERE 
            trang_thai = 'DA_PHE_DUYET'
            AND is_deleted = FALSE;
    """)