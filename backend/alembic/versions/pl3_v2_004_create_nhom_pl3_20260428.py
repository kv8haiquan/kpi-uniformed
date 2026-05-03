"""PL3 V2 - 004: Create nhom_cong_viec_pl3 table + seed 5 nhóm

Revision ID: pl3_v2_004_create_nhom_pl3_20260428
Revises: pl3_v2_003_danh_gia_thang_version_20260428
Create Date: 2026-04-28

Phase A.4 — Tạo bảng phân nhóm PL3 (thay 5 cấp độ C1-C5).

Bảng `nhom_cong_viec_pl3`:
  - 5 nhóm với điểm tối đa 100/200/300/400/500.
  - Read-only sau khi seed; admin chỉ chỉnh `ten_nhom`/`mo_ta`.
  - Bảng `cap_do_phuc_tap` (C1-C5) GIỮ làm fallback cho V1 (Quyết định LOCKED 6).
"""

from datetime import datetime, timezone
from typing import Sequence, Union
from uuid import uuid4

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID as PG_UUID


revision: str = "pl3_v2_004_nhom_20260428"
down_revision: Union[str, None] = "pl3_v2_003_dg_ver_20260428"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


TBL = "nhom_cong_viec_pl3"

# Dữ liệu seed
NHOM_DATA = [
    (1, "Nhóm 1 - Đơn giản", 100, "Công việc đơn giản, mức độ phức tạp thấp"),
    (2, "Nhóm 2 - Thông thường", 200, "Công việc thông thường, có quy trình rõ ràng"),
    (3, "Nhóm 3 - Nâng cao", 300, "Công việc nâng cao, đòi hỏi kinh nghiệm chuyên môn"),
    (4, "Nhóm 4 - Phức tạp", 400, "Công việc phức tạp, phối hợp nhiều bên"),
    (5, "Nhóm 5 - Đặc thù", 500, "Công việc đặc thù, mức độ phức tạp cao nhất"),
]


def upgrade() -> None:
    op.create_table(
        TBL,
        sa.Column(
            "id",
            PG_UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("nhom", sa.SmallInteger(), nullable=False, unique=True),
        sa.Column("ten_nhom", sa.String(length=200), nullable=False),
        sa.Column("diem_toi_da", sa.SmallInteger(), nullable=False),
        sa.Column("mo_ta", sa.Text(), nullable=True),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("TRUE"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.CheckConstraint("nhom BETWEEN 1 AND 5", name="ck_nhom_pl3_range"),
        sa.CheckConstraint("diem_toi_da > 0", name="ck_nhom_pl3_diem_pos"),
    )

    # Seed 5 nhóm
    now = datetime.now(timezone.utc)
    rows = []
    for nhom, ten, diem, mo_ta in NHOM_DATA:
        rows.append({
            "id": str(uuid4()),
            "nhom": nhom,
            "ten_nhom": ten,
            "diem_toi_da": diem,
            "mo_ta": mo_ta,
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        })

    nhom_table = sa.table(
        TBL,
        sa.column("id", PG_UUID(as_uuid=False)),
        sa.column("nhom", sa.SmallInteger),
        sa.column("ten_nhom", sa.String),
        sa.column("diem_toi_da", sa.SmallInteger),
        sa.column("mo_ta", sa.Text),
        sa.column("is_active", sa.Boolean),
        sa.column("created_at", sa.DateTime(timezone=True)),
        sa.column("updated_at", sa.DateTime(timezone=True)),
    )
    op.bulk_insert(nhom_table, rows)


def downgrade() -> None:
    op.drop_table(TBL)
