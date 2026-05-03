"""Meeting 008: meeting.bien_ban

Revision ID: mt_008_bien_ban_20260430
Revises: mt_007_y_kien_20260430
Create Date: 2026-04-30

Biên bản họp với editor TipTap (JSON) + Mock CKS (MVP).
Theo HKG_DATABASE_DESIGN.md §4.7.

MVP: Mock CKS = SHA-256 + QR + watermark. CKS PAdES thật → Phase 6.

Mỗi cuộc họp chỉ có 1 biên bản → cuoc_hop_id UNIQUE.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "mt_008_bien_ban_20260430"
down_revision: Union[str, None] = "mt_007_y_kien_20260430"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


SCHEMA = "meeting"
TBL = "bien_ban"


def upgrade() -> None:
    op.create_table(
        TBL,
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()"), nullable=False),

        # Mỗi cuộc họp chỉ có 1 biên bản
        sa.Column("cuoc_hop_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("meeting.cuoc_hop.id", ondelete="CASCADE"),
                  unique=True, nullable=False),

        # Nội dung biên bản (TipTap JSON + cache HTML)
        sa.Column("noi_dung_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("noi_dung_html", sa.Text(), nullable=True),

        # Trạng thái
        sa.Column("trang_thai", sa.String(30),
                  server_default="DANG_SOAN", nullable=False),

        # File xuất ra
        sa.Column("file_pdf_minio_key", sa.String(500), nullable=True),
        sa.Column("file_docx_minio_key", sa.String(500), nullable=True),

        # Mock CKS (MVP) — chữ ký thật ở Phase 6
        sa.Column("is_mock_signed", sa.Boolean(),
                  server_default=sa.text("FALSE"), nullable=False),
        sa.Column("qr_xac_thuc", sa.String(500), nullable=True),
        sa.Column("hash_noi_dung", sa.String(64), nullable=True),

        # Audit ký
        sa.Column("nguoi_soan_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("public.cong_chuc.id"), nullable=False),
        sa.Column("nguoi_ky_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("public.cong_chuc.id"), nullable=True),
        sa.Column("thoi_gian_ky", postgresql.TIMESTAMP(timezone=True), nullable=True),

        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", postgresql.TIMESTAMP(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),

        sa.CheckConstraint(
            "trang_thai IN ('DANG_SOAN', 'TRINH_KY', 'DA_KY', 'CONG_BO')",
            name="ck_bien_ban_trang_thai",
        ),

        schema=SCHEMA,
    )

    op.create_index("idx_bien_ban_trang_thai", TBL, ["trang_thai"], schema=SCHEMA)


def downgrade() -> None:
    op.drop_index("idx_bien_ban_trang_thai", table_name=TBL, schema=SCHEMA)
    op.drop_table(TBL, schema=SCHEMA)
