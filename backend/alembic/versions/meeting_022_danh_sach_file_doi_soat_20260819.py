"""meeting_022: danh sách tên file cho màn hình đối soát

Màn hình đối soát (G4.9) phải hiện được TÊN từng file trong thư mục, không chỉ
số lượng: 34 cụm còn lại đều là thư mục mà tên không đủ để đoán ra cuộc họp
("TL HN chỉ số", "260519-CCT lv KTSTQ"), nên nhiều khi phải nhìn tên file bên
trong mới nhận ra.

Lưu thành JSONB ngay trên `di_tru_doi_soat` thay vì bảng con: đây là dữ liệu
chỉ đọc, dùng đúng một lần trong đợt chuyển đổi, và luôn được lấy trọn gói
theo thư mục — tách bảng chỉ thêm một phép nối mà không được gì.

Revision ID: mt_022_ds_file_doi_soat_20260819
Revises: mt_021_dong_bo_ngay_ht_20260817
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
# Giữ dưới 32 ký tự — alembic_version.version_num là varchar(32).
revision: str = "mt_022_ds_file_doi_soat_20260819"
down_revision: Union[str, None] = "mt_021_dong_bo_ngay_ht_20260817"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SCHEMA = "meeting"
TBL = "di_tru_doi_soat"


def upgrade() -> None:
    op.add_column(
        TBL,
        sa.Column(
            "danh_sach_file",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            comment="[{drive_file_id, ten, so_byte}] — tên file trong thư mục, "
                    "để màn hình đối soát đoán ra cuộc họp",
        ),
        schema=SCHEMA,
    )


def downgrade() -> None:
    op.drop_column(TBL, "danh_sach_file", schema=SCHEMA)
