"""
add ghi_chu_loi columns to ke_khai_lanh_dao AND ke_khai_cong_viec

Revision ID: add_ghi_chu_loi_v274_20260202
Revises: drop_uq_ke_khai_20260201
Create Date: 2026-02-02

v2.7.4: Thêm các column mô tả lỗi:
- ke_khai_lanh_dao: +2 columns (ghi_chu_loi_chat_luong, ghi_chu_loi_tien_do)
- ke_khai_cong_viec: +4 columns (ghi_chu_tu_dg_chat_luong, ghi_chu_tu_dg_tien_do,
                                  ghi_chu_loi_chat_luong, ghi_chu_loi_tien_do)

LƯU Ý: Migration này THAY THẾ add_ghi_chu_loi_kkld_20260202 (chỉ cho lãnh đạo).
Nếu đã chạy migration cũ, cần rollback trước rồi chạy migration mới này.
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = 'add_ghi_chu_loi_v274_20260202'
down_revision = 'drop_uq_ke_khai_20260201'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # =========================================================================
    # BẢNG 1: ke_khai_lanh_dao (Lãnh đạo tự nhập khi kê khai)
    # =========================================================================
    
    # Mô tả lỗi chất lượng
    op.add_column(
        'ke_khai_lanh_dao',
        sa.Column(
            'ghi_chu_loi_chat_luong',
            sa.Text(),
            nullable=True,
            comment='Mô tả / giải trình lỗi chất lượng'
        )
    )
    
    # Mô tả lỗi tiến độ
    op.add_column(
        'ke_khai_lanh_dao',
        sa.Column(
            'ghi_chu_loi_tien_do',
            sa.Text(),
            nullable=True,
            comment='Mô tả / giải trình lỗi tiến độ'
        )
    )
    
    # =========================================================================
    # BẢNG 2: ke_khai_cong_viec (Công chức)
    # =========================================================================
    
    # --- Mô tả lỗi TỰ ĐÁNH GIÁ (CC tự nhập khi kê khai) ---
    
    # Mô tả lỗi CL tự đánh giá
    op.add_column(
        'ke_khai_cong_viec',
        sa.Column(
            'ghi_chu_tu_dg_chat_luong',
            sa.Text(),
            nullable=True,
            comment='Mô tả lỗi chất lượng do CC tự đánh giá'
        )
    )
    
    # Mô tả lỗi TĐ tự đánh giá
    op.add_column(
        'ke_khai_cong_viec',
        sa.Column(
            'ghi_chu_tu_dg_tien_do',
            sa.Text(),
            nullable=True,
            comment='Mô tả lỗi tiến độ do CC tự đánh giá'
        )
    )
    
    # --- Mô tả lỗi LÃNH ĐẠO CHỐT (LĐ nhập khi phê duyệt) ---
    
    # Mô tả lỗi CL lãnh đạo chốt
    op.add_column(
        'ke_khai_cong_viec',
        sa.Column(
            'ghi_chu_loi_chat_luong',
            sa.Text(),
            nullable=True,
            comment='Mô tả lỗi chất lượng do lãnh đạo chốt'
        )
    )
    
    # Mô tả lỗi TĐ lãnh đạo chốt
    op.add_column(
        'ke_khai_cong_viec',
        sa.Column(
            'ghi_chu_loi_tien_do',
            sa.Text(),
            nullable=True,
            comment='Mô tả lỗi tiến độ do lãnh đạo chốt'
        )
    )


def downgrade() -> None:
    # Bảng ke_khai_cong_viec
    op.drop_column('ke_khai_cong_viec', 'ghi_chu_loi_tien_do')
    op.drop_column('ke_khai_cong_viec', 'ghi_chu_loi_chat_luong')
    op.drop_column('ke_khai_cong_viec', 'ghi_chu_tu_dg_tien_do')
    op.drop_column('ke_khai_cong_viec', 'ghi_chu_tu_dg_chat_luong')
    
    # Bảng ke_khai_lanh_dao
    op.drop_column('ke_khai_lanh_dao', 'ghi_chu_loi_tien_do')
    op.drop_column('ke_khai_lanh_dao', 'ghi_chu_loi_chat_luong')