"""Meeting 021: trigger đồng bộ ngay_hien_thi + loai_lich cho dòng HKG

Revision ID: mt_021_dong_bo_ngay_ht_20260817
Revises: mt_020_luu_vet_di_tru_20260817
Create Date: 2026-08-17

Sửa hai lỗi phát hiện khi rà lại migration 016 — cả hai đều phá vỡ tiêu chí 8.3
("cuộc họp phải tự hiện trên Lịch công tác, đổi giờ hoặc huỷ thì lịch cập nhật
theo"):

  1. Cuộc họp HKG TẠO MỚI có ngay_hien_thi = NULL.
     Model CuocHop và cuoc_hop_service.tao_moi() không biết cột này (đúng thiết
     kế — HKG không phải quan tâm field của Lịch công tác), nên INSERT bỏ trống.
     Migration 016 chỉ backfill 9 dòng sẵn có, không lo được cho dòng tương lai.
     → Lịch công tác lọc theo ngay_hien_thi sẽ KHÔNG thấy cuộc họp HKG nào mới.

  2. Cuộc họp HKG ĐỔI NGÀY thì ngay_hien_thi giữ nguyên ngày cũ.
     cuoc_hop_service.cap_nhat() dùng setattr theo model, mà model không có cột
     này → lịch hiển thị sai ngày sau khi dời họp.

Cách sửa: trigger ở mức cơ sở dữ liệu thay vì sửa model và service.
Lý do chọn hướng này — giữ đúng nguyên tắc của phương án một-bảng: HKG không
phải biết gì về Lịch công tác. Sửa ở model thì mọi đường ghi khác (script di
trú, seed, sửa tay) vẫn có thể quên; trigger thì đúng với mọi đường ghi.

Quy tắc:
  - nguon = 'HKG'          → ngay_hien_thi LUÔN bằng ngay_hop (gương)
  - nguon = 'LICH_CONG_TAC' → giữ giá trị người dùng đặt; chỉ điền khi để trống
                              (lichkv8 có NGAY_HIEN_THI khác ngày bắt đầu thật)

Trigger cũng gán loai_lich = 'HOP' cho dòng HKG còn trống: cuộc họp HKG về bản
chất là "họp", nếu để NULL thì bộ lọc theo loại lịch trên màn hình Lịch công
tác sẽ bỏ sót toàn bộ cuộc họp HKG.
"""

from typing import Sequence, Union

from alembic import op


revision: str = "mt_021_dong_bo_ngay_ht_20260817"
down_revision: Union[str, None] = "mt_020_luu_vet_di_tru_20260817"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


SCHEMA = "meeting"
FUNC = f"{SCHEMA}.fn_dong_bo_ngay_hien_thi"
TRIG = "trg_dong_bo_ngay_hien_thi"


def upgrade() -> None:
    op.execute(f"""
        CREATE OR REPLACE FUNCTION {FUNC}() RETURNS TRIGGER AS $$
        BEGIN
            IF NEW.nguon = 'HKG' THEN
                -- HKG không quản lý ngày hiển thị → luôn soi gương ngay_hop,
                -- kể cả khi dời họp.
                NEW.ngay_hien_thi := NEW.ngay_hop;
                IF NEW.loai_lich IS NULL THEN
                    NEW.loai_lich := 'HOP';
                END IF;
            ELSIF NEW.ngay_hien_thi IS NULL THEN
                -- Lịch công tác được phép đặt ngày hiển thị khác ngày bắt đầu;
                -- chỉ điền hộ khi bỏ trống.
                NEW.ngay_hien_thi := NEW.ngay_hop;
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.execute(f"""
        CREATE TRIGGER {TRIG}
        BEFORE INSERT OR UPDATE OF ngay_hop, ngay_hien_thi, nguon, loai_lich
        ON {SCHEMA}.cuoc_hop
        FOR EACH ROW EXECUTE FUNCTION {FUNC}();
    """)

    # Dòng HKG sẵn có chưa có loai_lich (migration 016 chỉ backfill ngay_hien_thi).
    op.execute(f"""
        UPDATE {SCHEMA}.cuoc_hop
        SET loai_lich = 'HOP'
        WHERE nguon = 'HKG' AND loai_lich IS NULL
    """)


def downgrade() -> None:
    op.execute(f"DROP TRIGGER IF EXISTS {TRIG} ON {SCHEMA}.cuoc_hop")
    op.execute(f"DROP FUNCTION IF EXISTS {FUNC}()")
