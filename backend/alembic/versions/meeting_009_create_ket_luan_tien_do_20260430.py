"""Meeting 009: meeting.ket_luan + meeting.tien_do

Revision ID: mt_009_ket_luan_20260430
Revises: mt_008_bien_ban_20260430
Create Date: 2026-04-30

Bảng 4.8 (ket_luan) + 4.9 (tien_do) gộp 1 migration vì:
- ket_luan là parent, tien_do FK ket_luan.id ON DELETE CASCADE
- 2 bảng nhỏ, dễ rollback chung

Theo HKG_DATABASE_DESIGN.md §4.8 + §4.9.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "mt_009_ket_luan_20260430"
down_revision: Union[str, None] = "mt_008_bien_ban_20260430"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


SCHEMA = "meeting"
TBL_KL = "ket_luan"
TBL_TD = "tien_do"


def upgrade() -> None:
    # ──────────────────────────────────────────────────────────────────
    # 4.8 ket_luan
    # ──────────────────────────────────────────────────────────────────
    op.create_table(
        TBL_KL,
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()"), nullable=False),

        sa.Column("cuoc_hop_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("meeting.cuoc_hop.id", ondelete="CASCADE"),
                  nullable=False),

        sa.Column("noi_dung", sa.Text(), nullable=False),
        sa.Column("nguoi_phu_trach_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("public.cong_chuc.id"), nullable=False),
        sa.Column("don_vi_phu_trach_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("public.don_vi.id"), nullable=True),

        sa.Column("han_hoan_thanh", sa.Date(), nullable=True),
        sa.Column("muc_uu_tien", sa.String(10),
                  server_default="TRUNG_BINH", nullable=False),

        sa.Column("tien_do_phan_tram", sa.Integer(),
                  server_default="0", nullable=False),

        sa.Column("trang_thai", sa.String(30),
                  server_default="CHUA_BAT_DAU", nullable=False),

        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", postgresql.TIMESTAMP(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
        sa.Column("is_deleted", sa.Boolean(),
                  server_default=sa.text("FALSE"), nullable=False),

        sa.CheckConstraint(
            "muc_uu_tien IN ('CAO', 'TRUNG_BINH', 'THAP')",
            name="ck_ket_luan_muc_uu_tien",
        ),
        sa.CheckConstraint(
            "tien_do_phan_tram BETWEEN 0 AND 100",
            name="ck_ket_luan_tien_do_range",
        ),
        sa.CheckConstraint(
            "trang_thai IN ('CHUA_BAT_DAU', 'DANG_LAM', 'HOAN_THANH', 'TRE_HAN', 'HUY')",
            name="ck_ket_luan_trang_thai",
        ),

        schema=SCHEMA,
    )

    where_active = sa.text("is_deleted = FALSE")
    op.create_index("idx_ket_luan_cuoc_hop", TBL_KL, ["cuoc_hop_id"],
                    schema=SCHEMA, postgresql_where=where_active)
    op.create_index("idx_ket_luan_phu_trach", TBL_KL, ["nguoi_phu_trach_id"],
                    schema=SCHEMA, postgresql_where=where_active)
    op.create_index(
        "idx_ket_luan_han", TBL_KL, ["han_hoan_thanh"],
        schema=SCHEMA,
        postgresql_where=sa.text("is_deleted = FALSE AND trang_thai != 'HOAN_THANH'"),
    )

    # ──────────────────────────────────────────────────────────────────
    # 4.9 tien_do
    # ──────────────────────────────────────────────────────────────────
    op.create_table(
        TBL_TD,
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()"), nullable=False),

        sa.Column("ket_luan_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("meeting.ket_luan.id", ondelete="CASCADE"),
                  nullable=False),

        sa.Column("mo_ta", sa.Text(), nullable=False),
        sa.Column("phan_tram_truoc", sa.Integer(), nullable=True),
        sa.Column("phan_tram_sau", sa.Integer(), nullable=False),

        sa.Column("file_minh_chung_minio_key", sa.String(500), nullable=True),

        sa.Column("nguoi_cap_nhat_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("public.cong_chuc.id"), nullable=False),
        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),

        sa.CheckConstraint(
            "phan_tram_sau BETWEEN 0 AND 100",
            name="ck_tien_do_phan_tram_sau_range",
        ),

        schema=SCHEMA,
    )

    op.create_index("idx_tien_do_ket_luan", TBL_TD, ["ket_luan_id"], schema=SCHEMA)


def downgrade() -> None:
    op.drop_index("idx_tien_do_ket_luan", table_name=TBL_TD, schema=SCHEMA)
    op.drop_table(TBL_TD, schema=SCHEMA)

    op.drop_index("idx_ket_luan_han", table_name=TBL_KL, schema=SCHEMA)
    op.drop_index("idx_ket_luan_phu_trach", table_name=TBL_KL, schema=SCHEMA)
    op.drop_index("idx_ket_luan_cuoc_hop", table_name=TBL_KL, schema=SCHEMA)
    op.drop_table(TBL_KL, schema=SCHEMA)
