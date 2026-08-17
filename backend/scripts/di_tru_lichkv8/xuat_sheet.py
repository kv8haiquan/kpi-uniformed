"""Xuất bản sống của cơ sở dữ liệu lichkv8 (Google Sheets) và đối chiếu số dòng.

Cơ sở dữ liệu của lichkv8 là một Google Sheets 18 sheet, nằm **ngay tại gốc**
kho tài liệu họp trên Drive (`01.TAI_LIEU_HOP`) — không phải ngoài kho như tài
liệu bàn giao ngụ ý. Vì thư mục kho đang chia sẻ công khai nên xuất được trực
tiếp, không cần xác thực.

Mã nguồn Apps Script để `CFG.SPREADSHEET_ID = ''` và dùng
`SpreadsheetApp.getActiveSpreadsheet()` — nên ID này không xuất hiện ở bất kỳ
đâu trong mã; nó chỉ tìm được bằng cách quét kho Drive.

Cách dùng:
    python xuat_sheet.py              # xuất + so với mốc đã ghim
    python xuat_sheet.py --moc <file> # so với một bản .xlsx khác
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from doc_sheet import SheetFile, doc_bang

SPREADSHEET_ID = "1Kyp9ce15Og0b6z9iqNIWk0rziuiukJ-05hG5nbKfo-w"
EXPORT_URL = (
    f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=xlsx"
)

HERE = Path(__file__).resolve().parent
DUMP = HERE / "dumps" / "lichkv8_live.xlsx"
MOC_BAN_GIAO = (
    HERE.parents[2] / "docs" / "Lich Hop Cong Tac" / "Google Appscript"
    / "LICH CONG TAC HQKV8.xlsx"
)

# Sheet → cột khoá dùng để đếm dòng có dữ liệu thật
COT_KHOA = {
    "MEETING": "MEETING_ID",
    "MEETING_PARTICIPANT": "PARTICIPANT_ID",
    "MEETING_FILE": "FILE_RECORD_ID",
    "MEETING_LOG": "LOG_ID",
    "MEETING_RATING": "RATING_ID",
    "MEETING_NOTE": "NOTE_ID",
    "MEETING_NOTE_FILE": "NOTE_FILE_ID",
    "NOTE_SHARE": "SHARE_ID",
    "MEETING_NOTIFICATION": "MEETING_ID",
    "DUTY_ENTRY": "DUTY_ID",
    "DUTY_UNIT_STATUS": "UNIT_CODE",
    "USER": "USER_ID",
    "DEPT": "MA_DON_VI",
    "SETUP": "CONFIG_KEY",
}


def xuat() -> Path:
    DUMP.parent.mkdir(parents=True, exist_ok=True)
    print(f"→ Xuất Google Sheets {SPREADSHEET_ID[:12]}…", flush=True)
    r = subprocess.run(
        ["curl", "-sL", "--max-time", "300", "--retry", "2",
         "-o", str(DUMP), "-w", "%{http_code} %{size_download}", EXPORT_URL],
        capture_output=True, text=True,
    )
    code, size = (r.stdout.split() + ["?", "?"])[:2]
    if code != "200" or not DUMP.exists() or DUMP.stat().st_size < 1000:
        print(f"  ! xuất thất bại (HTTP {code}, {size} byte). "
              f"Kiểm tra quyền chia sẻ của file Sheets.", file=sys.stderr)
        sys.exit(1)
    print(f"  HTTP {code} · {int(size):,} byte → {DUMP}", flush=True)
    return DUMP


def dem(path: Path) -> dict[str, int]:
    ket_qua = {}
    for sheet, khoa in COT_KHOA.items():
        try:
            _, rows = doc_bang(path, sheet, khoa)
            ket_qua[sheet] = len(rows)
        except KeyError:
            ket_qua[sheet] = -1  # sheet không tồn tại
    return ket_qua


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--moc", type=Path, default=MOC_BAN_GIAO,
                    help="bản .xlsx dùng làm mốc đối chiếu")
    args = ap.parse_args()

    live = xuat()
    print(f"  {len(SheetFile(live).ten_cac_sheet())} sheet\n", flush=True)

    if not args.moc.exists():
        print(f"! không thấy mốc đối chiếu {args.moc}", file=sys.stderr)
        return

    a, b = dem(args.moc), dem(live)
    print(f"{'Sheet':<24}{'mốc':>8}{'sống':>8}{'chênh':>8}")
    tong = 0
    for sheet in COT_KHOA:
        d = b[sheet] - a[sheet]
        tong += max(d, 0)
        nhan = f"+{d}" if d > 0 else (str(d) if d else "—")
        print(f"{sheet:<24}{a[sheet]:>8}{b[sheet]:>8}{nhan:>8}")
    print(f"\nTổng dòng phát sinh so với mốc: {tong}")


if __name__ == "__main__":
    main()
