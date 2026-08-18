"""Thêm cột `loai` cho lich_su_dieu_chuyen (timeline hợp nhất)

Biến bảng lich_su_dieu_chuyen thành timeline hợp nhất: vừa ghi điều chuyển
đơn vị/vai trò, vừa ghi sự kiện vô hiệu hóa/kích hoạt tài khoản (kèm ngày
hiệu lực). Nhờ đó báo cáo suy được trạng thái công chức TẠI TỪNG THÁNG.

Cột mới `loai`:
- DIEU_CHUYEN : điều chuyển (mọi bản ghi cũ backfill về giá trị này qua
                server_default → an toàn với dữ liệu hiện có)
- VO_HIEU_HOA : sự kiện vô hiệu hóa
- KICH_HOAT   : sự kiện kích hoạt lại

Revision ID: lsdc_loai_20260717
Revises: phieu_quy_xep_loai_20260701
Create Date: 2026-07-17
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'lsdc_loai_20260717'
down_revision = 'phieu_quy_xep_loai_20260701'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'lich_su_dieu_chuyen',
        sa.Column(
            'loai',
            sa.String(20),
            nullable=False,
            server_default='DIEU_CHUYEN',
            comment='Loại bản ghi: DIEU_CHUYEN | VO_HIEU_HOA | KICH_HOAT',
        ),
    )


def downgrade() -> None:
    op.drop_column('lich_su_dieu_chuyen', 'loai')
