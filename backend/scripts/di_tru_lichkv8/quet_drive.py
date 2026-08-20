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
import threading
import time
from concurrent.futures import ThreadPoolExecutor
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

# Quét song song theo TỪNG MỨC. Mỗi thư mục là một lượt gọi mạng ~0,9 giây;
# kho tài liệu có 295 thư mục và thư viện 189, nên quét tuần tự mất khoảng 8
# phút cho mỗi lần chạy — mà lần nào cũng phải quét lại toàn bộ cây chỉ để
# phát hiện vài file mới. Tám luồng đưa con số đó xuống khoảng một phút.
#
# Tám chứ không nhiều hơn: đây là endpoint công khai không có khoá xác thực,
# ép mạnh thì Google chặn IP và cả đợt di trú đứng.
SO_LUONG = 8


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


def duyet(goc_id: str, goc_duong_dan: str,
          ket_qua: list[dict], quota: list[int]) -> None:
    """Duyệt cây theo BỀ RỘNG, mỗi mức quét song song.

    Đổi từ đệ quy theo chiều sâu sang bề rộng chỉ để chạy song song được: các
    thư mục cùng một mức không phụ thuộc nhau nên gọi mạng cùng lúc được, còn
    đệ quy thì mỗi lượt phải chờ lượt trước xong.

    Kết quả sắp lại theo đường dẫn ở cuối để hai lần chạy cho ra cùng thứ tự —
    file JSON này là mốc đối soát, khác thứ tự là mỗi lần so lại một kiểu.
    """
    khoa = threading.Lock()
    muc_nay = [(goc_id, goc_duong_dan)]

    for do_sau in range(MAX_DEPTH + 1):
        if not muc_nay or quota[0] <= 0:
            break

        # Cắt theo hạn ngạch TRƯỚC khi gọi mạng, để số lượt gọi không vượt
        # MAX_REQUESTS chỉ vì nhiều luồng cùng trừ một biến.
        with khoa:
            lam = muc_nay[:max(0, quota[0])]
            quota[0] -= len(lam)

        def mot(cap: tuple[str, str]) -> tuple[str, str, list[dict]]:
            fid, duong_dan = cap
            return fid, duong_dan, liet_ke(fid)

        with ThreadPoolExecutor(max_workers=SO_LUONG) as pool:
            dong = list(pool.map(mot, lam))

        muc_sau: list[tuple[str, str]] = []
        for fid, duong_dan, muc in dong:
            files = [x for x in muc if x["loai"] == "file"]
            thu_muc = [x for x in muc if x["loai"] == "thu_muc"]
            ket_qua.append({
                "drive_folder_id": fid,
                "duong_dan": duong_dan,
                "do_sau": do_sau,
                "so_file": len(files),
                "so_thu_muc_con": len(thu_muc),
                "files": [{"id": f["id"], "ten": f["ten"]} for f in files],
            })
            muc_sau += [(tm["id"], f"{duong_dan}/{tm['ten']}")
                        for tm in thu_muc]

        print(f"  mức {do_sau}: {len(lam)} thư mục", flush=True)
        muc_nay = muc_sau

    ket_qua.sort(key=lambda x: x["duong_dan"])


def quet(khoa: str) -> dict:
    cfg = KHO[khoa]
    print(f"→ Quét {cfg['ten']} ({cfg['mo_ta']})", flush=True)
    ket_qua: list[dict] = []
    bat_dau = time.monotonic()
    duyet(cfg["id"], cfg["ten"], ket_qua, [MAX_REQUESTS])
    tong_file = sum(x["so_file"] for x in ket_qua)
    print(f"  {len(ket_qua)} thư mục · {tong_file} file "
          f"· {time.monotonic() - bat_dau:.0f}s", flush=True)
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
