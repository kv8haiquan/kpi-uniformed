"""them bang lms.lich_su_reset_thi

Revision ID: lms_reset_luot_thi_20260831
Revises: lms_cau_hoi_hang_ngay_20260827
Create Date: 2026-08-31

Nhat ky reset luot thi DGNL. Truoc day muon xoa mot bai thi lam nham (nguoi
khac dang nhap nham tai khoan) phai sua tay bang SQL tren prod, khong luu vet
ai sua va vi sao. Bang nay bien viec do thanh mot thao tac co kiem soat:
bat buoc ly do, ghi ten nguoi thuc hien, va chup nguyen trang ban ghi truoc
khi sua vao `du_lieu_truoc` de con duong lui.

FK toi thi_sinh/ky_thi dung ON DELETE SET NULL (khong CASCADE): nhat ky phai
song lau hon doi tuong no ghi lai. Cac cot snapshot giu lai dinh danh khi FK
da bi go.

Bang nay CHI THEM MOI, khong sua bang nao dang chay.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


revision = 'lms_reset_luot_thi_20260831'
down_revision = 'lms_cau_hoi_hang_ngay_20260827'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'lich_su_reset_thi',
        sa.Column(
            'id', UUID(as_uuid=True), primary_key=True,
            server_default=sa.text('gen_random_uuid()'),
        ),
        sa.Column(
            'thi_sinh_id', UUID(as_uuid=True),
            sa.ForeignKey('lms.thi_sinh.id', ondelete='SET NULL'),
            nullable=True,
            comment='Ban ghi thi sinh bi reset (NULL neu ban ghi da bi xoa sau do)',
        ),
        sa.Column(
            'ky_thi_id', UUID(as_uuid=True),
            sa.ForeignKey('lms.ky_thi.id', ondelete='SET NULL'),
            nullable=True,
        ),
        sa.Column(
            'ky_thi_id_snapshot', UUID(as_uuid=True), nullable=False,
            comment='Dinh danh ky thi luu rieng — tra cuu duoc ca khi FK da NULL',
        ),
        sa.Column(
            'cong_chuc_id', UUID(as_uuid=True),
            sa.ForeignKey('public.cong_chuc.id'), nullable=False,
            comment='Nguoi bi reset',
        ),
        sa.Column(
            'nguoi_reset_id', UUID(as_uuid=True),
            sa.ForeignKey('public.cong_chuc.id'), nullable=False,
            comment='QT_DAO_TAO thuc hien reset',
        ),
        sa.Column(
            'loai_reset', sa.String(50), nullable=False,
            comment='XOA_SACH | MO_KHOA_LUOT',
        ),
        sa.Column('ly_do', sa.Text(), nullable=False),
        sa.Column('trang_thai_truoc', sa.String(50), nullable=True),
        sa.Column('lan_thi_truoc', sa.Integer(), nullable=True),
        sa.Column('diem_truoc', sa.Numeric(5, 2), nullable=True),
        sa.Column(
            'du_lieu_truoc', JSONB(), nullable=True,
            comment='Anh chup toan bo ban ghi thi_sinh truoc reset — duong lui',
        ),
        sa.Column(
            'thoi_gian', sa.DateTime(timezone=True),
            server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False,
        ),
        sa.Column(
            'created_at', sa.DateTime(timezone=True),
            server_default=sa.text('CURRENT_TIMESTAMP'),
        ),
        schema='lms',
    )
    # Tra nhat ky theo ky thi (man hinh thong ke) va theo nguoi (tra soat 1 CBCC)
    op.create_index(
        'idx_lms_reset_ky_thi', 'lich_su_reset_thi',
        ['ky_thi_id_snapshot', 'thoi_gian'], schema='lms',
    )
    op.create_index(
        'idx_lms_reset_cong_chuc', 'lich_su_reset_thi',
        ['cong_chuc_id'], schema='lms',
    )


def downgrade() -> None:
    op.drop_index('idx_lms_reset_cong_chuc', table_name='lich_su_reset_thi', schema='lms')
    op.drop_index('idx_lms_reset_ky_thi', table_name='lich_su_reset_thi', schema='lms')
    op.drop_table('lich_su_reset_thi', schema='lms')
