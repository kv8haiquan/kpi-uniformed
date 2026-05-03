"""PL3 V2 - 007: Add 'E' to muc_xep_loai_enum (nghỉ thai sản — không xếp loại)

Revision ID: pl3_v2_007_add_e_to_muc_xep_loai_20260428
Revises: pl3_v2_006_seed_kpi_version_default_20260428
Create Date: 2026-04-28

Phase A.6b — Mở rộng enum muc_xep_loai_enum với value 'E'.

Quyết định LOCKED 20:
  - Mức D: CC kê 0 SP làm việc bình thường → KPI = 0 → xếp D.
  - Mức E: CC nghỉ thai sản → KHÔNG xếp loại.

Bảng bao_cao_xep_loai_chi_tiet (và .quy) đã dùng VARCHAR(1) với CHECK constraint
IN ('A','B','C','D','E') từ trước, nên không cần sửa. Chỉ enum Postgres còn thiếu E.

Enum này được dùng ở public.danh_gia_thang:
  - muc_xep_loai_tu_dong
  - muc_xep_loai_de_xuat
  - muc_xep_loai_chinh_thuc

LƯU Ý KỸ THUẬT:
  - PostgreSQL `ALTER TYPE ... ADD VALUE` KHÔNG chạy được trong transaction block.
  - Phải dùng `autocommit_block()` của Alembic để wrap.
  - Downgrade KHÔNG hỗ trợ trực tiếp `DROP VALUE` — phải tạo enum mới.
    Để đơn giản, downgrade là no-op (với cảnh báo log).
"""

from typing import Sequence, Union

from alembic import op


revision: str = "pl3_v2_007_add_e_20260428"
down_revision: Union[str, None] = "pl3_v2_006_seed_def_20260428"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ALTER TYPE ADD VALUE phải chạy ngoài transaction
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE muc_xep_loai_enum ADD VALUE IF NOT EXISTS 'E'")


def downgrade() -> None:
    # PostgreSQL không hỗ trợ DROP VALUE trực tiếp.
    # Để rollback an toàn, cần:
    #   1. Cập nhật mọi row có muc_xep_loai_* = 'E' về NULL hoặc giá trị khác.
    #   2. Tạo enum mới (A,B,C,D), cast columns, drop enum cũ, rename.
    # Quá rủi ro để tự động hoá — yêu cầu rollback thủ công nếu cần.
    print(
        "[WARNING] downgrade pl3_v2_007: PostgreSQL không hỗ trợ DROP VALUE từ enum. "
        "Value 'E' vẫn còn trong muc_xep_loai_enum sau downgrade. "
        "Để rollback hoàn toàn, cần migration thủ công recreate enum."
    )
