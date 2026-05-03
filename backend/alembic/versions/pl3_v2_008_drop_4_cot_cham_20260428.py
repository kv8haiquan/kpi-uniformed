"""PL3 V2 - 008: Drop 4 cột chấm chi tiết khỏi danh_muc_sp_cong_viec

Revision ID: pl3_v2_008_drop_cham_20260428
Revises: pl3_v2_007_add_e_20260428
Create Date: 2026-04-28

Phase A.7b — Bỏ 4 cột chấm chi tiết theo quyết định nghiệp vụ:
  - Chỉ giữ 2 cột "quan trọng" cho V2_PL3: diem_cham + he_so_quy_doi
  - khung_diem_toi_da derive từ nhom_pl3 (Nhóm 1→100, Nhóm 2→200,..., Nhóm 5→500)
  - 4 cột chi tiết (kho/sáng tạo, quy trình/thời gian, phối hợp, phạm vi áp dụng)
    KHÔNG dùng cho nghiệp vụ → bỏ để giảm cồng kềnh.

Cột bị DROP:
  - diem_kho_sang_tao
  - diem_quy_trinh_thoi_gian
  - diem_phoi_hop
  - diem_pham_vi_ap_dung
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "pl3_v2_008_drop_cham_20260428"
down_revision: Union[str, None] = "pl3_v2_007_add_e_20260428"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


TBL = "danh_muc_sp_cong_viec"


def upgrade() -> None:
    op.drop_column(TBL, "diem_pham_vi_ap_dung")
    op.drop_column(TBL, "diem_phoi_hop")
    op.drop_column(TBL, "diem_quy_trinh_thoi_gian")
    op.drop_column(TBL, "diem_kho_sang_tao")


def downgrade() -> None:
    # Khôi phục 4 cột với giá trị NULL (data cũ không recover được)
    op.add_column(TBL, sa.Column(
        "diem_kho_sang_tao", sa.SmallInteger(), nullable=True,
        comment="Cột G Excel PL3"
    ))
    op.add_column(TBL, sa.Column(
        "diem_quy_trinh_thoi_gian", sa.SmallInteger(), nullable=True,
        comment="Cột H Excel PL3"
    ))
    op.add_column(TBL, sa.Column(
        "diem_phoi_hop", sa.SmallInteger(), nullable=True,
        comment="Cột I Excel PL3"
    ))
    op.add_column(TBL, sa.Column(
        "diem_pham_vi_ap_dung", sa.SmallInteger(), nullable=True,
        comment="Cột J Excel PL3"
    ))
