"""
add tu_choi_tc columns + update trang_thai_tc enum for v3.5.0

Revision ID: add_tu_choi_tc_v350_20260202
Revises: add_ghi_chu_loi_v274_20260202
Create Date: 2026-02-02

v3.5.0: Hỗ trợ từ chối tiêu chí chung:
1. Thêm 2 giá trị enum TrangThaiTieuChi: CHO_CAP2, TU_CHOI
2. Thêm 3 cột vào danh_gia_thang:
   - ly_do_tu_choi_tc (Text)
   - nguoi_tu_choi_tc_id (UUID FK → cong_chuc)
   - ngay_tu_choi_tc (DateTime with timezone)
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID as PG_UUID


# revision identifiers
revision = 'add_tu_choi_tc_v350_20260202'
down_revision = 'add_ghi_chu_loi_v274_20260202'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # =========================================================================
    # STEP 1: Cập nhật PostgreSQL enum 'trangthaitieuchi'
    # Thêm CHO_CAP2 và TU_CHOI
    # =========================================================================
    
    # PostgreSQL yêu cầu ALTER TYPE ... ADD VALUE
    # Tên enum trong DB: trang_thai_tieu_chi_enum (xem model: name="trang_thai_tieu_chi_enum")
    op.execute("ALTER TYPE trang_thai_tieu_chi_enum ADD VALUE IF NOT EXISTS 'CHO_CAP2'")
    op.execute("ALTER TYPE trang_thai_tieu_chi_enum ADD VALUE IF NOT EXISTS 'TU_CHOI'")
    
    # =========================================================================
    # STEP 2: Thêm 3 cột từ chối vào bảng danh_gia_thang
    # =========================================================================
    
    # Lý do từ chối
    op.add_column(
        'danh_gia_thang',
        sa.Column(
            'ly_do_tu_choi_tc',
            sa.Text(),
            nullable=True,
            comment='Lý do từ chối tiêu chí chung'
        )
    )
    
    # Người từ chối (FK → cong_chuc)
    op.add_column(
        'danh_gia_thang',
        sa.Column(
            'nguoi_tu_choi_tc_id',
            PG_UUID(as_uuid=True),
            nullable=True,
            comment='ID người từ chối tiêu chí chung'
        )
    )
    
    # Foreign key constraint
    op.create_foreign_key(
        'fk_danh_gia_thang_nguoi_tu_choi_tc',
        'danh_gia_thang',
        'cong_chuc',
        ['nguoi_tu_choi_tc_id'],
        ['id'],
        ondelete='SET NULL'
    )
    
    # Ngày từ chối
    op.add_column(
        'danh_gia_thang',
        sa.Column(
            'ngay_tu_choi_tc',
            sa.DateTime(timezone=True),
            nullable=True,
            comment='Thời điểm từ chối tiêu chí chung'
        )
    )


def downgrade() -> None:
    # Drop columns (reverse order)
    op.drop_column('danh_gia_thang', 'ngay_tu_choi_tc')
    
    op.drop_constraint(
        'fk_danh_gia_thang_nguoi_tu_choi_tc',
        'danh_gia_thang',
        type_='foreignkey'
    )
    op.drop_column('danh_gia_thang', 'nguoi_tu_choi_tc_id')
    
    op.drop_column('danh_gia_thang', 'ly_do_tu_choi_tc')
    
    # LƯU Ý: PostgreSQL KHÔNG hỗ trợ DROP VALUE từ enum.
    # Để xóa CHO_CAP2 và TU_CHOI, cần recreate enum thủ công.
    # Trong thực tế, thường để nguyên enum values khi downgrade.