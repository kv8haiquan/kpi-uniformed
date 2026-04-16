"""add lms dgnl tables (linh_vuc, vi_tri_viec_lam, ky_thi, cau_truc_de, thi_sinh) + alter cau_hoi

Revision ID: add_lms_dgnl_20260405
Create Date: 2026-04-05

Them 5 bang moi cho module Danh gia Nang luc:
  - lms.linh_vuc — Linh vuc nghiep vu
  - lms.vi_tri_viec_lam — Vi tri viec lam
  - lms.ky_thi — Ky thi danh gia nang luc
  - lms.cau_truc_de — Cau truc de thi theo vi tri
  - lms.thi_sinh — Thi sinh + ket qua

Sua bang lms.cau_hoi: them cot linh_vuc_id (FK -> linh_vuc)
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = 'add_lms_dgnl_20260405'
down_revision = ('add_lms_enrollment_approval', 'add_lms_anti_cheat_20260316')
branch_labels = None
depends_on = None


def upgrade() -> None:
    # === 1. linh_vuc ===
    op.create_table(
        'linh_vuc',
        sa.Column('id', UUID(), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('ma_linh_vuc', sa.String(50), nullable=False, unique=True),
        sa.Column('ten_linh_vuc', sa.String(200), nullable=False),
        sa.Column('mo_ta', sa.Text(), nullable=True),
        sa.Column('thu_tu', sa.Integer(), server_default='0'),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        schema='lms',
    )

    # Seed data linh vuc
    op.execute("""
        INSERT INTO lms.linh_vuc (ma_linh_vuc, ten_linh_vuc, mo_ta, thu_tu) VALUES
        ('KIEN_THUC_CHUNG', 'Kiến thức chung', 'Pháp luật, quy định hải quan chung', 1),
        ('GIAM_SAT', 'Nghiệp vụ giám sát', 'Giám sát hàng hóa, phương tiện', 2),
        ('KIEM_SOAT', 'Nghiệp vụ kiểm soát', 'Kiểm soát hải quan, chống buôn lậu', 3),
        ('KTSTTQ', 'Kiểm tra sau thông quan', 'Kiểm tra sau thông quan', 4)
    """)

    # === 2. vi_tri_viec_lam ===
    op.create_table(
        'vi_tri_viec_lam',
        sa.Column('id', UUID(), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('ma_vi_tri', sa.String(50), nullable=False, unique=True),
        sa.Column('ten_vi_tri', sa.String(200), nullable=False),
        sa.Column('mo_ta', sa.Text(), nullable=True),
        sa.Column('linh_vuc_ids', JSONB(), server_default=sa.text("'[]'::jsonb")),
        sa.Column('thu_tu', sa.Integer(), server_default='0'),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        schema='lms',
    )

    # Seed data vi tri viec lam
    op.execute("""
        INSERT INTO lms.vi_tri_viec_lam (ma_vi_tri, ten_vi_tri, thu_tu) VALUES
        ('GIAM_SAT_VIEN', 'Công chức giám sát', 1),
        ('KIEM_SOAT_VIEN', 'Công chức kiểm soát', 2),
        ('KTSTTQ_VIEN', 'Công chức KTSTTQ', 3),
        ('TONG_HOP', 'Công chức tổng hợp', 4),
        ('CNTT', 'Công chức CNTT', 5)
    """)

    # === 3. ky_thi ===
    op.create_table(
        'ky_thi',
        sa.Column('id', UUID(), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('ma_ky_thi', sa.String(50), nullable=False, unique=True),
        sa.Column('ten_ky_thi', sa.String(300), nullable=False),
        sa.Column('mo_ta', sa.Text(), nullable=True),
        # Thoi gian
        sa.Column('ngay_bat_dau', sa.DateTime(), nullable=False),
        sa.Column('ngay_ket_thuc', sa.DateTime(), nullable=False),
        sa.Column('thoi_gian_lam_bai_phut', sa.Integer(), nullable=False, server_default='60'),
        # Cau hinh
        sa.Column('diem_dat', sa.Numeric(5, 2), server_default='50.00'),
        sa.Column('so_lan_thi_toi_da', sa.Integer(), server_default='1'),
        sa.Column('tron_cau_hoi', sa.Boolean(), server_default=sa.text('true')),
        sa.Column('tron_dap_an', sa.Boolean(), server_default=sa.text('true')),
        sa.Column('hien_ket_qua', sa.Boolean(), server_default=sa.text('true')),
        sa.Column('hien_dap_an', sa.Boolean(), server_default=sa.text('false')),
        # Trang thai: NHAP, CHO_DUYET, DANG_MO, DA_DONG
        sa.Column('trang_thai', sa.String(50), server_default='NHAP'),
        sa.Column('nguoi_tao_id', UUID(), sa.ForeignKey('public.cong_chuc.id'), nullable=False),
        sa.Column('nguoi_duyet_id', UUID(), sa.ForeignKey('public.cong_chuc.id'), nullable=True),
        sa.Column('ngay_duyet', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        schema='lms',
    )

    op.create_index('idx_lms_kt_trang_thai', 'ky_thi', ['trang_thai'],
                     schema='lms', postgresql_where=sa.text("is_active = true"))
    op.create_index('idx_lms_kt_thoi_gian', 'ky_thi', ['ngay_bat_dau', 'ngay_ket_thuc'], schema='lms')

    # === 4. cau_truc_de ===
    op.create_table(
        'cau_truc_de',
        sa.Column('id', UUID(), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('ky_thi_id', UUID(), sa.ForeignKey('lms.ky_thi.id', ondelete='CASCADE'), nullable=False),
        sa.Column('vi_tri_id', UUID(), sa.ForeignKey('lms.vi_tri_viec_lam.id'), nullable=False),
        sa.Column('linh_vuc_id', UUID(), sa.ForeignKey('lms.linh_vuc.id'), nullable=False),
        sa.Column('so_cau_de', sa.Integer(), server_default='0'),
        sa.Column('so_cau_trung_binh', sa.Integer(), server_default='0'),
        sa.Column('so_cau_kho', sa.Integer(), server_default='0'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.UniqueConstraint('ky_thi_id', 'vi_tri_id', 'linh_vuc_id', name='uq_cau_truc_de_kt_vt_lv'),
        schema='lms',
    )

    op.create_index('idx_lms_ctd_ky_thi', 'cau_truc_de', ['ky_thi_id'], schema='lms')
    op.create_index('idx_lms_ctd_vi_tri', 'cau_truc_de', ['ky_thi_id', 'vi_tri_id'], schema='lms')

    # === 5. thi_sinh ===
    op.create_table(
        'thi_sinh',
        sa.Column('id', UUID(), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('ky_thi_id', UUID(), sa.ForeignKey('lms.ky_thi.id', ondelete='CASCADE'), nullable=False),
        sa.Column('cong_chuc_id', UUID(), sa.ForeignKey('public.cong_chuc.id'), nullable=False),
        sa.Column('vi_tri_id', UUID(), sa.ForeignKey('lms.vi_tri_viec_lam.id'), nullable=False),
        # Trang thai
        sa.Column('trang_thai', sa.String(50), server_default='CHUA_THI'),
        sa.Column('lan_thi_hien_tai', sa.Integer(), server_default='0'),
        # Ket qua tot nhat
        sa.Column('diem_tong', sa.Numeric(5, 2), nullable=True),
        sa.Column('xep_loai', sa.String(50), nullable=True),
        sa.Column('so_cau_dung', sa.Integer(), nullable=True),
        sa.Column('so_cau_sai', sa.Integer(), nullable=True),
        sa.Column('tong_so_cau', sa.Integer(), nullable=True),
        sa.Column('diem_theo_linh_vuc', JSONB(), server_default=sa.text("'{}'::jsonb")),
        # Thoi gian
        sa.Column('thoi_gian_bat_dau', sa.DateTime(), nullable=True),
        sa.Column('thoi_gian_nop', sa.DateTime(), nullable=True),
        sa.Column('thoi_gian_lam_giay', sa.Integer(), nullable=True),
        # De thi random
        sa.Column('de_thi_ids', JSONB(), server_default=sa.text("'[]'::jsonb")),
        sa.Column('chi_tiet_tra_loi', JSONB(), server_default=sa.text("'[]'::jsonb")),
        sa.Column('lich_su_thi', JSONB(), server_default=sa.text("'[]'::jsonb")),
        # Unique
        sa.UniqueConstraint('ky_thi_id', 'cong_chuc_id', name='uq_thi_sinh_kt_cc'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        schema='lms',
    )

    op.create_index('idx_lms_ts_ky_thi', 'thi_sinh', ['ky_thi_id'], schema='lms')
    op.create_index('idx_lms_ts_cc', 'thi_sinh', ['cong_chuc_id'], schema='lms')
    op.create_index('idx_lms_ts_tt', 'thi_sinh', ['ky_thi_id', 'trang_thai'], schema='lms')

    # === 6. Alter lms.cau_hoi — them linh_vuc_id ===
    op.add_column(
        'cau_hoi',
        sa.Column('linh_vuc_id', UUID(), sa.ForeignKey('lms.linh_vuc.id'), nullable=True),
        schema='lms',
    )
    op.create_index('idx_lms_ch_linh_vuc', 'cau_hoi', ['linh_vuc_id'],
                     schema='lms', postgresql_where=sa.text("is_active = true"))
    op.create_index('idx_lms_ch_lv_dk', 'cau_hoi', ['linh_vuc_id', 'do_kho'],
                     schema='lms', postgresql_where=sa.text("is_active = true"))


def downgrade() -> None:
    op.drop_index('idx_lms_ch_lv_dk', 'cau_hoi', schema='lms')
    op.drop_index('idx_lms_ch_linh_vuc', 'cau_hoi', schema='lms')
    op.drop_column('cau_hoi', 'linh_vuc_id', schema='lms')

    op.drop_table('thi_sinh', schema='lms')
    op.drop_table('cau_truc_de', schema='lms')
    op.drop_table('ky_thi', schema='lms')
    op.drop_table('vi_tri_viec_lam', schema='lms')
    op.drop_table('linh_vuc', schema='lms')
