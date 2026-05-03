"""PL3 V2 - 003: Add version flag + cache mẫu số to danh_gia_thang

Revision ID: pl3_v2_003_danh_gia_thang_version_20260428
Revises: pl3_v2_002_kekhai_version_20260428
Create Date: 2026-04-28

Phase A.3 — Cờ phiên bản tính điểm + cache mẫu số V2.

Quyết định LOCKED 11: version_tinh_diem IN ('V1','V2_PL3') NOT NULL DEFAULT 'V1'.
Quyết định LOCKED 12: 1 tháng = 1 version (enforce ở service layer).

Thêm các cột:
  - tong_sp_ke_khai (NUMERIC(12,2), nullable) — cache mẫu số V2,
    snapshot lúc CCT phê duyệt (đồng thời với is_khoa=TRUE).
  - version_tinh_diem (VARCHAR(10), NOT NULL DEFAULT 'V1').

Constraint:
  - CHECK version_tinh_diem IN ('V1','V2_PL3').
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "pl3_v2_003_dg_ver_20260428"
down_revision: Union[str, None] = "pl3_v2_002_kk_ver_20260428"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


TBL = "danh_gia_thang"


def upgrade() -> None:
    op.add_column(TBL, sa.Column(
        "tong_sp_ke_khai",
        sa.Numeric(12, 2),
        nullable=True,
        comment="V2: cache mẫu số = SUM(so_sp_goc_quy_doi đã duyệt), snapshot lúc CCT phê duyệt",
    ))
    op.add_column(TBL, sa.Column(
        "version_tinh_diem",
        sa.String(length=10),
        nullable=False,
        server_default=sa.text("'V1'"),
        comment="Phiên bản công thức tính điểm: V1 hoặc V2_PL3",
    ))

    op.create_check_constraint(
        "ck_dgthang_version",
        TBL,
        "version_tinh_diem IN ('V1', 'V2_PL3')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_dgthang_version", TBL, type_="check")
    op.drop_column(TBL, "version_tinh_diem")
    op.drop_column(TBL, "tong_sp_ke_khai")
