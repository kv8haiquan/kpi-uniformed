"""Create common schema — Module dung chung (Thong bao, File, Knowledge Base, KPI Log)

Revision ID: create_common_schema_20260224
Revises: create_portal_schema_20260222
Create Date: 2026-02-24

Tao schema common voi 4 bang:
  1. thong_bao          — Notification Center (da module)
  2. file_storage       — Metadata file tren MinIO
  3. knowledge_base     — Kho SOP / FAQ + Full-text search
  4. kpi_integration_log — Tich hop diem KPI tu cac module

Indexes: 11 custom indexes (bao gom 2 GIN indexes)
Trigger: FTS trigger tren knowledge_base (search_vector tsvector)
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'create_common_schema_20260224'
down_revision = 'create_portal_schema_20260222'
branch_labels = None
depends_on = None


def upgrade():
    # 1. Tao schema va cap quyen
    op.execute("CREATE SCHEMA IF NOT EXISTS common")
    op.execute("GRANT ALL ON SCHEMA common TO postgres")

    # -------------------------------------------------------------------
    # 2. Bang thong_bao — Notification Center
    # -------------------------------------------------------------------
    op.create_table(
        'thong_bao',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            'nguoi_nhan_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('public.cong_chuc.id'),
            nullable=False,
        ),
        sa.Column('tieu_de', sa.String(300), nullable=False),
        sa.Column('noi_dung', sa.Text(), nullable=True),
        sa.Column('loai', sa.String(50), nullable=False),
        # 'KPI', 'LMS', 'FORUM', 'LEGAL', 'PORTAL', 'HE_THONG'
        sa.Column('link_url', sa.Text(), nullable=True),
        sa.Column('doi_tuong_type', sa.String(50), nullable=True),
        # 'KHOA_HOC', 'BAI_KIEM_TRA', 'CHU_DE', 'TRA_LOI', 'VAN_BAN', 'BAI_VIET'
        sa.Column('doi_tuong_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('da_doc', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('ngay_doc', sa.TIMESTAMP(), nullable=True),
        sa.Column(
            'muc_do',
            sa.String(20),
            server_default='BINH_THUONG',
            nullable=False,
        ),
        # 'KHAN', 'QUAN_TRONG', 'BINH_THUONG'
        sa.Column(
            'created_at',
            sa.TIMESTAMP(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        schema='common',
    )

    # -------------------------------------------------------------------
    # 3. Bang file_storage — Metadata file tren MinIO
    # -------------------------------------------------------------------
    op.create_table(
        'file_storage',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column('file_name', sa.String(500), nullable=False),
        sa.Column('file_path', sa.Text(), nullable=False),
        # "lms/videos/uuid.mp4"
        sa.Column('file_size_bytes', sa.BigInteger(), nullable=True),
        sa.Column('mime_type', sa.String(100), nullable=True),
        sa.Column('module', sa.String(50), nullable=False),
        # 'LMS', 'FORUM', 'LEGAL', 'PORTAL'
        sa.Column('doi_tuong_type', sa.String(50), nullable=True),
        # 'BAI_HOC', 'CHU_DE', 'VAN_BAN', 'BAI_VIET'
        sa.Column('doi_tuong_id', postgresql.UUID(as_uuid=True), nullable=True),
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
        schema='common',
    )

    # -------------------------------------------------------------------
    # 4. Bang knowledge_base — Kho SOP / FAQ
    # -------------------------------------------------------------------
    op.create_table(
        'knowledge_base',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column('loai', sa.String(20), nullable=False),
        # 'SOP', 'FAQ'
        sa.Column('tieu_de', sa.String(500), nullable=False),
        sa.Column('noi_dung', sa.Text(), nullable=False),
        # HTML/Markdown
        sa.Column(
            'chuyen_de',
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            'tags',
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            'chu_so_huu_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('public.cong_chuc.id'),
            nullable=True,
        ),
        sa.Column(
            'trang_thai',
            sa.String(50),
            server_default='NHAP',
            nullable=False,
        ),
        # 'NHAP', 'CHO_DUYET', 'DA_XUAT_BAN', 'CAN_CAP_NHAT'
        sa.Column(
            'van_ban_lien_quan',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        # Array IDs legal.van_ban
        sa.Column(
            'chu_de_forum_lien_quan',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        # Array IDs forum.chu_de
        sa.Column('phien_ban', sa.Integer(), server_default='1', nullable=False),
        sa.Column('ngay_cap_nhat_cuoi', sa.TIMESTAMP(), nullable=True),
        sa.Column(
            'search_vector',
            postgresql.TSVECTOR(),
            nullable=True,
        ),
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
        schema='common',
    )

    # -------------------------------------------------------------------
    # 5. Bang kpi_integration_log — Tich hop KPI
    # -------------------------------------------------------------------
    op.create_table(
        'kpi_integration_log',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            'cong_chuc_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('public.cong_chuc.id'),
            nullable=False,
        ),
        sa.Column(
            'thang',
            sa.Integer(),
            sa.CheckConstraint('thang BETWEEN 1 AND 12', name='ck_common_kpi_thang'),
            nullable=False,
        ),
        sa.Column(
            'nam',
            sa.Integer(),
            sa.CheckConstraint('nam >= 2025', name='ck_common_kpi_nam'),
            nullable=False,
        ),
        sa.Column('module', sa.String(50), nullable=False),
        # 'LMS', 'FORUM', 'LEGAL'
        sa.Column(
            'metrics',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column('diem_quy_doi', sa.Numeric(5, 2), nullable=True),
        sa.Column(
            'synced_at',
            sa.TIMESTAMP(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.UniqueConstraint(
            'cong_chuc_id', 'thang', 'nam', 'module',
            name='uq_common_kpi_cc_thang_nam_module',
        ),
        schema='common',
    )

    # -------------------------------------------------------------------
    # 6. INDEXES — 11 indexes theo spec
    # -------------------------------------------------------------------

    # Thong bao — 4 indexes
    op.create_index(
        'idx_common_tb_nn',
        'thong_bao',
        ['nguoi_nhan_id'],
        schema='common',
    )
    op.create_index(
        'idx_common_tb_chua_doc',
        'thong_bao',
        ['da_doc'],
        schema='common',
        postgresql_where=sa.text('da_doc = FALSE'),
    )
    op.create_index(
        'idx_common_tb_loai',
        'thong_bao',
        ['loai'],
        schema='common',
    )
    op.create_index(
        'idx_common_tb_time',
        'thong_bao',
        [sa.text('created_at DESC')],
        schema='common',
    )

    # File storage — 1 composite index
    op.create_index(
        'idx_common_fs_module',
        'file_storage',
        ['module', 'doi_tuong_type', 'doi_tuong_id'],
        schema='common',
    )

    # Knowledge base — 4 indexes (bao gom 2 GIN)
    op.create_index(
        'idx_common_kb_loai',
        'knowledge_base',
        ['loai'],
        schema='common',
    )
    op.create_index(
        'idx_common_kb_tags',
        'knowledge_base',
        ['tags'],
        schema='common',
        postgresql_using='gin',
    )
    op.create_index(
        'idx_common_kb_tt',
        'knowledge_base',
        ['trang_thai'],
        schema='common',
    )
    op.create_index(
        'idx_common_kb_search',
        'knowledge_base',
        ['search_vector'],
        schema='common',
        postgresql_using='gin',
    )

    # KPI integration — 2 indexes
    op.create_index(
        'idx_common_kpi_cc',
        'kpi_integration_log',
        ['cong_chuc_id', 'thang', 'nam'],
        schema='common',
    )
    op.create_index(
        'idx_common_kpi_module',
        'kpi_integration_log',
        ['module'],
        schema='common',
    )

    # -------------------------------------------------------------------
    # 7. Full-Text Search Trigger cho knowledge_base
    # -------------------------------------------------------------------
    op.execute("""
        CREATE OR REPLACE FUNCTION common.update_kb_search()
        RETURNS trigger AS $$
        BEGIN
            NEW.search_vector := to_tsvector('simple',
                COALESCE(NEW.tieu_de, '') || ' ' || COALESCE(NEW.noi_dung, ''));
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
    """)

    op.execute("""
        CREATE TRIGGER trg_common_kb_search
            BEFORE INSERT OR UPDATE ON common.knowledge_base
            FOR EACH ROW EXECUTE FUNCTION common.update_kb_search()
    """)


def downgrade():
    # 1. Drop trigger va function truoc
    op.execute("DROP TRIGGER IF EXISTS trg_common_kb_search ON common.knowledge_base")
    op.execute("DROP FUNCTION IF EXISTS common.update_kb_search()")

    # 2. Drop indexes (nguoc thu tu)
    op.drop_index('idx_common_kpi_module', table_name='kpi_integration_log', schema='common')
    op.drop_index('idx_common_kpi_cc', table_name='kpi_integration_log', schema='common')
    op.drop_index('idx_common_kb_search', table_name='knowledge_base', schema='common')
    op.drop_index('idx_common_kb_tt', table_name='knowledge_base', schema='common')
    op.drop_index('idx_common_kb_tags', table_name='knowledge_base', schema='common')
    op.drop_index('idx_common_kb_loai', table_name='knowledge_base', schema='common')
    op.drop_index('idx_common_fs_module', table_name='file_storage', schema='common')
    op.drop_index('idx_common_tb_time', table_name='thong_bao', schema='common')
    op.drop_index('idx_common_tb_loai', table_name='thong_bao', schema='common')
    op.drop_index('idx_common_tb_chua_doc', table_name='thong_bao', schema='common')
    op.drop_index('idx_common_tb_nn', table_name='thong_bao', schema='common')

    # 3. Drop tables (thu tu nguoc)
    op.drop_table('kpi_integration_log', schema='common')
    op.drop_table('knowledge_base', schema='common')
    op.drop_table('file_storage', schema='common')
    op.drop_table('thong_bao', schema='common')

    # KHONG drop schema — cac migration khac co the dung chung
