"""Kiểm thử thuần hàm cho trực ban — thứ tự chức vụ và mốc tuần.

Tách riêng khỏi `test_truc_ban.py` vì không đụng cơ sở dữ liệu: file kia gắn
`pytestmark = pytest.mark.asyncio` cho cả module, mà gắn nhãn đó lên hàm đồng
bộ thì pytest cảnh báo.
"""

from __future__ import annotations

from datetime import date

from meeting_service.services.truc_ban_service import bac_chuc_vu, tuan_chua


def test_bac_chuc_vu_dung_thu_tu():
    assert bac_chuc_vu("Chi cục trưởng") < bac_chuc_vu("Phó Chi cục trưởng")
    assert bac_chuc_vu("Phó Chi cục trưởng") < bac_chuc_vu("Đội trưởng")
    assert bac_chuc_vu("Đội trưởng") < bac_chuc_vu("Phó Đội trưởng")
    assert bac_chuc_vu("Phó Đội trưởng") < bac_chuc_vu("Công chức")


def test_chanh_van_phong_khong_bi_nham_la_cap_pho():
    """"Chánh Văn phòng" bỏ dấu thành "chanh van phong" — chứa chuỗi "pho"."""
    assert bac_chuc_vu("Chánh Văn phòng") == bac_chuc_vu("Trưởng phòng")
    assert bac_chuc_vu("Chánh Văn phòng") < bac_chuc_vu("Phó Chánh Văn phòng")


def test_chuc_vu_trong_xuong_cuoi():
    assert bac_chuc_vu(None) == bac_chuc_vu("") == 9


def test_tuan_chua_bat_dau_tu_thu_hai():
    dau, cuoi = tuan_chua(date(2026, 8, 19))   # Thứ Tư
    assert dau == date(2026, 8, 17) and dau.weekday() == 0
    assert cuoi == date(2026, 8, 23)
    assert tuan_chua(date(2026, 8, 19), 1)[0] == date(2026, 8, 24)
