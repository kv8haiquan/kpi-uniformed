"""Nạp danh sách tên file vào `di_tru_doi_soat.danh_sach_file`.

Màn hình đối soát cần TÊN file để đoán ra cuộc họp — tên thư mục nhiều khi
viết tắt quá ("TL HN chỉ số"), phải nhìn file bên trong mới nhận ra.

Nguồn là `dumps/drive_files_manifest.json` do `05_tai_file_drive.py` sinh ra.

    python nap_ten_file_doi_soat.py            # DB test
    CHO_PHEP_PROD=toi_dong_y python nap_ten_file_doi_soat.py
"""

from __future__ import annotations

import json
from pathlib import Path

from ket_noi import ket_noi

HERE = Path(__file__).resolve().parent
MANIFEST = HERE / "dumps" / "drive_files_manifest.json"


def main() -> None:
    manifest = json.loads(MANIFEST.read_text())

    conn = ket_noi()
    with conn, conn.cursor() as cur:
        cur.execute("SELECT id, drive_folder_id, duong_dan_thu_muc, so_file "
                    "FROM meeting.di_tru_doi_soat")
        hang = cur.fetchall()

        cap_nhat = lech = 0
        for row_id, folder_id, duong_dan, so_file in hang:
            # Gom theo ĐƯỜNG DẪN chứ không theo drive_folder_id: nhiều thư mục
            # có thư mục con, mà file trong thư mục con mang folder_id của
            # thư mục con. Gom theo id thì thư mục "DA_KET_THUC" 75 file chỉ
            # còn 4 — đúng những cụm khó đoán nhất lại mất hết tên file.
            ds = sorted(
                ({"drive_file_id": fid,
                  "ten": m["ten"],
                  "so_byte": m.get("so_byte"),
                  # Đường dẫn con so với thư mục gốc, rỗng nếu nằm ngay trong.
                  "thu_muc_con": m["duong_dan"][len(duong_dan):].lstrip("/")}
                 for fid, m in manifest.items()
                 if m["duong_dan"] == duong_dan
                 or m["duong_dan"].startswith(duong_dan + "/")),
                key=lambda x: (x["thu_muc_con"].lower(), x["ten"].lower()))
            if len(ds) != so_file:
                # Không tự sửa so_file — lệch là dấu hiệu manifest và bảng đối
                # soát sinh ra từ hai lần quét khác nhau, cần người xem lại.
                print(f"  ⚠ lệch số file: {folder_id} bảng={so_file} "
                      f"manifest={len(ds)}")
                lech += 1
            cur.execute(
                "UPDATE meeting.di_tru_doi_soat SET danh_sach_file = %s::jsonb "
                " WHERE id = %s",
                (json.dumps(ds, ensure_ascii=False), row_id))
            cap_nhat += 1

    print(f"Đã nạp tên file cho {cap_nhat} thư mục, {lech} thư mục lệch số file.")


if __name__ == "__main__":
    main()
