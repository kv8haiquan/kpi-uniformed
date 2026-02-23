"""
Migration: Tao schema lms va 11 bang cho module Dao tao
Author: Platform Team
Date: 2026-02-20

Schema: lms
Bang: chuyen_de, khoa_hoc, bai_hoc, cau_hoi, bai_kiem_tra,
      bai_kiem_tra_cau_hoi, dang_ky_khoa_hoc, tien_do_bai_hoc,
      ket_qua_bai_kiem_tra, chung_chi, khao_sat

Full-text search: khoa_hoc.search_vector (tsvector + trigger + GIN index)

Tham chieu: docs/lms/LMS_DATABASE_DESIGN.md
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


# Revision identifiers
revision = 'create_lms_schema_20260220'
down_revision = 'add_platform_tables_20260220'
branch_labels = None
depends_on = None


def upgrade():
    # =========================================================================
    # SCHEMA
    # =========================================================================
    op.execute("CREATE SCHEMA IF NOT EXISTS lms")
    # GRANT chi chay neu role kpi_user ton tai (production)
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'kpi_user') THEN
                EXECUTE 'GRANT ALL ON SCHEMA lms TO kpi_user';
            END IF;
        END $$
    """)

    # =========================================================================
    # 1. lms.chuyen_de — Chuyen de dao tao (muc 3.1)
    # =========================================================================
    op.create_table(
        'chuyen_de',
        sa.Column('id', UUID(), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('ma_chuyen_de', sa.String(50), nullable=False, unique=True),
        sa.Column('ten_chuyen_de', sa.String(200), nullable=False),
        sa.Column('mo_ta', sa.Text(), nullable=True),
        sa.Column('anh_dai_dien', sa.Text(), nullable=True),
        sa.Column('thu_tu', sa.Integer(), server_default='0', nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=True),
        sa.Column('created_by', UUID(), sa.ForeignKey('public.cong_chuc.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        schema='lms',
    )

    # =========================================================================
    # 2. lms.khoa_hoc — Khoa hoc (muc 3.2)
    # =========================================================================
    op.create_table(
        'khoa_hoc',
        sa.Column('id', UUID(), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('ma_khoa_hoc', sa.String(50), nullable=False, unique=True),
        sa.Column('ten_khoa_hoc', sa.String(300), nullable=False),
        sa.Column('mo_ta', sa.Text(), nullable=True),
        sa.Column('chuyen_de_id', UUID(), sa.ForeignKey('lms.chuyen_de.id'), nullable=True),
        # Loai khoa hoc: TU_HOC, BAT_BUOC, TRUC_TUYEN, KET_HOP
        sa.Column('loai', sa.String(50), nullable=False, server_default='TU_HOC'),
        # Noi dung
        sa.Column('anh_dai_dien', sa.Text(), nullable=True),
        sa.Column('thoi_luong_phut', sa.Integer(), nullable=True),
        sa.Column('so_bai_hoc', sa.Integer(), server_default='0', nullable=True),
        # Dieu kien
        sa.Column('dieu_kien_tien_quyet', JSONB(), nullable=True),
        sa.Column('diem_dat_yeu_cau', sa.Numeric(5, 2), server_default='70.00', nullable=True),
        # Thoi gian
        sa.Column('ngay_bat_dau', sa.Date(), nullable=True),
        sa.Column('ngay_ket_thuc', sa.Date(), nullable=True),
        # Giang vien
        sa.Column('giang_vien_id', UUID(), sa.ForeignKey('public.cong_chuc.id'), nullable=True),
        # Trang thai: NHAP, CHO_DUYET, DA_XUAT_BAN, TAM_DUNG, DA_DONG
        sa.Column('trang_thai', sa.String(50), server_default='NHAP', nullable=True),
        sa.Column('nguoi_duyet_id', UUID(), sa.ForeignKey('public.cong_chuc.id'), nullable=True),
        sa.Column('ngay_duyet', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        schema='lms',
    )

    # Them cot search_vector bang raw SQL (tsvector khong co trong sa.types)
    op.execute("ALTER TABLE lms.khoa_hoc ADD COLUMN search_vector tsvector")

    # =========================================================================
    # 3. lms.bai_hoc — Bai hoc / noi dung khoa hoc (muc 3.3)
    # =========================================================================
    op.create_table(
        'bai_hoc',
        sa.Column('id', UUID(), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('khoa_hoc_id', UUID(), sa.ForeignKey('lms.khoa_hoc.id'), nullable=False),
        sa.Column('thu_tu', sa.Integer(), nullable=False),
        sa.Column('tieu_de', sa.String(300), nullable=False),
        # Loai noi dung: VIDEO, PDF, SLIDE, HTML, SCORM, QUIZ
        sa.Column('loai_noi_dung', sa.String(50), nullable=False),
        sa.Column('noi_dung', sa.Text(), nullable=True),
        sa.Column('file_url', sa.Text(), nullable=True),
        sa.Column('file_size_mb', sa.Numeric(10, 2), nullable=True),
        sa.Column('thoi_luong_phut', sa.Integer(), nullable=True),
        # Dieu kien hoan thanh
        sa.Column('phai_xem_het', sa.Boolean(), server_default=sa.text('true'), nullable=True),
        sa.Column('thoi_gian_toi_thieu_giay', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        schema='lms',
    )

    # =========================================================================
    # 4. lms.cau_hoi — Ngan hang cau hoi (muc 3.4)
    # =========================================================================
    op.create_table(
        'cau_hoi',
        sa.Column('id', UUID(), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('khoa_hoc_id', UUID(), sa.ForeignKey('lms.khoa_hoc.id'), nullable=True),
        sa.Column('chuyen_de_id', UUID(), sa.ForeignKey('lms.chuyen_de.id'), nullable=True),
        # Noi dung cau hoi
        sa.Column('noi_dung', sa.Text(), nullable=False),
        # Loai: TRAC_NGHIEM_1, TRAC_NGHIEM_NHIEU, DUNG_SAI, TU_LUAN, GHEP_DOI
        sa.Column('loai', sa.String(50), nullable=False),
        # Dap an (JSONB)
        sa.Column('dap_an', JSONB(), nullable=False),
        sa.Column('diem', sa.Numeric(5, 2), server_default='1.0', nullable=True),
        # Do kho: DE, TRUNG_BINH, KHO
        sa.Column('do_kho', sa.String(20), server_default='TRUNG_BINH', nullable=True),
        # Cross-module reference den legal.van_ban
        sa.Column('van_ban_lien_quan_ids', JSONB(), nullable=True),
        sa.Column('nguoi_tao_id', UUID(), sa.ForeignKey('public.cong_chuc.id'), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        schema='lms',
    )

    # =========================================================================
    # 5. lms.bai_kiem_tra — Bai kiem tra (muc 3.5)
    # =========================================================================
    op.create_table(
        'bai_kiem_tra',
        sa.Column('id', UUID(), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('khoa_hoc_id', UUID(), sa.ForeignKey('lms.khoa_hoc.id'), nullable=True),
        sa.Column('tieu_de', sa.String(300), nullable=False),
        sa.Column('mo_ta', sa.Text(), nullable=True),
        # Cau hinh de thi
        sa.Column('so_cau_hoi', sa.Integer(), nullable=False),
        sa.Column('thoi_gian_lam_bai_phut', sa.Integer(), nullable=True),
        sa.Column('so_lan_lam_toi_da', sa.Integer(), server_default='3', nullable=True),
        sa.Column('diem_dat', sa.Numeric(5, 2), server_default='70.00', nullable=True),
        sa.Column('tron_de', sa.Boolean(), server_default=sa.text('true'), nullable=True),
        sa.Column('tron_dap_an', sa.Boolean(), server_default=sa.text('true'), nullable=True),
        # Thoi gian mo
        sa.Column('ngay_mo', sa.Date(), nullable=True),
        sa.Column('ngay_dong', sa.Date(), nullable=True),
        sa.Column('nguoi_tao_id', UUID(), sa.ForeignKey('public.cong_chuc.id'), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        schema='lms',
    )

    # =========================================================================
    # 6. lms.bai_kiem_tra_cau_hoi — Lien ket BKT <-> Cau hoi (muc 3.6)
    #    Composite PK: (bai_kiem_tra_id, cau_hoi_id)
    # =========================================================================
    op.create_table(
        'bai_kiem_tra_cau_hoi',
        sa.Column('bai_kiem_tra_id', UUID(), sa.ForeignKey('lms.bai_kiem_tra.id'), nullable=False),
        sa.Column('cau_hoi_id', UUID(), sa.ForeignKey('lms.cau_hoi.id'), nullable=False),
        sa.Column('thu_tu', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('bai_kiem_tra_id', 'cau_hoi_id'),
        schema='lms',
    )

    # =========================================================================
    # 7. lms.dang_ky_khoa_hoc — Dang ky / Giao khoa hoc (muc 3.7)
    # =========================================================================
    op.create_table(
        'dang_ky_khoa_hoc',
        sa.Column('id', UUID(), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('cong_chuc_id', UUID(), sa.ForeignKey('public.cong_chuc.id'), nullable=False),
        sa.Column('khoa_hoc_id', UUID(), sa.ForeignKey('lms.khoa_hoc.id'), nullable=False),
        # Loai dang ky: TU_NGUYEN, BAT_BUOC, GIAO_VIEC
        sa.Column('loai_dang_ky', sa.String(50), server_default='TU_NGUYEN', nullable=True),
        sa.Column('nguoi_giao_id', UUID(), sa.ForeignKey('public.cong_chuc.id'), nullable=True),
        sa.Column('han_hoan_thanh', sa.Date(), nullable=True),
        # Tien do: CHUA_BAT_DAU, DANG_HOC, HOAN_THANH, KHONG_DAT, QUA_HAN
        sa.Column('trang_thai', sa.String(50), server_default='CHUA_BAT_DAU', nullable=True),
        sa.Column('phan_tram_hoan_thanh', sa.Numeric(5, 2), server_default='0', nullable=True),
        sa.Column('ngay_bat_dau_hoc', sa.DateTime(), nullable=True),
        sa.Column('ngay_hoan_thanh', sa.DateTime(), nullable=True),
        # Ket qua
        sa.Column('diem_cao_nhat', sa.Numeric(5, 2), nullable=True),
        sa.Column('so_lan_lam_bai', sa.Integer(), server_default='0', nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.UniqueConstraint('cong_chuc_id', 'khoa_hoc_id', name='uq_lms_dkkh_cc_kh'),
        schema='lms',
    )

    # =========================================================================
    # 8. lms.tien_do_bai_hoc — Tien do hoc tung bai (muc 3.8)
    # =========================================================================
    op.create_table(
        'tien_do_bai_hoc',
        sa.Column('id', UUID(), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('cong_chuc_id', UUID(), sa.ForeignKey('public.cong_chuc.id'), nullable=False),
        sa.Column('bai_hoc_id', UUID(), sa.ForeignKey('lms.bai_hoc.id'), nullable=False),
        # Trang thai: CHUA_XEM, DANG_XEM, DA_HOAN_THANH
        sa.Column('trang_thai', sa.String(50), server_default='CHUA_XEM', nullable=True),
        sa.Column('thoi_gian_xem_giay', sa.Integer(), server_default='0', nullable=True),
        sa.Column('lan_xem_cuoi', sa.DateTime(), nullable=True),
        sa.Column('ngay_hoan_thanh', sa.DateTime(), nullable=True),
        sa.UniqueConstraint('cong_chuc_id', 'bai_hoc_id', name='uq_lms_tdbh_cc_bh'),
        schema='lms',
    )

    # =========================================================================
    # 9. lms.ket_qua_bai_kiem_tra — Ket qua lam bai (muc 3.9)
    # =========================================================================
    op.create_table(
        'ket_qua_bai_kiem_tra',
        sa.Column('id', UUID(), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('cong_chuc_id', UUID(), sa.ForeignKey('public.cong_chuc.id'), nullable=False),
        sa.Column('bai_kiem_tra_id', UUID(), sa.ForeignKey('lms.bai_kiem_tra.id'), nullable=False),
        sa.Column('lan_thu', sa.Integer(), nullable=False, server_default='1'),
        # Ket qua
        sa.Column('diem', sa.Numeric(5, 2), nullable=True),
        sa.Column('so_cau_dung', sa.Integer(), nullable=True),
        sa.Column('so_cau_sai', sa.Integer(), nullable=True),
        sa.Column('thoi_gian_lam_giay', sa.Integer(), nullable=True),
        sa.Column('chi_tiet_tra_loi', JSONB(), nullable=True),
        sa.Column('dat_yeu_cau', sa.Boolean(), nullable=True),
        sa.Column('ngay_lam', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        schema='lms',
    )

    # =========================================================================
    # 10. lms.chung_chi — Chung chi / Chung nhan hoan thanh (muc 3.10)
    # =========================================================================
    op.create_table(
        'chung_chi',
        sa.Column('id', UUID(), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('cong_chuc_id', UUID(), sa.ForeignKey('public.cong_chuc.id'), nullable=False),
        sa.Column('khoa_hoc_id', UUID(), sa.ForeignKey('lms.khoa_hoc.id'), nullable=False),
        sa.Column('ma_chung_chi', sa.String(50), nullable=False, unique=True),
        sa.Column('ten_chung_chi', sa.String(300), nullable=True),
        sa.Column('diem_dat', sa.Numeric(5, 2), nullable=True),
        sa.Column('ngay_cap', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('nguoi_cap_id', UUID(), sa.ForeignKey('public.cong_chuc.id'), nullable=True),
        sa.Column('file_url', sa.Text(), nullable=True),
        sa.UniqueConstraint('cong_chuc_id', 'khoa_hoc_id', name='uq_lms_cc_kh'),
        schema='lms',
    )

    # =========================================================================
    # 11. lms.khao_sat — Khao sat sau khoa hoc (muc 3.11)
    # =========================================================================
    op.create_table(
        'khao_sat',
        sa.Column('id', UUID(), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('khoa_hoc_id', UUID(), sa.ForeignKey('lms.khoa_hoc.id'), nullable=False),
        sa.Column('cong_chuc_id', UUID(), sa.ForeignKey('public.cong_chuc.id'), nullable=False),
        sa.Column('noi_dung', JSONB(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.UniqueConstraint('cong_chuc_id', 'khoa_hoc_id', name='uq_lms_ks_cc_kh'),
        schema='lms',
    )

    # =========================================================================
    # INDEXES (muc 4 — LMS_DATABASE_DESIGN.md)
    # =========================================================================
    op.create_index('idx_lms_kh_chuyen_de', 'khoa_hoc', ['chuyen_de_id'], schema='lms')
    op.create_index('idx_lms_kh_giang_vien', 'khoa_hoc', ['giang_vien_id'], schema='lms')
    op.create_index('idx_lms_kh_trang_thai', 'khoa_hoc', ['trang_thai'], schema='lms')
    op.create_index('idx_lms_bh_khoa_hoc', 'bai_hoc', ['khoa_hoc_id'], schema='lms')
    op.create_index('idx_lms_ch_khoa_hoc', 'cau_hoi', ['khoa_hoc_id'], schema='lms')
    op.create_index('idx_lms_dkkh_cc', 'dang_ky_khoa_hoc', ['cong_chuc_id'], schema='lms')
    op.create_index('idx_lms_dkkh_kh', 'dang_ky_khoa_hoc', ['khoa_hoc_id'], schema='lms')
    op.create_index('idx_lms_dkkh_tt', 'dang_ky_khoa_hoc', ['trang_thai'], schema='lms')
    op.create_index('idx_lms_kqbkt_cc', 'ket_qua_bai_kiem_tra', ['cong_chuc_id'], schema='lms')
    op.create_index('idx_lms_kqbkt_bkt', 'ket_qua_bai_kiem_tra', ['bai_kiem_tra_id'], schema='lms')
    op.create_index('idx_lms_tdbh_cc', 'tien_do_bai_hoc', ['cong_chuc_id'], schema='lms')
    op.create_index('idx_lms_tdbh_bh', 'tien_do_bai_hoc', ['bai_hoc_id'], schema='lms')

    # =========================================================================
    # FULL-TEXT SEARCH (muc 5 — tsvector + trigger + GIN index)
    # =========================================================================
    op.execute("""
        CREATE OR REPLACE FUNCTION lms.update_khoa_hoc_search()
        RETURNS trigger AS $$
        BEGIN
            NEW.search_vector := to_tsvector('simple',
                COALESCE(NEW.ten_khoa_hoc, '') || ' ' || COALESCE(NEW.mo_ta, ''));
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
    """)

    op.execute("""
        CREATE TRIGGER trg_lms_khoa_hoc_search
            BEFORE INSERT OR UPDATE ON lms.khoa_hoc
            FOR EACH ROW EXECUTE FUNCTION lms.update_khoa_hoc_search()
    """)

    op.execute("""
        CREATE INDEX idx_lms_kh_search ON lms.khoa_hoc USING GIN (search_vector)
    """)


def downgrade():
    # DROP SCHEMA CASCADE xoa tat ca: bang, index, trigger, function
    op.execute("DROP SCHEMA IF EXISTS lms CASCADE")
