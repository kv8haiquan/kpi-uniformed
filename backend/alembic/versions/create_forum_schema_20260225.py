"""Create forum schema — Module Dien dan nghiep vu (5 bang)

Revision ID: create_forum_schema_20260225
Revises: them_vai_tro_qldv_20260225
Create Date: 2026-02-25

Tao schema forum voi 5 bang:
  1. chuyen_muc    — Chuyen muc dien dan (phan cap cha-con)
  2. chu_de        — Chu de / Thread (full-text search, tags, moderation)
  3. tra_loi       — Tra loi / Binh luan (threaded, dap an chuan)
  4. bieu_quyet    — Upvote / Downvote (polymorphic)
  5. theo_doi      — Theo doi chu de (composite PK)

Indexes: 10 custom indexes (bao gom 2 GIN indexes)
Trigger: FTS trigger tren chu_de (search_vector tsvector)
Seed: 8 chuyen muc mac dinh
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'create_forum_schema_20260225'
down_revision = 'them_vai_tro_qldv_20260225'
branch_labels = None
depends_on = None


def upgrade():
    # ===================================================================
    # 1. Tao schema va cap quyen
    # ===================================================================
    op.execute("CREATE SCHEMA IF NOT EXISTS forum")
    op.execute("GRANT ALL ON SCHEMA forum TO postgres")

    # -------------------------------------------------------------------
    # 2. Bang chuyen_muc — Chuyen muc dien dan
    # -------------------------------------------------------------------
    op.create_table(
        'chuyen_muc',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column('ten_chuyen_muc', sa.String(200), nullable=False),
        sa.Column('mo_ta', sa.Text(), nullable=True),
        sa.Column('icon', sa.String(50), nullable=True),
        sa.Column('thu_tu', sa.Integer(), nullable=True),
        sa.Column(
            'parent_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('forum.chuyen_muc.id'),
            nullable=True,
            comment='Phan cap cha-con, toi da 2 cap',
        ),
        sa.Column(
            'chi_doc',
            sa.Boolean(),
            server_default='false',
            nullable=False,
            comment='TRUE = chi expert/admin dang bai',
        ),
        sa.Column(
            'yeu_cau_duyet',
            sa.Boolean(),
            server_default='false',
            nullable=False,
            comment='TRUE = bai moi can duyet',
        ),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column(
            'created_at',
            sa.TIMESTAMP(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        schema='forum',
    )

    # -------------------------------------------------------------------
    # 3. Bang chu_de — Chu de / Thread
    # -------------------------------------------------------------------
    op.create_table(
        'chu_de',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            'chuyen_muc_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('forum.chuyen_muc.id'),
            nullable=False,
        ),
        sa.Column('tieu_de', sa.String(500), nullable=False),
        sa.Column('noi_dung', sa.Text(), nullable=False),
        sa.Column(
            'tags',
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            'tac_gia_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('public.cong_chuc.id'),
            nullable=False,
        ),
        sa.Column(
            'trang_thai',
            sa.String(50),
            server_default='MO',
            nullable=False,
            comment='CHO_DUYET, MO, DONG, AN',
        ),
        sa.Column('is_ghim', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('is_khoa', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('so_luot_xem', sa.Integer(), server_default='0', nullable=False),
        sa.Column('so_tra_loi', sa.Integer(), server_default='0', nullable=False),
        sa.Column('so_upvote', sa.Integer(), server_default='0', nullable=False),
        # tra_loi_chuan_id — FK se duoc them sau khi tao bang tra_loi
        sa.Column(
            'tra_loi_chuan_id',
            postgresql.UUID(as_uuid=True),
            nullable=True,
            comment='FK -> forum.tra_loi(id), them sau',
        ),
        sa.Column(
            'van_ban_lien_quan',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            comment='UUIDs van ban phap luat tu module Legal',
        ),
        sa.Column(
            'sop_lien_quan',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            comment='UUIDs tu common.knowledge_base',
        ),
        sa.Column(
            'nguoi_duyet_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('public.cong_chuc.id'),
            nullable=True,
        ),
        sa.Column('ngay_duyet', sa.TIMESTAMP(), nullable=True),
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
        sa.Column(
            'search_vector',
            postgresql.TSVECTOR(),
            nullable=True,
        ),
        schema='forum',
    )

    # -------------------------------------------------------------------
    # 4. Bang tra_loi — Tra loi / Binh luan
    # -------------------------------------------------------------------
    op.create_table(
        'tra_loi',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            'chu_de_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('forum.chu_de.id'),
            nullable=False,
        ),
        sa.Column(
            'parent_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('forum.tra_loi.id'),
            nullable=True,
            comment='Reply long nhau, max 2 cap',
        ),
        sa.Column('noi_dung', sa.Text(), nullable=False),
        sa.Column(
            'tac_gia_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('public.cong_chuc.id'),
            nullable=False,
        ),
        sa.Column(
            'is_dap_an_chuan',
            sa.Boolean(),
            server_default='false',
            nullable=False,
        ),
        sa.Column(
            'is_an',
            sa.Boolean(),
            server_default='false',
            nullable=False,
        ),
        sa.Column('so_upvote', sa.Integer(), server_default='0', nullable=False),
        sa.Column(
            'can_cu_phap_ly',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            comment='[{"loai": "VAN_BAN"|"SOP", "id": "uuid", "trich_dan": "..."}]',
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
        schema='forum',
    )

    # Them FK chu_de.tra_loi_chuan_id -> forum.tra_loi(id) sau khi tao bang tra_loi
    op.create_foreign_key(
        'fk_forum_cd_tra_loi_chuan',
        'chu_de', 'tra_loi',
        ['tra_loi_chuan_id'], ['id'],
        source_schema='forum',
        referent_schema='forum',
    )

    # -------------------------------------------------------------------
    # 5. Bang bieu_quyet — Upvote / Downvote (polymorphic)
    # -------------------------------------------------------------------
    op.create_table(
        'bieu_quyet',
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
            'doi_tuong_type',
            sa.String(20),
            nullable=False,
            comment='CHU_DE hoac TRA_LOI',
        ),
        sa.Column(
            'doi_tuong_id',
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            'loai',
            sa.String(10),
            nullable=False,
            comment='UP hoac DOWN',
        ),
        sa.Column(
            'created_at',
            sa.TIMESTAMP(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.UniqueConstraint(
            'cong_chuc_id', 'doi_tuong_type', 'doi_tuong_id',
            name='uq_forum_bq_cc_dt',
        ),
        schema='forum',
    )

    # -------------------------------------------------------------------
    # 6. Bang theo_doi — Theo doi chu de (composite PK)
    # -------------------------------------------------------------------
    op.create_table(
        'theo_doi',
        sa.Column(
            'cong_chuc_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('public.cong_chuc.id'),
            primary_key=True,
        ),
        sa.Column(
            'chu_de_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('forum.chu_de.id'),
            primary_key=True,
        ),
        sa.Column(
            'created_at',
            sa.TIMESTAMP(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        schema='forum',
    )

    # ===================================================================
    # 7. INDEXES — 10 indexes theo spec
    # ===================================================================

    # chu_de — 6 indexes
    op.create_index(
        'idx_forum_cd_cm',
        'chu_de',
        ['chuyen_muc_id'],
        schema='forum',
    )
    op.create_index(
        'idx_forum_cd_tg',
        'chu_de',
        ['tac_gia_id'],
        schema='forum',
    )
    op.create_index(
        'idx_forum_cd_tt',
        'chu_de',
        ['trang_thai'],
        schema='forum',
    )
    op.create_index(
        'idx_forum_cd_tags',
        'chu_de',
        ['tags'],
        schema='forum',
        postgresql_using='gin',
    )
    op.create_index(
        'idx_forum_cd_created',
        'chu_de',
        [sa.text('created_at DESC')],
        schema='forum',
    )
    op.create_index(
        'idx_forum_cd_search',
        'chu_de',
        ['search_vector'],
        schema='forum',
        postgresql_using='gin',
    )

    # tra_loi — 3 indexes
    op.create_index(
        'idx_forum_tl_cd',
        'tra_loi',
        ['chu_de_id'],
        schema='forum',
    )
    op.create_index(
        'idx_forum_tl_tg',
        'tra_loi',
        ['tac_gia_id'],
        schema='forum',
    )
    op.create_index(
        'idx_forum_tl_parent',
        'tra_loi',
        ['parent_id'],
        schema='forum',
    )

    # bieu_quyet — 1 composite index
    op.create_index(
        'idx_forum_bq_dt',
        'bieu_quyet',
        ['doi_tuong_type', 'doi_tuong_id'],
        schema='forum',
    )

    # ===================================================================
    # 8. Full-Text Search Trigger cho chu_de
    # ===================================================================
    op.execute("""
        CREATE OR REPLACE FUNCTION forum.update_chu_de_search()
        RETURNS trigger AS $$
        BEGIN
            NEW.search_vector := to_tsvector('simple',
                COALESCE(NEW.tieu_de, '') || ' ' || COALESCE(NEW.noi_dung, ''));
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
    """)

    op.execute("""
        CREATE TRIGGER trg_forum_chu_de_search
            BEFORE INSERT OR UPDATE ON forum.chu_de
            FOR EACH ROW EXECUTE FUNCTION forum.update_chu_de_search()
    """)

    # ===================================================================
    # 9. Seed data — 8 chuyen muc mac dinh
    # ===================================================================
    op.execute("""
        INSERT INTO forum.chuyen_muc (ten_chuyen_muc, mo_ta, icon, thu_tu) VALUES
        ('Thủ tục hải quan', 'Thảo luận về quy trình, thủ tục hải quan XNK', '📋', 1),
        ('Kiểm tra sau thông quan', 'Nghiệp vụ kiểm tra sau thông quan, thanh tra', '🔍', 2),
        ('Thuế XNK & Chính sách', 'Thuế xuất nhập khẩu, chính sách thuế, ưu đãi', '💰', 3),
        ('Kiểm soát hải quan', 'Phòng chống buôn lậu, gian lận thương mại', '🛡️', 4),
        ('CNTT & Hệ thống', 'Hệ thống CNTT hải quan, VNACCS/VCIS, một cửa', '💻', 5),
        ('Pháp luật & Văn bản', 'Trao đổi về văn bản pháp luật, nghị định, thông tư', '📜', 6),
        ('Tình huống thực tế', 'Chia sẻ tình huống, case study thực tế', '💡', 7),
        ('Góp ý & Đề xuất', 'Góp ý cải tiến quy trình, đề xuất sáng kiến', '✍️', 8)
    """)


def downgrade():
    # 1. Drop trigger va function truoc
    op.execute("DROP TRIGGER IF EXISTS trg_forum_chu_de_search ON forum.chu_de")
    op.execute("DROP FUNCTION IF EXISTS forum.update_chu_de_search()")

    # 2. Drop FK chu_de.tra_loi_chuan_id truoc khi drop bang tra_loi
    op.drop_constraint('fk_forum_cd_tra_loi_chuan', 'chu_de', schema='forum', type_='foreignkey')

    # 3. Drop indexes (nguoc thu tu)
    op.drop_index('idx_forum_bq_dt', table_name='bieu_quyet', schema='forum')
    op.drop_index('idx_forum_tl_parent', table_name='tra_loi', schema='forum')
    op.drop_index('idx_forum_tl_tg', table_name='tra_loi', schema='forum')
    op.drop_index('idx_forum_tl_cd', table_name='tra_loi', schema='forum')
    op.drop_index('idx_forum_cd_search', table_name='chu_de', schema='forum')
    op.drop_index('idx_forum_cd_created', table_name='chu_de', schema='forum')
    op.drop_index('idx_forum_cd_tags', table_name='chu_de', schema='forum')
    op.drop_index('idx_forum_cd_tt', table_name='chu_de', schema='forum')
    op.drop_index('idx_forum_cd_tg', table_name='chu_de', schema='forum')
    op.drop_index('idx_forum_cd_cm', table_name='chu_de', schema='forum')

    # 4. Drop tables (nguoc thu tu dependency)
    op.drop_table('theo_doi', schema='forum')
    op.drop_table('bieu_quyet', schema='forum')
    op.drop_table('tra_loi', schema='forum')
    op.drop_table('chu_de', schema='forum')
    op.drop_table('chuyen_muc', schema='forum')

    # 5. Drop schema
    op.execute("DROP SCHEMA IF EXISTS forum CASCADE")
