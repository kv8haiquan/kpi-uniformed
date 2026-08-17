"""Meeting 017: meeting.lanh_dao_lien_quan

Revision ID: mt_017_ld_lien_quan_20260817
Revises: mt_016_mo_rong_cuoc_hop_20260817
Create Date: 2026-08-17

Lãnh đạo liên quan tới cuộc họp — trục của ba chức năng: Lịch lãnh đạo,
Dashboard thống kê theo lãnh đạo, và Tóm tắt lịch.
Xem docs/lich-cong-tac/KE_HOACH_TRIEN_KHAI.md §G2.2.

Vì sao chuẩn hoá được sạch: cột LANH_DAO_LIEN_QUAN của lichkv8 là văn bản tự
do phân cách bằng ';', nhưng đo trên dữ liệu thật thì 480/480 token khớp đúng
public.cong_chuc.ho_ten — 100%. Khác với CHU_TRI chỉ khớp 91%.

Đây KHÔNG phải bảng thành phần tham dự. Bảng MEETING_PARTICIPANT của lichkv8
thực chất cũng chỉ là chỉ mục sinh tự động từ trường này (294/294 dòng mang
ROLE_IN_MEETING='LANH_DAO_LIEN_QUAN'), không phải danh sách người dự do ai
nhập — nên dữ liệu người dự thật của 489 cuộc họp lịch sử không tồn tại.
Thành phần tham dự dùng bảng meeting.thanh_phan sẵn có, chỉ cho cuộc họp mới.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "mt_017_ld_lien_quan_20260817"
down_revision: Union[str, None] = "mt_016_mo_rong_cuoc_hop_20260817"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


SCHEMA = "meeting"
TBL = "lanh_dao_lien_quan"


def upgrade() -> None:
    op.create_table(
        TBL,
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("cuoc_hop_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("meeting.cuoc_hop.id", ondelete="CASCADE"),
                  nullable=False),
        sa.Column("cong_chuc_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("public.cong_chuc.id"), nullable=False),

        # Giữ thứ tự xuất hiện trong chuỗi gốc — lãnh đạo đầu tiên thường là
        # người chủ trì, thứ tự có ý nghĩa khi in tóm tắt lịch.
        sa.Column("thu_tu", sa.Integer(), server_default="1", nullable=False),

        # Nguyên văn token trước khi khớp, để truy vết khi đối soát.
        sa.Column("ten_goc", sa.String(200), nullable=True),

        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),

        sa.UniqueConstraint("cuoc_hop_id", "cong_chuc_id",
                            name="uq_lanh_dao_lien_quan_cuoc_hop_cong_chuc"),
        schema=SCHEMA,
    )

    op.create_index("idx_lanh_dao_lien_quan_cong_chuc", TBL, ["cong_chuc_id"],
                    schema=SCHEMA)
    op.create_index("idx_lanh_dao_lien_quan_cuoc_hop", TBL, ["cuoc_hop_id"],
                    schema=SCHEMA)


def downgrade() -> None:
    op.drop_index("idx_lanh_dao_lien_quan_cuoc_hop", table_name=TBL, schema=SCHEMA)
    op.drop_index("idx_lanh_dao_lien_quan_cong_chuc", table_name=TBL, schema=SCHEMA)
    op.drop_table(TBL, schema=SCHEMA)
