"""PL3 V2 - 005: Add kpi_version_pinned to cong_chuc

Revision ID: pl3_v2_005_cong_chuc_pin_version_20260428
Revises: pl3_v2_004_create_nhom_pl3_20260428
Create Date: 2026-04-28

Phase A.5 — Cờ pin version cho từng công chức (Quyết định LOCKED 19).

Logic fallback:
  1. Nếu cong_chuc.kpi_version_pinned IS NOT NULL → dùng giá trị này.
  2. Ngược lại → đọc platform_config.value WHERE key='kpi_version_default'
     (seed mặc định 'V2_PL3' ở migration A.5b kế tiếp).

Test env: default V2_PL3 (đa số CC sẽ NULL → dùng V2_PL3 luôn).
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "pl3_v2_005_cc_pin_20260428"
down_revision: Union[str, None] = "pl3_v2_004_nhom_20260428"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


TBL = "cong_chuc"


def upgrade() -> None:
    op.add_column(TBL, sa.Column(
        "kpi_version_pinned",
        sa.String(length=10),
        nullable=True,
        comment="Pin riêng version cho CC. NULL = dùng platform_config(key='kpi_version_default')",
    ))

    op.create_check_constraint(
        "ck_cc_kpi_version",
        TBL,
        "kpi_version_pinned IS NULL OR kpi_version_pinned IN ('V1', 'V2_PL3')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_cc_kpi_version", TBL, type_="check")
    op.drop_column(TBL, "kpi_version_pinned")
