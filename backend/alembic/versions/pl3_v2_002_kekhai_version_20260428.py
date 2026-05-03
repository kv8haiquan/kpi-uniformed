"""PL3 V2 - 002: Add version flag + snapshot fields to ke_khai_cong_viec

Revision ID: pl3_v2_002_kekhai_version_20260428
Revises: pl3_v2_001_extend_danh_muc_20260428
Create Date: 2026-04-28

Phase A.2 — Cờ phiên bản + snapshot cho bản kê khai.

Quyết định LOCKED 8: cap_do_id thành nullable (V2 không dùng C1-C5).
Quyết định LOCKED 10: version_kekhai IN ('V1','V2_PL3') NOT NULL DEFAULT 'V1'.
Quyết định LOCKED 13: he_so_quy_doi_snapshot lưu lúc tạo, immutable
  (admin sửa danh mục về sau KHÔNG ảnh hưởng kê khai cũ).

Thêm các cột:
  - version_kekhai (VARCHAR(10), NOT NULL DEFAULT 'V1')
  - he_so_quy_doi_snapshot (NUMERIC(8,4), nullable — chỉ V2 mới có)
  - nhom_pl3_snapshot (SMALLINT, nullable)
  - linh_vuc_snapshot (VARCHAR(10), nullable)

Constraints:
  - CHECK version_kekhai IN ('V1','V2_PL3')
  - CHECK V2 phải có he_so_quy_doi_snapshot

Index:
  - idx_kekhai_version (version_kekhai, thang, nam) — tăng tốc query phân nhánh.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID as PG_UUID


revision: str = "pl3_v2_002_kk_ver_20260428"
down_revision: Union[str, None] = "pl3_v2_001_dm_20260428"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


TBL = "ke_khai_cong_viec"


def upgrade() -> None:
    # =========================================================================
    # 1) cap_do_id → nullable (V2 không dùng C1-C5)
    # =========================================================================
    op.alter_column(TBL, "cap_do_id", existing_type=PG_UUID(), nullable=True)

    # =========================================================================
    # 2) Thêm cờ version + snapshot fields
    # =========================================================================
    op.add_column(TBL, sa.Column(
        "version_kekhai",
        sa.String(length=10),
        nullable=False,
        server_default=sa.text("'V1'"),
        comment="Phiên bản công thức: V1 (ngày×96) hoặc V2_PL3 (tổng SP kê khai)",
    ))
    op.add_column(TBL, sa.Column(
        "he_so_quy_doi_snapshot",
        sa.Numeric(8, 4),
        nullable=True,
        comment="V2: snapshot he_so_quy_doi tại thời điểm kê khai (immutable)",
    ))
    op.add_column(TBL, sa.Column(
        "nhom_pl3_snapshot",
        sa.SmallInteger(),
        nullable=True,
        comment="V2: snapshot nhóm 1-5",
    ))
    op.add_column(TBL, sa.Column(
        "linh_vuc_snapshot",
        sa.String(length=10),
        nullable=True,
        comment="V2: snapshot lĩnh vực I-XV",
    ))

    # =========================================================================
    # 3) Check constraints
    # =========================================================================
    op.create_check_constraint(
        "ck_kekhai_version",
        TBL,
        "version_kekhai IN ('V1', 'V2_PL3')",
    )
    op.create_check_constraint(
        "ck_kekhai_v2_required",
        TBL,
        "version_kekhai <> 'V2_PL3' OR he_so_quy_doi_snapshot IS NOT NULL",
    )

    # =========================================================================
    # 4) Index hỗ trợ phân nhánh theo version
    # =========================================================================
    op.create_index(
        "idx_kekhai_version",
        TBL,
        ["version_kekhai", "thang", "nam"],
    )


def downgrade() -> None:
    op.drop_index("idx_kekhai_version", table_name=TBL)

    op.drop_constraint("ck_kekhai_v2_required", TBL, type_="check")
    op.drop_constraint("ck_kekhai_version", TBL, type_="check")

    op.drop_column(TBL, "linh_vuc_snapshot")
    op.drop_column(TBL, "nhom_pl3_snapshot")
    op.drop_column(TBL, "he_so_quy_doi_snapshot")
    op.drop_column(TBL, "version_kekhai")

    # Khôi phục cap_do_id NOT NULL — sẽ fail nếu có row V2 với cap_do_id NULL
    op.alter_column(TBL, "cap_do_id", existing_type=PG_UUID(), nullable=False)
