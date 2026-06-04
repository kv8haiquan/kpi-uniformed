#!/usr/bin/env python3
"""
scripts/backfill_bulk_ane_diem_2026_05_15.py
============================================
Backfill các đơn bị bulk approve cấp 1/cấp 2 ăn điểm thập phân từ ngày
11–15/05/2026, do bug trong endpoint `phe_duyet_tieu_chi_bulk` dùng
`_diem_pd_tu_ld` (binary) thay vì `_apply_dieu_chinh_ld` (preserve điểm).

Bug đã fix trong commit cùng ngày 15/05/2026. Script này khôi phục lại
điểm bị ăn cho 23 TC trên 15 công chức, tháng 4/2026.

CÁCH CHẠY:
    cd backend && source venv/bin/activate

    # 1) Dry-run — chỉ in diff, KHÔNG đụng DB
    python scripts/backfill_bulk_ane_diem_2026_05_15.py --dry-run

    # 2) Sau khi review → commit thật
    python scripts/backfill_bulk_ane_diem_2026_05_15.py --commit

AN TOÀN:
- 1 transaction; rollback nếu bất kỳ lỗi nào.
- Idempotent: chạy lại lần 2 báo "0 rows changed".
- Chỉ UPDATE diem_phe_duyet (TC) + diem_tc_cap1/cap2/diem_tieu_chi_chung (DGT).
- KHÔNG đụng: diem_tu_cham, is_achieved_*, snapshot [PDV:N], approver IDs,
  timestamps phê duyệt, xếp loại.
"""

from __future__ import annotations

import argparse
import re
import sys
from decimal import Decimal
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import create_engine, text

from app.config import settings


PDV_SNAPSHOT_REGEX = re.compile(r"^\[PDV:([\d.]+)\]")

# 11 công chức bị ảnh hưởng — chốt scope, tránh side-effect ngoài
# LOẠI: 4 case Văn phòng (0019, 0031, 0177, 0561) — ly_do có "| ĐT: ..." là
# ĐT cố ý điều chỉnh xuống 0, KHÔNG phải bug bulk.
AFFECTED_CCS = (
    # Type 1 — HQCK Hòn Gai (cấp 1 ăn, không snapshot)
    "20ZZ-0143", "20ZZ-0175", "20ZZ-0201", "20ZZ-0360", "20ZZ-0392", "20ZZ-0501",
    # Type 2 — Hòn Gai (cấp 2 ăn, có snapshot)
    "20ZZ-0265",
    # Type 2 — Phòng TCCB
    "20ZZ-0211", "20ZZ-0312", "20ZZ-0321", "20ZZ-0322",
)


def find_type2_records(conn):
    """Type 2: TC có [PDV:N>0] snapshot nhưng diem_phe_duyet=0."""
    sql = text("""
        SELECT
            tccdg.id AS tc_id,
            tccdg.danh_gia_thang_id,
            cc.ma_cc, dv.ten_don_vi,
            dgt.thang, dgt.nam, tcc.ma_tieu_chi,
            tccdg.diem_tu_cham, tccdg.diem_phe_duyet,
            tccdg.ly_do_dieu_chinh
        FROM tieu_chi_chung_danh_gia tccdg
        JOIN danh_gia_thang dgt ON dgt.id = tccdg.danh_gia_thang_id
        JOIN cong_chuc cc ON cc.id = dgt.cong_chuc_id
        JOIN don_vi dv ON dv.id = cc.don_vi_id
        JOIN tieu_chi_chung tcc ON tcc.id = tccdg.tieu_chi_id
        WHERE dgt.is_deleted = false
          AND cc.ma_cc = ANY(:ma_cc_list)
          AND dgt.thang = 4 AND dgt.nam = 2026
          AND tccdg.ly_do_dieu_chinh ~ '^\\[PDV:[0-9.]+\\]'
          AND tccdg.ly_do_dieu_chinh NOT LIKE '%| ĐT:%'
          AND tccdg.diem_phe_duyet = 0
        ORDER BY cc.ma_cc, tcc.ma_tieu_chi
    """)
    rows = conn.execute(sql, {"ma_cc_list": list(AFFECTED_CCS)}).mappings().all()
    result = []
    for row in rows:
        m = PDV_SNAPSHOT_REGEX.match(row["ly_do_dieu_chinh"] or "")
        if not m:
            continue
        pdv_diem = Decimal(m.group(1))
        if pdv_diem <= 0:
            continue
        result.append({**dict(row), "diem_moi": pdv_diem})
    return result


def find_type1_records(conn):
    """Type 1: TC không có snapshot, CC chấm thập phân nhưng diem_phe_duyet=0."""
    sql = text("""
        SELECT
            tccdg.id AS tc_id,
            tccdg.danh_gia_thang_id,
            cc.ma_cc, dv.ten_don_vi,
            dgt.thang, dgt.nam, tcc.ma_tieu_chi,
            tccdg.diem_tu_cham, tccdg.diem_phe_duyet,
            tccdg.ly_do_dieu_chinh
        FROM tieu_chi_chung_danh_gia tccdg
        JOIN danh_gia_thang dgt ON dgt.id = tccdg.danh_gia_thang_id
        JOIN cong_chuc cc ON cc.id = dgt.cong_chuc_id
        JOIN don_vi dv ON dv.id = cc.don_vi_id
        JOIN tieu_chi_chung tcc ON tcc.id = tccdg.tieu_chi_id
        WHERE dgt.is_deleted = false
          AND cc.ma_cc = ANY(:ma_cc_list)
          AND dgt.thang = 4 AND dgt.nam = 2026
          AND tccdg.diem_tu_cham > 0
          AND tccdg.diem_phe_duyet = 0
          AND tccdg.is_achieved_cc = false
          AND (tccdg.ly_do_dieu_chinh IS NULL OR tccdg.ly_do_dieu_chinh NOT LIKE '[PDV:%')
          AND dgt.trang_thai_tc IN ('DA_PHE_DUYET','CHO_CAP2')
        ORDER BY cc.ma_cc, tcc.ma_tieu_chi
    """)
    rows = conn.execute(sql, {"ma_cc_list": list(AFFECTED_CCS)}).mappings().all()
    return [{**dict(row), "diem_moi": row["diem_tu_cham"]} for row in rows]


def update_tc(conn, tc_id, diem_moi):
    conn.execute(
        text("UPDATE tieu_chi_chung_danh_gia SET diem_phe_duyet = :diem WHERE id = :id"),
        {"diem": diem_moi, "id": tc_id},
    )


def recompute_dgt_aggregate(conn, dgt_id, is_type1):
    """Sau khi update TC, tính lại điểm tổng cho DanhGiaThang.

    Type 1 (cấp 1 bị ăn): cả diem_tc_cap1 và diem_tc_cap2 đều phải update.
    Type 2 (cấp 2 bị ăn): chỉ diem_tc_cap2 + diem_tieu_chi_chung.
    """
    new_total = conn.execute(
        text("""
            SELECT COALESCE(SUM(diem_phe_duyet), 0)
            FROM tieu_chi_chung_danh_gia
            WHERE danh_gia_thang_id = :id
        """),
        {"id": dgt_id},
    ).scalar()

    if is_type1:
        conn.execute(
            text("""
                UPDATE danh_gia_thang
                SET diem_tc_cap1 = :diem,
                    diem_tc_cap2 = :diem,
                    diem_tieu_chi_chung = :diem
                WHERE id = :id
            """),
            {"diem": new_total, "id": dgt_id},
        )
    else:
        conn.execute(
            text("""
                UPDATE danh_gia_thang
                SET diem_tc_cap2 = :diem,
                    diem_tieu_chi_chung = :diem
                WHERE id = :id
            """),
            {"diem": new_total, "id": dgt_id},
        )
    return new_total


def print_plan(type1, type2):
    print("=" * 100)
    print("BACKFILL PLAN — bulk approve ăn điểm thập phân (11-15/05/2026)")
    print("=" * 100)

    print(f"\n📌 TYPE 2: Cấp 2 bulk ăn điểm (CÓ snapshot [PDV:N]) — {len(type2)} TC")
    print("-" * 100)
    print(f"{'ma_cc':<12} {'đơn vị':<22} {'T/N':<8} {'TC':<6} {'CC chấm':>8} {'PD cũ':>8} {'PD mới':>8} {'+ điểm':>8}")
    print("-" * 100)
    sum_type2 = Decimal("0")
    for r in type2:
        delta = r["diem_moi"] - r["diem_phe_duyet"]
        sum_type2 += delta
        print(f"{r['ma_cc']:<12} {r['ten_don_vi'][:22]:<22} "
              f"{r['thang']}/{r['nam']:<6} {r['ma_tieu_chi']:<6} "
              f"{float(r['diem_tu_cham']):>8.2f} {float(r['diem_phe_duyet']):>8.2f} "
              f"{float(r['diem_moi']):>8.2f} {float(delta):>+8.2f}")
    print(f"\n  → Tổng cộng Type 2: +{sum_type2:.2f} điểm trên {len(type2)} TC")

    print(f"\n📌 TYPE 1: Cấp 1 bulk ăn điểm (KHÔNG có snapshot, dùng diem_tu_cham) — {len(type1)} TC")
    print("-" * 100)
    print(f"{'ma_cc':<12} {'đơn vị':<22} {'T/N':<8} {'TC':<6} {'CC chấm':>8} {'PD cũ':>8} {'PD mới':>8} {'+ điểm':>8}")
    print("-" * 100)
    sum_type1 = Decimal("0")
    for r in type1:
        delta = r["diem_moi"] - r["diem_phe_duyet"]
        sum_type1 += delta
        print(f"{r['ma_cc']:<12} {r['ten_don_vi'][:22]:<22} "
              f"{r['thang']}/{r['nam']:<6} {r['ma_tieu_chi']:<6} "
              f"{float(r['diem_tu_cham']):>8.2f} {float(r['diem_phe_duyet']):>8.2f} "
              f"{float(r['diem_moi']):>8.2f} {float(delta):>+8.2f}")
    print(f"\n  → Tổng cộng Type 1: +{sum_type1:.2f} điểm trên {len(type1)} TC")

    print("\n" + "=" * 100)
    print(f"TỔNG: +{sum_type1 + sum_type2:.2f} điểm trên {len(type1) + len(type2)} TC")
    print(f"      Số đơn vị DGT bị ảnh hưởng: {len({r['danh_gia_thang_id'] for r in type1 + type2})}")
    print("=" * 100)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    grp = parser.add_mutually_exclusive_group(required=True)
    grp.add_argument("--dry-run", action="store_true", help="Chỉ in plan, KHÔNG đụng DB")
    grp.add_argument("--commit", action="store_true", help="Thực hiện UPDATE (trong transaction)")
    args = parser.parse_args()

    engine = create_engine(settings.database_url_sync, echo=False)

    with engine.connect() as conn:
        # luôn READ trước để in plan
        type1 = find_type1_records(conn)
        type2 = find_type2_records(conn)
        print_plan(type1, type2)

    if args.dry_run:
        print("\n[DRY-RUN] KHÔNG đụng DB. Chạy với --commit để thực hiện.")
        return

    # === COMMIT ===
    print("\n🚀 BẮT ĐẦU UPDATE trong 1 transaction...")
    with engine.begin() as conn:
        # type 2 trước (an toàn nhất, có snapshot)
        for r in type2:
            update_tc(conn, r["tc_id"], r["diem_moi"])
        # type 1
        for r in type1:
            update_tc(conn, r["tc_id"], r["diem_moi"])

        # recompute aggregate cho từng DGT
        type1_dgt_ids = {r["danh_gia_thang_id"] for r in type1}
        type2_dgt_ids = {r["danh_gia_thang_id"] for r in type2}
        # union — Type 1 ưu tiên (vì cần update cả cap1)
        all_dgt = {dgt_id: (dgt_id in type1_dgt_ids) for dgt_id in (type1_dgt_ids | type2_dgt_ids)}

        for dgt_id, is_t1 in all_dgt.items():
            new_total = recompute_dgt_aggregate(conn, dgt_id, is_t1)
            print(f"  DGT {dgt_id} → diem mới = {new_total} ({'Type1' if is_t1 else 'Type2'})")

        # Validation: 0 row còn lại
        remain_t1 = find_type1_records(conn)
        remain_t2 = find_type2_records(conn)
        if remain_t1 or remain_t2:
            raise RuntimeError(
                f"Validation FAIL — vẫn còn {len(remain_t1)} Type1 + {len(remain_t2)} Type2 records!"
            )

    print(f"\n✅ HOÀN TẤT — đã backfill {len(type1) + len(type2)} TC trên {len(all_dgt)} đơn DGT.")
    print("Validation: Q1 + Q3 đều = 0 rows. ✓")


if __name__ == "__main__":
    main()
