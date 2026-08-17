"""Meeting 019: meeting.danh_gia_cuoc_hop + ghi_chu + ghi_chu_chia_se

Revision ID: mt_019_danh_gia_ghi_chu_20260817
Revises: mt_018_truc_ban_20260817
Create Date: 2026-08-17

Hai nghiệp vụ phụ của lichkv8, quyết định 17/08/2026 là giữ lại.
Xem docs/lich-cong-tac/KE_HOACH_TRIEN_KHAI.md §G2.4.

Khối lượng dữ liệu rất nhỏ nên thiết kế gọn, không tối ưu sớm:
  MEETING_RATING     105 bản ghi (SCORE 5.0 ×102, 4.0 ×3)
  MEETING_NOTE         7 bản ghi (3 còn hiệu lực)
  NOTE_SHARE           0 bản ghi
  MEETING_NOTE_FILE    1 bản ghi

Ghi chú của lichkv8 lưu nội dung dài thành file Drive riêng để tránh vượt giới
hạn kích thước ô Sheets. Trên PostgreSQL không còn giới hạn đó nên nội dung
lưu thẳng vào cột TEXT; file đính kèm dùng bảng meeting.tai_lieu sẵn có thông
qua ghi_chu_id.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "mt_019_danh_gia_ghi_chu_20260817"
down_revision: Union[str, None] = "mt_018_truc_ban_20260817"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


SCHEMA = "meeting"
T_DG = "danh_gia_cuoc_hop"
T_GC = "ghi_chu"
T_GC_CS = "ghi_chu_chia_se"


def upgrade() -> None:
    # --- đánh giá cuộc họp --------------------------------------------------
    op.create_table(
        T_DG,
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("cuoc_hop_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("meeting.cuoc_hop.id", ondelete="CASCADE"),
                  nullable=False),
        sa.Column("cong_chuc_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("public.cong_chuc.id"), nullable=False),
        sa.Column("diem", sa.SmallInteger(), nullable=False),
        sa.Column("ghi_chu", sa.Text(), nullable=True),
        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", postgresql.TIMESTAMP(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),

        # Một người chấm một cuộc họp một lần; chấm lại thì cập nhật.
        sa.UniqueConstraint("cuoc_hop_id", "cong_chuc_id",
                            name="uq_danh_gia_cuoc_hop_nguoi"),
        sa.CheckConstraint("diem BETWEEN 1 AND 5", name="ck_danh_gia_diem"),
        schema=SCHEMA,
    )
    op.create_index("idx_danh_gia_cuoc_hop", T_DG, ["cuoc_hop_id"], schema=SCHEMA)

    # --- ghi chú -----------------------------------------------------------
    op.create_table(
        T_GC,
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()"), nullable=False),
        # NULL = ghi chú độc lập, không gắn cuộc họp nào.
        sa.Column("cuoc_hop_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("meeting.cuoc_hop.id", ondelete="SET NULL"),
                  nullable=True),
        sa.Column("tieu_de", sa.String(300), nullable=False),
        sa.Column("noi_dung", sa.Text(), nullable=True),
        sa.Column("cong_chuc_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("public.cong_chuc.id"), nullable=False),
        sa.Column("is_ghim", sa.Boolean(), server_default=sa.text("FALSE"),
                  nullable=False),
        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", postgresql.TIMESTAMP(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), server_default=sa.text("FALSE"),
                  nullable=False),
        schema=SCHEMA,
    )
    where_active = sa.text("is_deleted = FALSE")
    op.create_index("idx_ghi_chu_nguoi_tao", T_GC, ["cong_chuc_id"],
                    schema=SCHEMA, postgresql_where=where_active)
    op.create_index("idx_ghi_chu_cuoc_hop", T_GC, ["cuoc_hop_id"],
                    schema=SCHEMA, postgresql_where=where_active)

    # --- chia sẻ ghi chú ---------------------------------------------------
    op.create_table(
        T_GC_CS,
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("ghi_chu_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("meeting.ghi_chu.id", ondelete="CASCADE"),
                  nullable=False),
        sa.Column("nguoi_gui_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("public.cong_chuc.id"), nullable=False),
        sa.Column("nguoi_nhan_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("public.cong_chuc.id"), nullable=False),
        sa.Column("loi_nhan", sa.Text(), nullable=True),
        sa.Column("da_doc", sa.Boolean(), server_default=sa.text("FALSE"),
                  nullable=False),
        sa.Column("thoi_diem_doc", postgresql.TIMESTAMP(timezone=True),
                  nullable=True),
        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),

        sa.UniqueConstraint("ghi_chu_id", "nguoi_nhan_id",
                            name="uq_ghi_chu_chia_se_nguoi_nhan"),
        sa.CheckConstraint("nguoi_gui_id <> nguoi_nhan_id",
                           name="ck_ghi_chu_chia_se_khac_nguoi"),
        schema=SCHEMA,
    )
    # Đếm ghi chú chưa đọc của một người — truy vấn chạy mỗi lần mở app.
    op.create_index("idx_ghi_chu_chia_se_chua_doc", T_GC_CS, ["nguoi_nhan_id"],
                    schema=SCHEMA, postgresql_where=sa.text("da_doc = FALSE"))

    # --- file đính kèm ghi chú: tái dùng meeting.tai_lieu -------------------
    op.add_column(
        "tai_lieu",
        sa.Column("ghi_chu_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("meeting.ghi_chu.id", ondelete="CASCADE"),
                  nullable=True),
        schema=SCHEMA,
    )
    op.alter_column("tai_lieu", "cuoc_hop_id", schema=SCHEMA, nullable=True)
    # Tài liệu phải thuộc đúng một trong hai: cuộc họp hoặc ghi chú.
    op.create_check_constraint(
        "ck_tai_lieu_chu_the", "tai_lieu",
        "(cuoc_hop_id IS NOT NULL AND ghi_chu_id IS NULL) OR "
        "(cuoc_hop_id IS NULL AND ghi_chu_id IS NOT NULL)",
        schema=SCHEMA,
    )
    op.create_index("idx_tai_lieu_ghi_chu", "tai_lieu", ["ghi_chu_id"],
                    schema=SCHEMA, postgresql_where=sa.text("ghi_chu_id IS NOT NULL"))


def downgrade() -> None:
    op.drop_index("idx_tai_lieu_ghi_chu", table_name="tai_lieu", schema=SCHEMA)
    op.drop_constraint("ck_tai_lieu_chu_the", "tai_lieu", type_="check", schema=SCHEMA)
    op.execute(f"DELETE FROM {SCHEMA}.tai_lieu WHERE cuoc_hop_id IS NULL")
    op.alter_column("tai_lieu", "cuoc_hop_id", schema=SCHEMA, nullable=False)
    op.drop_column("tai_lieu", "ghi_chu_id", schema=SCHEMA)

    op.drop_index("idx_ghi_chu_chia_se_chua_doc", table_name=T_GC_CS, schema=SCHEMA)
    op.drop_table(T_GC_CS, schema=SCHEMA)

    op.drop_index("idx_ghi_chu_cuoc_hop", table_name=T_GC, schema=SCHEMA)
    op.drop_index("idx_ghi_chu_nguoi_tao", table_name=T_GC, schema=SCHEMA)
    op.drop_table(T_GC, schema=SCHEMA)

    op.drop_index("idx_danh_gia_cuoc_hop", table_name=T_DG, schema=SCHEMA)
    op.drop_table(T_DG, schema=SCHEMA)
