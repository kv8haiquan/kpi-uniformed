"""Thêm cột điều chỉnh điểm tổng cho chi_tiet_xep_loai (lãnh đạo sửa điểm)

Cho phép lãnh đạo (TDV/CCT) sửa điểm tổng của CC trong báo cáo xếp loại.
Lưu dưới dạng override nullable (diem_tong_dieu_chinh), KHÔNG đụng diem_tong
hệ thống — hàm tính lại điểm không chạm cột này nên override luôn được giữ.

Revision ID: add_diem_dc_ctxl_20260623
Revises: lms_phien_giamsat_20260622
Create Date: 2026-06-23
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_diem_dc_ctxl_20260623'
down_revision = 'lms_phien_giamsat_20260622'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'chi_tiet_xep_loai',
        sa.Column(
            'diem_tong_dieu_chinh',
            sa.Numeric(5, 2),
            nullable=True,
            comment='Điểm tổng lãnh đạo sửa tay (NULL = dùng diem_tong hệ thống)',
        ),
    )
    op.add_column(
        'chi_tiet_xep_loai',
        sa.Column(
            'ly_do_dieu_chinh_diem',
            sa.Text(),
            nullable=True,
            comment='Lý do lãnh đạo điều chỉnh điểm tổng',
        ),
    )


def downgrade() -> None:
    op.drop_column('chi_tiet_xep_loai', 'ly_do_dieu_chinh_diem')
    op.drop_column('chi_tiet_xep_loai', 'diem_tong_dieu_chinh')
