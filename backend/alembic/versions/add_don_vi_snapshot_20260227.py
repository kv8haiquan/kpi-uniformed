"""Add don_vi_id_snapshot to DanhGiaThang and KeKhaiCongViec

Revision ID: add_don_vi_snapshot_20260227
Revises: create_forum_schema_20260225
Create Date: 2026-02-27

Purpose:
  Fix bug: when Admin transfers a staff member from Unit A to Unit B,
  historical records should remain tied to the original unit in reports.

Changes:
  1. Add don_vi_id_snapshot column to danh_gia_thang (nullable UUID FK to don_vi)
  2. Add don_vi_id_snapshot column to ke_khai_cong_viec (nullable UUID FK to don_vi)
  3. Add indexes on (don_vi_id_snapshot, thang, nam) for both tables
  4. Backfill existing records with current don_vi_id from cong_chuc
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'add_don_vi_snapshot_20260227'
down_revision = 'create_forum_schema_20260225'
branch_labels = None
depends_on = None


def upgrade():
    # ===================================================================
    # 1. Add don_vi_id_snapshot to danh_gia_thang
    # ===================================================================
    op.add_column(
        'danh_gia_thang',
        sa.Column(
            'don_vi_id_snapshot',
            postgresql.UUID(as_uuid=True),
            nullable=True,
            comment='Snapshot đơn vị tại thời điểm đánh giá (dùng cho báo cáo)'
        )
    )

    # Add foreign key constraint
    op.create_foreign_key(
        'fk_danh_gia_thang_don_vi_snapshot',
        'danh_gia_thang',
        'don_vi',
        ['don_vi_id_snapshot'],
        ['id'],
        ondelete='RESTRICT'
    )

    # Add index
    op.create_index(
        'idx_danh_gia_don_vi_snapshot',
        'danh_gia_thang',
        ['don_vi_id_snapshot', 'thang', 'nam']
    )

    # Backfill existing records
    op.execute("""
        UPDATE danh_gia_thang
        SET don_vi_id_snapshot = (
            SELECT don_vi_id
            FROM cong_chuc
            WHERE cong_chuc.id = danh_gia_thang.cong_chuc_id
        )
        WHERE don_vi_id_snapshot IS NULL
    """)

    # ===================================================================
    # 2. Add don_vi_id_snapshot to ke_khai_cong_viec
    # ===================================================================
    op.add_column(
        'ke_khai_cong_viec',
        sa.Column(
            'don_vi_id_snapshot',
            postgresql.UUID(as_uuid=True),
            nullable=True,
            comment='Snapshot đơn vị tại thời điểm kê khai (dùng cho báo cáo)'
        )
    )

    # Add foreign key constraint
    op.create_foreign_key(
        'fk_ke_khai_cong_viec_don_vi_snapshot',
        'ke_khai_cong_viec',
        'don_vi',
        ['don_vi_id_snapshot'],
        ['id'],
        ondelete='RESTRICT'
    )

    # Add index
    op.create_index(
        'idx_ke_khai_don_vi_snapshot',
        'ke_khai_cong_viec',
        ['don_vi_id_snapshot', 'thang', 'nam']
    )

    # Backfill existing records
    op.execute("""
        UPDATE ke_khai_cong_viec
        SET don_vi_id_snapshot = (
            SELECT don_vi_id
            FROM cong_chuc
            WHERE cong_chuc.id = ke_khai_cong_viec.cong_chuc_id
        )
        WHERE don_vi_id_snapshot IS NULL
    """)


def downgrade():
    # Drop indexes
    op.drop_index('idx_ke_khai_don_vi_snapshot', table_name='ke_khai_cong_viec')
    op.drop_index('idx_danh_gia_don_vi_snapshot', table_name='danh_gia_thang')

    # Drop foreign key constraints
    op.drop_constraint('fk_ke_khai_cong_viec_don_vi_snapshot', 'ke_khai_cong_viec', type_='foreignkey')
    op.drop_constraint('fk_danh_gia_thang_don_vi_snapshot', 'danh_gia_thang', type_='foreignkey')

    # Drop columns
    op.drop_column('ke_khai_cong_viec', 'don_vi_id_snapshot')
    op.drop_column('danh_gia_thang', 'don_vi_id_snapshot')
