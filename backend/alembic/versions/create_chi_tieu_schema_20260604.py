"""
Migration: Tao schema chi_tieu (Module Quan ly Chi tieu Don vi)

Author: Platform Team
Date: 2026-06-04

Schema: chi_tieu
Bang: linh_vuc, danh_muc_chi_tieu, giao_nam, dang_ky_thang, lich_su_duyet
View:  v_luy_ke_thang (luy ke chay theo tung thang)
Vai tro bo sung (public.platform_role): THEO_DOI_CHI_TIEU, QT_CHI_TIEU

Quy uoc: KHONG dung PostgreSQL ENUM — moi truong trang thai/loai dung VARCHAR + CHECK.

Tham chieu: docs/Chi Tieu/CHI_TIEU_DATABASE_DESIGN.md (v1.1)
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


# Revision identifiers
revision = 'create_chi_tieu_schema_20260604'
down_revision = 'hdld_vb714_20260601'
branch_labels = None
depends_on = None


def upgrade():
    # =========================================================================
    # SCHEMA
    # =========================================================================
    op.execute("CREATE SCHEMA IF NOT EXISTS chi_tieu")
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'kpi_user') THEN
                EXECUTE 'GRANT ALL ON SCHEMA chi_tieu TO kpi_user';
            END IF;
        END $$
    """)

    # =========================================================================
    # 1. chi_tieu.linh_vuc — Linh vuc cong tac
    # =========================================================================
    op.create_table(
        'linh_vuc',
        sa.Column('id', UUID(), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('ma_linh_vuc', sa.String(30), nullable=False, unique=True),
        sa.Column('ten_linh_vuc', sa.String(200), nullable=False),
        sa.Column('van_ban_ke_hoach', sa.String(300), nullable=True),
        sa.Column('thu_tu', sa.Integer(), server_default='0', nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        schema='chi_tieu',
    )

    # =========================================================================
    # 2. chi_tieu.danh_muc_chi_tieu — Danh muc chi tieu
    # =========================================================================
    op.create_table(
        'danh_muc_chi_tieu',
        sa.Column('id', UUID(), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('linh_vuc_id', UUID(), sa.ForeignKey('chi_tieu.linh_vuc.id'), nullable=False),
        sa.Column('ma_chi_tieu', sa.String(30), nullable=False, unique=True),
        sa.Column('ten_chi_tieu', sa.String(500), nullable=False),
        sa.Column('don_vi_tinh', sa.String(50), nullable=False),
        # Kieu du lieu: SO_NGUYEN | THAP_PHAN | PHAN_TRAM
        sa.Column('kieu_du_lieu', sa.String(20), nullable=False, server_default='THAP_PHAN'),
        sa.Column('co_phan_dau', sa.Boolean(), server_default=sa.text('false'), nullable=True),
        sa.Column('van_ban_giao', sa.String(300), nullable=True),
        sa.Column('mo_ta', sa.Text(), nullable=True),
        sa.Column('thu_tu', sa.Integer(), server_default='0', nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.CheckConstraint(
            "kieu_du_lieu IN ('SO_NGUYEN', 'THAP_PHAN', 'PHAN_TRAM')",
            name='ck_ct_danhmuc_kieu_du_lieu',
        ),
        schema='chi_tieu',
    )
    op.create_index('idx_ct_danhmuc_linhvuc', 'danh_muc_chi_tieu', ['linh_vuc_id'], schema='chi_tieu')

    # =========================================================================
    # 3. chi_tieu.giao_nam — Chi tieu giao nam cho don vi
    # =========================================================================
    op.create_table(
        'giao_nam',
        sa.Column('id', UUID(), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('don_vi_id', UUID(), sa.ForeignKey('public.don_vi.id'), nullable=False),
        sa.Column('chi_tieu_id', UUID(), sa.ForeignKey('chi_tieu.danh_muc_chi_tieu.id'), nullable=False),
        sa.Column('nam', sa.Integer(), nullable=False),
        # Loai muc: PHAP_LENH | PHAN_DAU
        sa.Column('loai_muc', sa.String(20), nullable=False, server_default='PHAP_LENH'),
        sa.Column('gia_tri_giao', sa.Numeric(18, 3), nullable=False),
        sa.Column('luy_ke_dau_ky', sa.Numeric(18, 3), server_default='0', nullable=True),
        sa.Column('nguoi_giao_id', UUID(), sa.ForeignKey('public.cong_chuc.id'), nullable=True),
        sa.Column('ghi_chu', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), server_default=sa.text('false'), nullable=True),
        sa.CheckConstraint('nam >= 2025', name='ck_ct_giaonam_nam'),
        sa.CheckConstraint("loai_muc IN ('PHAP_LENH', 'PHAN_DAU')", name='ck_ct_giaonam_loai_muc'),
        sa.UniqueConstraint('don_vi_id', 'chi_tieu_id', 'nam', 'loai_muc', name='uq_ct_giaonam'),
        schema='chi_tieu',
    )
    op.create_index('idx_ct_giaonam_donvi', 'giao_nam', ['don_vi_id', 'nam'], schema='chi_tieu')
    op.create_index('idx_ct_giaonam_chitieu', 'giao_nam', ['chi_tieu_id'], schema='chi_tieu')

    # =========================================================================
    # 4. chi_tieu.dang_ky_thang — Dang ky + ket qua theo thang (BANG LOI)
    # =========================================================================
    op.create_table(
        'dang_ky_thang',
        sa.Column('id', UUID(), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('don_vi_id', UUID(), sa.ForeignKey('public.don_vi.id'), nullable=False),
        sa.Column('chi_tieu_id', UUID(), sa.ForeignKey('chi_tieu.danh_muc_chi_tieu.id'), nullable=False),
        sa.Column('thang', sa.Integer(), nullable=False),
        sa.Column('nam', sa.Integer(), nullable=False),
        # Dang ky dau thang
        sa.Column('khong_dang_ky', sa.Boolean(), server_default=sa.text('false'), nullable=True),
        sa.Column('gia_tri_dang_ky', sa.Numeric(18, 3), nullable=True),
        # Ket qua cuoi thang
        sa.Column('gia_tri_ket_qua', sa.Numeric(18, 3), nullable=True),
        # Danh gia
        sa.Column('danh_gia_tu_dong', sa.String(100), nullable=True),
        sa.Column('danh_gia_ghi_chu', sa.String(200), nullable=True),
        # Trang thai vong doi
        sa.Column('trang_thai', sa.String(30), nullable=False, server_default='NHAP'),
        # Nguoi lien quan
        sa.Column('nguoi_theo_doi_id', UUID(), sa.ForeignKey('public.cong_chuc.id'), nullable=False),
        sa.Column('nguoi_duyet_id', UUID(), sa.ForeignKey('public.cong_chuc.id'), nullable=True),
        # Moc thoi gian quy trinh
        sa.Column('ngay_gui_dang_ky', sa.DateTime(), nullable=True),
        sa.Column('ngay_duyet_dang_ky', sa.DateTime(), nullable=True),
        sa.Column('ngay_gui_ket_qua', sa.DateTime(), nullable=True),
        sa.Column('ngay_duyet_ket_qua', sa.DateTime(), nullable=True),
        sa.Column('ly_do_tu_choi', sa.Text(), nullable=True),
        # Khoa sau khi chot
        sa.Column('is_khoa', sa.Boolean(), server_default=sa.text('false'), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), server_default=sa.text('false'), nullable=True),
        sa.CheckConstraint('thang BETWEEN 1 AND 12', name='ck_ct_dk_thang'),
        sa.CheckConstraint('nam >= 2025', name='ck_ct_dk_nam'),
        sa.CheckConstraint(
            "trang_thai IN ('NHAP', 'CHO_DUYET_DANG_KY', 'DA_DUYET_DANG_KY', "
            "'CHO_DUYET_SUA', 'CHO_DUYET_KET_QUA', 'DA_DUYET_KET_QUA')",
            name='ck_ct_dk_trang_thai',
        ),
        sa.UniqueConstraint('don_vi_id', 'chi_tieu_id', 'thang', 'nam', name='uq_ct_dangky'),
        schema='chi_tieu',
    )
    op.create_index('idx_ct_dk_donvi', 'dang_ky_thang', ['don_vi_id', 'thang', 'nam'], schema='chi_tieu')
    op.create_index('idx_ct_dk_chitieu', 'dang_ky_thang', ['chi_tieu_id'], schema='chi_tieu')
    op.create_index('idx_ct_dk_trangthai', 'dang_ky_thang', ['trang_thai'], schema='chi_tieu')
    op.create_index('idx_ct_dk_nguoiduyet', 'dang_ky_thang', ['nguoi_duyet_id'], schema='chi_tieu')

    # =========================================================================
    # 5. chi_tieu.lich_su_duyet — Lich su thao tac/duyet (audit)
    # =========================================================================
    op.create_table(
        'lich_su_duyet',
        sa.Column('id', UUID(), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('dang_ky_thang_id', UUID(), sa.ForeignKey('chi_tieu.dang_ky_thang.id'), nullable=False),
        sa.Column('hanh_dong', sa.String(30), nullable=False),
        sa.Column('nguoi_thuc_hien_id', UUID(), sa.ForeignKey('public.cong_chuc.id'), nullable=False),
        sa.Column('noi_dung_truoc', JSONB(), nullable=True),
        sa.Column('noi_dung_sau', JSONB(), nullable=True),
        sa.Column('ghi_chu', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.CheckConstraint(
            "hanh_dong IN ('GUI_DANG_KY', 'DUYET_DANG_KY', 'TU_CHOI_DANG_KY', "
            "'GUI_SUA', 'DUYET_SUA', 'TU_CHOI_SUA', "
            "'GUI_KET_QUA', 'DUYET_KET_QUA', 'TU_CHOI_KET_QUA', 'MO_KHOA')",
            name='ck_ct_lichsu_hanh_dong',
        ),
        schema='chi_tieu',
    )
    op.create_index('idx_ct_lichsu_dangky', 'lich_su_duyet', ['dang_ky_thang_id'], schema='chi_tieu')

    # =========================================================================
    # 6. VIEW — luy ke chay theo tung thang (tinh tu ket qua DA DUYET)
    # =========================================================================
    op.execute("""
        CREATE OR REPLACE VIEW chi_tieu.v_luy_ke_thang AS
        SELECT
            g.don_vi_id,
            g.chi_tieu_id,
            g.nam,
            g.loai_muc,
            g.gia_tri_giao,
            d.thang,
            g.luy_ke_dau_ky
              + SUM(d.gia_tri_ket_qua) OVER (
                    PARTITION BY g.don_vi_id, g.chi_tieu_id, g.nam, g.loai_muc
                    ORDER BY d.thang
                    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
                ) AS luy_ke_den_thang,
            CASE WHEN g.gia_tri_giao > 0
                 THEN ROUND((g.luy_ke_dau_ky
                      + SUM(d.gia_tri_ket_qua) OVER (
                            PARTITION BY g.don_vi_id, g.chi_tieu_id, g.nam, g.loai_muc
                            ORDER BY d.thang
                            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
                        )) / g.gia_tri_giao * 100, 2)
                 ELSE NULL END AS dat_phan_tram_den_thang
        FROM chi_tieu.giao_nam g
        JOIN chi_tieu.dang_ky_thang d
               ON d.don_vi_id = g.don_vi_id
              AND d.chi_tieu_id = g.chi_tieu_id
              AND d.nam = g.nam
              AND d.trang_thai = 'DA_DUYET_KET_QUA'
              AND d.is_deleted = FALSE
        WHERE g.is_deleted = FALSE;
    """)

    # =========================================================================
    # 7. VAI TRO BO SUNG (public.platform_role) — INSERT du lieu, KHONG sua cau truc
    # =========================================================================
    op.execute("""
        INSERT INTO public.platform_role (id, ma_role, ten_role, mo_ta, is_active, created_at)
        VALUES
        (gen_random_uuid(), 'THEO_DOI_CHI_TIEU', 'Nguoi theo doi chi tieu',
         'Dang ky chi tieu dau thang va nhap ket qua cuoi thang cho don vi', true, CURRENT_TIMESTAMP),
        (gen_random_uuid(), 'QT_CHI_TIEU', 'Quan tri chi tieu',
         'Quan ly danh muc chi tieu, giao chi tieu nam, xem bao cao toan Chi cuc', true, CURRENT_TIMESTAMP)
        ON CONFLICT (ma_role) DO NOTHING;
    """)


def downgrade():
    op.execute("DELETE FROM public.platform_role WHERE ma_role IN ('THEO_DOI_CHI_TIEU', 'QT_CHI_TIEU')")
    op.execute("DROP VIEW IF EXISTS chi_tieu.v_luy_ke_thang")
    op.drop_table('lich_su_duyet', schema='chi_tieu')
    op.drop_table('dang_ky_thang', schema='chi_tieu')
    op.drop_table('giao_nam', schema='chi_tieu')
    op.drop_table('danh_muc_chi_tieu', schema='chi_tieu')
    op.drop_table('linh_vuc', schema='chi_tieu')
    op.execute("DROP SCHEMA IF EXISTS chi_tieu CASCADE")
