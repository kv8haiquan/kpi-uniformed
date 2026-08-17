"""Đọc bản xuất .xlsx của Google Sheets lichkv8 — không cần thư viện ngoài.

Google Sheets xuất ra file có ô rỗng dạng tự đóng `<c r="M7" s="43"/>`; nếu
regex không bắt riêng nhánh đó thì `(.*?)</c>` sẽ nuốt luôn ô kế tiếp và gán
giá trị sang sai cột. Đây là lỗi dễ mắc và làm lệch toàn bộ số liệu.

Cách dùng:
    from doc_sheet import doc_bang
    idx, rows = doc_bang('dumps/lichkv8_live.xlsx', 'MEETING')
    print(rows[0][idx['MEETING_ID']])
"""

from __future__ import annotations

import re
import zipfile
from pathlib import Path

_CELL = re.compile(r'<c r="([A-Z]+)\d+"([^>]*?)(?:/>|>(.*?)</c>)', re.S)
_ROW = re.compile(r'<row [^>]*r="(\d+)"[^>]*>(.*?)</row>', re.S)
_SI = re.compile(r"<si>(.*?)</si>", re.S)
_TAG = re.compile(r"<[^>]+>")


class SheetFile:
    def __init__(self, path: str | Path):
        self.z = zipfile.ZipFile(path)
        try:
            raw = self.z.read("xl/sharedStrings.xml").decode("utf8")
            self.ss = [_TAG.sub("", s) for s in _SI.findall(raw)]
        except KeyError:
            self.ss = []
        wb = self.z.read("xl/workbook.xml").decode("utf8")
        rels = dict(
            re.findall(
                r'Id="(rId\d+)"[^>]*Target="([^"]+)"',
                self.z.read("xl/_rels/workbook.xml.rels").decode("utf8"),
            )
        )
        self.sheets: dict[str, str] = {}
        for s in re.findall(r"<sheet[^>]*/>", wb):
            ten = re.search(r'name="([^"]+)"', s).group(1)
            rid = re.search(r'r:id="([^"]+)"', s).group(1)
            self.sheets[ten] = "xl/" + rels[rid].lstrip("/")

    def ten_cac_sheet(self) -> list[str]:
        return list(self.sheets)

    def grid(self, ten_sheet: str) -> list[dict[str, str]]:
        """Trả về danh sách dòng, mỗi dòng là dict {cột: giá trị}."""
        d = self.z.read(self.sheets[ten_sheet]).decode("utf8", "ignore")
        out: list[dict[str, str]] = []
        for _, noi_dung in _ROW.findall(d):
            row: dict[str, str] = {}
            for m in _CELL.finditer(noi_dung):
                col, attrs, body = m.groups()
                if body is None:  # ô rỗng tự đóng
                    row[col] = ""
                    continue
                t = re.search(r't="(\w+)"', attrs)
                v = re.search(r"<v>([^<]*)</v>", body)
                iv = re.search(r"<is>.*?<t[^>]*>(.*?)</t>", body, re.S)
                val = v.group(1) if v else (iv.group(1) if iv else "")
                if t and t.group(1) == "s" and val.isdigit() and int(val) < len(self.ss):
                    val = self.ss[int(val)]
                row[col] = val
            out.append(row)
        return out


def doc_bang(path: str | Path, ten_sheet: str,
             cot_khoa: str | None = None) -> tuple[dict[str, str], list[dict]]:
    """Đọc một sheet, tự tìm dòng header (một số sheet có dòng tiêu đề trước).

    Trả về (idx, rows) với idx = {tên cột: chữ cái cột}.
    """
    g = SheetFile(path).grid(ten_sheet)
    if not g:
        return {}, []
    # Dòng header là dòng đầu tiên có nhiều ô chữ IN HOA kiểu MA_COT
    def diem(r: dict[str, str]) -> int:
        return sum(1 for v in r.values() if re.fullmatch(r"[A-Z][A-Z0-9_]{2,}", v or ""))

    hi = max(range(min(5, len(g))), key=lambda i: diem(g[i]))
    idx = {v: k for k, v in g[hi].items() if v}
    rows = g[hi + 1:]
    if cot_khoa and cot_khoa in idx:
        rows = [r for r in rows if (r.get(idx[cot_khoa], "") or "").strip()]
    return idx, rows
