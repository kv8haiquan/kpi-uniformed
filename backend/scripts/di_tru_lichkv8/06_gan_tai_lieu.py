"""G3.2 — Đẩy file đã tải vào kho nền tảng và gắn vào cuộc họp.

Nguyên tắc: **thư mục Drive là nguồn sự thật của file**, không phải bảng
MEETING_FILE. Bảng đó chỉ biết 590/1.226 file — 605 file vào kho bằng cách thả
thẳng lên Drive, không qua phần mềm. Di trú theo thư mục thì file nằm trong
`LH0347_…` tự về đúng LH0347 bất kể hệ cũ có ghi nhận hay không.

Đường đi của file:  dumps/drive_files/<drive_id>  →
                    uploads/meeting/tai-lieu/<cuoc_hop_id>/<uuid>_<tên gốc>

Trùng khớp quy ước của meeting_service/services/storage_service.py để API xem
và tải tài liệu sẵn có dùng được ngay, không phải sửa gì.

Phân nhóm A–E xem phan_nhom.py. Nhóm A, B, C gắn tự động; D và E đưa vào hàng
đợi `meeting.di_tru_doi_soat` cho màn hình đối soát ở G4.9.

Whitelist phần mở rộng của HKG (13 loại) KHÔNG áp dụng khi di trú: file đã tồn
tại trên hệ cũ, từ chối là mất dữ liệu. Script báo riêng các file ngoài danh
sách để quyết định có mở rộng whitelist cho upload mới hay không.

    python 06_gan_tai_lieu.py [--thu]
"""

from __future__ import annotations

import argparse
import collections
import json
import os
import re
import shutil
import sys
import uuid as uuid_mod
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from ket_noi import ghi_nguon, ket_noi, lay_tai_khoan_he_thong
from phan_nhom import phan_nhom

HERE = Path(__file__).resolve().parent
DUMPS = HERE / "dumps"
KHO_FILE = DUMPS / "drive_files"
MANIFEST = DUMPS / "drive_files_manifest.json"

# Kho đích. Mặc định là `backend/uploads/meeting` của CÂY CHỨA SCRIPT NÀY —
# đúng cho môi trường phát triển, SAI cho production.
#
# Đã vấp 19/08/2026: chạy script từ cây dev nhưng ghi vào DB production. Bản ghi
# tài liệu vào prod trong khi file nằm lại cây dev, nên 816 tài liệu tra ra thì
# thấy nhưng bấm tải là hỏng. Phải chỉ định rõ khi chạy cho prod:
#
#     HKG_UPLOAD_DIR=/var/data/kpi/uploads/meeting \
#     CHO_PHEP_PROD=toi_dong_y DB_NAME=kpi_haiquan python 06_gan_tai_lieu.py
#
# Cùng tên biến mà meeting_service dùng, nên hai bên không thể lệch nhau.
UPLOAD_ROOT = Path(
    os.environ.get("HKG_UPLOAD_DIR") or (HERE.parents[1] / "uploads" / "meeting")
)

CHO_PHEP = {".doc", ".docx", ".gif", ".jpeg", ".jpg", ".pdf", ".png",
            ".ppt", ".pptx", ".txt", ".webp", ".xls", ".xlsx"}

# Thư mục lưu trữ chứa NHIỀU cuộc họp con, không phải một cuộc họp.
# Phải xét ở cấp con, nếu không sẽ coi 75 file là của cùng một cuộc họp.
KHO_LUU_TRU = {"01.TAI_LIEU_HOP/DA_KET_THUC"}


def goc_cua(duong_dan: str) -> str:
    """Thư mục gốc (cấp 1) của một đường dẫn — đơn vị ra quyết định đối soát.

    '01.TAI_LIEU_HOP/260226-TL UBND.../BC NQ 57' → '01.TAI_LIEU_HOP/260226-TL UBND...'
    """
    phan = duong_dan.split("/")
    return "/".join(phan[:2]) if len(phan) > 1 else duong_dan


def kieu_mime(ten: str) -> str | None:
    import mimetypes
    return mimetypes.guess_type(ten)[0]


def _chan_ghi_lech_kho() -> None:
    """Chặn ghi bản ghi vào prod trong khi file rơi lại kho của cây làm việc.

    Từ 19/08/2026 chỗ này chỉ có một dòng ghi chú nhắc phải đặt
    `HKG_UPLOAD_DIR`. Ghi chú không chặn được ai — ngày 21/08 lại vấp đúng lỗi
    đó lần nữa: 10 tài liệu mới vào cơ sở dữ liệu thật còn file nằm lại
    `backend/uploads/`, tra ra thì thấy mà bấm tải là hỏng. Nay thành rào cứng.
    """
    if os.environ.get("DB_NAME") != "kpi_haiquan":
        return
    if os.environ.get("HKG_UPLOAD_DIR"):
        return
    sys.exit(
        "⛔ Ghi vào cơ sở dữ liệu THẬT mà chưa chỉ định kho file.\n"
        f"   Mặc định sẽ ghi file vào {HERE.parents[1] / 'uploads' / 'meeting'},\n"
        "   tức là bản ghi vào prod còn file nằm lại cây làm việc — tài liệu\n"
        "   hiện trên danh sách nhưng bấm tải là hỏng.\n\n"
        "   Chạy lại kèm kho thật:\n"
        "     HKG_UPLOAD_DIR=/var/data/kpi/uploads/meeting \\\n"
        "     DB_NAME=kpi_haiquan CHO_PHEP_PROD=toi_dong_y \\\n"
        "     python 06_gan_tai_lieu.py"
    )


def da_gan(conn) -> set:
    """Cặp (tên file, cỡ file) ĐÃ có trong kho — khoá chống gắn hai lần.

    Script này KHÔNG idempotent cho tới 21/08/2026: chạy lại là gắn lại từ đầu
    toàn bộ, đẻ ra 809 bản sao trên cơ sở dữ liệu thật.

    🔴 Khoá phải là NỘI DUNG FILE, không phải (cuộc họp, tên file). Lý do: hàm
    khớp thư mục → cuộc họp KHÔNG TẤT ĐỊNH. Ngày nào cũng có 2–8 cuộc họp nên
    không thư mục nào có ứng viên duy nhất (xem G4.9 trong kế hoạch); lượt này
    script gán 5 file vào LH0445, lượt trước gán đúng 5 file đó vào LH0007 và
    LH0009. Khoá theo cuộc họp là vô dụng vì cuộc họp đổi mỗi lượt chạy — đã
    thử và vẫn lọt 5 bản sao.

    Đánh đổi đã chấp nhận: một tài liệu thật sự dùng chung cho hai cuộc họp sẽ
    chỉ gắn vào cuộc họp bắt được trước. Thà thiếu một liên kết mà sửa tay được
    còn hơn đẻ bản sao mỗi lần chạy lại.

    Không dùng ràng buộc UNIQUE ở cơ sở dữ liệu được vì dữ liệu di trú vốn đã
    có 54 nhóm trùng sẵn từ các đợt trước.
    """
    with conn.cursor() as cur:
        cur.execute("""SELECT ten_tai_lieu, file_size FROM meeting.tai_lieu
                        WHERE is_deleted = false AND ten_tai_lieu IS NOT NULL""")
        return {(r[0], r[1]) for r in cur.fetchall()}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--thu", action="store_true", help="chỉ thống kê, không ghi")
    ap.add_argument("--gan-lai", action="store_true",
                    help="gắn lại cả tài liệu đã có (mặc định bỏ qua)")
    args = ap.parse_args()

    if not args.thu:
        _chan_ghi_lech_kho()

    if not MANIFEST.exists():
        sys.exit("⛔ Chưa có manifest — chạy 05_tai_file_drive.py trước")
    manifest = json.loads(MANIFEST.read_text(encoding="utf8"))
    print(f"Manifest: {len(manifest)} file đã tải\n", flush=True)

    conn = ket_noi()
    he_thong = lay_tai_khoan_he_thong(conn)
    san_co = set() if args.gan_lai else da_gan(conn)
    if san_co:
        print(f"Đã gắn từ trước: {len(san_co)} tài liệu — sẽ bỏ qua\n", flush=True)

    # Chỉ mục cuộc họp để tra nhanh
    with conn.cursor() as cur:
        cur.execute("SELECT ma_lich, id, tieu_de FROM meeting.cuoc_hop "
                    "WHERE nguon = 'LICH_CONG_TAC' AND ma_lich IS NOT NULL")
        rows = cur.fetchall()
        theo_ma = {r[0]: r[1] for r in rows}

        cur.execute("SELECT id, ngay_hop, tieu_de, so_van_ban, mo_ta "
                    "FROM meeting.cuoc_hop WHERE nguon = 'LICH_CONG_TAC'")
        theo_ngay: dict = collections.defaultdict(list)
        theo_so: dict = collections.defaultdict(set)
        for cid, ngay, tieu_de, so_vb, mo_ta in cur.fetchall():
            theo_ngay[ngay].append((cid, tieu_de or ""))
            for n in re.findall(r"\b(\d{2,4})\b",
                                " ".join(filter(None, [so_vb, tieu_de, mo_ta]))):
                theo_so[n].add(cid)

    print(f"Chỉ mục: {len(theo_ma)} mã lịch · {len(theo_ngay)} ngày · "
          f"{len(theo_so)} số hiệu\n", flush=True)

    # CHỈ xử lý kho tài liệu họp. Kho thư viện (23 file) thuộc mục Tài liệu
    # của portal theo quyết định 17/08/2026 — không gắn vào cuộc họp nào.
    tai_lieu_hop = {k: v for k, v in manifest.items()
                    if v.get("kho") == "tai-lieu"}
    bo_qua_thu_vien = len(manifest) - len(tai_lieu_hop)
    if bo_qua_thu_vien:
        print(f"Bỏ qua {bo_qua_thu_vien} file kho thư viện — thuộc portal, "
              f"xử lý ở G5.1\n", flush=True)

    # Gom file theo thư mục chứa nó
    theo_thu_muc: dict = collections.defaultdict(list)
    for fid, m in tai_lieu_hop.items():
        theo_thu_muc[(m["duong_dan"], m["drive_folder_id"])].append((fid, m))

    tk = collections.Counter()
    ngoai_whitelist: collections.Counter = collections.Counter()
    thieu_file = []
    cho_doi_soat: dict = collections.defaultdict(list)

    with conn.cursor() as cur:
        for (duong_dan, folder_id), ds_file in sorted(theo_thu_muc.items()):
            # Thư mục lưu trữ: bỏ qua ở cấp gốc, các thư mục con xét riêng.
            if duong_dan in KHO_LUU_TRU:
                tk["bỏ qua thư mục lưu trữ cấp gốc"] += 1
                continue

            nhom, ma_lich, ung_vien = phan_nhom(duong_dan, theo_ngay, theo_so)
            cuoc_hop_id = theo_ma.get(ma_lich) if ma_lich else None
            if nhom in ("B", "C") and ung_vien:
                cuoc_hop_id = ung_vien[0][0]

            tk[f"thư mục nhóm {nhom}"] += 1
            tk[f"file nhóm {nhom}"] += len(ds_file)

            # Nhóm D, E: không gắn được bằng máy → đưa vào hàng đợi đối soát.
            #
            # Gom về THƯ MỤC GỐC chứ không mỗi thư mục con một dòng: người rà
            # quyết định ở cấp cuộc họp, thư mục con đương nhiên theo cha.
            # Nếu để mỗi thư mục con một dòng thì 34 quyết định phình thành 91.
            if nhom in ("D", "E") or not cuoc_hop_id:
                cho_doi_soat[goc_cua(duong_dan)].append(
                    (folder_id, duong_dan, len(ds_file),
                     nhom if nhom in ("D", "E") else "E"))
                tk["thư mục con chờ đối soát"] += 1
                continue

            # Nhóm A, B, C: gắn thẳng.
            for fid, m in ds_file:
                nguon_file = KHO_FILE / fid
                if not nguon_file.exists():
                    thieu_file.append((fid, m["ten"]))
                    tk["file chưa tải được"] += 1
                    continue

                ext = Path(m["ten"]).suffix.lower()
                if ext not in CHO_PHEP:
                    ngoai_whitelist[ext or "(không đuôi)"] += 1

                # Đã gắn rồi thì thôi — xem docstring `da_gan`. Tên file cắt
                # đúng như lúc ghi để hai bên so được với nhau.
                khoa = (m["ten"][:500], m["so_byte"])
                if not args.gan_lai and khoa in san_co:
                    tk["bỏ qua (đã gắn từ trước)"] += 1
                    continue

                if args.thu:
                    tk["sẽ gắn"] += 1
                    san_co.add(khoa)  # để --thu đếm đúng như lúc chạy thật
                    continue

                san_co.add(khoa)  # cùng một lượt chạy cũng không gắn hai lần
                ten_dich = f"{uuid_mod.uuid4().hex}_{m['ten']}"
                rel_key = f"tai-lieu/{cuoc_hop_id}/{ten_dich}"
                dich = UPLOAD_ROOT / rel_key
                dich.parent.mkdir(parents=True, exist_ok=True)
                if not dich.exists():
                    shutil.copy2(nguon_file, dich)

                cur.execute("""
                    INSERT INTO meeting.tai_lieu
                        (cuoc_hop_id, ten_tai_lieu, minio_bucket, minio_key,
                         file_size, mime_type, extension, phan_quyen, created_by)
                    VALUES (%s,%s,'meeting',%s,%s,%s,%s,'CONG_KHAI',%s)
                    RETURNING id
                """, (cuoc_hop_id, m["ten"][:500], rel_key, m["so_byte"],
                      kieu_mime(m["ten"]), ext[:10] or None, he_thong))
                ghi_nguon(cur, "DRIVE_FILE", fid, "meeting.tai_lieu",
                          cur.fetchone()[0], drive_file_id=fid,
                          ghi_chu=f"nhóm {nhom} · {duong_dan}")
                tk["đã gắn"] += 1

    # Ghi hàng đợi đối soát — mỗi thư mục gốc một dòng.
    with conn.cursor() as cur:
        from phan_nhom import ngay_tu_ten, so_gm_tu_ten
        for goc, ds_con in sorted(cho_doi_soat.items()):
            tong_file = sum(x[2] for x in ds_con)
            # Nhóm của cả cụm: ưu tiên D (có gợi ý) hơn E (không có gì).
            nhom_cum = "D" if any(x[3] == "D" for x in ds_con) else "E"
            folder_goc = next((x[0] for x in ds_con if x[1] == goc), ds_con[0][0])
            tk[f"cụm chờ đối soát nhóm {nhom_cum}"] += 1
            tk["file chờ đối soát"] += tong_file
            if args.thu:
                continue
            cur.execute("""
                INSERT INTO meeting.di_tru_doi_soat
                    (drive_folder_id, duong_dan_thu_muc, so_file,
                     ngay_suy_ra, so_gm_suy_ra, nhom, ghi_chu)
                VALUES (%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (drive_folder_id) DO UPDATE SET
                    so_file = EXCLUDED.so_file, nhom = EXCLUDED.nhom,
                    ghi_chu = EXCLUDED.ghi_chu
            """, (folder_goc, goc, tong_file, ngay_tu_ten(goc),
                  so_gm_tu_ten(goc), nhom_cum,
                  f"{len(ds_con)} thư mục con" if len(ds_con) > 1 else None))

    if not args.thu:
        conn.commit()

    print("── Kết quả ──")
    for k in sorted(tk):
        print(f"   {tk[k]:>5}  {k}")
    if ngoai_whitelist:
        print(f"\nFile ngoài whitelist HKG (vẫn di trú, whitelist chỉ áp cho "
              f"upload mới):")
        for e, n in ngoai_whitelist.most_common():
            print(f"   ×{n:<3} {e}")
    if thieu_file:
        print(f"\nFile có trong manifest nhưng thiếu trên đĩa: {len(thieu_file)}")
        for fid, ten in thieu_file[:5]:
            print(f"   {ten[:60]}")
    conn.close()


if __name__ == "__main__":
    main()
