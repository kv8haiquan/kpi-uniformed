"""Tạo bảng dieu_chinh_kqcv + thêm is_loai_tru_kpi vào ke_khai_cong_viec

Revision ID: dieu_chinh_kqcv_20260506
Revises: phan_cong_phu_trach_20260505
Create Date: 2026-05-06

Yêu cầu 2 (Phase 3++) — Điều chỉnh KQCV:
- Thêm cờ is_loai_tru_kpi vào ke_khai_cong_viec (default false). Khi true,
  CV không được tính vào KPI của cả CC và LĐ.
- Tạo bảng dieu_chinh_kqcv lưu lịch sử + workflow phê duyệt mỗi lần LĐ
  điều chỉnh CV của CC (so_loi_chat_luong / so_loi_tien_do / is_loai_tru_kpi).
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "dieu_chinh_kqcv_20260506"
down_revision: Union[str, None] = "phan_cong_phu_trach_20260505"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


TBL = "dieu_chinh_kqcv"


def upgrade() -> None:
    # 1. Thêm cờ is_loai_tru_kpi vào ke_khai_cong_viec
    op.add_column(
        "ke_khai_cong_viec",
        sa.Column(
            "is_loai_tru_kpi",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
            comment="LĐ đánh dấu loại trừ CV này khỏi KPI (cả CC lẫn LĐ)",
        ),
    )

    # 2. Tạo bảng dieu_chinh_kqcv
    op.create_table(
        TBL,
        sa.Column(
            "id",
            sa.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "ke_khai_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("ke_khai_cong_viec.id", ondelete="RESTRICT"),
            nullable=False,
            comment="FK → ke_khai_cong_viec.id (CV bị điều chỉnh)",
        ),
        sa.Column(
            "nguoi_dieu_chinh_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("cong_chuc.id", ondelete="RESTRICT"),
            nullable=False,
            comment="LĐ tạo đề xuất điều chỉnh",
        ),
        sa.Column(
            "nguoi_phe_duyet_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("cong_chuc.id", ondelete="RESTRICT"),
            nullable=False,
            comment="LĐ cấp trên phê duyệt (auto-fill theo cấp bậc)",
        ),
        sa.Column(
            "gia_tri_cu",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            comment="Snapshot {so_loi_chat_luong, so_loi_tien_do, is_loai_tru_kpi} trước sửa",
        ),
        sa.Column(
            "gia_tri_moi",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            comment="Giá trị mới {so_loi_chat_luong, so_loi_tien_do, is_loai_tru_kpi}",
        ),
        sa.Column(
            "ly_do",
            sa.Text(),
            nullable=False,
            comment="Lý do điều chỉnh (bắt buộc)",
        ),
        sa.Column(
            "trang_thai",
            sa.String(20),
            nullable=False,
            server_default="NHAP",
            comment="NHAP / CHO_PHE_DUYET / DA_PHE_DUYET / TU_CHOI",
        ),
        sa.Column(
            "y_kien_phe_duyet",
            sa.Text(),
            nullable=True,
            comment="Ý kiến của LĐ cấp trên khi duyệt/từ chối",
        ),
        sa.Column(
            "ngay_phe_duyet",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="Thời điểm cấp trên duyệt (NULL nếu chưa)",
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
            "trang_thai IN ('NHAP', 'CHO_PHE_DUYET', 'DA_PHE_DUYET', 'TU_CHOI')",
            name="ck_dieu_chinh_kqcv_trang_thai",
        ),
        comment="Lịch sử + workflow điều chỉnh KQCV (Yêu cầu 2 — 06/05/2026)",
    )

    op.create_index("idx_dckqcv_ke_khai", TBL, ["ke_khai_id"])
    op.create_index("idx_dckqcv_nguoi_dc", TBL, ["nguoi_dieu_chinh_id"])
    op.create_index("idx_dckqcv_nguoi_pd", TBL, ["nguoi_phe_duyet_id"])
    op.create_index("idx_dckqcv_trang_thai", TBL, ["trang_thai"])


def downgrade() -> None:
    op.drop_index("idx_dckqcv_trang_thai", table_name=TBL)
    op.drop_index("idx_dckqcv_nguoi_pd", table_name=TBL)
    op.drop_index("idx_dckqcv_nguoi_dc", table_name=TBL)
    op.drop_index("idx_dckqcv_ke_khai", table_name=TBL)
    op.drop_table(TBL)
    op.drop_column("ke_khai_cong_viec", "is_loai_tru_kpi")
