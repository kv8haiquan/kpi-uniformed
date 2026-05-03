"""Favorites V2 - 001: Tạo bảng cong_viec_yeu_thich

Revision ID: fav_001_create_cvyt_20260430
Revises: hd111_001_create_20260429
Create Date: 2026-04-30

Tính năng "Công việc yêu thích của tôi" cho /ke-khai-v2:
Mỗi công chức mark các danh_muc_sp_cong_viec hay dùng để pick nhanh
trong các tháng sau.

Bảng public.cong_viec_yeu_thich:
- cong_chuc_id  → public.cong_chuc(id) ON DELETE CASCADE
- danh_muc_sp_id → public.danh_muc_sp_cong_viec(id) ON DELETE CASCADE
- UNIQUE(cong_chuc_id, danh_muc_sp_id) — idempotent POST

ON DELETE CASCADE để tự dọn favorites khi:
- Công chức bị xoá
- Danh mục PL3 bị admin xoá / soft-delete (tránh stale FK)
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "fav_001_create_cvyt_20260430"
down_revision: Union[str, None] = "hd111_001_create_20260429"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


TBL = "cong_viec_yeu_thich"


def upgrade() -> None:
    op.create_table(
        TBL,
        sa.Column(
            "id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "cong_chuc_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("cong_chuc.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "danh_muc_sp_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("danh_muc_sp_cong_viec.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "cong_chuc_id",
            "danh_muc_sp_id",
            name="uq_cvyt_cc_dm",
        ),
    )

    op.create_index(
        "idx_cvyt_cc_created",
        TBL,
        ["cong_chuc_id", sa.text("created_at DESC")],
    )


def downgrade() -> None:
    op.drop_index("idx_cvyt_cc_created", table_name=TBL)
    op.drop_table(TBL)
