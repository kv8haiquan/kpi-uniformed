"""G3.1 — Di trú 489 dòng MEETING của lichkv8 sang meeting.cuoc_hop.

Chạy:
    python 01_cuoc_hop.py            # trên kpi_haiquan_test (mặc định)
    python 01_cuoc_hop.py --thu      # chỉ in thống kê, không ghi

🔴 NGÀY THÁNG — điểm dễ hỏng nhất, đọc kỹ trước khi sửa script này:

Cột serial `NGAY_BAT_DAU`/`NGAY_KET_THUC` bị **lệch sớm 1 ngày ở 212/489 dòng
(43%)**. Đã dùng cột `THU` (thứ trong tuần, do người nhập) làm trọng tài:

    THU khớp NGAY_HIEN_THI   : 476/476  (100%)
    THU khớp NGAY_BAT_DAU    :   0/476

Nên `NGAY_HIEN_THI` (chuỗi dd/mm/yyyy) mới là ngày ĐÚNG, serial là dẫn xuất bị
lỗi. Nếu lấy serial làm chuẩn thì 212 cuộc họp rơi sai ngày trên lịch.

Độ dài sự kiện thì cặp serial vẫn nhất quán (kiểm 13/13 dòng nhiều ngày khớp),
nên `ngay_ket_thuc` = ngày đúng + (serial_kt - serial_bd).

13 ô `NGAY_HIEN_THI` chứa KHOẢNG ngày dạng '20/04/2026 - 24/04/2026' → lấy vế
đầu làm ngày bắt đầu, vế sau làm ngày kết thúc.

🔴 GIỜ — `GIO_BAT_DAU` lẫn hai định dạng: 278 dòng 'HH:MM' và 211 dòng phân số
Excel ('0.3333' = 08:00). Bộ chuyển đổi trong chuyen_doi.py xử lý cả hai.
"""

from __future__ import annotations

import argparse
import collections
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from anh_xa import TRANG_THAI
from chuyen_doi import doc_bool, doc_gio, doc_ngay, doc_thoi_diem, gon
from doc_sheet import doc_bang
from ket_noi import (BangTraCongChuc, da_di_tru, ghi_nguon, ket_noi,
                     lay_tai_khoan_he_thong)

NGUON = "MEETING"
XLSX = Path(__file__).resolve().parent / "dumps" / "lichkv8_live.xlsx"
RE_KHOANG = re.compile(r"^(\d{1,2}/\d{1,2}/\d{4})\s*-\s*(\d{1,2}/\d{1,2}/\d{4})$")


def tinh_ngay(r: dict, idx: dict) -> tuple:
    """Trả về (ngay_hop, ngay_ket_thuc) đã sửa lệch. Xem docstring đầu file."""
    raw_ht = (r.get(idx["NGAY_HIEN_THI"], "") or "").strip()
    bd_serial = doc_ngay(r.get(idx["NGAY_BAT_DAU"], ""))
    kt_serial = doc_ngay(r.get(idx["NGAY_KET_THUC"], ""))
    so_ngay = (kt_serial - bd_serial).days if (bd_serial and kt_serial) else 0

    m = RE_KHOANG.match(raw_ht)
    if m:
        bd, kt = doc_ngay(m.group(1)), doc_ngay(m.group(2))
        return bd, (kt if bd and kt and kt > bd else None)

    bd = doc_ngay(raw_ht) or bd_serial
    if not bd:
        return None, None
    from datetime import timedelta
    return bd, (bd + timedelta(days=so_ngay) if so_ngay > 0 else None)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--thu", action="store_true", help="chỉ thống kê, không ghi")
    args = ap.parse_args()

    idx, rows = doc_bang(XLSX, "MEETING", "MEETING_ID")
    print(f"Đọc {len(rows)} dòng MEETING từ {XLSX.name}\n", flush=True)

    conn = ket_noi()
    tra = BangTraCongChuc(conn)
    he_thong = lay_tai_khoan_he_thong(conn)
    khop_u, tong_u = tra.nap_username(XLSX)
    print(f"Bảng tra công chức: {tra.tong} người "
          f"({len(tra.trung_ten)} tên bị trùng, sẽ bỏ qua)")
    print(f"Ánh xạ username lichkv8 → công chức: {khop_u}/{tong_u}\n", flush=True)

    tk = collections.Counter()
    khong_khop_chu_tri: collections.Counter = collections.Counter()

    with conn.cursor() as cur:
        da_co = da_di_tru(cur, NGUON)
        if da_co:
            print(f"Đã di trú trước đó: {len(da_co)} dòng → sẽ cập nhật\n",
                  flush=True)

        for r in rows:
            ma_lich = gon(r.get(idx["MEETING_ID"], ""), 20)
            if not ma_lich:
                tk["bỏ qua (không mã lịch)"] += 1
                continue

            ngay_hop, ngay_kt = tinh_ngay(r, idx)
            if not ngay_hop:
                tk["bỏ qua (không đọc được ngày)"] += 1
                continue

            gio_bd = doc_gio(r.get(idx["GIO_BAT_DAU"], ""))
            if not gio_bd:
                # gio_bat_dau NOT NULL — không có thì coi như cả ngày.
                gio_bd = doc_gio("00:00")
                tk["thiếu giờ bắt đầu → 00:00"] += 1

            # Chủ trì: khớp được thì gán FK, không thì giữ nguyên văn.
            raw_ct = gon(r.get(idx["CHU_TRI"], ""))
            chu_toa_id = tra.tim(raw_ct) if raw_ct else None
            if raw_ct and not chu_toa_id:
                khong_khop_chu_tri[raw_ct[:40]] += 1

            # NGUOI_TAO là USERNAME của lichkv8, không phải mã công chức.
            # 272/489 dòng ghi 'import' (do job nhập liệu, không phải người thật).
            nguoi_tao = gon(r.get(idx["NGUOI_TAO"], ""))
            created_by = tra.tim_theo_username(nguoi_tao) if nguoi_tao else None
            if not created_by:
                created_by = he_thong
                tk["created_by → tài khoản hệ thống"] += 1
            else:
                tk["created_by → người thật"] += 1

            trang_thai = TRANG_THAI.get(
                gon(r.get(idx["TRANG_THAI"], "")) or "", "DA_THONG_BAO")

            gia_tri = {
                "ma_lich": ma_lich,
                "tieu_de": gon(r.get(idx["NOI_DUNG"], ""), 500) or "(không có nội dung)",
                "mo_ta": gon(r.get(idx["GHI_CHU"], "")),
                "ngay_hop": ngay_hop,
                "ngay_ket_thuc": ngay_kt,
                "ngay_hien_thi": ngay_hop,
                "gio_bat_dau": gio_bd,
                "gio_ket_thuc": doc_gio(r.get(idx["GIO_KET_THUC"], "")),
                "dia_diem": gon(r.get(idx["DIA_DIEM"], ""), 300),
                "loai_lich": gon(r.get(idx["LOAI_LICH"], ""), 30) or "LICH_KHAC",
                "trang_thai": trang_thai,
                "chu_toa_id": chu_toa_id,
                "chu_tri_text": raw_ct[:300] if raw_ct else None,
                "thanh_phan_text": gon(r.get(idx["THANH_PHAN"], "")),
                "don_vi_chuan_bi": gon(r.get(idx["DON_VI_CHUAN_BI"], ""), 200),
                "so_van_ban": gon(r.get(idx["SO_VAN_BAN"], ""), 100),
                "ly_do_huy": gon(r.get(idx["LY_DO_HUY"], "")),
                "created_by": created_by,
                "created_at": doc_thoi_diem(r.get(idx["NGAY_TAO"], "")),
                "updated_at": doc_thoi_diem(r.get(idx["NGAY_SUA"], "")),
                "is_deleted": doc_bool(r.get(idx["IS_DELETED"], "")),
            }
            tk["loại: " + gia_tri["loai_lich"]] += 1
            tk["trạng thái: " + trang_thai] += 1
            if chu_toa_id:
                tk["khớp chủ trì"] += 1
            if ngay_kt:
                tk["sự kiện nhiều ngày"] += 1

            if args.thu:
                continue

            cur.execute("""
                INSERT INTO meeting.cuoc_hop
                    (nguon, ma_lich, tieu_de, mo_ta, ngay_hop, ngay_ket_thuc,
                     ngay_hien_thi, gio_bat_dau, gio_ket_thuc, dia_diem,
                     loai_lich, trang_thai, chu_toa_id, chu_tri_text,
                     thanh_phan_text, don_vi_chuan_bi, so_van_ban, ly_do_huy,
                     created_by, created_at, updated_at, is_deleted)
                VALUES
                    ('LICH_CONG_TAC', %(ma_lich)s, %(tieu_de)s, %(mo_ta)s,
                     %(ngay_hop)s, %(ngay_ket_thuc)s, %(ngay_hien_thi)s,
                     %(gio_bat_dau)s, %(gio_ket_thuc)s, %(dia_diem)s,
                     %(loai_lich)s, %(trang_thai)s, %(chu_toa_id)s,
                     %(chu_tri_text)s, %(thanh_phan_text)s, %(don_vi_chuan_bi)s,
                     %(so_van_ban)s, %(ly_do_huy)s, %(created_by)s,
                     COALESCE(%(created_at)s, NOW()),
                     COALESCE(%(updated_at)s, NOW()), %(is_deleted)s)
                ON CONFLICT (ma_lich) WHERE ma_lich IS NOT NULL
                DO UPDATE SET
                    tieu_de = EXCLUDED.tieu_de,
                    mo_ta = EXCLUDED.mo_ta,
                    ngay_hop = EXCLUDED.ngay_hop,
                    ngay_ket_thuc = EXCLUDED.ngay_ket_thuc,
                    ngay_hien_thi = EXCLUDED.ngay_hien_thi,
                    gio_bat_dau = EXCLUDED.gio_bat_dau,
                    gio_ket_thuc = EXCLUDED.gio_ket_thuc,
                    dia_diem = EXCLUDED.dia_diem,
                    loai_lich = EXCLUDED.loai_lich,
                    trang_thai = EXCLUDED.trang_thai,
                    chu_toa_id = EXCLUDED.chu_toa_id,
                    chu_tri_text = EXCLUDED.chu_tri_text,
                    thanh_phan_text = EXCLUDED.thanh_phan_text,
                    don_vi_chuan_bi = EXCLUDED.don_vi_chuan_bi,
                    so_van_ban = EXCLUDED.so_van_ban,
                    ly_do_huy = EXCLUDED.ly_do_huy,
                    updated_at = EXCLUDED.updated_at,
                    is_deleted = EXCLUDED.is_deleted
                RETURNING id
            """, gia_tri)
            id_moi = cur.fetchone()[0]
            ghi_nguon(cur, NGUON, ma_lich, "meeting.cuoc_hop", id_moi)
            tk["đã ghi"] += 1

    if not args.thu:
        conn.commit()

    print("── Kết quả ──")
    for k in sorted(tk):
        print(f"   {tk[k]:>4}  {k}")
    print(f"\nChủ trì không khớp công chức: {sum(khong_khop_chu_tri.values())} "
          f"lượt / {len(khong_khop_chu_tri)} giá trị khác nhau")
    for v, n in khong_khop_chu_tri.most_common(8):
        print(f"   ×{n:<3} {v}")
    conn.close()


if __name__ == "__main__":
    main()
