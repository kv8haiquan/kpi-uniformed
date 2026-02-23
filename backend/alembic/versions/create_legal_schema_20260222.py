"""Create legal schema — Module Pho bien Phap luat

Revision ID: create_legal_schema_20260222
Revises: add_pdf_url_bai_hoc_20260222
Create Date: 2026-02-22

Tao schema legal voi 6 bang:
  1. loai_van_ban  — Danh muc loai van ban (8 loai seed)
  2. van_ban       — Kho van ban phap luat (FTS + trigger)
  3. van_ban_lien_ket — Lien ket N:N giua cac van ban
  4. xac_nhan_doc  — Xac nhan da doc van ban
  5. quiz_van_ban  — Quiz kien thuc phap luat
  6. ket_qua_quiz  — Ket qua quiz

Indexes: 12 custom indexes + 1 GIN search_vector
FTS: tsvector trigger tren van_ban (so_hieu, trich_yeu, tom_tat, diem_moi)
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'create_legal_schema_20260222'
down_revision = 'add_pdf_url_bai_hoc_20260222'
branch_labels = None
depends_on = None


def upgrade():
    # 1. Tao schema va cap quyen
    op.execute("CREATE SCHEMA IF NOT EXISTS legal")
    op.execute("GRANT ALL ON SCHEMA legal TO postgres")

    # 2. Bang loai_van_ban — Danh muc loai van ban
    op.create_table(
        'loai_van_ban',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column('ma', sa.String(50), nullable=False),
        sa.Column('ten', sa.String(200), nullable=False),
        sa.Column('thu_tu', sa.Integer(), server_default='0'),
        sa.UniqueConstraint('ma', name='uq_loai_van_ban_ma'),
        schema='legal',
    )

    # Seed data 8 loai van ban theo spec
    op.execute("""
        INSERT INTO legal.loai_van_ban (ma, ten, thu_tu) VALUES
        ('LUAT', 'Luật', 1),
        ('NGHI_DINH', 'Nghị định', 2),
        ('THONG_TU', 'Thông tư', 3),
        ('QUYET_DINH', 'Quyết định', 4),
        ('CONG_VAN', 'Công văn', 5),
        ('CHI_THI', 'Chỉ thị', 6),
        ('HUONG_DAN', 'Hướng dẫn', 7),
        ('NOI_BO', 'Văn bản nội bộ', 8)
    """)

    # 3. Bang van_ban — Kho van ban phap luat
    # Tao truoc de van_ban_thay_the_id co the FK self-reference
    op.create_table(
        'van_ban',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        # Thong tin van ban
        sa.Column('so_hieu', sa.String(100), nullable=False),
        sa.Column('trich_yeu', sa.String(500), nullable=False),
        sa.Column(
            'loai_van_ban_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('legal.loai_van_ban.id'),
            nullable=True,
        ),
        # Co quan / ngay
        sa.Column('co_quan_ban_hanh', sa.String(200), nullable=True),
        sa.Column('ngay_ban_hanh', sa.Date(), nullable=True),
        sa.Column('ngay_hieu_luc', sa.Date(), nullable=True),
        sa.Column('ngay_het_hieu_luc', sa.Date(), nullable=True),
        # Hieu luc — VARCHAR(50) thay vi ENUM
        # CON_HIEU_LUC | HET_HIEU_LUC | BI_THAY_THE | DANG_SUA_DOI
        sa.Column(
            'trang_thai_hieu_luc',
            sa.String(50),
            server_default='CON_HIEU_LUC',
            nullable=False,
        ),
        # Self-reference: van ban thay the
        sa.Column(
            'van_ban_thay_the_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('legal.van_ban.id'),
            nullable=True,
        ),
        # Noi dung
        sa.Column('tom_tat', sa.Text(), nullable=True),
        sa.Column('noi_dung_html', sa.Text(), nullable=True),
        sa.Column('file_goc_url', sa.Text(), nullable=True),
        # Phan loai — JSONB
        sa.Column(
            'chuyen_de',
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            'doi_tuong_ap_dung',
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
        # Diem moi quy dinh
        sa.Column('diem_moi', sa.Text(), nullable=True),
        sa.Column('viec_can_lam', sa.Text(), nullable=True),
        # Muc do quan trong — VARCHAR(50)
        # KHAN | QUAN_TRONG | BINH_THUONG
        sa.Column(
            'muc_do',
            sa.String(50),
            server_default='BINH_THUONG',
            nullable=False,
        ),
        sa.Column('bat_buoc_doc', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('han_xac_nhan', sa.Date(), nullable=True),
        # Workflow duyet dang — NHAP | CHO_DUYET | DA_DUYET | DA_XUAT_BAN
        sa.Column(
            'nguoi_nhap_id',
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
        sa.Column(
            'trang_thai_duyet',
            sa.String(50),
            server_default='NHAP',
            nullable=False,
        ),
        sa.Column('ngay_xuat_ban', sa.TIMESTAMP(), nullable=True),
        # Versioning
        sa.Column('phien_ban', sa.Integer(), server_default='1', nullable=False),
        # Meta
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
        # Full-text search vector (se duoc cap nhat boi trigger)
        sa.Column('search_vector', postgresql.TSVECTOR(), nullable=True),
        schema='legal',
    )

    # 4. Bang van_ban_lien_ket — Lien ket N:N giua cac van ban
    op.create_table(
        'van_ban_lien_ket',
        sa.Column(
            'van_ban_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('legal.van_ban.id'),
            nullable=False,
        ),
        sa.Column(
            'van_ban_lien_quan_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('legal.van_ban.id'),
            nullable=False,
        ),
        # THAY_THE | BO_SUNG | HUONG_DAN | LIEN_QUAN
        sa.Column('loai_lien_ket', sa.String(50), nullable=True),
        sa.PrimaryKeyConstraint('van_ban_id', 'van_ban_lien_quan_id'),
        schema='legal',
    )

    # 5. Bang xac_nhan_doc — Xac nhan da doc van ban
    op.create_table(
        'xac_nhan_doc',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            'van_ban_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('legal.van_ban.id'),
            nullable=False,
        ),
        sa.Column(
            'cong_chuc_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('public.cong_chuc.id'),
            nullable=False,
        ),
        sa.Column('da_doc', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('ngay_doc', sa.TIMESTAMP(), nullable=True),
        sa.Column('thoi_gian_doc_giay', sa.Integer(), nullable=True),
        sa.Column('da_xac_nhan', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('ngay_xac_nhan', sa.TIMESTAMP(), nullable=True),
        sa.Column('ghi_chu', sa.Text(), nullable=True),
        sa.Column(
            'created_at',
            sa.TIMESTAMP(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.UniqueConstraint('van_ban_id', 'cong_chuc_id', name='uq_xac_nhan_doc_vb_cc'),
        schema='legal',
    )

    # 6. Bang quiz_van_ban — Quiz kien thuc phap luat
    op.create_table(
        'quiz_van_ban',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            'van_ban_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('legal.van_ban.id'),
            nullable=False,
        ),
        sa.Column('tieu_de', sa.String(300), nullable=False),
        sa.Column('so_cau_hoi', sa.Integer(), nullable=False),
        sa.Column('thoi_gian_phut', sa.Integer(), nullable=True),
        sa.Column(
            'diem_dat',
            sa.Numeric(precision=5, scale=2),
            server_default='70.00',
            nullable=False,
        ),
        # Cau hoi nhung truc tiep — JSONB
        sa.Column(
            'cau_hoi',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column(
            'nguoi_tao_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('public.cong_chuc.id'),
            nullable=True,
        ),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column(
            'created_at',
            sa.TIMESTAMP(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        schema='legal',
    )

    # 7. Bang ket_qua_quiz — Ket qua quiz
    op.create_table(
        'ket_qua_quiz',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            'quiz_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('legal.quiz_van_ban.id'),
            nullable=False,
        ),
        sa.Column(
            'cong_chuc_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('public.cong_chuc.id'),
            nullable=False,
        ),
        sa.Column('diem', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('so_cau_dung', sa.Integer(), nullable=True),
        sa.Column('dat_yeu_cau', sa.Boolean(), nullable=True),
        sa.Column(
            'chi_tiet',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            'created_at',
            sa.TIMESTAMP(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        schema='legal',
    )

    # 8. INDEXES theo spec LEGAL_DATABASE_DESIGN.md

    # van_ban indexes
    op.create_index('idx_legal_vb_so_hieu', 'van_ban', ['so_hieu'], schema='legal')
    op.create_index('idx_legal_vb_loai', 'van_ban', ['loai_van_ban_id'], schema='legal')
    op.create_index('idx_legal_vb_hieu_luc', 'van_ban', ['trang_thai_hieu_luc'], schema='legal')
    op.create_index('idx_legal_vb_duyet', 'van_ban', ['trang_thai_duyet'], schema='legal')
    op.create_index('idx_legal_vb_muc_do', 'van_ban', ['muc_do'], schema='legal')

    # GIN indexes cho JSONB columns
    op.create_index(
        'idx_legal_vb_tags',
        'van_ban',
        ['tags'],
        schema='legal',
        postgresql_using='gin',
    )
    op.create_index(
        'idx_legal_vb_chuyen_de',
        'van_ban',
        ['chuyen_de'],
        schema='legal',
        postgresql_using='gin',
    )

    # xac_nhan_doc indexes
    op.create_index('idx_legal_xnd_vb', 'xac_nhan_doc', ['van_ban_id'], schema='legal')
    op.create_index('idx_legal_xnd_cc', 'xac_nhan_doc', ['cong_chuc_id'], schema='legal')

    # Partial index: cac ban ghi chua doc — dung WHERE da_doc = FALSE theo spec
    op.create_index(
        'idx_legal_xnd_chua_doc',
        'xac_nhan_doc',
        ['da_doc'],
        schema='legal',
        postgresql_where=sa.text("da_doc = FALSE"),
    )

    # ket_qua_quiz indexes
    op.create_index('idx_legal_kqq_quiz', 'ket_qua_quiz', ['quiz_id'], schema='legal')
    op.create_index('idx_legal_kqq_cc', 'ket_qua_quiz', ['cong_chuc_id'], schema='legal')

    # 9. FULL-TEXT SEARCH — Trigger function cap nhat search_vector

    # Tao trigger function
    op.execute("""
        CREATE OR REPLACE FUNCTION legal.update_van_ban_search()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.search_vector := to_tsvector('simple',
                COALESCE(NEW.so_hieu, '') || ' ' ||
                COALESCE(NEW.trich_yeu, '') || ' ' ||
                COALESCE(NEW.tom_tat, '') || ' ' ||
                COALESCE(NEW.diem_moi, '')
            );
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    # Tao trigger BEFORE INSERT OR UPDATE
    op.execute("""
        CREATE TRIGGER trg_legal_van_ban_search
        BEFORE INSERT OR UPDATE ON legal.van_ban
        FOR EACH ROW EXECUTE FUNCTION legal.update_van_ban_search();
    """)

    # GIN index tren search_vector
    op.create_index(
        'idx_legal_vb_search',
        'van_ban',
        ['search_vector'],
        schema='legal',
        postgresql_using='gin',
    )


def downgrade():
    # Xoa trigger va function truoc
    op.execute("DROP TRIGGER IF EXISTS trg_legal_van_ban_search ON legal.van_ban")
    op.execute("DROP FUNCTION IF EXISTS legal.update_van_ban_search()")

    # Xoa indexes (thu tu khong quan trong nhung nen xoa truoc khi drop table)
    op.drop_index('idx_legal_vb_search', table_name='van_ban', schema='legal')
    op.drop_index('idx_legal_kqq_cc', table_name='ket_qua_quiz', schema='legal')
    op.drop_index('idx_legal_kqq_quiz', table_name='ket_qua_quiz', schema='legal')
    op.drop_index('idx_legal_xnd_chua_doc', table_name='xac_nhan_doc', schema='legal')
    op.drop_index('idx_legal_xnd_cc', table_name='xac_nhan_doc', schema='legal')
    op.drop_index('idx_legal_xnd_vb', table_name='xac_nhan_doc', schema='legal')
    op.drop_index('idx_legal_vb_chuyen_de', table_name='van_ban', schema='legal')
    op.drop_index('idx_legal_vb_tags', table_name='van_ban', schema='legal')
    op.drop_index('idx_legal_vb_muc_do', table_name='van_ban', schema='legal')
    op.drop_index('idx_legal_vb_duyet', table_name='van_ban', schema='legal')
    op.drop_index('idx_legal_vb_hieu_luc', table_name='van_ban', schema='legal')
    op.drop_index('idx_legal_vb_loai', table_name='van_ban', schema='legal')
    op.drop_index('idx_legal_vb_so_hieu', table_name='van_ban', schema='legal')

    # Xoa cac bang theo thu tu nguoc (con truoc, cha sau)
    op.drop_table('ket_qua_quiz', schema='legal')
    op.drop_table('quiz_van_ban', schema='legal')
    op.drop_table('xac_nhan_doc', schema='legal')
    op.drop_table('van_ban_lien_ket', schema='legal')
    op.drop_table('van_ban', schema='legal')
    op.drop_table('loai_van_ban', schema='legal')

    # KHONG drop schema — cac migration khac co the dung chung schema legal
