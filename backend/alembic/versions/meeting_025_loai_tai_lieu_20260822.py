"""G4.11b — cột `loai_tai_lieu` cho meeting.tai_lieu.

Loại tài liệu đang được lưu bằng chính **chuỗi nhãn** vào `mo_ta`
("Giấy mời"), không phải mã. Ba hậu quả đo được:

  1. Đổi tên một loại trên màn hình Quản trị danh mục là **mọi tài liệu
     đang mang loại đó thành mồ côi**: bản ghi vẫn ghi "Giấy mời" trong khi
     danh mục đã thành "Giấy mời họp".
  2. `dem_su_dung` đối chiếu theo nhãn nên sau khi đổi tên nó báo **0 đang
     dùng** — màn hình quản trị lúc đó CHO PHÉP XOÁ một mục vẫn có tài liệu.
     Tức nút "Sửa tên" chính là cái làm hỏng dữ liệu, không cảnh báo gì.
  3. `mo_ta` phải gánh hai nghĩa (mô tả tự do và loại) nên không chỗ nào
     dám dùng nó đúng nghĩa mô tả.

Nay tách thành cột riêng lưu **MÃ** — mã là thứ không đổi được sau khi tạo
(xem `DanhMucService.cap_nhat` chối `ma`), nên đổi tên nhãn bao nhiêu lần
liên kết vẫn nguyên.

Thời điểm chuyển rẻ nhất có thể: **854/854 tài liệu đang có `mo_ta` rỗng**
— chưa ai tải tài liệu qua giao diện mới. Vẫn viết đủ phần chuyển đổi cho
môi trường khác và cho trường hợp chạy muộn.

Cố ý KHÔNG đặt khoá ngoại sang `meeting.danh_muc`: đơn vị được xoá một mục
danh mục, mà xoá xong thì tài liệu cũ vẫn phải đọc được với mã cũ — giống
cách `loai_lich` đang làm. Hợp lệ được kiểm ở tầng nghiệp vụ lúc ghi.
"""

from alembic import op
import sqlalchemy as sa

revision = "mt_025_loai_tai_lieu_20260822"
down_revision = "mt_024_danh_muc_20260821"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "tai_lieu",
        sa.Column("loai_tai_lieu", sa.String(50), nullable=True),
        schema="meeting",
    )

    # Chuyển nhãn đang nằm trong `mo_ta` sang mã. Đối chiếu không phân biệt
    # hoa thường và khoảng trắng thừa vì nhãn từng đi qua ô nhập tay.
    op.execute("""
        UPDATE meeting.tai_lieu t
           SET loai_tai_lieu = dm.ma
          FROM meeting.danh_muc dm
         WHERE dm.nhom = 'LOAI_TAI_LIEU'
           AND t.mo_ta IS NOT NULL
           AND lower(btrim(t.mo_ta)) = lower(btrim(dm.nhan))
    """)

    # Dọn `mo_ta` ở đúng những dòng vừa chuyển được, trả cột này về đúng
    # nghĩa mô tả tự do. Dòng nào không khớp nhãn nào thì GIỮ NGUYÊN — đó là
    # mô tả thật người dùng gõ, không được xoá.
    op.execute("""
        UPDATE meeting.tai_lieu t
           SET mo_ta = NULL
          FROM meeting.danh_muc dm
         WHERE dm.nhom = 'LOAI_TAI_LIEU'
           AND t.loai_tai_lieu = dm.ma
           AND t.mo_ta IS NOT NULL
           AND lower(btrim(t.mo_ta)) = lower(btrim(dm.nhan))
    """)

    # Lọc theo loại là thao tác của trang Thống kê tài liệu và kho tài liệu;
    # chỉ đánh chỉ mục phần còn hiệu lực cho gọn.
    op.execute("""
        CREATE INDEX idx_tai_lieu_loai ON meeting.tai_lieu (loai_tai_lieu)
         WHERE is_deleted = false AND loai_tai_lieu IS NOT NULL
    """)


def downgrade() -> None:
    # Trả nhãn về `mo_ta` trước khi bỏ cột, nếu không quay lui là mất sạch
    # loại đã đặt.
    op.execute("""
        UPDATE meeting.tai_lieu t
           SET mo_ta = dm.nhan
          FROM meeting.danh_muc dm
         WHERE dm.nhom = 'LOAI_TAI_LIEU'
           AND t.loai_tai_lieu = dm.ma
           AND t.mo_ta IS NULL
    """)
    op.execute("DROP INDEX IF EXISTS meeting.idx_tai_lieu_loai")
    op.drop_column("tai_lieu", "loai_tai_lieu", schema="meeting")
