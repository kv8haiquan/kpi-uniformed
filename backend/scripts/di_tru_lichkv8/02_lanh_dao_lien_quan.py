"""G3.1 — Di trú lãnh đạo liên quan sang meeting.lanh_dao_lien_quan.

Nguồn: cột LANH_DAO_LIEN_QUAN của sheet MEETING (văn bản tự do, phân cách ';').
Đây là trục của ba chức năng: Lịch lãnh đạo, Dashboard theo lãnh đạo, Tóm tắt
lịch — nên phải chuẩn hoá sạch, không để dạng text.

Khảo sát G1: 480/480 token khớp public.cong_chuc.ho_ten (100%), khác hẳn
CHU_TRI chỉ khớp 91%. Vì vậy bảng này dùng khoá ngoại thật, không cần cột text
dự phòng — token nào không khớp thì vẫn lưu `ten_goc` để truy vết.

KHÔNG dùng sheet MEETING_PARTICIPANT: cả 294 dòng của nó đều mang
ROLE_IN_MEETING='LANH_DAO_LIEN_QUAN', tức chỉ là chỉ mục sinh tự động từ chính
cột này, không phải danh sách người dự do ai nhập.

Chạy:  python 02_lanh_dao_lien_quan.py [--thu]
"""

from __future__ import annotations

import argparse
import collections
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from chuyen_doi import tach_danh_sach
from doc_sheet import doc_bang
from ket_noi import BangTraCongChuc, ket_noi

XLSX = Path(__file__).resolve().parent / "dumps" / "lichkv8_live.xlsx"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--thu", action="store_true", help="chỉ thống kê, không ghi")
    args = ap.parse_args()

    idx, rows = doc_bang(XLSX, "MEETING", "MEETING_ID")
    conn = ket_noi()
    tra = BangTraCongChuc(conn)

    tk = collections.Counter()
    khong_khop: collections.Counter = collections.Counter()

    with conn.cursor() as cur:
        cur.execute(
            "SELECT ma_lich, id FROM meeting.cuoc_hop "
            "WHERE nguon = 'LICH_CONG_TAC' AND ma_lich IS NOT NULL")
        id_theo_ma = dict(cur.fetchall())
        print(f"Cuộc họp đã di trú: {len(id_theo_ma)}\n", flush=True)

        for r in rows:
            ma_lich = (r.get(idx["MEETING_ID"], "") or "").strip()
            cuoc_hop_id = id_theo_ma.get(ma_lich)
            if not cuoc_hop_id:
                tk["bỏ qua (cuộc họp chưa di trú)"] += 1
                continue

            tokens = tach_danh_sach(r.get(idx["LANH_DAO_LIEN_QUAN"], ""))
            if not tokens:
                tk["cuộc họp không có lãnh đạo liên quan"] += 1
                continue
            tk["cuộc họp có lãnh đạo liên quan"] += 1

            da_them: set = set()
            for thu_tu, token in enumerate(tokens, start=1):
                cc_id = tra.tim(token)
                if not cc_id:
                    khong_khop[token[:40]] += 1
                    tk["token không khớp"] += 1
                    continue
                if cc_id in da_them:
                    tk["token trùng trong cùng cuộc họp"] += 1
                    continue
                da_them.add(cc_id)
                tk["token khớp"] += 1

                if args.thu:
                    continue
                cur.execute("""
                    INSERT INTO meeting.lanh_dao_lien_quan
                        (cuoc_hop_id, cong_chuc_id, thu_tu, ten_goc)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (cuoc_hop_id, cong_chuc_id) DO UPDATE
                        SET thu_tu = EXCLUDED.thu_tu, ten_goc = EXCLUDED.ten_goc
                """, (cuoc_hop_id, cc_id, thu_tu, token[:200]))
                tk["đã ghi"] += 1

    if not args.thu:
        conn.commit()

    print("── Kết quả ──")
    for k in sorted(tk):
        print(f"   {tk[k]:>4}  {k}")
    if khong_khop:
        print(f"\nToken không khớp: {sum(khong_khop.values())} lượt")
        for v, n in khong_khop.most_common(10):
            print(f"   ×{n:<3} {v}")
    conn.close()


if __name__ == "__main__":
    main()
