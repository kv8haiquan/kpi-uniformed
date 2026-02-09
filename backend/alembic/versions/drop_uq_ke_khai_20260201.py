"""
Drop uq_ke_khai_unique - cho phep cung CV cap do ngay

Revision ID: drop_uq_ke_khai_20260201
Revises: add_ngay_gui_duyet_20260201
Create Date: 2026-02-01

Mô tả:
- DROP unique constraint uq_ke_khai_unique trên bảng ke_khai_cong_viec
- Cho phép CC kê khai cùng công việc + cùng cấp độ + cùng ngày nhiều lần
- Ví dụ: "Phục vụ thanh tra, kiểm tra" C3 ngày 01/02 - buổi sáng 1 lần, buổi chiều 1 lần
- Fix lỗi: UPDATE chỉ thêm số lỗi chất lượng/tiến độ cũng bị báo DUPLICATE_KE_KHAI
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = 'drop_uq_ke_khai_20260201'
down_revision = 'add_ngay_gui_duyet_20260201'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Xóa unique constraint - cho phép kê khai trùng CV + cấp độ + ngày.
    """
    op.drop_constraint('uq_ke_khai_unique', 'ke_khai_cong_viec', type_='unique')


def downgrade() -> None:
    """
    Rollback: Khôi phục unique constraint (nếu cần).
    LƯU Ý: Nếu đã có data trùng, downgrade sẽ FAIL.
    """
    op.create_unique_constraint(
        'uq_ke_khai_unique',
        'ke_khai_cong_viec',
        ['cong_chuc_id', 'danh_muc_sp_id', 'cap_do_id', 'thang', 'nam', 'ngay_thuc_hien']
    )