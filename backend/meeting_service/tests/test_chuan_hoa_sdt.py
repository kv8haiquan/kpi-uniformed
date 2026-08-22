"""Chuẩn hoá số điện thoại trực ban.

Bản xuất XLSX của lichkv8 ghi **691/724** số điện thoại ở dạng khoa học
(`9.13264387E8`) vì Google Sheets coi số điện thoại là SỐ chứ không phải
chuỗi, nên rụng số 0 đứng đầu. Trên cơ sở dữ liệu thật có 331 ca trực mang
số hỏng kiểu này — người dùng nhìn thấy ngay ở trang tóm tắt lịch.

Đối chiếu được: mỗi số hỏng đều có bản ghi ĐÚNG của **chính người đó** ở ca
trực khác, và cả 56 cặp đều khớp y hệt sau khi đổi. Các ca dưới đây lấy
nguyên từ dữ liệu thật đó.
"""

from __future__ import annotations

import pytest

from meeting_service.services.lich_cong_tac_service import chuan_hoa_sdt


@pytest.mark.parametrize("vao,ra", [
    # Dạng khoa học — số thật lấy từ prod, đã đối chiếu với bản ghi đúng
    ("9.13264387E8", "0913264387"),
    ("8.88262333E8", "0888262333"),
    ("3.94501808E8", "0394501808"),
    # Đuôi 0 bị nuốt trong phần định trị: 9.1326434E8 vẫn phải ra đủ 10 số
    ("9.1326434E8", "0913264340"),
    ("9.8326361E8", "0983263610"),
    ("9.8208988E8", "0982089880"),
    # Excel chèn dấu phân cách hàng nghìn
    ("0916,382,222", "0916382222"),
    ("0913.263.854", "0913263854"),
    # Mã quốc gia
    ("+84913263854", "0913263854"),
    ("84913263854", "0913263854"),
    # Rụng số 0 nhưng không ở dạng khoa học
    ("913263854", "0913263854"),
    # Đã đúng thì giữ nguyên
    ("0913263854", "0913263854"),
    # Rỗng
    (None, None), ("", None), ("   ", None),
])
def test_chuan_hoa(vao, ra):
    assert chuan_hoa_sdt(vao) == ra


def test_moi_so_ra_deu_dung_khuon_viet_nam():
    """Lưới chặn: đổi xong mà ra số 9 chữ số là vẫn còn lỗi cũ."""
    for s in ("9.13264387E8", "8.88262333E8", "3.94501808E8",
              "9.1326434E8", "9.8326361E8", "9.8208988E8"):
        ra = chuan_hoa_sdt(s)
        assert ra.startswith("0") and len(ra) == 10, f"{s} → {ra}"


def test_khong_pha_gia_tri_la():
    """Không nhận ra khuôn nào thì trả lại số đã lọc, KHÔNG được ném lỗi —
    dữ liệu di trú luôn có vài dòng người ta gõ tay linh tinh."""
    assert chuan_hoa_sdt("0913 263 854 (nhà riêng)") == "0913263854"
    assert chuan_hoa_sdt("chưa có") is None
    assert chuan_hoa_sdt("1900545481") == "1900545481"
