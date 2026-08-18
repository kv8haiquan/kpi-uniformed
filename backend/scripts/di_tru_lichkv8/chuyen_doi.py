"""Chuyển đổi kiểu dữ liệu từ bản xuất Google Sheets sang kiểu PostgreSQL.

Đây là chỗ dễ làm hỏng dữ liệu nhất khi di trú, vì cùng một cột trong Sheets
có thể chứa nhiều định dạng khác nhau tuỳ dòng được nhập tay hay do máy ghi.
Khảo sát trên bản sống 17/08/2026 (489 dòng MEETING):

  NGAY_BAT_DAU   100% số serial Excel      '46090.0'      → 2026-03-09
  NGAY_HIEN_THI  100% chuỗi dd/mm/yyyy     '09/03/2026'
  GIO_BAT_DAU    LẪN LỘN hai kiểu:
                   - chuỗi 'HH:MM'          '07:30'
                   - phân số ngày Excel     '0.3333333'   → 08:00
                 Nếu chỉ parse 'HH:MM' thì mất giờ của ~200 cuộc họp.
  NGAY_TAO       serial Excel kèm phần thập phân là giờ '46168.375'

Serial Excel đếm từ 1899-12-30 (không phải 1900-01-01 — Excel có lỗi năm
nhuận 1900 lịch sử, và Google Sheets giữ nguyên để tương thích).
"""

from __future__ import annotations

import re
from datetime import date, datetime, time, timedelta

EPOCH = date(1899, 12, 30)

_RE_NGAY_VN = re.compile(r"^(\d{1,2})/(\d{1,2})/(\d{4})$")
_RE_NGAY_ISO = re.compile(r"^(\d{4})-(\d{1,2})-(\d{1,2})")
_RE_GIO = re.compile(r"^(\d{1,2}):(\d{2})(?::(\d{2}))?$")


def _so(v: str) -> float | None:
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def doc_ngay(v: str | None) -> date | None:
    """Đọc ngày từ serial Excel, dd/mm/yyyy, hoặc yyyy-mm-dd."""
    v = (v or "").strip()
    if not v:
        return None

    n = _so(v)
    if n is not None:
        # Serial hợp lệ trong khoảng 1900-2100; số nhỏ hơn là dữ liệu rác.
        if 1 <= n <= 80000:
            return EPOCH + timedelta(days=int(n))
        return None

    m = _RE_NGAY_VN.match(v)
    if m:
        d, thang, nam = (int(x) for x in m.groups())
        try:
            return date(nam, thang, d)
        except ValueError:
            return None

    m = _RE_NGAY_ISO.match(v)
    if m:
        nam, thang, d = (int(x) for x in m.groups())
        try:
            return date(nam, thang, d)
        except ValueError:
            return None
    return None


def doc_gio(v: str | None) -> time | None:
    """Đọc giờ từ chuỗi 'HH:MM' hoặc phân số ngày Excel (0.3333 → 08:00)."""
    v = (v or "").strip()
    if not v:
        return None

    m = _RE_GIO.match(v)
    if m:
        gio, phut = int(m.group(1)), int(m.group(2))
        giay = int(m.group(3) or 0)
        if 0 <= gio <= 23 and 0 <= phut <= 59:
            return time(gio, phut, min(giay, 59))
        return None

    n = _so(v)
    if n is None:
        return None
    # Phân số của một ngày. Serial kèm ngày (vd 46168.375) cũng lấy phần lẻ.
    phan_le = n % 1
    tong_giay = round(phan_le * 86400)
    gio, du = divmod(tong_giay, 3600)
    phut, giay = divmod(du, 60)
    if gio > 23:
        return None
    return time(gio, phut, giay)


def doc_thoi_diem(v: str | None) -> datetime | None:
    """Đọc mốc thời gian từ serial Excel có phần thập phân là giờ."""
    v = (v or "").strip()
    if not v:
        return None
    n = _so(v)
    if n is not None and 1 <= n <= 80000:
        return datetime.combine(
            EPOCH + timedelta(days=int(n)), doc_gio(v) or time(0, 0))
    ng = doc_ngay(v)
    return datetime.combine(ng, time(0, 0)) if ng else None


def doc_bool(v: str | None) -> bool:
    v = (v or "").strip().lower()
    return v in {"1", "true", "yes", "x", "co", "có"}


def gon(v: str | None, gioi_han: int | None = None) -> str | None:
    """Chuẩn hoá khoảng trắng; None nếu rỗng. Cắt bớt nếu vượt độ dài cột."""
    if v is None:
        return None
    s = re.sub(r"\s+", " ", str(v)).strip()
    if not s:
        return None
    return s[:gioi_han] if gioi_han else s


def tach_danh_sach(v: str | None) -> list[str]:
    """Tách chuỗi nhiều giá trị phân cách bằng ';' hoặc xuống dòng."""
    if not v:
        return []
    return [x for p in re.split(r"[;\n]", v) if (x := gon(p))]
