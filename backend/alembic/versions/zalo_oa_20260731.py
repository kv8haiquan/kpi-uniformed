"""Zalo OA: 3 bảng hạ tầng gửi thông báo qua Zalo (common schema)

Revision ID: zalo_oa_20260731
Revises: lms_ctd_template_20260730
Create Date: 2026-07-31

MỤC ĐÍCH
========
Thêm kênh đẩy (push) Zalo cho hệ thống thông báo hiện có. Lý do: đo trên dữ
liệu thật, thông báo in-app có trung vị 58 giờ mới được đọc (loại MEETING) —
lời nhắc họp tới tay người nhận sau khi cuộc họp đã tan.

NGUYÊN TẮC THIẾT KẾ
===================
1. **KHÔNG đụng vào bảng `common.thong_bao`.** Bảng đó đang được 3 module ghi
   vào bằng 2 đường khác nhau (KPI + LMS gọi Internal API; HKG INSERT raw SQL
   tại meeting_service/services/notification_service.py:35). Thêm cột vào đó
   là rủi ro không cần thiết. Thay vào đó `zalo_outbox` tham chiếu ngược lại
   bằng FK — worker quét ra bản ghi chưa có outbox thì tạo mới.
   → Hệ quả: bật/tắt Zalo KHÔNG cần sửa một dòng nào của HKG/KPI/LMS.

2. **TIMESTAMPTZ cho toàn bộ cột thời gian mới.** Theo convention đã chuẩn hóa
   ở schema `lms` (migration lms_timestamptz_20260730). LƯU Ý: `thong_bao.created_at`
   là TIMESTAMP *naive* lưu giờ VN (Postgres timezone = Asia/Ho_Chi_Minh) —
   mọi so sánh với cột đó PHẢI làm bằng SQL CURRENT_TIMESTAMP, tuyệt đối không
   dùng datetime.utcnow() phía Python (sẽ lệch 7 giờ).

3. **Trạng thái dùng VARCHAR(50), không dùng PostgreSQL ENUM** (coding convention).

Bảng tạo:
    common.zalo_lien_ket  — ánh xạ công chức ↔ số điện thoại / zalo_user_id
    common.zalo_outbox    — hàng đợi gửi (outbox pattern, có retry + backoff)
    common.zalo_token     — lưu OAuth token của OA (refresh_token XOAY VÒNG)
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "zalo_oa_20260731"
down_revision: Union[str, None] = "lms_ctd_template_20260730"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


SCHEMA = "common"


def upgrade() -> None:
    # ------------------------------------------------------------------
    # 1. zalo_lien_ket — ai nhận được tin Zalo, qua số nào
    # ------------------------------------------------------------------
    op.create_table(
        "zalo_lien_ket",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "cong_chuc_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("public.cong_chuc.id"),
            nullable=False,
            comment="FK public.cong_chuc — mỗi công chức tối đa 1 liên kết",
        ),
        sa.Column(
            "so_dien_thoai",
            sa.String(20),
            nullable=True,
            comment="ĐÃ CHUẨN HÓA dạng 84xxxxxxxxx (định dạng ZNS yêu cầu)",
        ),
        sa.Column(
            "so_goc",
            sa.String(30),
            nullable=True,
            comment="Số nguyên bản lúc import — giữ lại để đối chiếu khi nghi ngờ sai",
        ),
        sa.Column(
            "zalo_user_id",
            sa.String(50),
            nullable=True,
            comment=(
                "Chỉ có khi người dùng CHỦ ĐỘNG follow OA (giai đoạn 2). "
                "KHÔNG suy ra được từ số điện thoại — Zalo không cung cấp API tra cứu."
            ),
        ),
        sa.Column(
            "trang_thai",
            sa.String(50),
            nullable=False,
            server_default="CHUA_XAC_MINH",
            comment="CHUA_XAC_MINH | HOAT_DONG | SO_LOI | TU_CHOI_NHAN",
        ),
        sa.Column(
            "da_dong_y",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
            comment=(
                "Cờ opt-out theo Nghị định 13/2023/NĐ-CP về bảo vệ dữ liệu cá nhân. "
                "Đặt false khi công chức yêu cầu ngừng nhận — worker sẽ bỏ qua."
            ),
        ),
        sa.Column(
            "nguon",
            sa.String(50),
            nullable=True,
            comment="IMPORT_EXCEL | TU_KHAI_BAO | OA_FOLLOW",
        ),
        sa.Column("ghi_chu", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        schema=SCHEMA,
    )
    op.create_unique_constraint(
        "uq_zalo_lien_ket_cong_chuc", "zalo_lien_ket", ["cong_chuc_id"], schema=SCHEMA
    )
    op.create_index(
        "idx_zalo_lk_sdt", "zalo_lien_ket", ["so_dien_thoai"], schema=SCHEMA
    )
    op.create_index(
        "idx_zalo_lk_trang_thai", "zalo_lien_ket", ["trang_thai"], schema=SCHEMA
    )

    # ------------------------------------------------------------------
    # 2. zalo_outbox — hàng đợi gửi
    # ------------------------------------------------------------------
    op.create_table(
        "zalo_outbox",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "thong_bao_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("common.thong_bao.id", ondelete="CASCADE"),
            nullable=False,
            comment=(
                "Khóa chống gửi trùng: UNIQUE nên dù worker chạy 2 lần hay 2 tiến "
                "trình song song thì mỗi thông báo chỉ sinh đúng 1 bản ghi outbox."
            ),
        ),
        sa.Column(
            "cong_chuc_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("public.cong_chuc.id"),
            nullable=False,
        ),
        sa.Column(
            "so_dien_thoai",
            sa.String(20),
            nullable=True,
            comment="Chụp lại tại thời điểm xếp hàng — số ở lien_ket có thể đổi sau",
        ),
        sa.Column(
            "template_id",
            sa.String(50),
            nullable=True,
            comment="ID template ZNS đã được Zalo duyệt",
        ),
        sa.Column(
            "template_data",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            comment="Tham số điền vào template, ví dụ {'thoi_gian': '14:00 31/07'}",
        ),
        sa.Column(
            "trang_thai",
            sa.String(50),
            nullable=False,
            server_default="CHO_GUI",
            comment="CHO_GUI | DANG_GUI | DA_GUI | THAT_BAI | BO_QUA",
        ),
        sa.Column(
            "ly_do_bo_qua",
            sa.String(100),
            nullable=True,
            comment="KHONG_CO_SDT | DA_TU_CHOI | KHONG_CO_TEMPLATE | TAT_TINH_NANG",
        ),
        sa.Column(
            "so_lan_thu",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "gui_sau",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
            comment="Backoff: lần thử kế tiếp không sớm hơn mốc này",
        ),
        sa.Column("ma_loi", sa.String(50), nullable=True),
        sa.Column("mo_ta_loi", sa.Text(), nullable=True),
        sa.Column(
            "zns_message_id",
            sa.String(100),
            nullable=True,
            comment="msg_id Zalo trả về — để đối soát khi có khiếu nại",
        ),
        sa.Column(
            "ngay_gui", postgresql.TIMESTAMP(timezone=True), nullable=True
        ),
        sa.Column(
            "created_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        schema=SCHEMA,
    )
    op.create_unique_constraint(
        "uq_zalo_outbox_thong_bao", "zalo_outbox", ["thong_bao_id"], schema=SCHEMA
    )
    # Index phục vụ truy vấn chính của worker: lấy việc tới hạn
    op.create_index(
        "idx_zalo_ob_cho_gui",
        "zalo_outbox",
        ["trang_thai", "gui_sau"],
        schema=SCHEMA,
    )
    op.create_index(
        "idx_zalo_ob_time",
        "zalo_outbox",
        [sa.text("created_at DESC")],
        schema=SCHEMA,
    )

    # ------------------------------------------------------------------
    # 3. zalo_token — OAuth token của OA
    # ------------------------------------------------------------------
    op.create_table(
        "zalo_token",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "ten",
            sa.String(50),
            nullable=False,
            server_default="OA",
            comment="Định danh bộ token — hiện chỉ dùng 1 dòng 'OA'",
        ),
        sa.Column("access_token", sa.Text(), nullable=True),
        sa.Column(
            "refresh_token",
            sa.Text(),
            nullable=True,
            comment=(
                "CẢNH BÁO VẬN HÀNH: Zalo cấp refresh_token MỚI sau mỗi lần refresh "
                "và vô hiệu token cũ. Bắt buộc ghi đè vào đây ngay sau mỗi lần gọi. "
                "Mất token này = phải vào Zalo dashboard ủy quyền lại bằng tay."
            ),
        ),
        sa.Column(
            "het_han_luc",
            postgresql.TIMESTAMP(timezone=True),
            nullable=True,
            comment="Thời điểm access_token hết hạn (Zalo cấp ~1 giờ)",
        ),
        sa.Column(
            "lan_refresh_cuoi", postgresql.TIMESTAMP(timezone=True), nullable=True
        ),
        sa.Column(
            "created_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        schema=SCHEMA,
    )
    op.create_unique_constraint(
        "uq_zalo_token_ten", "zalo_token", ["ten"], schema=SCHEMA
    )


def downgrade() -> None:
    op.drop_table("zalo_token", schema=SCHEMA)
    op.drop_index("idx_zalo_ob_time", table_name="zalo_outbox", schema=SCHEMA)
    op.drop_index("idx_zalo_ob_cho_gui", table_name="zalo_outbox", schema=SCHEMA)
    op.drop_table("zalo_outbox", schema=SCHEMA)
    op.drop_index("idx_zalo_lk_trang_thai", table_name="zalo_lien_ket", schema=SCHEMA)
    op.drop_index("idx_zalo_lk_sdt", table_name="zalo_lien_ket", schema=SCHEMA)
    op.drop_table("zalo_lien_ket", schema=SCHEMA)
