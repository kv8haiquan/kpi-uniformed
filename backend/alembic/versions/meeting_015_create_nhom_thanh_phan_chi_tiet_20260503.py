"""Meeting 015: meeting.nhom_thanh_phan_chi_tiet

Revision ID: mt_015_nhom_tp_chi_tiet_20260503
Revises: mt_014_nhom_tp_20260503
Create Date: 2026-05-03

Chi tiết thành viên trong nhóm — kèm vai_tro (CHU_TRI/THU_KY/THANH_VIEN)
và loai_tham_du (BAT_BUOC/THAM_KHAO).

Khi add nhóm vào cuộc họp:
- vai_tro CHU_TRI → auto-fill cuoc_hop.chu_toa_id nếu đang NULL
- vai_tro THU_KY  → auto-fill cuoc_hop.thu_ky_id nếu đang NULL
- vai_tro THANH_VIEN → chỉ là thành viên thường
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "mt_015_nhom_tp_chi_tiet_20260503"
down_revision: Union[str, None] = "mt_014_nhom_tp_20260503"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


SCHEMA = "meeting"
TBL = "nhom_thanh_phan_chi_tiet"


def upgrade() -> None:
    op.create_table(
        TBL,
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()"), nullable=False),

        sa.Column("nhom_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("meeting.nhom_thanh_phan.id", ondelete="CASCADE"),
                  nullable=False),
        sa.Column("cong_chuc_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("public.cong_chuc.id"), nullable=False),

        sa.Column("vai_tro", sa.String(20),
                  server_default="THANH_VIEN", nullable=False),
        sa.Column("loai_tham_du", sa.String(20),
                  server_default="BAT_BUOC", nullable=False),

        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),

        sa.CheckConstraint(
            "vai_tro IN ('CHU_TRI', 'THU_KY', 'THANH_VIEN')",
            name="ck_nhom_tp_chi_tiet_vai_tro",
        ),
        sa.CheckConstraint(
            "loai_tham_du IN ('BAT_BUOC', 'THAM_KHAO')",
            name="ck_nhom_tp_chi_tiet_loai_tham_du",
        ),
        sa.UniqueConstraint("nhom_id", "cong_chuc_id",
                            name="uq_nhom_tp_chi_tiet_nhom_cong_chuc"),

        schema=SCHEMA,
    )

    op.create_index("idx_nhom_tp_chi_tiet_nhom", TBL, ["nhom_id"], schema=SCHEMA)
    op.create_index("idx_nhom_tp_chi_tiet_cong_chuc", TBL, ["cong_chuc_id"], schema=SCHEMA)


def downgrade() -> None:
    op.drop_index("idx_nhom_tp_chi_tiet_cong_chuc", table_name=TBL, schema=SCHEMA)
    op.drop_index("idx_nhom_tp_chi_tiet_nhom", table_name=TBL, schema=SCHEMA)
    op.drop_table(TBL, schema=SCHEMA)
