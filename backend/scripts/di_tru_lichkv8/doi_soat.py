"""G3.3 — Đối soát dữ liệu trước và sau di trú.

Sinh biên bản đối chiếu mà mục V và XII của yêu cầu chuyển đổi bắt phải nộp
khi nghiệm thu. Chạy lại được bất cứ lúc nào; chạy sau G6.2 để lấy bản cuối.

Chạy:  python doi_soat.py            # in ra màn hình
       python doi_soat.py --md FILE  # ghi thêm ra file Markdown
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from doc_sheet import doc_bang
from ket_noi import ket_noi

XLSX = Path(__file__).resolve().parent / "dumps" / "lichkv8_live.xlsx"

# Chênh lệch ĐÃ BIẾT và chấp nhận được — ghi rõ để biên bản không báo động giả.
# Cả hai đều là làm sạch dữ liệu, không phải mất dữ liệu.
CHENH_LECH_BIET_TRUOC = {
    "Trạng thái nộp trực ban": (
        -2, "nguồn có 2 cặp (ngày, trụ sở) bị lặp — 20/06 CHICUC và 11/07 "
            "MONGCAI; ràng buộc UNIQUE gộp lại còn một"),
    "Ghi chú": (
        -1, "1 ghi chú của tài khoản 'superadmin' — không phải công chức thật"),
}

# (nhãn, sheet nguồn, cột khoá, lọc dòng nguồn, câu đếm bên đích)
MUC = [
    ("Cuộc họp", "MEETING", "MEETING_ID", None,
     "SELECT count(*) FROM meeting.cuoc_hop WHERE nguon='LICH_CONG_TAC'"),
    ("Trực ban (còn hiệu lực)", "DUTY_ENTRY", "DUTY_ID",
     lambda r, i: (r.get(i["STATUS"], "") or "").strip() != "Deleted",
     "SELECT count(*) FROM meeting.truc_ban"),
    ("Trạng thái nộp trực ban", "DUTY_UNIT_STATUS", "UNIT_CODE", None,
     "SELECT count(*) FROM meeting.truc_ban_tru_so"),
    ("Ghi chú", "MEETING_NOTE", "NOTE_ID", None,
     "SELECT count(*) FROM meeting.ghi_chu"),
    ("Chia sẻ ghi chú", "NOTE_SHARE", "SHARE_ID", None,
     "SELECT count(*) FROM meeting.ghi_chu_chia_se"),
]

KIEM_TRA_THEM = [
    ("Lãnh đạo liên quan (bản ghi)",
     "SELECT count(*) FROM meeting.lanh_dao_lien_quan"),
    ("Cuộc họp có lãnh đạo liên quan",
     "SELECT count(DISTINCT cuoc_hop_id) FROM meeting.lanh_dao_lien_quan"),
    ("Đánh giá cuộc họp",
     "SELECT count(*) FROM meeting.danh_gia_cuoc_hop"),
    ("Cuộc họp khớp được chủ trì",
     "SELECT count(*) FROM meeting.cuoc_hop "
     "WHERE nguon='LICH_CONG_TAC' AND chu_toa_id IS NOT NULL"),
    ("Cuộc họp giữ nguyên văn chủ trì",
     "SELECT count(*) FROM meeting.cuoc_hop "
     "WHERE nguon='LICH_CONG_TAC' AND chu_tri_text IS NOT NULL"),
    ("Sự kiện nhiều ngày",
     "SELECT count(*) FROM meeting.cuoc_hop "
     "WHERE nguon='LICH_CONG_TAC' AND ngay_ket_thuc IS NOT NULL"),
    ("Mã lịch bị trùng (phải = 0)",
     "SELECT count(*) FROM (SELECT ma_lich FROM meeting.cuoc_hop "
     "WHERE ma_lich IS NOT NULL GROUP BY 1 HAVING count(*) > 1) x"),
    ("Cuộc họp thiếu ngày hiển thị (phải = 0)",
     "SELECT count(*) FROM meeting.cuoc_hop WHERE ngay_hien_thi IS NULL"),
    ("Trực ban thiếu số điện thoại",
     "SELECT count(*) FROM meeting.truc_ban WHERE so_dien_thoai IS NULL"),
    ("Cuộc họp HKG (không được đụng tới)",
     "SELECT count(*) FROM meeting.cuoc_hop WHERE nguon='HKG'"),
]

# G3.2 — đối soát kho tài liệu. Chỉ chạy khi đã có manifest tải file.
KIEM_TRA_FILE = [
    ("Tài liệu di trú từ Drive",
     "SELECT count(*) FROM meeting.di_tru_nguon WHERE bang_nguon='DRIVE_FILE'"),
    ("Tài liệu sẵn có của HKG (không đụng)",
     "SELECT count(*) FROM meeting.tai_lieu tl JOIN meeting.cuoc_hop ch "
     "ON ch.id = tl.cuoc_hop_id WHERE ch.nguon = 'HKG'"),
    ("Cuộc họp có tài liệu",
     "SELECT count(DISTINCT cuoc_hop_id) FROM meeting.tai_lieu "
     "WHERE cuoc_hop_id IS NOT NULL"),
    ("Tổng dung lượng đã gắn (MB)",
     "SELECT COALESCE(round(sum(file_size)/1048576.0, 1), 0) "
     "FROM meeting.tai_lieu"),
    ("Thư mục chờ đối soát (nhóm D)",
     "SELECT count(*) FROM meeting.di_tru_doi_soat WHERE nhom='D'"),
    ("Thư mục chờ đối soát (nhóm E)",
     "SELECT count(*) FROM meeting.di_tru_doi_soat WHERE nhom='E'"),
    ("File chờ đối soát",
     "SELECT COALESCE(sum(so_file), 0) FROM meeting.di_tru_doi_soat "
     "WHERE quyet_dinh IS NULL"),
    ("Tài liệu trùng khoá lưu trữ (phải = 0)",
     "SELECT count(*) FROM (SELECT minio_key FROM meeting.tai_lieu "
     "GROUP BY 1 HAVING count(*) > 1) x"),
]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--md", type=Path, help="ghi biên bản ra file Markdown")
    args = ap.parse_args()

    conn = ket_noi()
    dong: list[str] = []

    def ra(s: str = "") -> None:
        print(s)
        dong.append(s)

    ra("# Biên bản đối chiếu di trú lichkv8")
    ra()
    ra("## Đối chiếu số lượng bản ghi")
    ra()
    ra("| Nhóm dữ liệu | Nguồn | Đích | Chênh | Ghi chú |")
    ra("|---|---:|---:|---:|---|")

    tat_ca_khop = True
    giai_thich: list[str] = []
    with conn.cursor() as cur:
        for nhan, sheet, khoa, loc, sql in MUC:
            idx, rows = doc_bang(XLSX, sheet, khoa)
            n_nguon = sum(1 for r in rows if (loc is None or loc(r, idx)))
            cur.execute(sql)
            n_dich = cur.fetchone()[0]
            lech = n_dich - n_nguon
            biet_truoc = CHENH_LECH_BIET_TRUOC.get(nhan)
            if lech == 0:
                dau, ghi = "✅", ""
            elif biet_truoc and lech == biet_truoc[0]:
                dau, ghi = f"✅ {lech:+d}", biet_truoc[1]
            else:
                dau, ghi = f"⚠️ {lech:+d}", "**chênh lệch ngoài dự kiến**"
                tat_ca_khop = False
            ra(f"| {nhan} | {n_nguon} | {n_dich} | {dau} | {ghi} |")

        ra()
        ra("## Kiểm tra chất lượng")
        ra()
        ra("| Chỉ tiêu | Giá trị |")
        ra("|---|---:|")
        for nhan, sql in KIEM_TRA_THEM:
            cur.execute(sql)
            ra(f"| {nhan} | {cur.fetchone()[0]} |")

        # Đối chiếu thứ trong tuần — bắt lỗi lệch ngày, xem 01_cuoc_hop.py
        # ── kho tài liệu ────────────────────────────────────────────
        cur.execute("SELECT count(*) FROM meeting.tai_lieu")
        if cur.fetchone()[0]:
            ra()
            ra("## Kho tài liệu")
            ra()
            ra("| Chỉ tiêu | Giá trị |")
            ra("|---|---:|")
            for nhan, sql in KIEM_TRA_FILE:
                cur.execute(sql)
                ra(f"| {nhan} | {cur.fetchone()[0]} |")

            manifest = XLSX.parent / "drive_files_manifest.json"
            if manifest.exists():
                import json as _json
                # CHỈ so kho tài liệu họp. 23 file kho thư viện thuộc portal
                # (quyết định 17/08), xử lý riêng ở G5.1 — không tính vào đây.
                m = {k: v for k, v in
                     _json.loads(manifest.read_text(encoding="utf8")).items()
                     if v.get("kho") == "tai-lieu"}
                cur.execute("SELECT count(*) FROM meeting.di_tru_nguon "
                            "WHERE bang_nguon = 'DRIVE_FILE'")
                da_gan = cur.fetchone()[0]
                cur.execute("SELECT COALESCE(sum(so_file),0) "
                            "FROM meeting.di_tru_doi_soat")
                cho = cur.fetchone()[0]
                ra()
                ra(f"File kho tài liệu họp tải về: **{len(m)}** · đã gắn cuộc họp: "
                   f"**{da_gan}** · chờ đối soát: **{cho}** · "
                   f"tổng đã xử lý: **{da_gan + cho}**")
                if da_gan + cho != len(m):
                    ra()
                    ra(f"> ⚠️ Lệch {len(m) - da_gan - cho} file so với manifest "
                       f"— cần rà lại trước khi nghiệm thu.")

        ra()
        ra("## Đối chiếu thứ trong tuần")
        ra()
        THU = {0: "Thứ Hai", 1: "Thứ Ba", 2: "Thứ Tư", 3: "Thứ Năm",
               4: "Thứ Sáu", 5: "Thứ Bảy", 6: "Chủ Nhật"}

        def chuan(s: str) -> str:
            return (s or "").strip().lower().replace(
                "chủ nhật", "cn").replace("thứ ", "t")

        idx, rows = doc_bang(XLSX, "MEETING", "MEETING_ID")
        goc = {(r.get(idx["MEETING_ID"], "") or "").strip():
               (r.get(idx["THU"], "") or "").strip() for r in rows}
        cur.execute("SELECT ma_lich, ngay_hop FROM meeting.cuoc_hop "
                    "WHERE nguon='LICH_CONG_TAC'")
        khop = lech = 0
        for ma, ng in cur.fetchall():
            t = goc.get(ma, "")
            if not t:
                continue
            if chuan(THU[ng.weekday()]) == chuan(t):
                khop += 1
            else:
                lech += 1
        if lech:
            tat_ca_khop = False
        ra(f"Ngày sau di trú khớp cột `THU` của bản gốc: **{khop} khớp, "
           f"{lech} lệch**.")
        ra()
        ra("> Cột serial `NGAY_BAT_DAU` của lichkv8 lệch sớm 1 ngày ở 212/489 "
           "dòng. Di trú lấy `NGAY_HIEN_THI` làm chuẩn vì cột `THU` xác nhận "
           "đó mới là ngày đúng.")

    ra()
    ra("**Kết luận:** " + ("✅ Toàn bộ khớp." if tat_ca_khop
                          else "⚠️ Có chênh lệch, xem bảng trên."))

    if args.md:
        args.md.write_text("\n".join(dong) + "\n", encoding="utf8")
        print(f"\n→ Đã ghi {args.md}")
    conn.close()


if __name__ == "__main__":
    main()
