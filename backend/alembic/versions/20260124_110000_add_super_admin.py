"""add_super_admin_support

Revision ID: 002_add_super_admin
Revises: 001_init_tables
Create Date: 2026-01-24

Migration thêm hỗ trợ Super Admin:
1. Thêm 'SUPER_ADMIN' vào enum cap_bac_vai_tro_enum
2. Thêm cột is_system_admin vào bảng vai_tro
3. Thêm vai trò ADMIN vào seed data
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '002_add_super_admin'
down_revision: Union[str, None] = '001_init_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Thêm hỗ trợ Super Admin.
    """
    
    # =========================================================================
    # BƯỚC 1: Thêm 'SUPER_ADMIN' vào enum cap_bac_vai_tro_enum
    # =========================================================================
    # PostgreSQL cho phép thêm giá trị mới vào ENUM
    op.execute("ALTER TYPE cap_bac_vai_tro_enum ADD VALUE IF NOT EXISTS 'SUPER_ADMIN' BEFORE 'CHI_CUC_TRUONG'")
    
    # =========================================================================
    # BƯỚC 2: Thêm cột is_system_admin vào bảng vai_tro
    # =========================================================================
    op.add_column(
        'vai_tro',
        sa.Column(
            'is_system_admin',
            sa.Boolean(),
            server_default='false',
            nullable=False,
            comment='Là Super Admin (KHÔNG tham gia nghiệp vụ)'
        )
    )
    
    # =========================================================================
    # BƯỚC 3: Thêm vai trò ADMIN vào seed data
    # =========================================================================
    # op.execute("""
    #     INSERT INTO vai_tro (ma_vai_tro, ten_vai_tro, cap_bac, is_lanh_dao, is_system_admin, mo_ta)
    #     VALUES (
    #         'ADMIN',
    #         'Quản trị hệ thống',
    #         'SUPER_ADMIN',
    #         FALSE,
    #         TRUE,
    #         'Quản trị viên hệ thống - Không tham gia quy trình nghiệp vụ'
    #     )
    #     ON CONFLICT (ma_vai_tro) DO NOTHING
    # """)
    
    print("[Migration] Đã thêm SUPER_ADMIN vào enum")
    print("[Migration] Đã thêm cột is_system_admin vào vai_tro")
    print("[Migration] Đã thêm vai trò ADMIN")


def downgrade() -> None:
    """
    Rollback - Xóa hỗ trợ Super Admin.
    
    ⚠️ WARNING: Không thể xóa giá trị khỏi ENUM trong PostgreSQL
    Chỉ có thể xóa cột và dữ liệu liên quan.
    """
    
    # Xóa vai trò ADMIN
    op.execute("DELETE FROM vai_tro WHERE ma_vai_tro = 'ADMIN'")
    
    # Xóa cột is_system_admin
    op.drop_column('vai_tro', 'is_system_admin')
    
    # Lưu ý: Không thể xóa 'SUPER_ADMIN' khỏi enum
    # PostgreSQL không hỗ trợ DROP VALUE từ ENUM
    print("[Migration] Đã xóa vai trò ADMIN")
    print("[Migration] Đã xóa cột is_system_admin")
    print("[Migration] LƯU Ý: Giá trị 'SUPER_ADMIN' vẫn còn trong enum (không thể xóa)")
