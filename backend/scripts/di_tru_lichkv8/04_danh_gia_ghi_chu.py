"""G3.1 — Di trú đánh giá cuộc họp và ghi chú.

    MEETING_RATING → meeting.danh_gia_cuoc_hop   (105 bản ghi)
    MEETING_NOTE   → meeting.ghi_chu             (7 bản ghi, 3 còn hiệu lực)
    NOTE_SHARE     → meeting.ghi_chu_chia_se     (0 bản ghi)

Khối lượng rất nhỏ nhưng vẫn di trú vì quyết định 17/08/2026 là giữ cả hai
nghiệp vụ. Điểm đánh giá gần như vô nghĩa về mặt thống kê (102/105 chấm 5 sao)
nhưng vẫn phải chuyển để giữ liên kết người–cuộc họp–đánh giá.

Ghi chú của lichkv8 lưu nội dung dài thành file Drive riêng (CONTENT_FILE_ID)
để tránh vượt giới hạn kích thước ô Sheets. Trên PostgreSQL không còn giới hạn
đó nên nội dung vào thẳng cột TEXT; nếu bản ghi chỉ có file thì giữ lại đường
dẫn trong nội dung để G3.2 xử lý cùng đợt tải file.

Chạy:  python 04_danh_gia_ghi_chu.py [--thu]
"""

from __future__ import annotations

import argparse
import collections
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from chuyen_doi import doc_bool, doc_thoi_diem, gon
from doc_sheet import doc_bang
from ket_noi import BangTraCongChuc, ghi_nguon, ket_noi

XLSX = Path(__file__).resolve().parent / "dumps" / "lichkv8_live.xlsx"


def lay(r: dict, idx: dict, *ten_cot: str) -> str | None:
    """Lấy giá trị theo cột đầu tiên tồn tại — tên cột lichkv8 không đồng nhất."""
    for c in ten_cot:
        if c in idx:
            v = gon(r.get(idx[c], ""))
            if v:
                return v
    return None


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--thu", action="store_true", help="chỉ thống kê, không ghi")
    args = ap.parse_args()

    conn = ket_noi()
    tra = BangTraCongChuc(conn)
    tra.nap_username(XLSX)
    tk = collections.Counter()

    with conn.cursor() as cur:
        cur.execute(
            "SELECT ma_lich, id FROM meeting.cuoc_hop "
            "WHERE nguon = 'LICH_CONG_TAC' AND ma_lich IS NOT NULL")
        id_theo_ma = dict(cur.fetchall())

    # ── đánh giá ─────────────────────────────────────────────────────────
    idx, rows = doc_bang(XLSX, "MEETING_RATING", "RATING_ID")
    print(f"MEETING_RATING: {len(rows)} dòng", flush=True)
    with conn.cursor() as cur:
        for r in rows:
            ch = id_theo_ma.get((r.get(idx["MEETING_ID"], "") or "").strip())
            nguoi = lay(r, idx, "OWNER_USERNAME")
            cc_id = tra.tim_theo_username(nguoi) if nguoi else None
            if not cc_id and (ho_ten := lay(r, idx, "OWNER_FULLNAME")):
                cc_id = tra.tim(ho_ten)
            try:
                diem = int(float(r.get(idx["SCORE"], "") or 0))
            except ValueError:
                diem = 0

            if not (ch and cc_id and 1 <= diem <= 5):
                tk["đánh giá: bỏ qua"] += 1
                continue
            tk["đánh giá: hợp lệ"] += 1
            if args.thu:
                continue
            cur.execute("""
                INSERT INTO meeting.danh_gia_cuoc_hop
                    (cuoc_hop_id, cong_chuc_id, diem, ghi_chu, created_at, updated_at)
                VALUES (%s,%s,%s,%s, COALESCE(%s,NOW()), COALESCE(%s,NOW()))
                ON CONFLICT (cuoc_hop_id, cong_chuc_id) DO UPDATE
                    SET diem = EXCLUDED.diem, ghi_chu = EXCLUDED.ghi_chu
                RETURNING id
            """, (ch, cc_id, diem, lay(r, idx, "GHI_CHU"),
                  doc_thoi_diem(r.get(idx.get("CREATED_AT", "ZZ"), "")),
                  doc_thoi_diem(r.get(idx.get("UPDATED_AT", "ZZ"), ""))))
            ghi_nguon(cur, "MEETING_RATING",
                      (r.get(idx["RATING_ID"], "") or "").strip(),
                      "meeting.danh_gia_cuoc_hop", cur.fetchone()[0])
            tk["đánh giá: đã ghi"] += 1

    # ── ghi chú ──────────────────────────────────────────────────────────
    idx, rows = doc_bang(XLSX, "MEETING_NOTE", "NOTE_ID")
    print(f"MEETING_NOTE: {len(rows)} dòng", flush=True)
    id_ghi_chu: dict[str, str] = {}
    with conn.cursor() as cur:
        for r in rows:
            note_id = (r.get(idx["NOTE_ID"], "") or "").strip()
            nguoi = lay(r, idx, "OWNER_USERNAME")
            cc_id = tra.tim_theo_username(nguoi) if nguoi else None
            if not cc_id and (ho_ten := lay(r, idx, "OWNER_FULLNAME")):
                cc_id = tra.tim(ho_ten)
            if not cc_id:
                tk["ghi chú: bỏ qua (không rõ người tạo)"] += 1
                continue

            noi_dung = lay(r, idx, "CONTENT", "CONTENT_PREVIEW")
            if not noi_dung and (url := lay(r, idx, "CONTENT_FILE_URL")):
                # Nội dung nằm ở file Drive riêng — giữ link cho G3.2 xử lý.
                noi_dung = f"[Nội dung lưu ở file Drive] {url}"
                tk["ghi chú: nội dung ở file Drive"] += 1

            da_xoa = ((r.get(idx["STATUS"], "") or "").strip() == "Deleted")
            tk["ghi chú: đã xoá" if da_xoa else "ghi chú: còn hiệu lực"] += 1
            if args.thu:
                continue
            cur.execute("""
                INSERT INTO meeting.ghi_chu
                    (cuoc_hop_id, tieu_de, noi_dung, cong_chuc_id, is_ghim,
                     created_at, updated_at, is_deleted)
                VALUES (%s,%s,%s,%s,%s, COALESCE(%s,NOW()), COALESCE(%s,NOW()), %s)
                RETURNING id
            """, (
                id_theo_ma.get((r.get(idx["MEETING_ID"], "") or "").strip()),
                (lay(r, idx, "TITLE") or "(không tiêu đề)")[:300],
                noi_dung, cc_id, doc_bool(r.get(idx.get("IS_PINNED", "ZZ"), "")),
                doc_thoi_diem(r.get(idx.get("CREATED_AT", "ZZ"), "")),
                doc_thoi_diem(r.get(idx.get("UPDATED_AT", "ZZ"), "")),
                da_xoa,
            ))
            gc_id = cur.fetchone()[0]
            id_ghi_chu[note_id] = gc_id
            ghi_nguon(cur, "MEETING_NOTE", note_id, "meeting.ghi_chu", gc_id)
            tk["ghi chú: đã ghi"] += 1

    # ── chia sẻ ghi chú ──────────────────────────────────────────────────
    idx, rows = doc_bang(XLSX, "NOTE_SHARE", "SHARE_ID")
    print(f"NOTE_SHARE: {len(rows)} dòng", flush=True)
    with conn.cursor() as cur:
        for r in rows:
            gc = id_ghi_chu.get((r.get(idx["NOTE_ID"], "") or "").strip())
            gui = tra.tim_theo_username(lay(r, idx, "FROM_USERNAME") or "")
            nhan = tra.tim_theo_username(lay(r, idx, "TO_USERNAME") or "")
            if not (gc and gui and nhan and gui != nhan):
                tk["chia sẻ: bỏ qua"] += 1
                continue
            tk["chia sẻ: hợp lệ"] += 1
            if args.thu:
                continue
            cur.execute("""
                INSERT INTO meeting.ghi_chu_chia_se
                    (ghi_chu_id, nguoi_gui_id, nguoi_nhan_id, loi_nhan, da_doc)
                VALUES (%s,%s,%s,%s,%s)
                ON CONFLICT (ghi_chu_id, nguoi_nhan_id) DO NOTHING
            """, (gc, gui, nhan, lay(r, idx, "MESSAGE"),
                  doc_bool(r.get(idx.get("IS_READ", "ZZ"), ""))))
            tk["chia sẻ: đã ghi"] += 1

    if not args.thu:
        conn.commit()

    print("\n── Kết quả ──")
    for k in sorted(tk):
        print(f"   {tk[k]:>4}  {k}")
    conn.close()


if __name__ == "__main__":
    main()
