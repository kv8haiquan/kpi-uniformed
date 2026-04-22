"""Add bai kiem tra thuc hanh (upload video) + cham tay columns

Revision ID: add_lms_bkt_thuc_hanh_20260422
Revises: add_last_recalc_quy_20260421
Create Date: 2026-04-22

Them cot cho:
  - lms.bai_kiem_tra:
      + loai_bai_kiem_tra (TRAC_NGHIEM | THUC_HANH) — default TRAC_NGHIEM
      + yeu_cau_bai_lam (TEXT) — hướng dẫn nộp cho học viên
      + dung_luong_toi_da_mb (INT) — giới hạn file upload
      + dinh_dang_cho_phep (VARCHAR) — CSV các extension (vd: "mp4,mov,webm")
  - lms.ket_qua_bai_kiem_tra:
      + bai_nop_url, bai_nop_ten_file, bai_nop_size_bytes, bai_nop_content_type
      + ngay_nop
      + nguoi_cham_id (FK public.cong_chuc)
      + diem_cham_tay
      + nhan_xet
      + trang_thai_cham (CHO_CHAM | DA_CHAM)
      + ngay_cham
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "add_lms_bkt_thuc_hanh_20260422"
down_revision: Union[str, None] = "add_last_recalc_quy_20260421"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # =====================================================================
    # lms.bai_kiem_tra — cau hinh cho BKT thuc hanh
    # =====================================================================
    op.add_column(
        "bai_kiem_tra",
        sa.Column(
            "loai_bai_kiem_tra",
            sa.String(50),
            server_default="TRAC_NGHIEM",
            nullable=False,
            comment="TRAC_NGHIEM | THUC_HANH",
        ),
        schema="lms",
    )
    op.add_column(
        "bai_kiem_tra",
        sa.Column(
            "yeu_cau_bai_lam",
            sa.Text(),
            nullable=True,
            comment="Hướng dẫn / yêu cầu bài nộp (thực hành)",
        ),
        schema="lms",
    )
    op.add_column(
        "bai_kiem_tra",
        sa.Column(
            "dung_luong_toi_da_mb",
            sa.Integer(),
            server_default="500",
            nullable=True,
            comment="Giới hạn dung lượng bài nộp (MB)",
        ),
        schema="lms",
    )
    op.add_column(
        "bai_kiem_tra",
        sa.Column(
            "dinh_dang_cho_phep",
            sa.String(200),
            server_default="mp4,mov,webm",
            nullable=True,
            comment="CSV định dạng file được chấp nhận (không có dấu chấm)",
        ),
        schema="lms",
    )

    # =====================================================================
    # lms.ket_qua_bai_kiem_tra — bai nop + cham tay
    # =====================================================================
    op.add_column(
        "ket_qua_bai_kiem_tra",
        sa.Column("bai_nop_url", sa.String(500), nullable=True),
        schema="lms",
    )
    op.add_column(
        "ket_qua_bai_kiem_tra",
        sa.Column("bai_nop_ten_file", sa.String(255), nullable=True),
        schema="lms",
    )
    op.add_column(
        "ket_qua_bai_kiem_tra",
        sa.Column("bai_nop_size_bytes", sa.BigInteger(), nullable=True),
        schema="lms",
    )
    op.add_column(
        "ket_qua_bai_kiem_tra",
        sa.Column("bai_nop_content_type", sa.String(100), nullable=True),
        schema="lms",
    )
    op.add_column(
        "ket_qua_bai_kiem_tra",
        sa.Column("ngay_nop", sa.DateTime(), nullable=True),
        schema="lms",
    )
    op.add_column(
        "ket_qua_bai_kiem_tra",
        sa.Column(
            "nguoi_cham_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("public.cong_chuc.id"),
            nullable=True,
        ),
        schema="lms",
    )
    op.add_column(
        "ket_qua_bai_kiem_tra",
        sa.Column("diem_cham_tay", sa.Numeric(5, 2), nullable=True),
        schema="lms",
    )
    op.add_column(
        "ket_qua_bai_kiem_tra",
        sa.Column("nhan_xet", sa.Text(), nullable=True),
        schema="lms",
    )
    op.add_column(
        "ket_qua_bai_kiem_tra",
        sa.Column(
            "trang_thai_cham",
            sa.String(50),
            nullable=True,
            comment="CHO_CHAM | DA_CHAM (NULL = BKT trắc nghiệm)",
        ),
        schema="lms",
    )
    op.add_column(
        "ket_qua_bai_kiem_tra",
        sa.Column("ngay_cham", sa.DateTime(), nullable=True),
        schema="lms",
    )


def downgrade() -> None:
    # lms.ket_qua_bai_kiem_tra
    op.drop_column("ket_qua_bai_kiem_tra", "ngay_cham", schema="lms")
    op.drop_column("ket_qua_bai_kiem_tra", "trang_thai_cham", schema="lms")
    op.drop_column("ket_qua_bai_kiem_tra", "nhan_xet", schema="lms")
    op.drop_column("ket_qua_bai_kiem_tra", "diem_cham_tay", schema="lms")
    op.drop_column("ket_qua_bai_kiem_tra", "nguoi_cham_id", schema="lms")
    op.drop_column("ket_qua_bai_kiem_tra", "ngay_nop", schema="lms")
    op.drop_column("ket_qua_bai_kiem_tra", "bai_nop_content_type", schema="lms")
    op.drop_column("ket_qua_bai_kiem_tra", "bai_nop_size_bytes", schema="lms")
    op.drop_column("ket_qua_bai_kiem_tra", "bai_nop_ten_file", schema="lms")
    op.drop_column("ket_qua_bai_kiem_tra", "bai_nop_url", schema="lms")

    # lms.bai_kiem_tra
    op.drop_column("bai_kiem_tra", "dinh_dang_cho_phep", schema="lms")
    op.drop_column("bai_kiem_tra", "dung_luong_toi_da_mb", schema="lms")
    op.drop_column("bai_kiem_tra", "yeu_cau_bai_lam", schema="lms")
    op.drop_column("bai_kiem_tra", "loai_bai_kiem_tra", schema="lms")
