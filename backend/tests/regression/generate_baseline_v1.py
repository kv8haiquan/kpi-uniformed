"""
tests/regression/generate_baseline_v1.py
=========================================
Generate baseline KPI V1 từ data hiện tại.

Cách chạy:
    cd backend && source venv/bin/activate
    python tests/regression/generate_baseline_v1.py

Output: tests/baselines/v1_kpi_results.json

Logic:
- Chọn 5-10 CC còn V1 trong tháng đã có data đủ.
- Chạy tinh_diem_kpi_70(db, cc_id, thang, nam, tam_tinh=False) → snapshot.
- Lưu vào file JSON (kết quả V1 đúng tại thời điểm này).

Test regression sau này load file này, gọi lại function, so kết quả với expected.
Nếu khác → V1 đã bị regression bởi code change phía sau.
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from uuid import UUID

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import text  # noqa: E402

from app.api.v1.endpoints.xep_loai_moi import tinh_diem_kpi_70  # noqa: E402
from app.db.session import AsyncSessionLocal  # noqa: E402


BASELINE_FILE = PROJECT_ROOT / "tests" / "baselines" / "v1_kpi_results.json"
NUM_TEST_CASES = 10  # 10 CC khác nhau, mỗi CC 1 tháng có data V1


async def find_v1_test_cases(db, limit: int) -> list[dict]:
    """Tìm các (cong_chuc_id, thang, nam) có data V1 đủ để test."""
    rows = (await db.execute(text("""
        SELECT
            cc.id::text AS cc_id,
            cc.ma_cc,
            cc.ho_ten,
            kk.thang,
            kk.nam,
            COUNT(*) AS so_kekhai_v1_da_duyet,
            COALESCE(SUM(kk.so_sp_goc_quy_doi), 0) AS tong_sp_da_duyet
        FROM ke_khai_cong_viec kk
        JOIN cong_chuc cc ON kk.cong_chuc_id = cc.id
        WHERE kk.version_kekhai = 'V1'
          AND kk.trang_thai = 'DA_PHE_DUYET'
          AND kk.is_deleted = false
          AND cc.is_active = true
          AND cc.is_deleted = false
          AND COALESCE(cc.is_lanh_dao, false) = false
        GROUP BY cc.id, cc.ma_cc, cc.ho_ten, kk.thang, kk.nam
        HAVING COUNT(*) >= 3
        ORDER BY COUNT(*) DESC, kk.nam DESC, kk.thang DESC
        LIMIT :limit
    """), {"limit": limit})).all()

    return [
        {
            "cong_chuc_id": r.cc_id,
            "ma_cc": r.ma_cc,
            "ho_ten": r.ho_ten,
            "thang": r.thang,
            "nam": r.nam,
            "so_kekhai_v1_da_duyet": r.so_kekhai_v1_da_duyet,
            "tong_sp_da_duyet": float(r.tong_sp_da_duyet),
        }
        for r in rows
    ]


def _to_serializable(d):
    """Convert dict có Decimal/None sang JSON-friendly."""
    out = {}
    for k, v in d.items():
        if isinstance(v, (int, float, str)) or v is None:
            out[k] = v
        else:
            try:
                out[k] = float(v)
            except (TypeError, ValueError):
                out[k] = str(v)
    return out


async def main():
    print(f"[INFO] Generate baseline V1 → {BASELINE_FILE}")
    BASELINE_FILE.parent.mkdir(parents=True, exist_ok=True)

    async with AsyncSessionLocal() as db:
        cases = await find_v1_test_cases(db, NUM_TEST_CASES)
        print(f"[INFO] Tìm thấy {len(cases)} test cases V1")

        baseline = []
        for case in cases:
            cc_uuid = UUID(case["cong_chuc_id"])
            print(f"  - {case['ma_cc']} | {case['ho_ten']} | {case['thang']}/{case['nam']}", end="... ")
            result = await tinh_diem_kpi_70(
                db, cc_uuid, case["thang"], case["nam"], tam_tinh=False
            )
            expected = _to_serializable(result)
            print(f"diem_70={expected.get('diem_70'):.2f}")
            baseline.append({
                "case": case,
                "expected": expected,
            })

    BASELINE_FILE.write_text(
        json.dumps(baseline, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"[DONE] Saved {len(baseline)} cases to {BASELINE_FILE}")


if __name__ == "__main__":
    asyncio.run(main())
