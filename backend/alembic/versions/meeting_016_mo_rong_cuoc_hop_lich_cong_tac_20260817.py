"""Meeting 016: mở rộng meeting.cuoc_hop cho Lịch công tác

Revision ID: mt_016_mo_rong_cuoc_hop_20260817
Revises: zalo_oa_20260731
Create Date: 2026-08-17

LƯU Ý: chuỗi alembic của repo này TUYẾN TÍNH qua tất cả module (kpi, lms,
zalo, meeting…), không tách nhánh theo module. Head thật lúc viết migration
này là `zalo_oa_20260731`, không phải `mt_015_nhom_tp_chi_tiet_20260503` —
nối vào mt_015 sẽ tạo head thứ hai và `alembic upgrade head` báo lỗi
"Multiple head revisions are present".

Hợp nhất nghiệp vụ Lịch công tác (lichkv8) vào cùng bảng cuộc họp của HKG.
Xem docs/lich-cong-tac/KE_HOACH_TRIEN_KHAI.md §G2.1.

Cách giữ ràng buộc của HKG mà vẫn nạp được dữ liệu lịch sử:
- Thêm cột phân loại `nguon` = HKG | LICH_CONG_TAC.
- Nới `chu_toa_id` và `don_vi_to_chuc_id` thành nullable, vì 117/489 cuộc họp
  lịch sử không có chủ trì và không xác định được đơn vị tổ chức.
- Bù lại bằng CHECK có điều kiện: dòng `nguon='HKG'` VẪN không thể thiếu chủ
  trì và đơn vị tổ chức — ép ở mức cơ sở dữ liệu, không phải tầng ứng dụng.

Nhờ vậy không phải sửa `chu_toa_id` ở 103 chỗ trong code HKG đã viết.
Field riêng của HKG phát sinh về sau cho vào bảng mở rộng `cuoc_hop_hkg`
quan hệ 1:1 — chưa làm ở migration này.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "mt_016_mo_rong_cuoc_hop_20260817"
down_revision: Union[str, None] = "zalo_oa_20260731"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


SCHEMA = "meeting"
TBL = "cuoc_hop"

# 6 loại lịch đang chạy thật trên lichkv8 (số liệu 17/08/2026):
# HOP 232 · TRUC_BAN 85 · HOI_NGHI 69 · LAM_VIEC 46 · CONG_TAC 37 · LICH_KHAC 18
# Khác trục với `khoi` của HKG (DANG/CHUYEN_MON/HANH_CHINH/BAN_NHOM) — giữ cả hai.
LOAI_LICH = ("HOP", "TRUC_BAN", "HOI_NGHI", "LAM_VIEC", "CONG_TAC", "LICH_KHAC")


def upgrade() -> None:
    # --- cột phân loại nguồn -------------------------------------------------
    # Dòng sẵn có đều là cuộc họp HKG → default 'HKG' là đúng cho dữ liệu cũ.
    op.add_column(
        TBL,
        sa.Column("nguon", sa.String(20), server_default="HKG", nullable=False),
        schema=SCHEMA,
    )

    # --- cột riêng của Lịch công tác ----------------------------------------
    for col in (
        # Mã lịch LHxxxx — BẮT BUỘC giữ nguyên mã lịch sử, là khoá liên kết
        # với tên thư mục tài liệu trên Drive.
        sa.Column("ma_lich", sa.String(20), nullable=True),
        sa.Column("ngay_ket_thuc", sa.Date(), nullable=True),
        # Ngày dùng để xếp lên lịch, có thể khác ngày bắt đầu thật.
        sa.Column("ngay_hien_thi", sa.Date(), nullable=True),
        sa.Column("loai_lich", sa.String(30), nullable=True),
        # 9% chủ trì là chức danh chung ("Chi cục trưởng") hoặc lãnh đạo ngoài
        # Chi cục ("Âu Anh Tuấn") → không khớp cong_chuc, giữ nguyên văn.
        sa.Column("chu_tri_text", sa.String(300), nullable=True),
        # Thành phần dạng văn bản tự do; rỗng ở 214/489 cuộc họp.
        sa.Column("thanh_phan_text", sa.Text(), nullable=True),
        # Trục của báo cáo Thống kê tài liệu họp.
        sa.Column("don_vi_chuan_bi", sa.String(200), nullable=True),
        sa.Column("so_van_ban", sa.String(100), nullable=True),
        sa.Column("ly_do_huy", sa.Text(), nullable=True),
        sa.Column(
            "updated_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("public.cong_chuc.id"),
            nullable=True,
        ),
    ):
        op.add_column(TBL, col, schema=SCHEMA)

    # --- nới ràng buộc để nạp được dữ liệu lịch sử --------------------------
    op.alter_column(TBL, "chu_toa_id", schema=SCHEMA, nullable=True)
    op.alter_column(TBL, "don_vi_to_chuc_id", schema=SCHEMA, nullable=True)

    # --- ràng buộc bù theo loại dòng ---------------------------------------
    op.create_check_constraint(
        "ck_cuoc_hop_nguon", TBL,
        "nguon IN ('HKG', 'LICH_CONG_TAC')",
        schema=SCHEMA,
    )
    # Dòng HKG vẫn phải có chủ trì + đơn vị tổ chức như trước migration này.
    op.create_check_constraint(
        "ck_cuoc_hop_hkg_bat_buoc", TBL,
        "nguon <> 'HKG' OR (chu_toa_id IS NOT NULL AND don_vi_to_chuc_id IS NOT NULL)",
        schema=SCHEMA,
    )
    # Dòng Lịch công tác phải có mã lịch và loại lịch.
    op.create_check_constraint(
        "ck_cuoc_hop_lct_bat_buoc", TBL,
        "nguon <> 'LICH_CONG_TAC' OR (ma_lich IS NOT NULL AND loai_lich IS NOT NULL)",
        schema=SCHEMA,
    )
    op.create_check_constraint(
        "ck_cuoc_hop_loai_lich", TBL,
        "loai_lich IS NULL OR loai_lich IN ("
        + ", ".join(f"'{x}'" for x in LOAI_LICH)
        + ")",
        schema=SCHEMA,
    )
    # ngay_ket_thuc không được trước ngay_hop (lịch nhiều ngày).
    op.create_check_constraint(
        "ck_cuoc_hop_khoang_ngay", TBL,
        "ngay_ket_thuc IS NULL OR ngay_ket_thuc >= ngay_hop",
        schema=SCHEMA,
    )

    # --- index -------------------------------------------------------------
    # ma_lich UNIQUE nhưng chỉ trên dòng có mã (dòng HKG để NULL).
    op.create_index(
        "uq_cuoc_hop_ma_lich", TBL, ["ma_lich"],
        unique=True, schema=SCHEMA,
        postgresql_where=sa.text("ma_lich IS NOT NULL"),
    )
    where_active = sa.text("is_deleted = FALSE")
    op.create_index("idx_cuoc_hop_nguon_ngay", TBL, ["nguon", "ngay_hien_thi"],
                    schema=SCHEMA, postgresql_where=where_active)
    op.create_index("idx_cuoc_hop_ngay_hien_thi", TBL, ["ngay_hien_thi"],
                    schema=SCHEMA, postgresql_where=where_active)
    op.create_index("idx_cuoc_hop_loai_lich", TBL, ["loai_lich"],
                    schema=SCHEMA, postgresql_where=where_active)
    op.create_index("idx_cuoc_hop_don_vi_chuan_bi", TBL, ["don_vi_chuan_bi"],
                    schema=SCHEMA, postgresql_where=where_active)

    # --- backfill ngay_hien_thi cho 9 cuộc họp HKG sẵn có -------------------
    # Lịch công tác đọc theo ngay_hien_thi; nếu để NULL thì cuộc họp HKG hiện
    # có sẽ không hiện lên lịch.
    op.execute(
        f"UPDATE {SCHEMA}.{TBL} SET ngay_hien_thi = ngay_hop "
        f"WHERE ngay_hien_thi IS NULL"
    )


def downgrade() -> None:
    op.drop_index("idx_cuoc_hop_don_vi_chuan_bi", table_name=TBL, schema=SCHEMA)
    op.drop_index("idx_cuoc_hop_loai_lich", table_name=TBL, schema=SCHEMA)
    op.drop_index("idx_cuoc_hop_ngay_hien_thi", table_name=TBL, schema=SCHEMA)
    op.drop_index("idx_cuoc_hop_nguon_ngay", table_name=TBL, schema=SCHEMA)
    op.drop_index("uq_cuoc_hop_ma_lich", table_name=TBL, schema=SCHEMA)

    for name in (
        "ck_cuoc_hop_khoang_ngay",
        "ck_cuoc_hop_loai_lich",
        "ck_cuoc_hop_lct_bat_buoc",
        "ck_cuoc_hop_hkg_bat_buoc",
        "ck_cuoc_hop_nguon",
    ):
        op.drop_constraint(name, TBL, type_="check", schema=SCHEMA)

    # Chỉ khôi phục NOT NULL được nếu không còn dòng Lịch công tác.
    op.execute(
        f"DELETE FROM {SCHEMA}.{TBL} WHERE nguon = 'LICH_CONG_TAC'"
    )
    op.alter_column(TBL, "don_vi_to_chuc_id", schema=SCHEMA, nullable=False)
    op.alter_column(TBL, "chu_toa_id", schema=SCHEMA, nullable=False)

    for col in (
        "updated_by", "ly_do_huy", "so_van_ban", "don_vi_chuan_bi",
        "thanh_phan_text", "chu_tri_text", "loai_lich", "ngay_hien_thi",
        "ngay_ket_thuc", "ma_lich", "nguon",
    ):
        op.drop_column(TBL, col, schema=SCHEMA)
