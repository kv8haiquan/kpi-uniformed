"""Kiểm thử thuần hàm tách từ khoá cho gợi ý đối soát — G4.9.

Tách khỏi `test_doi_soat.py` vì không đụng cơ sở dữ liệu; file kia gắn
`pytestmark = pytest.mark.asyncio` cho cả module.
"""

from __future__ import annotations

from meeting_service.services.doi_soat_service import tach_tu


def test_tach_tu_bo_tu_vo_nghia():
    """"Tài liệu họp" xuất hiện ở hầu hết tên thư mục nên không phân biệt gì."""
    tu = tach_tu("260425 Tai lieu hop BCD57 GM 553")
    assert "tai" not in tu and "lieu" not in tu and "hop" not in tu
    assert "bcd57" in tu


def test_tach_tu_bo_token_thuan_so():
    """`260425` là ngày, `553` là số giấy mời — đã có cột riêng."""
    assert not (tach_tu("260425 GM 553") & {"260425", "553"})


def test_tach_tu_bo_dau_tieng_viet():
    assert tach_tu("Họp Đảng ủy") == tach_tu("Hop Dang uy")
