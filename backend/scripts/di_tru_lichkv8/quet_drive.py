"""Quét metadata cây thư mục Drive của lichkv8 — CHỈ ĐỌC, không tải file.

Dùng endpoint `embeddedfolderview` công khai của Google Drive nên không cần
xác thực. Kết quả ghi ra JSON để làm mốc đối soát trước/sau di trú (G1.3, G6.2).

Cách dùng:
    python quet_drive.py                    # quét cả 2 kho
    python quet_drive.py --kho tai-lieu     # chỉ kho tài liệu họp
    python quet_drive.py --kho thu-vien     # chỉ thư viện văn bản

Lưu ý: file và thư mục phân biệt bằng dạng href, KHÔNG bằng aria-label:
    file    -> https://drive.google.com/file/d/<id>/view
    thư mục -> https://drive.google.com/drive/folders/<id>
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path

# Hai kho gốc — hardcode trong Mã.gs của lichkv8 (dòng 32 và 4134)
KHO = {
    "tai-lieu": {
        "id": "1AkMxFT-OQlmW5K9lLw_Aoj8X1tZWRSTx",
        "ten": "01.TAI_LIEU_HOP",
        "mo_ta": "Tài liệu cuộc họp, mỗi thư mục con là một cuộc họp",
    },
    "thu-vien": {
        "id": "1nDn4qEgJ99rRpdn5x-2VEEPA_SkX6rvv",
        "ten": "03.THU_VIEN_VAN_BAN",
        "mo_ta": "Thư viện văn bản pháp quy dùng chung",
    },
}

ENTRY = re.compile(
    r'<div class="flip-entry" id="entry-([^"]+)".*?'
    r'<a href="https://drive\.google\.com/(file/d/|drive/folders/).*?'
    r'<div class="flip-entry-title">([^<]*)</div>',
    re.S,
)

OUT_DIR = Path(__file__).resolve().parent / "dumps"
MAX_DEPTH = 3
MAX_REQUESTS = 900


def liet_ke(folder_id: str, so_lan_thu: int = 2) -> list[dict]:
    """Trả về danh sách mục con trực tiếp của một thư mục."""
    url = f"https://drive.google.com/embeddedfolderview?id={folder_id}#list"
    for _ in range(so_lan_thu + 1):
        r = subprocess.run(
            ["curl", "-sL", "--max-time", "45", "--compressed", url],
            capture_output=True,
            text=True,
        )
        if r.returncode == 0 and "flip-entries" in r.stdout:
            return [
                {
                    "id": m.group(1),
                    "loai": "file" if m.group(2).startswith("file") else "thu_muc",
                    "ten": m.group(3),
                }
                for m in ENTRY.finditer(r.stdout)
            ]
        time.sleep(1)
    print(f"  ! không đọc được thư mục {folder_id}", file=sys.stderr)
    return []


def duyet(folder_id: str, duong_dan: str, do_sau: int,
          ket_qua: list[dict], quota: list[int]) -> None:
    if quota[0] <= 0 or do_sau > MAX_DEPTH:
        return
    quota[0] -= 1
    muc = liet_ke(folder_id)
    files = [x for x in muc if x["loai"] == "file"]
    thu_muc = [x for x in muc if x["loai"] == "thu_muc"]
    ket_qua.append({
        "drive_folder_id": folder_id,
        "duong_dan": duong_dan,
        "do_sau": do_sau,
        "so_file": len(files),
        "so_thu_muc_con": len(thu_muc),
        "files": [{"id": f["id"], "ten": f["ten"]} for f in files],
    })
    for tm in thu_muc:
        duyet(tm["id"], f"{duong_dan}/{tm['ten']}", do_sau + 1, ket_qua, quota)
    time.sleep(0.1)


def quet(khoa: str) -> dict:
    cfg = KHO[khoa]
    print(f"→ Quét {cfg['ten']} ({cfg['mo_ta']})", flush=True)
    ket_qua: list[dict] = []
    duyet(cfg["id"], cfg["ten"], 0, ket_qua, [MAX_REQUESTS])
    tong_file = sum(x["so_file"] for x in ket_qua)
    print(f"  {len(ket_qua)} thư mục · {tong_file} file", flush=True)
    return {
        "kho": khoa,
        "drive_folder_id": cfg["id"],
        "ten_thu_muc": cfg["ten"],
        "tong_thu_muc": len(ket_qua),
        "tong_file": tong_file,
        "thu_muc": ket_qua,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--kho", choices=list(KHO), help="chỉ quét một kho")
    args = ap.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for khoa in ([args.kho] if args.kho else list(KHO)):
        data = quet(khoa)
        path = OUT_DIR / f"drive_{khoa}.json"
        path.write_text(json.dumps(data, ensure_ascii=False, indent=1),
                        encoding="utf8")
        print(f"  → {path}", flush=True)


if __name__ == "__main__":
    main()
