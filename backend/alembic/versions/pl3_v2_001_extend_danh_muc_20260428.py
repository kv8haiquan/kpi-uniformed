"""PL3 V2 - 001: Extend danh_muc_sp_cong_viec for PL3 catalog

Revision ID: pl3_v2_001_extend_danh_muc_20260428
Revises: add_lms_bkt_thuc_hanh_20260422
Create Date: 2026-04-28

Phase A.1 — Mở rộng bảng danh_muc_sp_cong_viec để chứa 2.812 mục PL3.

Các thay đổi:
  - Thêm 14 cột PL3 (linh_vuc, ten_linh_vuc, nhiem_vu, cong_viec_chi_tiet,
    san_pham_dau_ra, nhom_pl3, khung_diem_toi_da, 4 cột chấm điểm,
    diem_cham, he_so_quy_doi, nguon_du_lieu).
  - Thêm CHECK constraints cho nhom_pl3, he_so_quy_doi, nguon_du_lieu.
  - Thêm indexes (linh_vuc, nhom_pl3, nguon_du_lieu) + GIN full-text search.
  - DROP NOT NULL trên sp_chuan_id (V2 không bắt buộc map về SP1-SP4).

Quyết định LOCKED 7: MỞ RỘNG bảng, KHÔNG tạo bảng mới.
Quyết định LOCKED 13: snapshot immutable (không gắn vào ke_khai ở migration này).
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "pl3_v2_001_dm_20260428"
down_revision: Union[str, None] = "add_lms_bkt_thuc_hanh_20260422"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Tên bảng & các identifier dùng nhiều lần
TBL = "danh_muc_sp_cong_viec"


def upgrade() -> None:
    # =========================================================================
    # 1) Thêm 14 cột mới (đều nullable trừ nguon_du_lieu)
    # =========================================================================
    op.add_column(TBL, sa.Column("linh_vuc", sa.String(length=10), nullable=True,
                                 comment="Mã lĩnh vực La Mã: I-XV"))
    op.add_column(TBL, sa.Column("ten_linh_vuc", sa.String(length=200), nullable=True,
                                 comment="Tên đầy đủ lĩnh vực"))
    op.add_column(TBL, sa.Column("nhiem_vu", sa.String(length=500), nullable=True,
                                 comment="Cột B Excel PL3"))
    op.add_column(TBL, sa.Column("cong_viec_chi_tiet", sa.Text(), nullable=True,
                                 comment="Cột C Excel PL3"))
    op.add_column(TBL, sa.Column("san_pham_dau_ra", sa.Text(), nullable=True,
                                 comment="Cột D Excel PL3"))
    op.add_column(TBL, sa.Column("nhom_pl3", sa.SmallInteger(), nullable=True,
                                 comment="Phân nhóm 1-5"))
    op.add_column(TBL, sa.Column("khung_diem_toi_da", sa.SmallInteger(), nullable=True,
                                 comment="100/200/300/400/500 tương ứng nhóm"))
    op.add_column(TBL, sa.Column("diem_kho_sang_tao", sa.SmallInteger(), nullable=True,
                                 comment="Cột G Excel PL3"))
    op.add_column(TBL, sa.Column("diem_quy_trinh_thoi_gian", sa.SmallInteger(), nullable=True,
                                 comment="Cột H Excel PL3"))
    op.add_column(TBL, sa.Column("diem_phoi_hop", sa.SmallInteger(), nullable=True,
                                 comment="Cột I Excel PL3"))
    op.add_column(TBL, sa.Column("diem_pham_vi_ap_dung", sa.SmallInteger(), nullable=True,
                                 comment="Cột J Excel PL3"))
    op.add_column(TBL, sa.Column("diem_cham", sa.SmallInteger(), nullable=True,
                                 comment="Cột K Excel PL3 = tổng 4 cột chấm"))
    op.add_column(TBL, sa.Column("he_so_quy_doi", sa.Numeric(8, 4), nullable=True,
                                 comment="Cột L Excel PL3 = diem_cham / 25"))
    op.add_column(TBL, sa.Column(
        "nguon_du_lieu",
        sa.String(length=20),
        nullable=False,
        server_default=sa.text("'V1'"),
        comment="V1 = 46 mục cũ; PL3 = 2.812 mục mới"
    ))

    # =========================================================================
    # 2) Check constraints
    # =========================================================================
    op.create_check_constraint(
        "ck_dmsp_nhom_pl3",
        TBL,
        "nhom_pl3 IS NULL OR nhom_pl3 BETWEEN 1 AND 5",
    )
    op.create_check_constraint(
        "ck_dmsp_he_so_pos",
        TBL,
        "he_so_quy_doi IS NULL OR he_so_quy_doi > 0",
    )
    op.create_check_constraint(
        "ck_dmsp_nguon_du_lieu",
        TBL,
        "nguon_du_lieu IN ('V1', 'PL3')",
    )

    # =========================================================================
    # 3) Indexes
    # =========================================================================
    op.create_index("idx_dmsp_linh_vuc", TBL, ["linh_vuc"])
    op.create_index("idx_dmsp_nhom_pl3", TBL, ["nhom_pl3"])
    op.create_index("idx_dmsp_nguon_du_lieu", TBL, ["nguon_du_lieu"])

    # GIN full-text search index — phải dùng raw SQL vì op.create_index
    # không hỗ trợ to_tsvector expression trực tiếp
    op.execute(
        "CREATE INDEX idx_dmsp_search ON danh_muc_sp_cong_viec "
        "USING gin (to_tsvector('simple', "
        "coalesce(ten_cong_viec, '') || ' ' || coalesce(cong_viec_chi_tiet, '')))"
    )

    # =========================================================================
    # 4) DROP NOT NULL trên sp_chuan_id (V2 không bắt buộc map SP1-SP4)
    # =========================================================================
    op.alter_column(TBL, "sp_chuan_id", existing_type=sa.dialects.postgresql.UUID(),
                    nullable=True)


def downgrade() -> None:
    # Revert NOT NULL trên sp_chuan_id (chú ý: nếu đã có row PL3 với sp_chuan_id NULL,
    # downgrade sẽ FAIL — đây là behavior đúng để báo cáo data conflict)
    op.alter_column(TBL, "sp_chuan_id", existing_type=sa.dialects.postgresql.UUID(),
                    nullable=False)

    # Drop indexes
    op.execute("DROP INDEX IF EXISTS idx_dmsp_search")
    op.drop_index("idx_dmsp_nguon_du_lieu", table_name=TBL)
    op.drop_index("idx_dmsp_nhom_pl3", table_name=TBL)
    op.drop_index("idx_dmsp_linh_vuc", table_name=TBL)

    # Drop check constraints
    op.drop_constraint("ck_dmsp_nguon_du_lieu", TBL, type_="check")
    op.drop_constraint("ck_dmsp_he_so_pos", TBL, type_="check")
    op.drop_constraint("ck_dmsp_nhom_pl3", TBL, type_="check")

    # Drop columns (reverse order of upgrade)
    op.drop_column(TBL, "nguon_du_lieu")
    op.drop_column(TBL, "he_so_quy_doi")
    op.drop_column(TBL, "diem_cham")
    op.drop_column(TBL, "diem_pham_vi_ap_dung")
    op.drop_column(TBL, "diem_phoi_hop")
    op.drop_column(TBL, "diem_quy_trinh_thoi_gian")
    op.drop_column(TBL, "diem_kho_sang_tao")
    op.drop_column(TBL, "khung_diem_toi_da")
    op.drop_column(TBL, "nhom_pl3")
    op.drop_column(TBL, "san_pham_dau_ra")
    op.drop_column(TBL, "cong_viec_chi_tiet")
    op.drop_column(TBL, "nhiem_vu")
    op.drop_column(TBL, "ten_linh_vuc")
    op.drop_column(TBL, "linh_vuc")
