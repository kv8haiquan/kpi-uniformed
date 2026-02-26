"""Them vai tro QLDV (Quan ly Don vi) — read-only TDV + tra lai + export

Revision ID: them_vai_tro_qldv_20260225
Revises: create_common_schema_20260224
Create Date: 2026-02-25

Them:
  1. Gia tri enum 'QUAN_LY_DON_VI' vao cap_bac_vai_tro_enum
  2. Ban ghi vai_tro moi: QLDV (Quan ly Don vi)
"""
from alembic import op
import sqlalchemy as sa

revision = 'them_vai_tro_qldv_20260225'
down_revision = 'create_common_schema_20260224'
branch_labels = None
depends_on = None


def upgrade():
    # 1. Them gia tri enum moi vao cap_bac_vai_tro_enum
    # Luu y: ALTER TYPE ... ADD VALUE khong the chay trong transaction block
    # nen phai commit truoc khi INSERT
    op.execute("ALTER TYPE cap_bac_vai_tro_enum ADD VALUE IF NOT EXISTS 'QUAN_LY_DON_VI'")

    # 2. Insert vai tro QLDV
    op.execute("""
        INSERT INTO vai_tro (id, ma_vai_tro, ten_vai_tro, cap_bac, mo_ta, is_lanh_dao, is_system_admin, is_active, created_at, updated_at)
        VALUES (
            gen_random_uuid(),
            'QLDV',
            'Quản lý Đơn vị',
            'QUAN_LY_DON_VI',
            'Quản lý đơn vị: xem kê khai, đánh giá, xếp loại của đơn vị; trả lại kê khai; xuất báo cáo. KHÔNG có quyền phê duyệt.',
            FALSE,
            FALSE,
            TRUE,
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP
        )
        ON CONFLICT (ma_vai_tro) DO NOTHING
    """)


def downgrade():
    # Xoa vai tro QLDV
    op.execute("DELETE FROM vai_tro WHERE ma_vai_tro = 'QLDV'")
    # Khong the xoa enum value trong PostgreSQL nen chi xoa ban ghi
