"""
scripts/backfill_pl3_cong_tac.py
================================
Backfill 2 cột mới cong_tac + cong_tac_thu_tu cho 2.812 mục PL3 đã seed.

Đọc lại file Excel `docs/Danh mục công việc.xlsx`, parser tự detect
heading "Công tác" (bold cột A không số + cột B variant) và gắn vào mỗi
ParsedRow. Script chỉ UPDATE 2 cột mới — không xoá / insert mục.

CÁCH CHẠY:
    cd backend && source venv/bin/activate

    # 1) Dry-run — chỉ in diff, KHÔNG đụng DB
    python scripts/backfill_pl3_cong_tac.py --dry-run

    # 2) Sau khi review log → commit thật
    python scripts/backfill_pl3_cong_tac.py --commit

AN TOÀN:
- KHÔNG xoá / insert — chỉ UPDATE 2 cột (cong_tac, cong_tac_thu_tu).
- 1 transaction; rollback nếu lỗi.
- Idempotent: chạy lại lần 2 báo "0 rows changed".
- Bỏ qua ma_danh_muc trong Excel nhưng không có trong DB (in cảnh báo).
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
    ap = argparse.ArgumentParser(description="Backfill cong_tac cho PL3")
    grp = ap.add_mutually_exclusive_group(required=True)
    grp.add_argument("--dry-run", action="store_true", help="Chỉ in diff")
    grp.add_argument("--commit", action="store_true", help="UPDATE thật")
    ap.add_argument(
        "--sample", type=int, default=15,
        help="Số diff mẫu in trong dry-run (mặc định 15)",
    )
    args = ap.parse_args()

    if not EXCEL_PATH.exists():
        print(f"[ERROR] Không tìm thấy file Excel: {EXCEL_PATH}", file=sys.stderr)
        return 2

    print(f"Excel : {EXCEL_PATH}")
    print(f"DB    : {settings.db_user}@{settings.db_host}:{settings.db_port}/{settings.db_name}")
    print(f"Mode  : {'DRY-RUN' if args.dry_run else 'COMMIT'}")
    print("=" * 80)

    parsed = parse_pl3_excel(str(EXCEL_PATH))
    if parsed.errors:
        print(f"[ERROR] Parser báo {len(parsed.errors)} lỗi:", file=sys.stderr)
        for e in parsed.errors[:10]:
            print(f"  row={e.row} {e.error}", file=sys.stderr)
        return 3

    # Map: ma_danh_muc → (cong_tac, cong_tac_thu_tu)
    excel_map: dict[str, tuple[str | None, int | None]] = {
        r.ma_danh_muc: (r.cong_tac, r.cong_tac_thu_tu) for r in parsed.rows
    }
    total_excel = len(excel_map)
    has_ct = sum(1 for v in excel_map.values() if v[0])
    print(f"Parsed Excel : {total_excel} mục, {has_ct} có cong_tac")

    engine = create_engine(settings.database_url_sync, echo=False)
    with engine.begin() as conn:
        rows = conn.execute(text(
            """
            SELECT ma_danh_muc, cong_tac, cong_tac_thu_tu
            FROM danh_muc_sp_cong_viec
            WHERE nguon_du_lieu = 'PL3' AND is_deleted = false
            """
        )).fetchall()
        db_map: dict[str, tuple[str | None, int | None]] = {
            r[0]: (r[1], r[2]) for r in rows
        }
        print(f"DB hiện tại  : {len(db_map)} mục PL3, "
              f"{sum(1 for v in db_map.values() if v[0])} có cong_tac")

        in_excel_not_db = set(excel_map) - set(db_map)
        if in_excel_not_db:
            print(f"[WARN] {len(in_excel_not_db)} ma_danh_muc Excel không có trong DB. "
                  "Bỏ qua.")

        # Lập danh sách cần update
        def norm(t: tuple[str | None, int | None]) -> tuple[str, int]:
            ct = (t[0] or "").strip()
            tt = t[1] if t[1] is not None else 0
            return (ct, tt)

        to_update: list[tuple[str, tuple, tuple]] = []
        for ma, new_val in excel_map.items():
            if ma not in db_map:
                continue
            cur_val = db_map[ma]
            if norm(cur_val) != norm(new_val):
                to_update.append((ma, cur_val, new_val))

        print()
        print(f"Sẽ UPDATE   : {len(to_update)} mục")
        print(f"  NULL → có giá trị : {sum(1 for _, c, _ in to_update if not c[0])}")
        print(f"  có   → giá trị mới: {sum(1 for _, c, _ in to_update if c[0])}")
        print()

        if to_update:
            print(f"--- Mẫu {min(args.sample, len(to_update))} diff đầu tiên ---")
            for ma, cur, new in to_update[: args.sample]:
                print(f"  {ma}")
                print(f"    cũ : ct={cur[0]!r:60} thu_tu={cur[1]}")
                print(f"    mới: ct={new[0]!r:60} thu_tu={new[1]}")

        if args.dry_run:
            print()
            print("DRY-RUN xong. Chạy lại với --commit để áp dụng.")
            return 0

        if not to_update:
            print("Không có gì để update.")
            return 0

        print()
        print(f"Đang UPDATE {len(to_update)} mục…")
        conn.execute(
            text(
                """
                UPDATE danh_muc_sp_cong_viec
                SET cong_tac = :ct,
                    cong_tac_thu_tu = :tt,
                    updated_at = CURRENT_TIMESTAMP
                WHERE ma_danh_muc = :ma
                  AND nguon_du_lieu = 'PL3'
                  AND is_deleted = false
                """
            ),
            [
                {"ma": ma, "ct": new[0], "tt": new[1]}
                for ma, _, new in to_update
            ],
        )

        verify = conn.execute(text(
            """
            SELECT
              COUNT(*) FILTER (WHERE cong_tac IS NULL) AS null_ct,
              COUNT(*) FILTER (WHERE cong_tac IS NOT NULL) AS has_ct,
              COUNT(DISTINCT (linh_vuc, cong_tac))
                FILTER (WHERE cong_tac IS NOT NULL) AS distinct_ct,
              COUNT(*) AS total
            FROM danh_muc_sp_cong_viec
            WHERE nguon_du_lieu = 'PL3' AND is_deleted = false
            """
        )).first()
        print(f"Sau UPDATE  : total={verify[3]} | có cong_tac={verify[1]} | NULL={verify[0]}")
        print(f"Distinct (linh_vuc, cong_tac): {verify[2]}")

    print()
    print("✓ Done. Transaction đã commit.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
