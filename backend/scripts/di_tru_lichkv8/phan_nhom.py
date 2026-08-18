"""Phân nhóm thư mục Drive theo khả năng nhận diện cuộc họp.

Dùng chung cho 06_gan_tai_lieu.py và màn hình đối soát ở G4.9.

    A  tên thư mục là mã lịch LHxxxx            → chắc chắn
    B  khớp CẢ ngày lẫn số giấy mời             → chắc chắn
    C  khớp số giấy mời với SO_VAN_BAN          → chắc chắn
    D  chỉ khớp ngày, có 2–8 cuộc họp cùng ngày → cần người chọn
    E  không khớp gì                            → cần người xác định

Nhóm D không bao giờ có ứng viên duy nhất: ngày nào cũng có nhiều cuộc họp vì
mục "Chỉ đạo trực ban" lặp gần như hằng ngày. Vì vậy hàm xep_hang_ung_vien()
xếp hạng theo số từ khoá trùng giữa tên thư mục và nội dung cuộc họp, để màn
hình đối soát gợi ý được cái khả dĩ nhất thay vì đổ ra danh sách phẳng.
"""

from __future__ import annotations

import re
import unicodedata
from datetime import date

RE_LH = re.compile(r"(?:^|/)(LH\d{4})")
RE_GM = re.compile(r"\bGM[\s._-]*(\d{2,4})\b", re.I)
RE_NGAY = re.compile(r"(?:^|/)(\d{2})(\d{2})(\d{2})")

# Từ quá phổ biến trong cả tên thư mục lẫn nội dung họp — không phân biệt được gì.
TU_BO = {
    "tl", "tai", "lieu", "tailieu", "hop", "cua", "ve", "va", "theo", "gm",
    "cac", "de", "cho", "tren", "the", "nam", "thang", "ngay", "so", "bc",
    "ban", "to", "chuc", "lan", "khac", "moi", "chi", "hn", "du",
}


def _bo_dau(s: str) -> str:
    s = unicodedata.normalize("NFD", s or "")
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return s.replace("đ", "d").replace("Đ", "D")


def tu_khoa(s: str) -> set[str]:
    s = re.sub(r"[^a-z0-9\s]", " ", _bo_dau(s).lower())
    return {t for t in s.split() if len(t) > 1 and t not in TU_BO}


def ngay_tu_ten(duong_dan: str) -> date | None:
    """Rút ngày từ tiền tố YYMMDD trong tên thư mục (kể cả thư mục con)."""
    m = RE_NGAY.search(duong_dan)
    if not m:
        return None
    yy, mm, dd = (int(g) for g in m.groups())
    try:
        return date(2000 + yy, mm, dd)
    except ValueError:
        return None


def ma_lich_tu_ten(duong_dan: str) -> str | None:
    m = RE_LH.search(duong_dan)
    return m.group(1) if m else None


def so_gm_tu_ten(duong_dan: str) -> str | None:
    m = RE_GM.search(duong_dan)
    return m.group(1) if m else None


def phan_nhom(duong_dan: str, theo_ngay: dict, theo_so: dict) -> tuple:
    """Trả về (nhóm, ma_lich hoặc None, danh sách cuộc họp ứng viên).

    theo_ngay: {date: [(cuoc_hop_id, tieu_de), ...]}
    theo_so:   {'241': {cuoc_hop_id, ...}}
    """
    ma = ma_lich_tu_ten(duong_dan)
    if ma:
        return "A", ma, []

    gm = so_gm_tu_ten(duong_dan)
    ung_vien_gm = theo_so.get(gm, set()) if gm else set()
    ng = ngay_tu_ten(duong_dan)
    ung_vien_ngay = theo_ngay.get(ng, []) if ng else []
    id_ngay = {x[0] for x in ung_vien_ngay}

    if ung_vien_gm and id_ngay and (ung_vien_gm & id_ngay):
        chung = ung_vien_gm & id_ngay
        return "B", None, [x for x in ung_vien_ngay if x[0] in chung]
    if ung_vien_gm:
        return "C", None, [(i, "") for i in ung_vien_gm]
    if ung_vien_ngay:
        return "D", None, ung_vien_ngay
    return "E", None, []


def xep_hang_ung_vien(ten_thu_muc: str, ung_vien: list) -> list:
    """Xếp ứng viên theo số từ khoá trùng, nhiều nhất lên đầu.

    Đo trên dữ liệu thật: giúp rõ 9/29 thư mục nhóm D. Số còn lại tên viết tắt
    quá ('TL HN chỉ số', '260519-CCT lv KTSTQ') nên máy chịu, người đọc mới ra.
    """
    tk = tu_khoa(ten_thu_muc.split("/")[-1])
    return sorted(
        ((len(tk & tu_khoa(td)), cid, td) for cid, td in ung_vien),
        key=lambda x: -x[0],
    )
