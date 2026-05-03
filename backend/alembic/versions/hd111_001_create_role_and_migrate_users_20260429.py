"""HD_111 — tạo vai trò và migrate 109 user (29/04/2026)

Revision ID: hd111_001_create_20260429
Revises: pl3_v2_009_ma_30_20260428
Create Date: 2026-04-29

Phase 3 — HĐ 111 dùng form lãnh đạo (ke_khai_lanh_dao), không có d/đ/e.

Thay đổi:
  1. Insert vai_tro mới: HD_111 (cap_bac=CONG_CHUC, is_lanh_dao=FALSE)
  2. Cập nhật vai_tro_id cho 109 user có chuc_vu='Hợp đồng 111'
     (đã verify trên DB test: chính xác 1 pattern duy nhất, 109 row)

Idempotent: ON CONFLICT + WHERE để re-run an toàn.
"""
from alembic import op


revision = "hd111_001_create_20260429"
down_revision = "pl3_v2_009_ma_30_20260428"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Insert vai trò HD_111
    op.execute("""
        INSERT INTO vai_tro (
            id, ma_vai_tro, ten_vai_tro, cap_bac, mo_ta,
            is_lanh_dao, is_system_admin, is_active, created_at, updated_at
        )
        VALUES (
            gen_random_uuid(),
            'HD_111',
            'Hợp đồng 111',
            'CONG_CHUC',
            'Lao động hợp đồng theo Nghị định 111. Kê khai dùng form công việc đơn giản '
            '(giống lãnh đạo nhưng không có tiêu chí d/đ/e). Người phê duyệt do CC tự chọn.',
            FALSE,
            FALSE,
            TRUE,
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP
        )
        ON CONFLICT (ma_vai_tro) DO NOTHING
    """)

    # 2. Migrate 109 user: chuyển vai_tro_id sang HD_111
    #    Verify trên DB test: chuc_vu duy nhất = 'Hợp đồng 111' (109 row)
    op.execute("""
        UPDATE cong_chuc
        SET vai_tro_id = (SELECT id FROM vai_tro WHERE ma_vai_tro = 'HD_111'),
            updated_at = CURRENT_TIMESTAMP
        WHERE LOWER(TRIM(chuc_vu)) = 'hợp đồng 111'
          AND vai_tro_id <> (SELECT id FROM vai_tro WHERE ma_vai_tro = 'HD_111')
    """)


def downgrade() -> None:
    # Revert: chuyển HD_111 user về vai trò CC
    op.execute("""
        UPDATE cong_chuc
        SET vai_tro_id = (SELECT id FROM vai_tro WHERE ma_vai_tro = 'CC'),
            updated_at = CURRENT_TIMESTAMP
        WHERE vai_tro_id = (SELECT id FROM vai_tro WHERE ma_vai_tro = 'HD_111')
    """)
    # Xoá vai trò HD_111
    op.execute("DELETE FROM vai_tro WHERE ma_vai_tro = 'HD_111'")
