"""G3.1 — Di trú trực ban: DUTY_ENTRY → truc_ban, DUTY_UNIT_STATUS → truc_ban_tru_so.

Chỉ di trú bản ghi còn hiệu lực (STATUS != 'Deleted'): 333/709 dòng.
376 dòng còn lại là bản nháp đã xoá của các đợt nhập trước.

Khoá theo TRỤ SỞ, không theo đơn vị — xem docstring migration meeting_018.
Mã trụ sở giữ nguyên của lichkv8 (`unit_code_cu`) để đối soát được sau này.

Đặc điểm dữ liệu (khảo sát G1, 333 bản ghi còn hiệu lực):
    DUTY_TYPE   'Thứ 7/CN'  100%  → loai_truc = 'CUOI_TUAN'
    DUTY_SHIFT  'Cả ngày'   100%  → ca_truc   = 'CA_NGAY'
    PHONE       có giá trị  100%  → trường cốt lõi, không được mất
    POSITION    toàn lãnh đạo: Phó Đội trưởng 252, Đội trưởng 35,
                Phó CCT 22, Phó Chánh VP 22

Chạy:  python 03_truc_ban.py [--thu]
"""

from __future__ import annotations

import argparse
import collections
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from chuyen_doi import doc_bool, doc_ngay, doc_thoi_diem, gon
from doc_sheet import doc_bang
from ket_noi import BangTraCongChuc, ghi_nguon, ket_noi

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from meeting_service.services.lich_cong_tac_service import chuan_hoa_sdt

XLSX = Path(__file__).resolve().parent / "dumps" / "lichkv8_live.xlsx"


def da_co(conn) -> set:
    """Ca trực ĐÃ có trong CSDL — khoá chống ghi hai lần.

    `ghi_nguon` ghi ánh xạ nhưng vòng lặp INSERT không hề TRA ánh xạ đó, nên
    chạy lại script là đẻ thêm một bộ bản ghi mới rồi trỏ ánh xạ sang bộ mới —
    bộ cũ thành mồ côi, không ai biết. Đã xảy ra thật: 333 ca trực bị nhân đôi
    trên cơ sở dữ liệu thật, mỗi người hiện hai lần trong lịch trực.

    Khoá theo NỘI DUNG (ngày, trụ sở, họ tên) chứ không theo `DUTY_ID`: đúng
    bài học của `06_gan_tai_lieu.py` — ánh xạ có thể bị ghi đè, còn nội dung
    trùng thì người dùng nhìn thấy ngay.
    """
    with conn.cursor() as cur:
        cur.execute("""SELECT ngay_truc, tru_so_id, ho_ten
                         FROM meeting.truc_ban WHERE is_deleted = false""")
        return {(r[0], r[1], r[2]) for r in cur.fetchall()}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--thu", action="store_true", help="chỉ thống kê, không ghi")
    args = ap.parse_args()

    conn = ket_noi()
    tra = BangTraCongChuc(conn)
    tra.nap_username(XLSX)

    with conn.cursor() as cur:
        cur.execute("SELECT ma_tru_so, id FROM meeting.tru_so")
        tru_so = dict(cur.fetchall())
    print(f"Trụ sở trong danh mục: {len(tru_so)}\n", flush=True)

    tk = collections.Counter()
    ma_la: collections.Counter = collections.Counter()
    co_san = da_co(conn)
    print(f"Ca trực đã có trong CSDL: {len(co_san)}\n", flush=True)

    # ── DUTY_ENTRY → meeting.truc_ban ────────────────────────────────────
    idx, rows = doc_bang(XLSX, "DUTY_ENTRY", "DUTY_ID")
    print(f"DUTY_ENTRY: {len(rows)} dòng", flush=True)

    with conn.cursor() as cur:
        for r in rows:
            duty_id = gon(r.get(idx["DUTY_ID"], ""))
            if (r.get(idx["STATUS"], "") or "").strip() == "Deleted":
                tk["bỏ qua (đã xoá)"] += 1
                continue

            ngay = doc_ngay(r.get(idx["DUTY_DATE"], ""))
            unit = (gon(r.get(idx["UNIT_CODE"], "")) or "").upper()
            ts_id = tru_so.get(unit)
            if not ngay or not ts_id:
                ma_la[unit or "(rỗng)"] += 1
                tk["bỏ qua (không xác định được ngày/trụ sở)"] += 1
                continue

            ho_ten = gon(r.get(idx["FULLNAME"], ""), 100)
            if not ho_ten:
                tk["bỏ qua (không có họ tên)"] += 1
                continue

            if (ngay, ts_id, ho_ten) in co_san:
                tk["bỏ qua (đã có trong CSDL)"] += 1
                continue

            cc_id = tra.tim(ho_ten)
            tk["khớp công chức" if cc_id else "không khớp công chức"] += 1

            nguoi_tao = gon(r.get(idx["CREATED_BY"], ""))
            gia_tri = (
                ngay, ts_id, unit, cc_id, ho_ten,
                gon(r.get(idx["POSITION"], ""), 100),
                # Bản xuất XLSX ghi 691/724 số dạng khoa học `9.13264387E8` —
                # Google Sheets coi số điện thoại là SỐ nên rụng số 0 đứng
                # đầu. Ghi thẳng là toàn bộ lịch trực hiện sai số điện thoại.
                gon(chuan_hoa_sdt(r.get(idx["PHONE"], "")), 20),
                gon(r.get(idx["NOTE"], "")),
                "DA_NOP" if (r.get(idx["STATUS"], "") or "").strip().upper()
                == "SUBMITTED" else "NHAP",
                tra.tim_theo_username(nguoi_tao) if nguoi_tao else None,
                doc_thoi_diem(r.get(idx["CREATED_AT"], "")),
                doc_thoi_diem(r.get(idx["UPDATED_AT"], "")),
            )
            tk["hợp lệ"] += 1
            # Nhớ ngay, kể cả ở chế độ --thu: bản xuất có thể tự chứa hai dòng
            # cùng ca trực, khoá chỉ tra CSDL sẽ để lọt cặp trùng nội bộ.
            co_san.add((ngay, ts_id, ho_ten))
            if args.thu:
                continue

            cur.execute("""
                INSERT INTO meeting.truc_ban
                    (ngay_truc, tru_so_id, unit_code_cu, cong_chuc_id, ho_ten,
                     chuc_vu, so_dien_thoai, ghi_chu, trang_thai, created_by,
                     created_at, updated_at, loai_truc, ca_truc)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
                        COALESCE(%s, NOW()), COALESCE(%s, NOW()),
                        'CUOI_TUAN', 'CA_NGAY')
                RETURNING id
            """, gia_tri)
            ghi_nguon(cur, "DUTY_ENTRY", duty_id, "meeting.truc_ban",
                      cur.fetchone()[0])
            tk["đã ghi truc_ban"] += 1

    # ── DUTY_UNIT_STATUS → meeting.truc_ban_tru_so ───────────────────────
    idx2, rows2 = doc_bang(XLSX, "DUTY_UNIT_STATUS", "UNIT_CODE")
    print(f"DUTY_UNIT_STATUS: {len(rows2)} dòng", flush=True)

    with conn.cursor() as cur:
        for r in rows2:
            ngay = doc_ngay(r.get(idx2["DUTY_DATE"], ""))
            unit = (gon(r.get(idx2["UNIT_CODE"], "")) or "").upper()
            ts_id = tru_so.get(unit)
            if not ngay or not ts_id:
                tk["trạng thái: bỏ qua (không xác định)"] += 1
                continue
            nguoi_nop = gon(r.get(idx2["SUBMITTED_BY"], ""))
            tk["trạng thái: hợp lệ"] += 1
            if args.thu:
                continue
            cur.execute("""
                INSERT INTO meeting.truc_ban_tru_so
                    (ngay_truc, tru_so_id, trang_thai, nguoi_nop_id,
                     thoi_diem_nop, is_locked, ghi_chu, updated_at)
                VALUES (%s,%s,%s,%s,%s,%s,%s, COALESCE(%s, NOW()))
                ON CONFLICT (ngay_truc, tru_so_id) DO UPDATE SET
                    trang_thai = EXCLUDED.trang_thai,
                    nguoi_nop_id = EXCLUDED.nguoi_nop_id,
                    thoi_diem_nop = EXCLUDED.thoi_diem_nop,
                    is_locked = EXCLUDED.is_locked
            """, (
                ngay, ts_id,
                "DA_NOP" if (r.get(idx2["STATUS"], "") or "").strip().upper()
                == "SUBMITTED" else "NHAP",
                tra.tim_theo_username(nguoi_nop) if nguoi_nop else None,
                doc_thoi_diem(r.get(idx2["SUBMITTED_AT"], "")),
                doc_bool(r.get(idx2["LOCKED"], "")),
                gon(r.get(idx2["NOTE"], "")),
                doc_thoi_diem(r.get(idx2["UPDATED_AT"], "")),
            ))
            tk["đã ghi truc_ban_tru_so"] += 1

    if not args.thu:
        conn.commit()

    print("\n── Kết quả ──")
    for k in sorted(tk):
        print(f"   {tk[k]:>4}  {k}")
    if ma_la:
        print("\nMã trụ sở không có trong danh mục:")
        for v, n in ma_la.most_common():
            print(f"   ×{n:<3} {v}")
    conn.close()


if __name__ == "__main__":
    main()
