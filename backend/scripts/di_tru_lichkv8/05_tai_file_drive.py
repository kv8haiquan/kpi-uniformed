"""G3.2 — Tải toàn bộ file từ kho Drive về đĩa (bản lạnh).

Tải về `dumps/drive_files/<drive_file_id>` — đặt tên theo ID chứ không theo tên
file, vì tên file tiếng Việt dễ đụng nhau và dễ hỏng mã ký tự. Tên thật giữ
trong manifest.

Đây là **bản lạnh**: giữ nguyên sau khi đã đẩy vào uploads/meeting, ít nhất
cho tới khi nghiệm thu. Nếu bước gắn file (06) sai thì chạy lại được mà không
phải tải lại hơn 1 GB. Thư mục này bị .gitignore nên không lọt vào backup mã
nguồn — đó là chủ ý, nhưng cũng nghĩa là phải off-site nó TRƯỚC khi thu hồi
chia sẻ Drive ở G6.7.

Chạy lại được: file đã tải và còn nguyên vẹn thì bỏ qua.

    python 05_tai_file_drive.py               # tải cả 2 kho
    python 05_tai_file_drive.py --kho thu-vien
    python 05_tai_file_drive.py --lai         # tải lại cả file đã có
    python 05_tai_file_drive.py --thu-lai-loi # thử lại nhóm file từng hỏng
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
DUMPS = HERE / "dumps"
KHO_FILE = DUMPS / "drive_files"
MANIFEST = DUMPS / "drive_files_manifest.json"
FILE_LOI = DUMPS / "drive_files_loi.json"

SO_LUONG = 4          # tải song song — vừa đủ nhanh, không dồn ép Google
SO_LAN_THU = 3

# File Google gốc (Docs/Sheets/Slides) KHÔNG tải nhị phân được — endpoint
# uc?export=download trả HTTP 500. Phải dùng endpoint xuất tương ứng.
# Nhận biết: ID dài 44 ký tự (file tải lên thường 33), và trang xem khai báo
# mime application/vnd.google-apps.*
XUAT_GOOGLE = {
    "document": ("https://docs.google.com/document/d/{id}/export?format=pdf",
                 ".pdf"),
    "spreadsheet": ("https://docs.google.com/spreadsheets/d/{id}/export?format=xlsx",
                    ".xlsx"),
    "presentation": ("https://docs.google.com/presentation/d/{id}/export/pptx",
                     ".pptx"),
    "drawing": ("https://docs.google.com/drawings/d/{id}/export/pdf", ".pdf"),
}

# Chính là cơ sở dữ liệu của lichkv8, nằm ở gốc kho. Không phải tài liệu họp.
BO_QUA = {"1Kyp9ce15Og0b6z9iqNIWk0rziuiukJ-05hG5nbKfo-w"}

_khoa = threading.Lock()


def loai_google(fid: str) -> str | None:
    """Trả về 'document' | 'spreadsheet' | ... nếu là file Google gốc.

    Trang xem của Drive khai báo nhiều mime cùng lúc — file Docs có cả
    `vnd.google-apps.document` lẫn `vnd.google-apps.kix` (tên nội bộ của trình
    soạn thảo). Phải duyệt hết rồi lấy cái nào có trong danh mục xuất, không
    được lấy cái gặp đầu tiên.
    """
    r = subprocess.run(
        ["curl", "-sL", "--max-time", "60",
         f"https://drive.google.com/file/d/{fid}/view"],
        capture_output=True, text=True)
    for loai in re.findall(r"application/vnd\.google-apps\.(\w+)", r.stdout or ""):
        if loai in XUAT_GOOGLE:
            return loai
    return None


def tai_google(fid: str, loai: str) -> tuple[int, str | None]:
    mau, _ = XUAT_GOOGLE[loai]
    dich = KHO_FILE / fid
    r = subprocess.run(
        ["curl", "-sL", "--max-time", "300", "-o", str(dich),
         "-w", "%{http_code}", mau.format(id=fid)],
        capture_output=True, text=True)
    if (r.stdout or "").strip() == "200" and dich.exists() \
            and dich.stat().st_size > 0:
        return dich.stat().st_size, None
    dich.unlink(missing_ok=True)
    return 0, f"xuất {loai} thất bại (HTTP {r.stdout})"


def tai_mot(fid: str) -> tuple[str, int, str | None]:
    """Tải một file. Trả về (fid, số byte, lỗi)."""
    if fid in BO_QUA:
        return fid, 0, "bỏ qua: đây là cơ sở dữ liệu lichkv8, không phải tài liệu"

    dich = KHO_FILE / fid
    url = f"https://drive.google.com/uc?export=download&id={fid}"

    for lan in range(SO_LAN_THU):
        r = subprocess.run(
            ["curl", "-sL", "--max-time", "300", "--retry", "1",
             "-o", str(dich), "-w", "%{http_code} %{content_type}", url],
            capture_output=True, text=True,
        )
        phan = (r.stdout or "").split(None, 1)
        ma = phan[0] if phan else "000"
        kieu = phan[1] if len(phan) > 1 else ""

        if ma == "200" and dich.exists() and dich.stat().st_size > 0:
            # Trang HTML thay vì file: hoặc là Google Docs gốc, hoặc là trang
            # cảnh báo quét virus với file lớn.
            if "text/html" in kieu:
                noi_dung = dich.read_bytes()[:2000].decode("utf8", "ignore")
                if "confirm=" in noi_dung or "virus" in noi_dung.lower():
                    dich.unlink(missing_ok=True)
                    return fid, 0, "cần xác nhận quét virus (file lớn)"
                dich.unlink(missing_ok=True)
                return fid, 0, "là file Google Docs gốc, không tải nhị phân được"
            return fid, dich.stat().st_size, None

    # uc?export=download hỏng → thử xem có phải file Google gốc không.
    if (loai := loai_google(fid)):
        kich_thuoc, sai = tai_google(fid, loai)
        return fid, kich_thuoc, sai

    dich.unlink(missing_ok=True)
    return fid, 0, f"HTTP {ma}"


def bam(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for khoi in iter(lambda: f.read(1 << 20), b""):
            h.update(khoi)
    return h.hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--kho", choices=["tai-lieu", "thu-vien"])
    ap.add_argument("--lai", action="store_true", help="tải lại cả file đã có")
    ap.add_argument("--thu-lai-loi", action="store_true",
                    help="thử lại cả những file lần trước tải hỏng")
    args = ap.parse_args()

    KHO_FILE.mkdir(parents=True, exist_ok=True)
    manifest: dict = json.loads(MANIFEST.read_text(encoding="utf8")) \
        if MANIFEST.exists() else {}

    # Gom danh sách file từ bản quét Drive
    can_tai: dict[str, dict] = {}
    for khoa in ([args.kho] if args.kho else ["tai-lieu", "thu-vien"]):
        f = DUMPS / f"drive_{khoa}.json"
        if not f.exists():
            sys.exit(f"⛔ Chưa có {f.name} — chạy quet_drive.py trước")
        d = json.loads(f.read_text(encoding="utf8"))
        for tm in d["thu_muc"]:
            for fi in tm["files"]:
                can_tai[fi["id"]] = {
                    "ten": fi["ten"],
                    "duong_dan": tm["duong_dan"],
                    "drive_folder_id": tm["drive_folder_id"],
                    "kho": khoa,
                }

    print(f"Tổng file trong bản quét: {len(can_tai)}", flush=True)

    # File đã hỏng ở lần chạy trước thì bỏ qua, trừ khi bảo thử lại. Hai file
    # trong kho là Google Docs gốc / trả HTTP 500 vĩnh viễn; mỗi lượt thử tốn
    # tới 3 lần curl `--max-time 300` rồi thêm một lượt dò loại file, nên để
    # nguyên là mỗi lần chạy lại treo vài phút cho đúng hai file không bao giờ
    # tải được.
    da_loi: dict = {}
    if FILE_LOI.exists() and not args.thu_lai_loi and not args.lai:
        da_loi = json.loads(FILE_LOI.read_text(encoding="utf8"))

    con_lai = []
    for fid in can_tai:
        p = KHO_FILE / fid
        if not args.lai and p.exists() and p.stat().st_size > 0 \
                and fid in manifest:
            continue
        if fid in da_loi:
            continue
        con_lai.append(fid)
    print(f"Đã có sẵn: {len(can_tai) - len(con_lai) - len(da_loi)} "
          f"· bỏ qua vì lần trước lỗi: {len(da_loi)} "
          f"· cần tải: {len(con_lai)}", flush=True)
    if da_loi:
        print("  (chạy với --thu-lai-loi nếu muốn thử lại nhóm lỗi)\n",
              flush=True)

    if not con_lai:
        print("Không có gì để tải.")
        return

    xong = [0]
    loi: dict[str, str] = {}
    tong_byte = [0]

    def xu_ly(fid: str) -> None:
        _, kich_thuoc, sai = tai_mot(fid)
        with _khoa:
            xong[0] += 1
            if sai:
                loi[fid] = sai
            else:
                tong_byte[0] += kich_thuoc
                manifest[fid] = {
                    **can_tai[fid],
                    "so_byte": kich_thuoc,
                    "sha256": bam(KHO_FILE / fid),
                }
            if xong[0] % 50 == 0 or xong[0] == len(con_lai):
                print(f"  {xong[0]}/{len(con_lai)} · "
                      f"{tong_byte[0] / 1e6:.0f} MB · lỗi {len(loi)}", flush=True)

    with ThreadPoolExecutor(max_workers=SO_LUONG) as ex:
        list(ex.map(xu_ly, con_lai))

    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=1),
                        encoding="utf8")

    print(f"\n── Kết quả ──")
    print(f"   tải thành công : {len(con_lai) - len(loi)}")
    print(f"   dung lượng     : {tong_byte[0] / 1e6:.1f} MB")
    print(f"   trong manifest : {len(manifest)}")
    print(f"   lỗi            : {len(loi)}")
    for fid, sai in list(loi.items())[:15]:
        print(f"      {can_tai[fid]['ten'][:50]} — {sai}")
    if loi:
        FILE_LOI.write_text(
            json.dumps({k: {**can_tai[k], "loi": v} for k, v in loi.items()},
                       ensure_ascii=False, indent=1), encoding="utf8")
        print(f"   → chi tiết ở dumps/drive_files_loi.json")


if __name__ == "__main__":
    main()
