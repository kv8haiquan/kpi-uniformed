"""
scripts/fix_pl3_nhiem_vu.py
===========================
Fix dữ liệu PL3: backfill cột nhiem_vu cho 2.615 mục đang NULL do bug
parser cũ (không carry-forward nhiệm vụ từ row N.0 xuống các row N.M).

CÁCH CHẠY:
    cd backend && source venv/bin/activate

    # 1) Dry-run — chỉ in diff, KHÔNG đụng DB
    python scripts/fix_pl3_nhiem_vu.py --dry-run

    # 2) Sau khi review log → commit thật
    python scripts/fix_pl3_nhiem_vu.py --commit

AN TOÀN:
- KHÔNG xoá / insert mục mới — chỉ UPDATE cột nhiem_vu cho mục đã có
  cùng ma_danh_muc.
- Toàn bộ UPDATE chạy trong 1 transaction; rollback nếu bất kỳ row lỗi.
- Idempotent: chạy lại lần thứ 2 sẽ báo "0 rows changed".
- Bỏ qua row Excel có ma_danh_muc không tồn tại trong DB (in cảnh báo).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import create_engine, text

from app.config import settings
from app.core.pl3_excel_parser import parse_pl3_excel


EXCEL_PATH = PROJECT_ROOT.parent / "docs" / "Danh mục công việc.xlsx"


def main() -> int:
    ap = argparse.ArgumentParser(description="Fix nhiem_vu cho PL3")
    grp = ap.add_mutually_exclusive_group(required=True)
    grp.add_argument("--dry-run", action="store_true", help="Chỉ in diff, không đụng DB")
    grp.add_argument("--commit", action="store_true", help="UPDATE thật vào DB")
    ap.add_argument(
        "--sample", type=int, default=15,
        help="Số mẫu diff in ra trong dry-run (mặc định 15)",
    )
    args = ap.parse_args()

    if not EXCEL_PATH.exists():
        print(f"[ERROR] Không tìm thấy file Excel: {EXCEL_PATH}", file=sys.stderr)
        return 2

    print(f"Excel : {EXCEL_PATH}")
    print(f"DB    : {settings.db_user}@{settings.db_host}:{settings.db_port}/{settings.db_name}")
    print(f"Mode  : {'DRY-RUN (không đụng DB)' if args.dry_run else 'COMMIT (sẽ UPDATE)'}")
    print("=" * 80)

    parsed = parse_pl3_excel(str(EXCEL_PATH))
    if parsed.errors:
        print(f"[ERROR] Parser báo {len(parsed.errors)} lỗi:", file=sys.stderr)
        for e in parsed.errors[:10]:
            print(f"  row={e.row} {e.error}", file=sys.stderr)
        return 3

    # Map: ma_danh_muc → nhiem_vu (từ Excel parsed)
    excel_map: dict[str, str | None] = {r.ma_danh_muc: r.nhiem_vu for r in parsed.rows}
    total_excel = len(excel_map)
    print(f"Parsed Excel : {total_excel} mục, {sum(1 for v in excel_map.values() if v)} có nhiem_vu")

    engine = create_engine(settings.database_url_sync, echo=False)
    with engine.begin() as conn:
        # Lấy state hiện tại trong DB
        rows = conn.execute(text(
            """
            SELECT ma_danh_muc, nhiem_vu
            FROM danh_muc_sp_cong_viec
            WHERE nguon_du_lieu = 'PL3' AND is_deleted = false
            """
        )).fetchall()
        db_map: dict[str, str | None] = {r[0]: r[1] for r in rows}
        print(f"DB hiện tại  : {len(db_map)} mục PL3, "
              f"{sum(1 for v in db_map.values() if v)} có nhiem_vu, "
              f"{sum(1 for v in db_map.values() if not v)} NULL")

        # So khớp
        in_db_not_excel = set(db_map) - set(excel_map)
        in_excel_not_db = set(excel_map) - set(db_map)
        if in_excel_not_db:
            print(f"[WARN] {len(in_excel_not_db)} ma_danh_muc trong Excel không có trong DB "
                  "(seed cũ có thể đã -r{row} thêm hậu tố). Bỏ qua không UPDATE các mục này.")
        if in_db_not_excel:
            print(f"[INFO] {len(in_db_not_excel)} ma_danh_muc trong DB không thấy trong Excel "
                  "(có thể là duplicate handled khác). Giữ nguyên.")

        # Lập danh sách cần update: ma có trong cả Excel & DB, value KHÁC NHAU
        to_update: list[tuple[str, str | None, str | None]] = []
        for ma, new_nv in excel_map.items():
            if ma not in db_map:
                continue
            cur_nv = db_map[ma]
            # Chuẩn hoá so sánh: None ↔ "" coi như nhau, strip whitespace
            cur_norm = (cur_nv or "").strip()
            new_norm = (new_nv or "").strip()
            if cur_norm != new_norm:
                to_update.append((ma, cur_nv, new_nv))

        print()
        print(f"Sẽ UPDATE   : {len(to_update)} mục (Excel != DB)")
        print(f"  trong đó NULL → có giá trị: {sum(1 for _, c, _ in to_update if not c)}")
        print(f"  trong đó có → giá trị mới : {sum(1 for _, c, _ in to_update if c)}")
        print()

        if to_update:
            print(f"--- Mẫu {min(args.sample, len(to_update))} diff đầu tiên ---")
            for ma, cur, new in to_update[: args.sample]:
                print(f"  {ma}")
                print(f"    cũ : {repr(cur)[:90]}")
                print(f"    mới: {repr(new)[:90]}")

        if args.dry_run:
            print()
            print("DRY-RUN xong. Chạy lại với --commit để áp dụng.")
            # Rollback transaction (không changes)
            return 0

        # COMMIT mode
        if not to_update:
            print("Không có gì để update.")
            return 0

        print()
        print(f"Đang UPDATE {len(to_update)} mục…")
        # Bulk update qua params (1 transaction)
        conn.execute(
            text(
                """
                UPDATE danh_muc_sp_cong_viec
                SET nhiem_vu = :nv,
                    updated_at = CURRENT_TIMESTAMP
                WHERE ma_danh_muc = :ma
                  AND nguon_du_lieu = 'PL3'
                  AND is_deleted = false
                """
            ),
            [{"ma": ma, "nv": new} for ma, _, new in to_update],
        )

        # Verify sau update
        verify = conn.execute(text(
            """
            SELECT
              COUNT(*) FILTER (WHERE nhiem_vu IS NULL) AS still_null,
              COUNT(*) FILTER (WHERE nhiem_vu IS NOT NULL) AS has_nv,
              COUNT(*) AS total
            FROM danh_muc_sp_cong_viec
            WHERE nguon_du_lieu = 'PL3' AND is_deleted = false
            """
        )).first()
        print(f"Sau UPDATE  : total={verify[2]} | có nhiem_vu={verify[1]} | NULL={verify[0]}")

    print()
    print("✓ Done. Transaction đã commit.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
