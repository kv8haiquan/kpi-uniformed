"""add lms.cau_hoi_dgnl table + update linh_vuc seed data

Revision ID: add_lms_cau_hoi_dgnl_20260406
Revises: add_lms_dgnl_20260405
Create Date: 2026-04-06

- Tao bang lms.cau_hoi_dgnl — ngan hang cau hoi rieng cho DGNL
- Cap nhat seed linh_vuc: xoa 4 cu, them 8 moi
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = 'add_lms_cau_hoi_dgnl_20260406'
down_revision = 'add_lms_dgnl_20260405'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # === 1. Tao bang cau_hoi_dgnl ===
    op.create_table(
        'cau_hoi_dgnl',
        sa.Column('id', UUID(), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('linh_vuc_id', UUID(), sa.ForeignKey('lms.linh_vuc.id'), nullable=False),
        sa.Column('noi_dung', sa.Text(), nullable=False),
        sa.Column('giai_thich', sa.Text(), nullable=True),
        sa.Column('loai', sa.String(50), nullable=False),  # TRAC_NGHIEM_1, TRAC_NGHIEM_NHIEU, DUNG_SAI, TU_LUAN
        sa.Column('dap_an', JSONB(), nullable=False),
        sa.Column('diem', sa.Numeric(5, 2), server_default='1.0'),
        sa.Column('do_kho', sa.String(20), server_default='TRUNG_BINH'),  # DE, TRUNG_BINH, KHO
        sa.Column('nguoi_tao_id', UUID(), sa.ForeignKey('public.cong_chuc.id'), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        schema='lms',
    )

    op.create_index('idx_lms_chdgnl_linh_vuc', 'cau_hoi_dgnl', ['linh_vuc_id'],
                     schema='lms', postgresql_where=sa.text('is_active = true'))
    op.create_index('idx_lms_chdgnl_do_kho', 'cau_hoi_dgnl', ['do_kho'],
                     schema='lms', postgresql_where=sa.text('is_active = true'))
    op.create_index('idx_lms_chdgnl_lv_dk', 'cau_hoi_dgnl', ['linh_vuc_id', 'do_kho'],
                     schema='lms', postgresql_where=sa.text('is_active = true'))

    # === 2. Cap nhat seed linh_vuc ===
    # Soft-delete linh_vuc cu khong con dung (GIAM_SAT, KIEM_SOAT)
    op.execute("""
        UPDATE lms.linh_vuc SET is_active = FALSE
        WHERE ma_linh_vuc IN ('GIAM_SAT', 'KIEM_SOAT')
    """)

    # Upsert 8 linh vuc moi
    op.execute("""
        INSERT INTO lms.linh_vuc (ma_linh_vuc, ten_linh_vuc, mo_ta, thu_tu, is_active) VALUES
        ('KIEN_THUC_CHUNG', 'Kiến thức chung', 'Kiến thức pháp luật, quy định chung về hải quan', 1, TRUE),
        ('NGOAI_NGU_TRUNG', 'Ngoại ngữ tiếng Trung', 'Năng lực ngoại ngữ tiếng Trung Quốc', 2, TRUE),
        ('NGOAI_NGU_ANH', 'Ngoại ngữ tiếng Anh', 'Năng lực ngoại ngữ tiếng Anh', 3, TRUE),
        ('GIAM_SAT_HQ', 'Giám sát hải quan', 'Nghiệp vụ giám sát hải quan', 4, TRUE),
        ('THUE_HQ', 'Thuế hải quan', 'Nghiệp vụ thuế xuất nhập khẩu', 5, TRUE),
        ('CHONG_BUON_LAU', 'Chống buôn lậu', 'Nghiệp vụ chống buôn lậu, gian lận thương mại', 6, TRUE),
        ('KTSTTQ', 'Kiểm tra sau thông quan', 'Nghiệp vụ kiểm tra sau thông quan', 7, TRUE),
        ('CONG_VU_CC', 'Công vụ công chức', 'Kiến thức về công vụ, pháp luật cán bộ công chức', 8, TRUE)
        ON CONFLICT (ma_linh_vuc) DO UPDATE SET
            ten_linh_vuc = EXCLUDED.ten_linh_vuc,
            mo_ta = EXCLUDED.mo_ta,
            thu_tu = EXCLUDED.thu_tu,
            is_active = TRUE
    """)


def downgrade() -> None:
    op.drop_table('cau_hoi_dgnl', schema='lms')

    # Restore old seed
    op.execute("DELETE FROM lms.linh_vuc")
    op.execute("""
        INSERT INTO lms.linh_vuc (ma_linh_vuc, ten_linh_vuc, thu_tu) VALUES
        ('KIEN_THUC_CHUNG', 'Kiến thức chung', 1),
        ('GIAM_SAT', 'Nghiệp vụ giám sát', 2),
        ('KIEM_SOAT', 'Nghiệp vụ kiểm soát', 3),
        ('KTSTTQ', 'Kiểm tra sau thông quan', 4)
    """)
