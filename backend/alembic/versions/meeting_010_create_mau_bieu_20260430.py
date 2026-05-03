"""Meeting 010: meeting.mau_bieu

Revision ID: mt_010_mau_bieu_20260430
Revises: mt_009_ket_luan_20260430
Create Date: 2026-04-30

Template biên bản (DOCX) lưu trên MinIO. Theo HKG_DATABASE_DESIGN.md §4.10.

MVP: 1 template chung (ap_dung_cho='TAT_CA').
Phase 8: tách Đảng/Chuyên môn riêng.

LƯU Ý: seed template mặc định KHÔNG nằm trong G1.
G1 chỉ tạo bảng. Seed cần upload bien_ban_chung.docx → đẩy sang G3 (Module 9).
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "mt_010_mau_bieu_20260430"
down_revision: Union[str, None] = "mt_009_ket_luan_20260430"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


SCHEMA = "meeting"
TBL = "mau_bieu"


def upgrade() -> None:
    op.create_table(
        TBL,
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()"), nullable=False),

        sa.Column("loai", sa.String(30), nullable=False),

        sa.Column("ten_mau", sa.String(200), nullable=False),
        sa.Column("mo_ta", sa.Text(), nullable=True),

        # Áp dụng cho khối nào (MVP: TAT_CA)
        sa.Column("ap_dung_cho", sa.String(50),
                  server_default="TAT_CA", nullable=False),

        sa.Column("minio_key", sa.String(500), nullable=False),
        sa.Column("phien_ban", sa.Integer(),
                  server_default="1", nullable=False),
        sa.Column("la_mac_dinh", sa.Boolean(),
                  server_default=sa.text("FALSE"), nullable=False),

        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", postgresql.TIMESTAMP(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("public.cong_chuc.id"), nullable=False),
        sa.Column("is_deleted", sa.Boolean(),
                  server_default=sa.text("FALSE"), nullable=False),

        sa.CheckConstraint(
            "loai IN ('BIEN_BAN', 'GIAY_MOI', 'KET_LUAN', 'BAO_CAO')",
            name="ck_mau_bieu_loai",
        ),

        schema=SCHEMA,
    )

    op.create_index(
        "idx_mau_bieu_loai", TBL, ["loai"],
        schema=SCHEMA, postgresql_where=sa.text("is_deleted = FALSE"),
    )


def downgrade() -> None:
    op.drop_index("idx_mau_bieu_loai", table_name=TBL, schema=SCHEMA)
    op.drop_table(TBL, schema=SCHEMA)
