"""Meeting 020: meeting.di_tru_doi_soat + di_tru_nguon

Revision ID: mt_020_luu_vet_di_tru_20260817
Revises: mt_019_danh_gia_ghi_chu_20260817
Create Date: 2026-08-17

Hai bảng phục vụ riêng việc di trú từ lichkv8. Xem KE_HOACH_TRIEN_KHAI.md §G2.5.

`di_tru_doi_soat` — hàng đợi của màn hình đối soát tài liệu (§4.3 báo cáo phân
tích). Kho Drive có 1.226 file trong 230 thư mục cấp 1, mỗi thư mục là tài liệu
của một cuộc họp. 195 thư mục gắn được tự động (tên là mã lịch, hoặc suy từ số
giấy mời); 34 thư mục còn lại cần người xác định vì ngày nào cũng có 2–8 cuộc
họp nên chỉ khớp ngày là không đủ. Xuất bảng này ra Excel chính là biên bản đối
chiếu phải nộp khi nghiệm thu (mục V và XII của yêu cầu chuyển đổi).

`di_tru_nguon` — bảng truy vết chung: bản ghi cũ nào thành bản ghi mới nào. Cho
phép chạy lại script di trú mà không nhân đôi dữ liệu (idempotent), và tra
ngược khi đối soát phát hiện lệch.

Cả hai bảng chỉ dùng trong giai đoạn chuyển đổi; sau khi nghiệm thu có thể giữ
làm hồ sơ hoặc xoá, không ảnh hưởng nghiệp vụ.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "mt_020_luu_vet_di_tru_20260817"
down_revision: Union[str, None] = "mt_019_danh_gia_ghi_chu_20260817"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


SCHEMA = "meeting"
T_DS = "di_tru_doi_soat"
T_NG = "di_tru_nguon"


def upgrade() -> None:
    # --- hàng đợi đối soát thư mục tài liệu ---------------------------------
    op.create_table(
        T_DS,
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()"), nullable=False),

        sa.Column("drive_folder_id", sa.String(60), nullable=False),
        sa.Column("duong_dan_thu_muc", sa.Text(), nullable=False),
        sa.Column("so_file", sa.Integer(), server_default="0", nullable=False),
        # Ngày suy ra từ tiền tố YYMMDD trong tên thư mục, nếu có.
        sa.Column("ngay_suy_ra", sa.Date(), nullable=True),
        # Số giấy mời rút từ tên thư mục, nếu có.
        sa.Column("so_gm_suy_ra", sa.String(20), nullable=True),

        # A: tên thư mục là mã lịch · B: khớp cả ngày lẫn số GM ·
        # C: khớp số GM · D: chỉ khớp ngày · E: không khớp gì
        sa.Column("nhom", sa.String(2), nullable=False),

        # Quyết định của người rà. NULL = chưa xử lý.
        sa.Column("quyet_dinh", sa.String(30), nullable=True),
        sa.Column("cuoc_hop_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("meeting.cuoc_hop.id", ondelete="SET NULL"),
                  nullable=True),
        sa.Column("nguoi_quyet_dinh_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("public.cong_chuc.id"), nullable=True),
        sa.Column("thoi_diem_quyet_dinh", postgresql.TIMESTAMP(timezone=True),
                  nullable=True),
        sa.Column("ghi_chu", sa.Text(), nullable=True),

        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),

        sa.UniqueConstraint("drive_folder_id", name="uq_di_tru_doi_soat_folder"),
        sa.CheckConstraint("nhom IN ('A','B','C','D','E')",
                           name="ck_di_tru_doi_soat_nhom"),
        sa.CheckConstraint(
            "quyet_dinh IS NULL OR quyet_dinh IN "
            "('GAN_CUOC_HOP','TAO_CUOC_HOP_LICH_SU','KHO_LUU_TRU','KHONG_DI_TRU')",
            name="ck_di_tru_doi_soat_quyet_dinh",
        ),
        # Chọn gắn vào cuộc họp thì phải chỉ ra cuộc họp nào.
        sa.CheckConstraint(
            "quyet_dinh <> 'GAN_CUOC_HOP' OR cuoc_hop_id IS NOT NULL",
            name="ck_di_tru_doi_soat_can_cuoc_hop",
        ),
        schema=SCHEMA,
    )
    # Hàng đợi việc chưa xử lý — truy vấn chính của màn hình đối soát.
    op.create_index("idx_di_tru_doi_soat_chua_xu_ly", T_DS, ["nhom"],
                    schema=SCHEMA,
                    postgresql_where=sa.text("quyet_dinh IS NULL"))

    # --- truy vết bản ghi cũ → mới -----------------------------------------
    op.create_table(
        T_NG,
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()"), nullable=False),
        # Tên sheet nguồn: MEETING, MEETING_FILE, DUTY_ENTRY, USER…
        sa.Column("bang_nguon", sa.String(40), nullable=False),
        # Khoá chính bên lichkv8: LH0245, FR0123, DUTY_0007, 20ZZ-0224…
        sa.Column("khoa_nguon", sa.String(80), nullable=False),
        # Với file: id trên Drive, để đối soát và tải lại khi cần.
        sa.Column("drive_file_id", sa.String(60), nullable=True),

        sa.Column("bang_dich", sa.String(60), nullable=False),
        sa.Column("id_dich", postgresql.UUID(as_uuid=True), nullable=True),

        sa.Column("ghi_chu", sa.Text(), nullable=True),
        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),

        # Chạy lại script di trú không tạo bản ghi trùng.
        sa.UniqueConstraint("bang_nguon", "khoa_nguon",
                            name="uq_di_tru_nguon_khoa"),
        schema=SCHEMA,
    )
    op.create_index("idx_di_tru_nguon_dich", T_NG, ["bang_dich", "id_dich"],
                    schema=SCHEMA)
    op.create_index("idx_di_tru_nguon_drive", T_NG, ["drive_file_id"],
                    schema=SCHEMA,
                    postgresql_where=sa.text("drive_file_id IS NOT NULL"))


def downgrade() -> None:
    op.drop_index("idx_di_tru_nguon_drive", table_name=T_NG, schema=SCHEMA)
    op.drop_index("idx_di_tru_nguon_dich", table_name=T_NG, schema=SCHEMA)
    op.drop_table(T_NG, schema=SCHEMA)

    op.drop_index("idx_di_tru_doi_soat_chua_xu_ly", table_name=T_DS, schema=SCHEMA)
    op.drop_table(T_DS, schema=SCHEMA)
