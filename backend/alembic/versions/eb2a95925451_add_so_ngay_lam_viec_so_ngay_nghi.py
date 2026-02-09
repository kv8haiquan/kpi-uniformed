"""Add so_ngay_lam_viec so_ngay_nghi - SIMPLIFIED

Revision ID: eb2a95925451
Revises: 006_xep_loai_moi
Create Date: 2026-01-30 10:51:45.964137

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'eb2a95925451'
down_revision: Union[str, None] = '006_xep_loai_moi'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Chỉ thêm 2 cột mới vào bảng chi_tiet_xep_loai
    op.add_column('chi_tiet_xep_loai', 
        sa.Column('so_ngay_lam_viec', sa.Numeric(5, 1), nullable=True, 
                  comment='Số ngày làm việc trong tháng'))
    op.add_column('chi_tiet_xep_loai', 
        sa.Column('so_ngay_nghi', sa.Numeric(5, 1), nullable=True, 
                  comment='Số ngày nghỉ trong tháng'))


def downgrade() -> None:
    # Xóa 2 cột khi rollback
    op.drop_column('chi_tiet_xep_loai', 'so_ngay_nghi')
    op.drop_column('chi_tiet_xep_loai', 'so_ngay_lam_viec')