"""Add phieu_danh_gia_thang table

Revision ID: phieu_danh_gia_t_20260508
Revises: drop_chua_ht_kk_20260506
Create Date: 2026-05-08

Tạo bảng phiếu theo dõi, đánh giá công chức theo THÁNG (Mẫu 01A/01B):
- Mục 4 (Ưu điểm), 5 (Hạn chế) — CC tự nhập
- Mục 6 (Ý kiến cấp có thẩm quyền) — TDV/CCT nhập khi duyệt
- Workflow 1 cấp: NHAP → CHO_PHE_DUYET → DA_PHE_DUYET | BI_TU_CHOI

Cấu trúc giống `phieu_danh_gia_quy` nhưng key là (cong_chuc_id, thang, nam).
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "phieu_danh_gia_t_20260508"
down_revision: Union[str, None] = "drop_chua_ht_kk_20260506"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "phieu_danh_gia_thang",
        sa.Column(
            "id",
            sa.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            comment="Primary Key (UUID)",
        ),
        sa.Column(
            "cong_chuc_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("cong_chuc.id", ondelete="CASCADE"),
            nullable=False,
            comment="ID công chức sở hữu phiếu",
        ),
        sa.Column("thang", sa.SmallInteger(), nullable=False, comment="Tháng đánh giá (1-12)"),
        sa.Column("nam", sa.SmallInteger(), nullable=False, comment="Năm đánh giá"),
        sa.Column("uu_diem", sa.Text(), nullable=True, comment="Mục 4: Ưu điểm — CC tự nhập"),
        sa.Column("han_che", sa.Text(), nullable=True, comment="Mục 5: Hạn chế, khuyết điểm — CC tự nhập"),
        sa.Column(
            "y_kien_lanh_dao",
            sa.Text(),
            nullable=True,
            comment="Mục 6: Ý kiến nhận xét của cấp có thẩm quyền",
        ),
        sa.Column(
            "trang_thai",
            sa.String(length=20),
            server_default="NHAP",
            nullable=False,
            comment="Trạng thái workflow",
        ),
        sa.Column(
            "ngay_gui_duyet",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="Ngày CC nhấn gửi duyệt lần gần nhất",
        ),
        sa.Column(
            "nguoi_phe_duyet_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("cong_chuc.id", ondelete="SET NULL"),
            nullable=True,
            comment="ID người đã duyệt/từ chối",
        ),
        sa.Column(
            "ngay_phe_duyet",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="Ngày duyệt/từ chối gần nhất",
        ),
        sa.Column(
            "ly_do_tu_choi",
            sa.Text(),
            nullable=True,
            comment="Lý do từ chối (bắt buộc khi trang_thai=BI_TU_CHOI)",
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
            "cong_chuc_id", "thang", "nam",
            name="uq_phieu_thang_cc_thang_nam",
        ),
        sa.CheckConstraint("thang BETWEEN 1 AND 12", name="ck_phieu_thang_thang"),
        sa.CheckConstraint("nam BETWEEN 2020 AND 2100", name="ck_phieu_thang_nam"),
        sa.CheckConstraint(
            "trang_thai IN ('NHAP','CHO_PHE_DUYET','DA_PHE_DUYET','BI_TU_CHOI')",
            name="ck_phieu_thang_trang_thai",
        ),
    )

    op.create_index(
        "idx_phieu_thang_cc_thang_nam",
        "phieu_danh_gia_thang",
        ["cong_chuc_id", "thang", "nam"],
    )
    op.create_index("idx_phieu_thang_trang_thai", "phieu_danh_gia_thang", ["trang_thai"])
    op.create_index(
        "ix_phieu_danh_gia_thang_cong_chuc_id",
        "phieu_danh_gia_thang",
        ["cong_chuc_id"],
    )
    op.create_index(
        "ix_phieu_danh_gia_thang_nguoi_phe_duyet_id",
        "phieu_danh_gia_thang",
        ["nguoi_phe_duyet_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_phieu_danh_gia_thang_nguoi_phe_duyet_id", table_name="phieu_danh_gia_thang")
    op.drop_index("ix_phieu_danh_gia_thang_cong_chuc_id", table_name="phieu_danh_gia_thang")
    op.drop_index("idx_phieu_thang_trang_thai", table_name="phieu_danh_gia_thang")
    op.drop_index("idx_phieu_thang_cc_thang_nam", table_name="phieu_danh_gia_thang")
    op.drop_table("phieu_danh_gia_thang")
