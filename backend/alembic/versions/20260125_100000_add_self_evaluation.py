"""add_self_evaluation_columns

Revision ID: 003_add_self_evaluation
Revises: 002_add_super_admin
Create Date: 2026-01-25

Migration thêm chức năng tự đánh giá lỗi của công chức:
1. tu_danh_gia_chat_luong: Số lỗi CL do CC tự đánh giá
2. tu_danh_gia_tien_do: Số lần chậm tiến độ do CC tự đánh giá
3. ghi_chu_tu_danh_gia: Giải trình của CC
4. so_loi_chat_luong: Số lỗi CL chốt cuối (lãnh đạo xác nhận)
5. so_loi_tien_do: Số lỗi TĐ chốt cuối (lãnh đạo xác nhận)
6. y_kien_lanh_dao: Ý kiến phản hồi của lãnh đạo khi duyệt
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '003_add_self_evaluation'
down_revision: Union[str, None] = '002_add_super_admin'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Thêm các cột tự đánh giá và số lỗi chốt cuối.
    """
    
    # =========================================================================
    # BƯỚC 1: Thêm các cột TỰ ĐÁNH GIÁ CỦA CÔNG CHỨC
    # =========================================================================
    
    op.add_column(
        'ke_khai_cong_viec',
        sa.Column(
            'tu_danh_gia_chat_luong',
            sa.Integer(),
            server_default='0',
            nullable=False,
            comment='Số lỗi chất lượng do CC tự đánh giá'
        )
    )
    
    op.add_column(
        'ke_khai_cong_viec',
        sa.Column(
            'tu_danh_gia_tien_do',
            sa.Integer(),
            server_default='0',
            nullable=False,
            comment='Số lần chậm tiến độ do CC tự đánh giá'
        )
    )
    
    op.add_column(
        'ke_khai_cong_viec',
        sa.Column(
            'ghi_chu_tu_danh_gia',
            sa.Text(),
            nullable=True,
            comment='Giải trình của CC về lỗi tự đánh giá'
        )
    )
    
    # =========================================================================
    # BƯỚC 2: Thêm các cột SỐ LỖI CHỐT CUỐI (Lãnh đạo xác nhận)
    # =========================================================================
    
    op.add_column(
        'ke_khai_cong_viec',
        sa.Column(
            'so_loi_chat_luong',
            sa.Integer(),
            server_default='0',
            nullable=False,
            comment='Số lỗi CL chốt cuối (do lãnh đạo xác nhận)'
        )
    )
    
    op.add_column(
        'ke_khai_cong_viec',
        sa.Column(
            'so_loi_tien_do',
            sa.Integer(),
            server_default='0',
            nullable=False,
            comment='Số lỗi TĐ chốt cuối (do lãnh đạo xác nhận)'
        )
    )
    
    op.add_column(
        'ke_khai_cong_viec',
        sa.Column(
            'y_kien_lanh_dao',
            sa.Text(),
            nullable=True,
            comment='Ý kiến phản hồi của lãnh đạo khi duyệt'
        )
    )
    
    # =========================================================================
    # BƯỚC 3: Thêm CHECK CONSTRAINTS cho các cột số lỗi
    # =========================================================================
    
    op.create_check_constraint(
        'ck_ke_khai_tu_dg_cl',
        'ke_khai_cong_viec',
        'tu_danh_gia_chat_luong >= 0'
    )
    
    op.create_check_constraint(
        'ck_ke_khai_tu_dg_td',
        'ke_khai_cong_viec',
        'tu_danh_gia_tien_do >= 0'
    )
    
    op.create_check_constraint(
        'ck_ke_khai_loi_cl',
        'ke_khai_cong_viec',
        'so_loi_chat_luong >= 0'
    )
    
    op.create_check_constraint(
        'ck_ke_khai_loi_td',
        'ke_khai_cong_viec',
        'so_loi_tien_do >= 0'
    )
    
    print("[Migration] Đã thêm 6 cột mới vào ke_khai_cong_viec:")
    print("  - tu_danh_gia_chat_luong (CC tự đánh giá)")
    print("  - tu_danh_gia_tien_do (CC tự đánh giá)")
    print("  - ghi_chu_tu_danh_gia (Giải trình CC)")
    print("  - so_loi_chat_luong (Lãnh đạo chốt)")
    print("  - so_loi_tien_do (Lãnh đạo chốt)")
    print("  - y_kien_lanh_dao (Ý kiến lãnh đạo)")


def downgrade() -> None:
    """
    Rollback - Xóa các cột tự đánh giá.
    """
    
    # Xóa constraints trước
    op.drop_constraint('ck_ke_khai_tu_dg_cl', 'ke_khai_cong_viec', type_='check')
    op.drop_constraint('ck_ke_khai_tu_dg_td', 'ke_khai_cong_viec', type_='check')
    op.drop_constraint('ck_ke_khai_loi_cl', 'ke_khai_cong_viec', type_='check')
    op.drop_constraint('ck_ke_khai_loi_td', 'ke_khai_cong_viec', type_='check')
    
    # Xóa các cột
    op.drop_column('ke_khai_cong_viec', 'y_kien_lanh_dao')
    op.drop_column('ke_khai_cong_viec', 'so_loi_tien_do')
    op.drop_column('ke_khai_cong_viec', 'so_loi_chat_luong')
    op.drop_column('ke_khai_cong_viec', 'ghi_chu_tu_danh_gia')
    op.drop_column('ke_khai_cong_viec', 'tu_danh_gia_tien_do')
    op.drop_column('ke_khai_cong_viec', 'tu_danh_gia_chat_luong')
    
    print("[Migration] Đã xóa 6 cột tự đánh giá khỏi ke_khai_cong_viec")
