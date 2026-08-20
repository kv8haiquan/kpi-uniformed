"""meeting_023: phân quyền tài liệu 2 mức hạn chế (G5.4)

Trước migration này `meeting.tai_lieu.phan_quyen` chỉ nhận `CONG_KHAI` và
`HAN_CHE`, mà `HAN_CHE` chưa từng được kiểm ở bất kỳ đâu trong mã — nó là một
nhãn không có hiệu lực. Toàn bộ 856 dòng hiện có đều là `CONG_KHAI`.

Thay bằng thang ba mức có thứ bậc rõ ràng, ánh xạ thẳng sang vai trò nền tảng:

    CONG_KHAI         ai xem được cuộc họp thì xem được tài liệu
    LANH_DAO_DON_VI   thêm điều kiện: là lãnh đạo (phòng/đội trở lên)
    LANH_DAO_CHI_CUC  chỉ Chi cục trưởng, Phó Chi cục trưởng và quản trị

`HAN_CHE` bị loại khỏi danh mục. An toàn vì không dòng nào mang giá trị đó;
lệnh UPDATE bên dưới chỉ là lưới an toàn phòng khi có dòng phát sinh giữa lúc
soạn và lúc chạy migration — nếu có thì nâng lên `LANH_DAO_DON_VI` chứ không
hạ xuống công khai, vì hạ là lộ tài liệu ai đó đã cố ý đánh dấu hạn chế.

Revision ID: mt_023_phan_quyen_tl_20260820
Revises: mt_022_ds_file_doi_soat_20260819
"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
# Giữ dưới 32 ký tự — alembic_version.version_num là varchar(32).
revision: str = "mt_023_phan_quyen_tl_20260820"
down_revision: Union[str, None] = "mt_022_ds_file_doi_soat_20260819"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SCHEMA = "meeting"
TBL = "tai_lieu"
RANG_BUOC = "ck_tai_lieu_phan_quyen"

MUC_MOI = ("CONG_KHAI", "LANH_DAO_DON_VI", "LANH_DAO_CHI_CUC")
MUC_CU = ("CONG_KHAI", "HAN_CHE")


def _dat_check(muc: tuple[str, ...]) -> None:
    op.execute(
        f"ALTER TABLE {SCHEMA}.{TBL} DROP CONSTRAINT IF EXISTS {RANG_BUOC}"
    )
    danh_sach = ", ".join(f"'{m}'" for m in muc)
    op.execute(
        f"ALTER TABLE {SCHEMA}.{TBL} ADD CONSTRAINT {RANG_BUOC} "
        f"CHECK (phan_quyen IN ({danh_sach}))"
    )


def upgrade() -> None:
    op.execute(
        f"UPDATE {SCHEMA}.{TBL} SET phan_quyen = 'LANH_DAO_DON_VI' "
        f"WHERE phan_quyen = 'HAN_CHE'"
    )
    _dat_check(MUC_MOI)

    # Chỉ mục một phần: gần như toàn bộ tài liệu là CONG_KHAI nên đánh chỉ mục
    # cả cột là phí; truy vấn cần lọc chỉ quan tâm nhóm hạn chế.
    op.execute(
        f"CREATE INDEX IF NOT EXISTS idx_tai_lieu_han_che "
        f"ON {SCHEMA}.{TBL} (cuoc_hop_id) "
        f"WHERE phan_quyen <> 'CONG_KHAI' AND is_deleted = FALSE"
    )


def downgrade() -> None:
    op.execute(f"DROP INDEX IF EXISTS {SCHEMA}.idx_tai_lieu_han_che")
    # Gộp hai mức hạn chế về `HAN_CHE` — bản cũ không phân biệt được.
    op.execute(
        f"UPDATE {SCHEMA}.{TBL} SET phan_quyen = 'HAN_CHE' "
        f"WHERE phan_quyen IN ('LANH_DAO_DON_VI', 'LANH_DAO_CHI_CUC')"
    )
    _dat_check(MUC_CU)
