"""
Fix so_sp_chat_luong và so_sp_tien_do calculation for approved ke_khai

Revision ID: fix_sp_cl_td_20260131
Revises: admin_001_lich_su_dieu_chuyen
Create Date: 2026-01-31

Mô tả:
- Cập nhật lại so_sp_chat_luong và so_sp_tien_do cho các kê khai đã phê duyệt
- Sửa công thức từ: SP_đạt = SP_gốc - số_lỗi (SAI)
- Thành công thức đúng: SP_đạt = SP_gốc - (0.25 × min(Lỗi, SL×4) × SP_per_unit)
- Theo BUSINESS_RULES_FINAL.md - Mục 5.1: Mỗi lỗi trừ 25% của 1 đơn vị SP
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'fix_sp_cl_td_20260131'  # ≤32 ký tự
down_revision = 'admin_001_lich_su_dieu_chuyen'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Cập nhật so_sp_chat_luong và so_sp_tien_do với công thức đúng.
    
    Công thức (theo BUSINESS_RULES_FINAL.md):
    SP_đạt = SP_gốc - (0.25 × min(so_loi, so_luong × 4) × (SP_gốc / so_luong))
    
    Giải thích:
    - sp_per_unit = so_sp_goc / so_luong (SP cho 1 đơn vị công việc)
    - max_loi = so_luong × 4 (tối đa 4 lần lỗi/đơn vị = trừ 100%)
    - loi_tinh = min(so_loi, max_loi)
    - sp_tru = 0.25 × loi_tinh × sp_per_unit
    - SP_đạt = max(so_sp_goc - sp_tru, 0)
    
    Ví dụ:
    - 5 Quyết định × hệ số 96 = 480 SP, 8 lỗi CL
    - sp_per_unit = 480/5 = 96
    - sp_tru = 0.25 × 8 × 96 = 192
    - so_sp_chat_luong = 480 - 192 = 288 ✓
    """
    
    # Cập nhật với công thức đúng
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
    Rollback: Khôi phục về công thức cũ (SAI - không khuyến khích)
    Công thức cũ: SP_đạt = SP_gốc - so_loi (trừ trực tiếp số lỗi)
    
    WARNING: Công thức cũ là SAI theo Business Rules!
    """
    op.execute("""
        UPDATE ke_khai_cong_viec
        SET 
            so_sp_chat_luong = GREATEST(
                so_sp_goc_quy_doi - COALESCE(so_loi_chat_luong, 0),
                0
            ),
            so_sp_tien_do = GREATEST(
                so_sp_goc_quy_doi - COALESCE(so_loi_tien_do, 0),
                0
            ),
            updated_at = CURRENT_TIMESTAMP
        WHERE 
            trang_thai = 'DA_PHE_DUYET'
            AND is_deleted = FALSE
            AND so_sp_goc_quy_doi IS NOT NULL;
    """)