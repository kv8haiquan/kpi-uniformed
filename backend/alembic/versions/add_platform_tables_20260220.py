"""
Migration: Thêm 3 bảng platform vào schema public
Author: Platform Team
Date: 2026-02-20

Bảng mới:
1. public.platform_role — Vai trò bổ sung cho nền tảng mở rộng
2. public.cong_chuc_platform_role — Gán vai trò platform cho công chức
3. public.platform_config — Cấu hình key-value cho platform

Seed data: 7 platform roles (GIANG_VIEN, QT_DAO_TAO, BIEN_TAP, ...)

Tham chiếu: docs/shared/SHARED_DB_REFERENCE.md (mục 4)
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


# Revision identifiers
revision = 'add_platform_tables_20260220'
down_revision = 'add_tu_choi_tc_v350_20260202'
branch_labels = None
depends_on = None


def upgrade():
    # =========================================================================
    # 1. platform_role — Vai trò bổ sung cho nền tảng
    # =========================================================================
    op.create_table(
        'platform_role',
        sa.Column('id', UUID(), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('ma_role', sa.String(50), nullable=False, unique=True),
        sa.Column('ten_role', sa.String(100), nullable=False),
        sa.Column('mo_ta', sa.Text(), nullable=True),
        sa.Column('quyen_han', JSONB(), server_default=sa.text("'{}'::jsonb"), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        schema='public',
    )

    # =========================================================================
    # 2. cong_chuc_platform_role — Gán vai trò platform cho công chức
    # =========================================================================
    op.create_table(
        'cong_chuc_platform_role',
        sa.Column('id', UUID(), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('cong_chuc_id', UUID(), sa.ForeignKey('public.cong_chuc.id'), nullable=False),
        sa.Column('platform_role_id', UUID(), sa.ForeignKey('public.platform_role.id'), nullable=False),
        sa.Column('pham_vi', JSONB(), nullable=True),
        sa.Column('assigned_by', UUID(), sa.ForeignKey('public.cong_chuc.id'), nullable=True),
        sa.Column('assigned_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.UniqueConstraint('cong_chuc_id', 'platform_role_id', name='uq_cc_platform_role'),
        schema='public',
    )

    # Index cho cong_chuc_platform_role
    op.create_index(
        'idx_cc_platform_role_cong_chuc_id',
        'cong_chuc_platform_role',
        ['cong_chuc_id'],
        schema='public',
    )
    op.create_index(
        'idx_cc_platform_role_platform_role_id',
        'cong_chuc_platform_role',
        ['platform_role_id'],
        schema='public',
    )

    # =========================================================================
    # 3. platform_config — Cấu hình key-value cho platform
    # =========================================================================
    op.create_table(
        'platform_config',
        sa.Column('key', sa.String(100), primary_key=True),
        sa.Column('value', JSONB(), nullable=False),
        sa.Column('mo_ta', sa.Text(), nullable=True),
        sa.Column('updated_by', UUID(), sa.ForeignKey('public.cong_chuc.id'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        schema='public',
    )

    # =========================================================================
    # 4. Seed data — 7 platform roles
    # =========================================================================
    op.execute("""
        INSERT INTO public.platform_role (ma_role, ten_role, mo_ta) VALUES
        ('GIANG_VIEN',      'Giảng viên nội bộ',              'Giảng viên kiêm nhiệm trong hệ thống đào tạo (LMS)'),
        ('QT_DAO_TAO',      'Quản trị đào tạo',               'Quản lý khóa học, chương trình đào tạo (LMS)'),
        ('BIEN_TAP',        'Biên tập viên',                   'Biên tập nội dung văn bản pháp luật và portal'),
        ('DIEU_PHOI_FORUM', 'Điều phối diễn đàn',             'Quản lý chuyên mục, duyệt bài viết diễn đàn'),
        ('CHUYEN_GIA',      'Chuyên gia trả lời',             'Chuyên gia nghiệp vụ trả lời trên diễn đàn'),
        ('QT_NOI_DUNG',     'Quản trị nội dung',              'Quản lý tin tức, tài liệu trên portal'),
        ('QT_ATTT',         'Quản trị an toàn thông tin',     'Quản trị bảo mật, phân quyền toàn hệ thống')
    """)


def downgrade():
    # Xóa theo thứ tự ngược (tránh lỗi FK)
    op.drop_table('platform_config', schema='public')

    op.drop_index('idx_cc_platform_role_platform_role_id', table_name='cong_chuc_platform_role', schema='public')
    op.drop_index('idx_cc_platform_role_cong_chuc_id', table_name='cong_chuc_platform_role', schema='public')
    op.drop_table('cong_chuc_platform_role', schema='public')

    op.drop_table('platform_role', schema='public')
