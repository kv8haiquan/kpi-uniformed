"""
tests/regression/test_v1_unchanged.py
=====================================
Regression test: KPI V1 KHÔNG bị regression sau Phase A/B/C/D/E.

Cách hoạt động:
- Load baseline `tests/baselines/v1_kpi_results.json` (đã generate trước Phase B sửa code).
- Với từng case, gọi `tinh_diem_kpi_70(db, cc_id, thang, nam)`.
- So sánh kết quả với expected.
- Nếu khác (ngoài tolerance) → V1 đã bị thay đổi hành vi → FAIL.

Chạy:
    pytest tests/regression/test_v1_unchanged.py -v

Re-generate baseline khi data DB thay đổi tay:
    python tests/regression/generate_baseline_v1.py
"""

from __future__ import annotations

import json
from pathlib import Path
from uuid import UUID

import pytest

from app.api.v1.endpoints.xep_loai_moi import tinh_diem_kpi_70
from app.db.session import AsyncSessionLocal


BASELINE_FILE = Path(__file__).resolve().parent.parent / "baselines" / "v1_kpi_results.json"

# Số học so sánh: tolerance nhỏ cho float
FLOAT_TOLERANCE = 1e-4

# Các key số cần so sánh chính xác
NUMERIC_KEYS = [
    "so_ngay_lam_viec",
    "so_ngay_nghi",
    "sp_duoc_giao",
    "tong_sp_hoan_thanh",
    "sp_chat_luong",
    "sp_tien_do",
    "a_so_luong",
    "b_chat_luong",
    "c_tien_do",
    "diem_kpi",
    "diem_70",
]


def _load_baseline() -> list[dict]:
    if not BASELINE_FILE.exists():
        pytest.skip(
            f"Baseline file không tồn tại: {BASELINE_FILE}. "
            "Chạy `python tests/regression/generate_baseline_v1.py` để tạo."
        )
    return json.loads(BASELINE_FILE.read_text(encoding="utf-8"))


@pytest.mark.asyncio
async def test_v1_kpi_baseline_unchanged():
    """
    Với mỗi case baseline, kết quả tính KPI hiện tại phải khớp expected.

    Nếu fail: V1 logic đã bị thay đổi bởi Phase A/B/C/D/E → ai đó phá V1.
    Cần điều tra rồi (a) revert, hoặc (b) regenerate baseline nếu intentional.
    """
    baseline = _load_baseline()
    assert len(baseline) > 0, "Baseline file rỗng"

    failures: list[str] = []

    async with AsyncSessionLocal() as db:
        for entry in baseline:
            case = entry["case"]
            expected = entry["expected"]
            cc_id = UUID(case["cong_chuc_id"])
            thang = case["thang"]
            nam = case["nam"]
            label = f"{case['ma_cc']} | {thang}/{nam}"

            actual = await tinh_diem_kpi_70(db, cc_id, thang, nam, tam_tinh=False)

            for key in NUMERIC_KEYS:
                exp_val = expected.get(key)
                act_val = actual.get(key)
                if exp_val is None and act_val is None:
                    continue
                if exp_val is None or act_val is None:
                    failures.append(
                        f"{label} | {key}: expected={exp_val} actual={act_val} (None mismatch)"
                    )
                    continue
                exp_f = float(exp_val)
                act_f = float(act_val)
                if abs(exp_f - act_f) > FLOAT_TOLERANCE:
                    failures.append(
                        f"{label} | {key}: expected={exp_f} actual={act_f} (diff={abs(exp_f - act_f)})"
                    )

    if failures:
        msg = (
            f"V1 KPI regression detected ({len(failures)} mismatches):\n"
            + "\n".join(f"  - {f}" for f in failures[:30])
        )
        if len(failures) > 30:
            msg += f"\n  ... và {len(failures) - 30} mismatches khác"
        pytest.fail(msg)
