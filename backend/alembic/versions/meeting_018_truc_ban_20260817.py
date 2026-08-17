"""Meeting 018: meeting.tru_so + truc_ban + truc_ban_tru_so

Revision ID: mt_018_truc_ban_20260817
Revises: mt_017_ld_lien_quan_20260817
Create Date: 2026-08-17

Nghiệp vụ trực ban cuối tuần. Xem docs/lich-cong-tac/KE_HOACH_TRIEN_KHAI.md §G2.3.

QUAN TRỌNG — vì sao khoá theo trụ sở, không theo đơn vị:
Khảo sát G1.4 cho thấy trực ban tổ chức theo TRỤ SỞ VẬT LÝ. Cột UNIT_NAME của
lichkv8 ghi rõ "Trụ sở HQCK cảng Vạn Gia", "Trụ sở Chi cục HQKV VIII".
Quan hệ trụ sở ↔ đơn vị KHÔNG phải 1:1:
  - 6 trụ sở cửa khẩu  → khớp 1:1 với đơn vị HQCK tương ứng
  - KSHQ_HL + KSHQ_MC  → CÙNG một đơn vị KSHQ (một đơn vị, hai trụ sở)
  - CHICUC             → trụ sở dùng chung của VP, LDCC, CNTT, NVHQ, TCCB,
                         QLRR, PTSTQ — không ứng với đơn vị nào
Nếu khoá theo don_vi_id thì hai trụ sở Đội Kiểm soát sẽ chồng nhau và trụ sở
Chi cục không có chỗ để gắn.

Phạm vi: quyết định 17/08/2026 giữ nguyên trực ban chỉ cho thứ 7 và chủ nhật
(dữ liệu thật: 333/333 bản ghi đều DUTY_TYPE='Thứ 7/CN'). Cột `loai_truc` vẫn
được giữ để sau mở rộng ngày thường mà không phải sửa schema — giao diện lọc.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "mt_018_truc_ban_20260817"
down_revision: Union[str, None] = "mt_017_ld_lien_quan_20260817"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


SCHEMA = "meeting"
T_TRU_SO = "tru_so"
T_TRUC_BAN = "truc_ban"
T_TRUC_BAN_TS = "truc_ban_tru_so"

# 9 trụ sở, giữ nguyên mã cũ của lichkv8 để đối soát được.
# (ma_tru_so, ten_tru_so, ma_don_vi phụ trách hoặc None, thu_tu)
TRU_SO_SEED = [
    ("CHICUC",  "Trụ sở Chi cục HQKV VIII",                  None,       1),
    ("HONGAI",  "Trụ sở HQCK cảng Hòn Gai",                  "HQCK-HG",  2),
    ("CAMPHA",  "Trụ sở HQCK cảng Cẩm Phả",                  "HQCK-CP",  3),
    ("VANGIA",  "Trụ sở HQCK cảng Vạn Gia",                  "HQCK-VG",  4),
    ("HOANHMO", "Trụ sở HQCK Hoành Mô",                      "HQCK-HM",  5),
    ("BPS",     "Trụ sở HQCK Bắc Phong Sinh",                "HQCK-BPS", 6),
    ("MONGCAI", "Trụ sở HQCK quốc tế Móng Cái",              "HQCK-MC",  7),
    ("KSHQ_HL", "Đội Kiểm soát Hải quan - Khu vực Hạ Long",   "KSHQ",     8),
    ("KSHQ_MC", "Đội Kiểm soát Hải quan - Khu vực Móng Cái",  "KSHQ",     9),
]


def upgrade() -> None:
    # --- danh mục trụ sở ----------------------------------------------------
    op.create_table(
        T_TRU_SO,
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("ma_tru_so", sa.String(20), nullable=False),
        sa.Column("ten_tru_so", sa.String(200), nullable=False),
        # NULL với trụ sở dùng chung (CHICUC) — không ứng một đơn vị nào.
        sa.Column("don_vi_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("public.don_vi.id"), nullable=True),
        sa.Column("thu_tu", sa.Integer(), server_default="1", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("TRUE"),
                  nullable=False),
        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
        sa.UniqueConstraint("ma_tru_so", name="uq_tru_so_ma"),
        schema=SCHEMA,
    )

    # Seed 9 trụ sở, tra don_vi_id theo ma_don_vi. Đơn vị nào chưa có trong
    # public.don_vi thì để NULL thay vì làm migration vỡ.
    for ma, ten, ma_dv, thu_tu in TRU_SO_SEED:
        dv = f"(SELECT id FROM public.don_vi WHERE ma_don_vi = '{ma_dv}')" if ma_dv else "NULL"
        op.execute(
            f"INSERT INTO {SCHEMA}.{T_TRU_SO} "
            f"(ma_tru_so, ten_tru_so, don_vi_id, thu_tu) "
            f"VALUES ('{ma}', '{ten}', {dv}, {thu_tu})"
        )

    # --- bản ghi người trực -------------------------------------------------
    op.create_table(
        T_TRUC_BAN,
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("ngay_truc", sa.Date(), nullable=False),
        sa.Column("tru_so_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("meeting.tru_so.id"), nullable=False),

        # Mã đơn vị cũ của lichkv8 — giữ để đối soát sau di trú, không dùng
        # cho nghiệp vụ.
        sa.Column("unit_code_cu", sa.String(20), nullable=True),

        # cong_chuc_id nullable: người trực có thể là người ngoài danh sách,
        # hoặc tên không khớp được khi di trú.
        sa.Column("cong_chuc_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("public.cong_chuc.id"), nullable=True),
        sa.Column("ho_ten", sa.String(100), nullable=False),
        sa.Column("chuc_vu", sa.String(100), nullable=True),
        # Trường cốt lõi của nghiệp vụ này — 333/333 bản ghi đều có số.
        sa.Column("so_dien_thoai", sa.String(20), nullable=True),

        sa.Column("loai_truc", sa.String(20), server_default="CUOI_TUAN",
                  nullable=False),
        sa.Column("ca_truc", sa.String(20), server_default="CA_NGAY",
                  nullable=False),
        sa.Column("ghi_chu", sa.Text(), nullable=True),
        sa.Column("trang_thai", sa.String(20), server_default="NHAP",
                  nullable=False),

        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("public.cong_chuc.id"), nullable=True),
        sa.Column("updated_at", postgresql.TIMESTAMP(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("public.cong_chuc.id"), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), server_default=sa.text("FALSE"),
                  nullable=False),

        sa.CheckConstraint(
            "loai_truc IN ('CUOI_TUAN', 'NGAY_THUONG', 'LE_TET')",
            name="ck_truc_ban_loai",
        ),
        sa.CheckConstraint(
            "ca_truc IN ('CA_NGAY', 'SANG', 'CHIEU', 'DEM')",
            name="ck_truc_ban_ca",
        ),
        sa.CheckConstraint(
            "trang_thai IN ('NHAP', 'DA_NOP')",
            name="ck_truc_ban_trang_thai",
        ),
        schema=SCHEMA,
    )

    where_active = sa.text("is_deleted = FALSE")
    op.create_index("idx_truc_ban_ngay", T_TRUC_BAN, ["ngay_truc"],
                    schema=SCHEMA, postgresql_where=where_active)
    op.create_index("idx_truc_ban_tru_so", T_TRUC_BAN, ["tru_so_id"],
                    schema=SCHEMA, postgresql_where=where_active)
    op.create_index("idx_truc_ban_ngay_tru_so", T_TRUC_BAN,
                    ["ngay_truc", "tru_so_id"],
                    schema=SCHEMA, postgresql_where=where_active)

    # --- trạng thái nộp theo trụ sở + ngày ----------------------------------
    op.create_table(
        T_TRUC_BAN_TS,
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("ngay_truc", sa.Date(), nullable=False),
        sa.Column("tru_so_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("meeting.tru_so.id"), nullable=False),
        sa.Column("trang_thai", sa.String(20), server_default="NHAP",
                  nullable=False),
        sa.Column("nguoi_nop_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("public.cong_chuc.id"), nullable=True),
        sa.Column("thoi_diem_nop", postgresql.TIMESTAMP(timezone=True),
                  nullable=True),
        # Đã khoá thì đơn vị không sửa được nữa, chỉ quản trị mở lại.
        sa.Column("is_locked", sa.Boolean(), server_default=sa.text("FALSE"),
                  nullable=False),
        sa.Column("ghi_chu", sa.Text(), nullable=True),
        sa.Column("updated_at", postgresql.TIMESTAMP(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("public.cong_chuc.id"), nullable=True),

        sa.UniqueConstraint("ngay_truc", "tru_so_id",
                            name="uq_truc_ban_tru_so_ngay"),
        sa.CheckConstraint(
            "trang_thai IN ('NHAP', 'DA_NOP')",
            name="ck_truc_ban_tru_so_trang_thai",
        ),
        schema=SCHEMA,
    )
    op.create_index("idx_truc_ban_tru_so_ngay", T_TRUC_BAN_TS, ["ngay_truc"],
                    schema=SCHEMA)


def downgrade() -> None:
    op.drop_index("idx_truc_ban_tru_so_ngay", table_name=T_TRUC_BAN_TS, schema=SCHEMA)
    op.drop_table(T_TRUC_BAN_TS, schema=SCHEMA)

    op.drop_index("idx_truc_ban_ngay_tru_so", table_name=T_TRUC_BAN, schema=SCHEMA)
    op.drop_index("idx_truc_ban_tru_so", table_name=T_TRUC_BAN, schema=SCHEMA)
    op.drop_index("idx_truc_ban_ngay", table_name=T_TRUC_BAN, schema=SCHEMA)
    op.drop_table(T_TRUC_BAN, schema=SCHEMA)

    op.drop_table(T_TRU_SO, schema=SCHEMA)
