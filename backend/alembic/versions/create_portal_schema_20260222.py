"""Create portal schema — Module Trang chu / CMS / ECM

Revision ID: create_portal_schema_20260222
Revises: create_legal_schema_20260222
Create Date: 2026-02-22

Tao schema portal voi 4 bang:
  1. chuyen_muc — Chuyen muc tin tuc (4 loai seed)
  2. thu_muc    — Thu muc tai lieu ECM (5 muc seed)
  3. bai_viet   — Tin tuc / Bai viet (workflow duyet)
  4. tai_lieu   — Tai lieu ECM (versioning)

Indexes: 5 custom indexes
Seed data: 4 chuyen muc + 5 thu muc
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'create_portal_schema_20260222'
down_revision = 'create_legal_schema_20260222'
branch_labels = None
depends_on = None


def upgrade():
    # 1. Tao schema va cap quyen
    op.execute("CREATE SCHEMA IF NOT EXISTS portal")
    op.execute("GRANT ALL ON SCHEMA portal TO postgres")

    # 2. Bang chuyen_muc — Chuyen muc tin tuc
    op.create_table(
        'chuyen_muc',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column('ten', sa.String(200), nullable=False),
        sa.Column('slug', sa.String(200), nullable=False),
        sa.Column('mo_ta', sa.Text(), nullable=True),
        sa.Column('thu_tu', sa.Integer(), server_default='0'),
        sa.Column(
            'loai',
            sa.String(50),
            server_default='TIN_TUC',
            nullable=False,
        ),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column(
            'created_at',
            sa.TIMESTAMP(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.UniqueConstraint('slug', name='uq_portal_chuyen_muc_slug'),
        schema='portal',
    )

    # Seed data 4 chuyen muc theo spec
    op.execute("""
        INSERT INTO portal.chuyen_muc (ten, slug, loai, thu_tu) VALUES
        ('Tin chỉ đạo', 'tin-chi-dao', 'CHI_DAO', 1),
        ('Thông báo', 'thong-bao', 'THONG_BAO', 2),
        ('Tin hoạt động', 'tin-hoat-dong', 'TIN_TUC', 3),
        ('Cập nhật pháp luật', 'cap-nhat-phap-luat', 'LEGAL_UPDATE', 4)
    """)

    # 3. Bang thu_muc — Thu muc tai lieu ECM (self-reference)
    op.create_table(
        'thu_muc',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column('ten', sa.String(200), nullable=False),
        sa.Column(
            'parent_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('portal.thu_muc.id'),
            nullable=True,
        ),
        sa.Column('thu_tu', sa.Integer(), server_default='0'),
        sa.Column(
            'quyen_truy_cap',
            sa.String(50),
            server_default='TAT_CA',
            nullable=False,
        ),
        sa.Column(
            'don_vi_ids',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            'created_by',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('public.cong_chuc.id'),
            nullable=True,
        ),
        sa.Column(
            'created_at',
            sa.TIMESTAMP(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        schema='portal',
    )

    # Seed data 5 thu muc theo spec
    op.execute("""
        INSERT INTO portal.thu_muc (ten, thu_tu) VALUES
        ('Văn bản nội bộ', 1),
        ('Tài liệu đào tạo', 2),
        ('Biểu mẫu', 3),
        ('Quy trình nghiệp vụ', 4),
        ('Tài liệu tham khảo', 5)
    """)

    # 4. Bang bai_viet — Tin tuc / Bai viet
    op.create_table(
        'bai_viet',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            'chuyen_muc_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('portal.chuyen_muc.id'),
            nullable=True,
        ),
        sa.Column('tieu_de', sa.String(500), nullable=False),
        sa.Column('tom_tat', sa.Text(), nullable=True),
        sa.Column('noi_dung', sa.Text(), nullable=False),
        sa.Column('anh_dai_dien', sa.Text(), nullable=True),
        sa.Column(
            'trang_thai',
            sa.String(50),
            server_default='NHAP',
            nullable=False,
        ),
        sa.Column(
            'nguoi_soan_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('public.cong_chuc.id'),
            nullable=True,
        ),
        sa.Column(
            'nguoi_kiem_tra_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('public.cong_chuc.id'),
            nullable=True,
        ),
        sa.Column(
            'nguoi_duyet_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('public.cong_chuc.id'),
            nullable=True,
        ),
        sa.Column('ngay_xuat_ban', sa.TIMESTAMP(), nullable=True),
        sa.Column('is_ghim', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('so_luot_xem', sa.Integer(), server_default='0'),
        sa.Column(
            'created_at',
            sa.TIMESTAMP(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            'updated_at',
            sa.TIMESTAMP(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column('is_deleted', sa.Boolean(), server_default='false', nullable=False),
        schema='portal',
    )

    # 5. Bang tai_lieu — Tai lieu ECM
    op.create_table(
        'tai_lieu',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column('ten_tai_lieu', sa.String(300), nullable=False),
        sa.Column('mo_ta', sa.Text(), nullable=True),
        sa.Column(
            'thu_muc_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('portal.thu_muc.id'),
            nullable=True,
        ),
        sa.Column('file_url', sa.Text(), nullable=False),
        sa.Column('file_name', sa.String(300), nullable=True),
        sa.Column('file_size_bytes', sa.BigInteger(), nullable=True),
        sa.Column('file_type', sa.String(50), nullable=True),
        sa.Column('phien_ban', sa.Integer(), server_default='1', nullable=False),
        sa.Column(
            'phien_ban_truoc_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('portal.tai_lieu.id'),
            nullable=True,
        ),
        sa.Column(
            'tags',
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            'metadata',
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            'quyen_truy_cap',
            sa.String(50),
            server_default='TAT_CA',
            nullable=False,
        ),
        sa.Column(
            'don_vi_ids',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            'nguoi_tai_len_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('public.cong_chuc.id'),
            nullable=True,
        ),
        sa.Column(
            'created_at',
            sa.TIMESTAMP(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column('is_deleted', sa.Boolean(), server_default='false', nullable=False),
        schema='portal',
    )

    # 6. INDEXES theo spec PORTAL_COMMON_DATABASE_DESIGN.md

    # bai_viet indexes
    op.create_index('idx_portal_bv_cm', 'bai_viet', ['chuyen_muc_id'], schema='portal')
    op.create_index('idx_portal_bv_tt', 'bai_viet', ['trang_thai'], schema='portal')
    op.create_index(
        'idx_portal_bv_xb',
        'bai_viet',
        [sa.text('ngay_xuat_ban DESC')],
        schema='portal',
    )

    # tai_lieu indexes
    op.create_index('idx_portal_tl_tm', 'tai_lieu', ['thu_muc_id'], schema='portal')
    op.create_index(
        'idx_portal_tl_tags',
        'tai_lieu',
        ['tags'],
        schema='portal',
        postgresql_using='gin',
    )


def downgrade():
    # Xoa indexes truoc
    op.drop_index('idx_portal_tl_tags', table_name='tai_lieu', schema='portal')
    op.drop_index('idx_portal_tl_tm', table_name='tai_lieu', schema='portal')
    op.drop_index('idx_portal_bv_xb', table_name='bai_viet', schema='portal')
    op.drop_index('idx_portal_bv_tt', table_name='bai_viet', schema='portal')
    op.drop_index('idx_portal_bv_cm', table_name='bai_viet', schema='portal')

    # Xoa cac bang theo thu tu nguoc (con truoc, cha sau)
    op.drop_table('tai_lieu', schema='portal')
    op.drop_table('bai_viet', schema='portal')
    op.drop_table('thu_muc', schema='portal')
    op.drop_table('chuyen_muc', schema='portal')

    # KHONG drop schema — cac migration khac co the dung chung schema portal
