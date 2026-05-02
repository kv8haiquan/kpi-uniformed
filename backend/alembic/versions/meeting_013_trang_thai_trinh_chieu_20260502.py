"""Meeting 013: meeting.trang_thai_trinh_chieu

Revision ID: mt_013_ttc_20260502
Revises: mt_012_extend_dd_20260501
Create Date: 2026-05-02

Phase 4.1 — Page-Sync. State realtime của phiên trình chiếu trong cuộc họp.

Threat model + design notes:
- 1 cuộc họp = 1 row (UNIQUE cuoc_hop_id) → UPSERT pattern, KHÔNG có
  is_deleted vì state UPSERT 1-1, soft-delete vô nghĩa và sẽ chặn re-create.
  Cleanup data: ON DELETE CASCADE từ meeting.cuoc_hop.
- Lifecycle nhiều lần: bat_dau_luc/ket_thuc_luc lưu thời điểm CUỐI CÙNG
  (cho phép start/end nhiều lần, không lưu history — D8 plan v3.1).
- CHECK chk_ttc_active_has_doc: không cho is_active=TRUE mà chưa chọn
  tai_lieu — tránh state vô nghĩa.
- Index partial idx_ttc_active để query "đang trình chiếu" nhanh.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "mt_013_ttc_20260502"
down_revision: Union[str, None] = "mt_012_extend_dd_20260501"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


SCHEMA = "meeting"
TBL = "trang_thai_trinh_chieu"


def upgrade() -> None:
    op.create_table(
        TBL,
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        # 1-1 với cuoc_hop, CASCADE để dọn data khi xoá cuộc họp.
        sa.Column(
            "cuoc_hop_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("meeting.cuoc_hop.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        # Tài liệu hiện đang chiếu — SET NULL nếu tài liệu bị xoá để
        # client còn handler "tai liệu đã bị xoá" thay vì 500.
        sa.Column(
            "tai_lieu_hien_tai_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("meeting.tai_lieu.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "trang_hien_tai",
            sa.Integer(),
            server_default=sa.text("1"),
            nullable=False,
        ),
        sa.Column(
            "zoom_level",
            sa.Numeric(4, 2),
            server_default=sa.text("1.0"),
            nullable=False,
        ),
        # Lifecycle: cho phép start/end nhiều lần, ghi đè timestamp lần cuối.
        sa.Column(
            "is_active",
            sa.Boolean(),
            server_default=sa.text("FALSE"),
            nullable=False,
        ),
        sa.Column(
            "bat_dau_luc",
            postgresql.TIMESTAMP(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "ket_thuc_luc",
            postgresql.TIMESTAMP(timezone=True),
            nullable=True,
        ),
        # Audit
        sa.Column(
            "cap_nhat_luc",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.Column(
            "cap_nhat_boi_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("public.cong_chuc.id", ondelete="SET NULL"),
            nullable=True,
        ),
        # KHÔNG có is_deleted (v3.1 — state UPSERT 1-1, ON DELETE CASCADE đủ).
        sa.CheckConstraint(
            "trang_hien_tai > 0",
            name="chk_ttc_trang_positive",
        ),
        sa.CheckConstraint(
            "zoom_level >= 0.5 AND zoom_level <= 4.0",
            name="chk_ttc_zoom_range",
        ),
        sa.CheckConstraint(
            "NOT is_active OR tai_lieu_hien_tai_id IS NOT NULL",
            name="chk_ttc_active_has_doc",
        ),
        sa.CheckConstraint(
            "bat_dau_luc IS NULL OR ket_thuc_luc IS NULL OR bat_dau_luc <= ket_thuc_luc",
            name="chk_ttc_thoi_gian_hop_le",
        ),
        schema=SCHEMA,
    )

    # Index partial — chỉ index row đang trình chiếu (cardinality thấp).
    op.create_index(
        "idx_ttc_active",
        TBL,
        ["is_active"],
        schema=SCHEMA,
        postgresql_where=sa.text("is_active = TRUE"),
    )

    op.execute(
        "COMMENT ON TABLE meeting.trang_thai_trinh_chieu IS "
        "'Phase 4.1 — State phiên trình chiếu. 1 cuộc họp = 1 row, UPSERT, không soft delete.'"
    )


def downgrade() -> None:
    op.drop_index("idx_ttc_active", table_name=TBL, schema=SCHEMA)
    op.drop_table(TBL, schema=SCHEMA)
