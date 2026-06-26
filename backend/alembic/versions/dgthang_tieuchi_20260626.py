"""Thêm cột diem_danh_gia_thang cho tieu_chi_chung_danh_gia; gỡ cột sửa điểm tổng cũ

- Thêm tieu_chi_chung_danh_gia.diem_danh_gia_thang: điểm 'Đánh giá tháng' lãnh đạo
  chỉnh ở giai đoạn báo cáo xếp loại (NULL = dùng diem_phe_duyet / Trưởng duyệt).
- Drop chi_tiet_xep_loai.diem_tong_dieu_chinh + ly_do_dieu_chinh_diem (tính năng sửa
  điểm tổng trực tiếp đã bị thay thế; prod 0 dòng dữ liệu).

Revision ID: dgthang_tieuchi_20260626
Revises: add_diem_dc_ctxl_20260623
Create Date: 2026-06-26
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'dgthang_tieuchi_20260626'
down_revision = 'add_diem_dc_ctxl_20260623'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Thêm cột điểm "Đánh giá tháng" per-tiêu-chí
    op.add_column(
        'tieu_chi_chung_danh_gia',
        sa.Column(
            'diem_danh_gia_thang',
            sa.Numeric(4, 2),
            nullable=True,
            comment="Điểm 'Đánh giá tháng' lãnh đạo chỉnh ở giai đoạn báo cáo xếp loại (NULL = dùng diem_phe_duyet)",
        ),
    )
    # 2. Gỡ cột tính năng sửa điểm tổng trực tiếp (đã bị thay thế)
    op.drop_column('chi_tiet_xep_loai', 'ly_do_dieu_chinh_diem')
    op.drop_column('chi_tiet_xep_loai', 'diem_tong_dieu_chinh')


def downgrade() -> None:
    op.add_column(
        'chi_tiet_xep_loai',
        sa.Column('diem_tong_dieu_chinh', sa.Numeric(5, 2), nullable=True),
    )
    op.add_column(
        'chi_tiet_xep_loai',
        sa.Column('ly_do_dieu_chinh_diem', sa.Text(), nullable=True),
    )
    op.drop_column('tieu_chi_chung_danh_gia', 'diem_danh_gia_thang')
