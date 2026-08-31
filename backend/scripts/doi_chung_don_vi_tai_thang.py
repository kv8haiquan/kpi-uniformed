#!/usr/bin/env python3
"""
scripts/doi_chung_don_vi_tai_thang.py
=====================================
Đối chứng `_don_vi_tai_thang_expr` giữa HAI database, dùng CHÍNH biểu thức
trong code (không viết lại SQL bằng tay → không lệch khỏi thứ thật sự chạy).

Dùng để chứng minh đợt sửa 31/08/2026 (làm sạch `ngay_hieu_luc` + đổi mốc chốt
về cuối tháng M) không làm đổi báo cáo các tháng đã chốt.

Chạy:
    # A = prod (dữ liệu cũ), B = test (đã sửa) — cả hai đều CHỈ ĐỌC
    python scripts/doi_chung_don_vi_tai_thang.py --db-a kpi_haiquan --db-b kpi_haiquan_test

Lưu ý: cây code hiện tại quyết định mốc chốt cho CẢ HAI phía. Muốn so "code cũ vs
code mới" thì chạy script 2 lần (một lần trước khi sửa, một lần sau) rồi so file
JSON kết quả — dùng --xuat để ghi ra file.
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.config import settings
from app.models import CongChuc, DonVi
from app.api.v1.endpoints.bao_cao_xep_loai import _don_vi_tai_thang_expr

CAC_THANG = [(t, 2026) for t in range(1, 9)]


def url_cho_db(db_name: str) -> str:
    """Đổi tên database trong connection string, giữ nguyên host/user/password."""
    goc = settings.database_url
    return goc.rsplit("/", 1)[0] + "/" + db_name


async def lay_ket_qua(db_name: str) -> dict[str, dict[str, str]]:
    """{ 'T<thang>': { ma_cc: ma_don_vi } } — đơn vị-tại-tháng của mọi công chức."""
    engine = create_async_engine(url_cho_db(db_name), echo=False)
    Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    ket_qua: dict[str, dict[str, str]] = {}
    async with Session() as db:
        ma_don_vi_theo_id = {
            d.id: d.ma_don_vi
            for d in (await db.execute(select(DonVi))).scalars().all()
        }
        for thang, nam in CAC_THANG:
            rows = (await db.execute(
                select(CongChuc.ma_cc, _don_vi_tai_thang_expr(thang, nam))
                .where(CongChuc.is_deleted == False)
            )).all()
            ket_qua[f"T{thang}"] = {
                ma_cc: ma_don_vi_theo_id.get(dv_id, "?") for ma_cc, dv_id in rows
            }
    await engine.dispose()
    return ket_qua


async def main(db_a: str, db_b: str, xuat: str | None) -> int:
    print(f"A = {db_a}   (mong đợi: dữ liệu CŨ)")
    print(f"B = {db_b}   (mong đợi: dữ liệu ĐÃ SỬA)")
    print()

    a = await lay_ket_qua(db_a)
    b = await lay_ket_qua(db_b)

    if xuat:
        Path(xuat).write_text(json.dumps({"a": a, "b": b}, ensure_ascii=False, indent=1))
        print(f"→ đã ghi {xuat}")

    tong_lech = 0
    print(f"{'Tháng':<8}{'Số CC':>8}{'Khác nhau':>12}")
    print("-" * 28)
    chi_tiet: list[tuple[str, str, str, str]] = []
    for khoa in a:
        ma_cc_chung = set(a[khoa]) & set(b[khoa])
        lech = [m for m in ma_cc_chung if a[khoa][m] != b[khoa][m]]
        tong_lech += len(lech)
        print(f"{khoa:<8}{len(ma_cc_chung):>8}{len(lech):>12}")
        for m in sorted(lech):
            chi_tiet.append((khoa, m, a[khoa][m], b[khoa][m]))

    if chi_tiet:
        print()
        print("CHI TIẾT CÁC CA ĐỔI")
        print("-" * 60)
        for khoa, ma_cc, cu, moi in chi_tiet:
            print(f"  {khoa:<5} {ma_cc:<12} {cu:<12} -> {moi}")

    print()
    print(f"TỔNG SỐ CA ĐỔI: {tong_lech}")
    return 0


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Đối chứng đơn vị-tại-tháng giữa 2 database")
    p.add_argument("--db-a", required=True, help="Database A (dữ liệu cũ)")
    p.add_argument("--db-b", required=True, help="Database B (đã sửa)")
    p.add_argument("--xuat", help="Ghi kết quả thô ra file JSON")
    args = p.parse_args()
    sys.exit(asyncio.run(main(args.db_a, args.db_b, args.xuat)))
