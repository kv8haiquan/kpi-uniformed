"""
Add ngay_gui_duyet column to bao_cao_xep_loai

Revision ID: add_ngay_gui_duyet_20260201
Revises: fix_loi_tu_danh_gia_01
Create Date: 2026-02-01

Mô tả:
- Thêm column ngay_gui_duyet (DateTime, nullable)
- Fix: Endpoint gui-duyet và cho-phe-duyet tham chiếu column này nhưng chưa có trong model
- Backfill: Gán ngay_gui_duyet = ngay_lap cho các báo cáo đã gửi duyệt
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_ngay_gui_duyet_20260201'
down_revision = 'fix_loi_tu_danh_gia_01'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Bước 1: Thêm column ngay_gui_duyet
    Bước 2: Backfill dữ liệu cho báo cáo đã gửi duyệt / đã duyệt
    """

    # =========================================================================
    # BƯỚC 1: Thêm column
    # =========================================================================
    op.add_column('bao_cao_xep_loai',
        sa.Column(
            'ngay_gui_duyet',
            sa.DateTime(timezone=True),
            nullable=True,
            comment='Ngày gửi phê duyệt (Đội trưởng gửi lên CCT)'
        )
    )

    # =========================================================================
    # BƯỚC 2: Backfill cho các báo cáo đã ở trạng thái CHO_PHE_DUYET
    # hoặc DA_PHE_DUYET hoặc TU_CHOI (đã từng gửi duyệt)
    # Dùng ngay_lap làm giá trị mặc định vì đó là thời điểm gần nhất
    # =========================================================================
    op.execute("""
        UPDATE bao_cao_xep_loai
        SET ngay_gui_duyet = COALESCE(ngay_lap, updated_at, created_at)
        WHERE trang_thai IN ('CHO_PHE_DUYET', 'DA_PHE_DUYET', 'TU_CHOI')
          AND ngay_gui_duyet IS NULL
          AND is_deleted = FALSE;
    """)


def downgrade() -> None:
    """
    Rollback: Xóa column ngay_gui_duyet
    """
    op.drop_column('bao_cao_xep_loai', 'ngay_gui_duyet')