"""Thêm cột xếp loại cho phieu_danh_gia_quy (mẫu 02A/02B theo NĐ 335/2025)

Bổ sung 4 cột phục vụ in phiếu ĐÁNH GIÁ, XẾP LOẠI công chức theo QUÝ:
- tu_de_xuat_xep_loai   : Mục 5   — CC tự đề xuất mức xếp loại
- de_xuat_xep_loai      : Mục III.2 — người trực tiếp sử dụng đề xuất
- quyet_dinh_xep_loai   : Mục IV.1  — quyết định của cấp có thẩm quyền
- y_kien_cap_tham_quyen : Mục IV.2  — ý kiến của cấp có thẩm quyền

Giá trị mã: HTXSNV | HTTNV | HTNV | KHTNV (NULL = chưa chọn).
Chỉ thêm vào phieu_danh_gia_quy (phieu tháng giữ nguyên).

Revision ID: phieu_quy_xep_loai_20260701
Revises: dgthang_tieuchi_20260626
Create Date: 2026-07-01
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'phieu_quy_xep_loai_20260701'
down_revision = 'dgthang_tieuchi_20260626'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'phieu_danh_gia_quy',
        sa.Column(
            'tu_de_xuat_xep_loai',
            sa.String(20),
            nullable=True,
            comment="Mục 5: Cá nhân tự đề xuất mức xếp loại (CC nhập)",
        ),
    )
    op.add_column(
        'phieu_danh_gia_quy',
        sa.Column(
            'de_xuat_xep_loai',
            sa.String(20),
            nullable=True,
            comment="Mục III.2: Người trực tiếp sử dụng đề xuất mức xếp loại",
        ),
    )
    op.add_column(
        'phieu_danh_gia_quy',
        sa.Column(
            'quyet_dinh_xep_loai',
            sa.String(20),
            nullable=True,
            comment="Mục IV.1: Quyết định mức xếp loại của cấp có thẩm quyền",
        ),
    )
    op.add_column(
        'phieu_danh_gia_quy',
        sa.Column(
            'y_kien_cap_tham_quyen',
            sa.Text(),
            nullable=True,
            comment="Mục IV.2: Ý kiến nhận xét của cấp có thẩm quyền (nếu có)",
        ),
    )


def downgrade() -> None:
    op.drop_column('phieu_danh_gia_quy', 'y_kien_cap_tham_quyen')
    op.drop_column('phieu_danh_gia_quy', 'quyet_dinh_xep_loai')
    op.drop_column('phieu_danh_gia_quy', 'de_xuat_xep_loai')
    op.drop_column('phieu_danh_gia_quy', 'tu_de_xuat_xep_loai')
