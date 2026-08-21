"""meeting_024: bảng danh mục dùng chung của Lịch công tác (G4.11)

Yêu cầu chuyển đổi mục II.15 đòi màn hình "Quản trị danh mục", bảng nghiệm thu
XI.9 kiểm lại điểm này. Hệ cũ có sheet `SETUP` với 12 nhóm; bên ta trước
migration này viết chết trong mã nguồn: loại lịch nằm ở `NHAN_LOAI_LICH`,
trạng thái nằm trong CHECK của cơ sở dữ liệu, loại tài liệu nằm thẳng trong
giao diện. Thêm một loại lịch phải gọi người sửa mã — đúng thứ yêu cầu đòi bỏ.

Bốn nhóm được đưa vào bảng (không bê cả 12 nhóm của hệ cũ):

    LOAI_LICH       7 mục — hệ cũ có TIEP_DOAN mà ta làm sót, nay bổ sung
    TRANG_THAI_LICH 5 mục — ánh xạ sang trạng thái nền tảng
    LOAI_TAI_LIEU   7 mục — nguyên văn FILE_TYPE của hệ cũ
    PHONG_HOP       5 mục — nguyên văn ROOM_LIST, trước đây địa điểm gõ tay

Tám nhóm còn lại của `SETUP` KHÔNG mang sang vì nền tảng đã có nơi quản lý
thật, đưa vào đây là đẻ ra bản sao thứ hai rồi hai bên lệch nhau:
`ROLE_LIST`/`SCOPE_LIST` → `public.vai_tro` + RBAC; `DEPT_LIST` → `public.don_vi`
(15 đơn vị thật, hệ cũ chỉ có 13); `LEADER_LIST` → `cong_chuc.is_lanh_dao`;
`USER_STATUS` → `cong_chuc.is_active`; `PARTICIPANT_ROLE`/`PARTICIPANT_PERMISSION`
→ `meeting.thanh_phan.loai_tham_du` + phân quyền tài liệu G5.4; `YES_NO` là
kiểu dữ liệu, không phải danh mục.

── Cờ `he_thong` ────────────────────────────────────────────────────────
Mã của một số mục bị mã nguồn rẽ nhánh theo. Đếm thực tế trong
`meeting_service/`: `trang_thai` có 62 điểm rẽ nhánh, `loai_lich` có 0 (chỉ
dùng làm bộ lọc và giá trị mặc định). Nên:

    he_thong=true   sửa được NHÃN và thứ tự; KHÔNG đổi mã, KHÔNG xoá, KHÔNG tắt
    he_thong=false  sửa/tắt/xoá thoải mái (xoá chỉ khi chưa có dữ liệu dùng tới)

Cho quản trị đổi `DA_THONG_BAO` thành mã khác là làm hỏng cả luồng duyệt họp,
nhưng đổi nhãn hiển thị từ "Đã đăng" sang "Đã công bố" thì hoàn toàn vô hại —
cờ này tách đúng hai việc đó.

── Bỏ CHECK `ck_cuoc_hop_loai_lich` ─────────────────────────────────────
Giữ CHECK thì quản trị thêm loại lịch mới sẽ bị cơ sở dữ liệu chối — tức là
màn hình quản trị danh mục vô nghĩa. Chuyển sang kiểm ở tầng dịch vụ, đối
chiếu với chính bảng này. Đổi lại, đường ghi thẳng bằng SQL (script di trú)
mất lưới an toàn — chấp nhận, vì đó là đường chỉ người viết mã đi.

CHECK của `trang_thai` GIỮ NGUYÊN: mã trạng thái không bao giờ đổi (he_thong),
nên ràng buộc không cản trở ai mà vẫn chặn được dữ liệu rác.

Revision ID: mt_024_danh_muc_20260821
Revises: mt_023_phan_quyen_tl_20260820
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
# Giữ dưới 32 ký tự — alembic_version.version_num là varchar(32).
revision: str = "mt_024_danh_muc_20260821"
down_revision: Union[str, None] = "mt_023_phan_quyen_tl_20260820"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SCHEMA = "meeting"
TBL = "danh_muc"

NHOM = ("LOAI_LICH", "TRANG_THAI_LICH", "LOAI_TAI_LIEU", "PHONG_HOP")

# (nhom, ma, nhan, thu_tu, he_thong, mo_ta)
HAT_GIONG: tuple[tuple[str, str, str, int, bool, str | None], ...] = (
    # ── Loại lịch — nguyên văn MEETING_TYPE của hệ cũ, đủ 7 mục.
    # `HOP` là giá trị mặc định khi tạo lịch nên khoá lại; 6 mục còn lại
    # thuần phân loại, đơn vị tự thêm bớt được.
    ("LOAI_LICH", "HOP", "Họp", 1, True, "Giá trị mặc định khi tạo lịch mới"),
    ("LOAI_LICH", "TRUC_BAN", "Trực ban", 2, False, None),
    ("LOAI_LICH", "HOI_NGHI", "Hội nghị", 3, False, None),
    ("LOAI_LICH", "LAM_VIEC", "Làm việc", 4, False, None),
    ("LOAI_LICH", "CONG_TAC", "Đi công tác", 5, False, None),
    ("LOAI_LICH", "TIEP_DOAN", "Tiếp đoàn", 6, False,
     "Bổ sung 21/08/2026 — hệ cũ có nhưng đợt chuyển đổi làm sót"),
    ("LOAI_LICH", "LICH_KHAC", "Lịch khác", 7, False, None),

    # ── Trạng thái — toàn bộ he_thong, mã bị 62 điểm trong mã nguồn rẽ nhánh.
    # Nhãn lấy theo cách Văn phòng đang gọi, không dịch sát mã.
    ("TRANG_THAI_LICH", "LEN_KE_HOACH", "Dự kiến (chưa đăng)", 1, True, None),
    ("TRANG_THAI_LICH", "DA_THONG_BAO", "Đã đăng", 2, True, None),
    ("TRANG_THAI_LICH", "DANG_DIEN_RA", "Đang diễn ra", 3, True, None),
    ("TRANG_THAI_LICH", "HOAN_THANH", "Đã diễn ra", 4, True, None),
    ("TRANG_THAI_LICH", "HUY", "Đã huỷ", 5, True, None),

    # ── Loại tài liệu — nguyên văn FILE_TYPE của hệ cũ.
    ("LOAI_TAI_LIEU", "GIAY_MOI", "Giấy mời", 1, False, None),
    ("LOAI_TAI_LIEU", "TAI_LIEU_HOP", "Tài liệu họp", 2, False, None),
    ("LOAI_TAI_LIEU", "BAO_CAO", "Báo cáo", 3, False, None),
    ("LOAI_TAI_LIEU", "CHUONG_TRINH", "Chương trình", 4, False, None),
    ("LOAI_TAI_LIEU", "BIEN_BAN", "Biên bản", 5, False, None),
    ("LOAI_TAI_LIEU", "KET_LUAN", "Kết luận", 6, False, None),
    ("LOAI_TAI_LIEU", "TAI_LIEU_KHAC", "Tài liệu khác", 7, False, None),

    # ── Phòng họp — nguyên văn ROOM_LIST. Trước đây địa điểm là ô gõ tay nên
    # "P.701" / "Phòng 701" / "phòng họp 701" cùng tồn tại.
    ("PHONG_HOP", "P701", "Phòng họp 701", 1, False, None),
    ("PHONG_HOP", "P505", "Phòng họp 505", 2, False, None),
    ("PHONG_HOP", "P302", "Phòng họp 302", 3, False, None),
    ("PHONG_HOP", "TS_CHQ", "Trụ sở Cục Hải quan", 4, False, None),
    ("PHONG_HOP", "KHAC", "Khác", 5, False, None),
)


def upgrade() -> None:
    op.create_table(
        TBL,
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("nhom", sa.String(30), nullable=False),
        sa.Column("ma", sa.String(50), nullable=False),
        sa.Column("nhan", sa.String(150), nullable=False),
        sa.Column("thu_tu", sa.Integer, nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean, nullable=False,
                  server_default=sa.text("true")),
        # Mục hệ thống: mã bị mã nguồn rẽ nhánh theo — xem docstring.
        sa.Column("he_thong", sa.Boolean, nullable=False,
                  server_default=sa.text("false")),
        sa.Column("mo_ta", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.CheckConstraint(
            "nhom IN (" + ", ".join(f"'{n}'" for n in NHOM) + ")",
            name="ck_danh_muc_nhom",
        ),
        # Mã rỗng hoặc toàn khoảng trắng lọt vào là hỏng cả bộ lọc.
        sa.CheckConstraint("btrim(ma) <> ''", name="ck_danh_muc_ma_khac_rong"),
        sa.CheckConstraint("btrim(nhan) <> ''", name="ck_danh_muc_nhan_khac_rong"),
        schema=SCHEMA,
    )
    op.create_unique_constraint(
        "uq_danh_muc_nhom_ma", TBL, ["nhom", "ma"], schema=SCHEMA
    )
    # Truy vấn luôn theo (nhóm, còn hiệu lực) rồi sắp theo thứ tự.
    op.create_index(
        "idx_danh_muc_nhom_thu_tu", TBL, ["nhom", "thu_tu"], schema=SCHEMA
    )

    for nhom, ma, nhan, thu_tu, he_thong, mo_ta in HAT_GIONG:
        op.execute(
            sa.text(f"""
                INSERT INTO {SCHEMA}.{TBL} (nhom, ma, nhan, thu_tu, he_thong, mo_ta)
                VALUES (:nhom, :ma, :nhan, :thu_tu, :he_thong, :mo_ta)
                ON CONFLICT (nhom, ma) DO NOTHING
            """).bindparams(
                nhom=nhom, ma=ma, nhan=nhan, thu_tu=thu_tu,
                he_thong=he_thong, mo_ta=mo_ta,
            )
        )

    # Bỏ CHECK loại lịch — xem docstring. Dùng IF EXISTS vì ràng buộc này chỉ
    # sinh ra ở meeting_016, cơ sở dữ liệu dựng trước đó không có.
    op.execute(
        "ALTER TABLE meeting.cuoc_hop "
        "DROP CONSTRAINT IF EXISTS ck_cuoc_hop_loai_lich"
    )


def downgrade() -> None:
    # Dựng lại CHECK theo đúng 6 giá trị trước đây. Sự kiện lỡ mang loại mới
    # (TIEP_DOAN hoặc loại đơn vị tự thêm) sẽ chặn lệnh này — cố ý: hạ cấp mà
    # âm thầm sửa dữ liệu người dùng là cách chắc chắn để mất dữ liệu. Muốn hạ
    # thì đổi các sự kiện đó sang LICH_KHAC trước.
    op.execute(
        "ALTER TABLE meeting.cuoc_hop ADD CONSTRAINT ck_cuoc_hop_loai_lich "
        "CHECK (loai_lich IS NULL OR loai_lich IN "
        "('HOP','TRUC_BAN','HOI_NGHI','LAM_VIEC','CONG_TAC','LICH_KHAC'))"
    )
    op.drop_index("idx_danh_muc_nhom_thu_tu", table_name=TBL, schema=SCHEMA)
    op.drop_constraint("uq_danh_muc_nhom_ma", TBL, schema=SCHEMA, type_="unique")
    op.drop_table(TBL, schema=SCHEMA)
