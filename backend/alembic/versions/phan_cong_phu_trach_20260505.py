"""Tạo bảng phan_cong_phu_trach

Revision ID: phan_cong_phu_trach_20260505
Revises: pl3_v2_010_cong_tac_20260504
Create Date: 2026-05-05

Phase 1 — KPI lãnh đạo công thức mới (từ tháng 4/2026):
- Lưu phân công CCT/PCCT phụ trách đơn vị nào theo thời gian.
- Versioned: hieu_luc_den NULL = đang còn hiệu lực.
- Không có UNIQUE constraint trên (don_vi_id, hieu_luc_tu) ở DB level —
  việc đảm bảo "1 đơn vị tại 1 thời điểm chỉ thuộc 1 LĐ" do service layer
  kiểm tra (vì cần xét cả overlap range, không phải point-in-time).
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "phan_cong_phu_trach_20260505"
down_revision: Union[str, None] = "pl3_v2_010_cong_tac_20260504"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


TBL = "phan_cong_phu_trach"


def upgrade() -> None:
    op.create_table(
        TBL,
        sa.Column(
            "id",
            sa.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            comment="Primary Key (UUID)",
        ),
        sa.Column(
            "lanh_dao_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("cong_chuc.id", ondelete="RESTRICT"),
            nullable=False,
            comment="FK → cong_chuc.id (LĐ phụ trách — CCT hoặc PCCT)",
        ),
        sa.Column(
            "don_vi_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("don_vi.id", ondelete="RESTRICT"),
            nullable=False,
            comment="FK → don_vi.id (đơn vị được phụ trách)",
        ),
        sa.Column(
            "hieu_luc_tu",
            sa.Date(),
            nullable=False,
            comment="Ngày bắt đầu hiệu lực phân công",
        ),
        sa.Column(
            "hieu_luc_den",
            sa.Date(),
            nullable=True,
            comment="Ngày kết thúc hiệu lực (NULL = vẫn còn hiệu lực)",
        ),
        sa.Column(
            "ghi_chu",
            sa.Text(),
            nullable=True,
            comment="Ghi chú phân công",
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
        sa.Column(
            "is_deleted",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.CheckConstraint(
            "hieu_luc_den IS NULL OR hieu_luc_den >= hieu_luc_tu",
            name="ck_pcpt_hieu_luc_range",
        ),
        comment="Phân công CCT/PCCT phụ trách đơn vị (versioned theo thời gian)",
    )

    op.create_index("idx_pcpt_don_vi", TBL, ["don_vi_id"])
    op.create_index("idx_pcpt_lanh_dao", TBL, ["lanh_dao_id"])
    op.create_index("idx_pcpt_hieu_luc_tu", TBL, ["hieu_luc_tu"])
    op.create_index("idx_pcpt_hieu_luc_den", TBL, ["hieu_luc_den"])
    op.create_index(
        "idx_pcpt_active",
        TBL,
        ["don_vi_id"],
        postgresql_where=sa.text("is_deleted = false AND hieu_luc_den IS NULL"),
    )


def downgrade() -> None:
    op.drop_index("idx_pcpt_active", table_name=TBL)
    op.drop_index("idx_pcpt_hieu_luc_den", table_name=TBL)
    op.drop_index("idx_pcpt_hieu_luc_tu", table_name=TBL)
    op.drop_index("idx_pcpt_lanh_dao", table_name=TBL)
    op.drop_index("idx_pcpt_don_vi", table_name=TBL)
    op.drop_table(TBL)
