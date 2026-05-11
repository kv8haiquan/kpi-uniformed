#!/usr/bin/env python3
"""
revert_phe_duyet_tieu_chi_chung_sai.py
=======================================

Script revert các đơn TIÊU CHÍ CHUNG bị duyệt SAI theo logic cũ tick box
(tháng 04/2026, lỗi v3.6 trước khi sửa).

BUG: backend cũ tính diem_phe_duyet = (is_achieved_ld ? diem_toi_da : 0).
Khi CC chấm điểm thập phân (vd 4.5/5), backend cũ set is_achieved_cc = FALSE
(vì < max). Form duyệt cũ của LĐ hiển thị checkbox theo is_achieved_cc → LĐ
mặc định tick "không đạt" → diem_phe_duyet = 0, mất hết điểm CC tự chấm.

REVERT:
- Tất cả TC trong các đơn bị ảnh hưởng → reset is_achieved_ld, diem_phe_duyet,
  ly_do_dieu_chinh, ghi_chu_ld, ngay_phe_duyet, trang_thai = CHO_PHE_DUYET.
- Đơn (DanhGiaThang): reset trạng thái cấp 1/cấp 2, người duyệt, điểm cấp,
  diem_tieu_chi_chung. is_khoa giữ nguyên (chưa khóa).
- is_achieved_cc, diem_tu_cham, ghi_chu_cc của CC GIỮ NGUYÊN.

ĐIỀU KIỆN XÁC ĐỊNH ĐƠN SAI (giống query trong báo cáo):
    diem_tu_cham > 0
    AND diem_tu_cham < diem_toi_da (TIEU_CHI.diem_toi_da)
    AND diem_phe_duyet IS NOT NULL
    AND ABS(diem_phe_duyet - diem_tu_cham) > 0.01

Usage:
    python3 backend/scripts/revert_phe_duyet_tieu_chi_chung_sai.py            # dry-run (default)
    python3 backend/scripts/revert_phe_duyet_tieu_chi_chung_sai.py --commit   # apply

Date: 2026-05-11
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from decimal import Decimal
from pathlib import Path
from typing import Sequence

# Path setup
BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import select, text
from sqlalchemy.orm import selectinload

from app.db.session import AsyncSessionLocal
from app.models.kpi_assessment import (
    DanhGiaThang,
    TieuChiChungDanhGia,
    TrangThaiTieuChi,
)


# =============================================================================
# QUERIES
# =============================================================================

SQL_FIND_DON_SAI = text("""
    SELECT DISTINCT tcdg.danh_gia_thang_id
    FROM tieu_chi_chung_danh_gia tcdg
    JOIN tieu_chi_chung tc ON tc.id = tcdg.tieu_chi_id
    WHERE tcdg.diem_tu_cham > 0
      AND tcdg.diem_tu_cham < tc.diem_toi_da
      AND tcdg.diem_phe_duyet IS NOT NULL
      AND ABS(tcdg.diem_phe_duyet - tcdg.diem_tu_cham) > 0.01
""")


# =============================================================================
# CORE
# =============================================================================

async def find_don_can_revert(session) -> list:
    """Tìm tất cả danh_gia_thang_id cần revert."""
    result = await session.execute(SQL_FIND_DON_SAI)
    return [row[0] for row in result.fetchall()]


async def load_don_full(session, danh_gia_ids: Sequence) -> list[DanhGiaThang]:
    """Load toàn bộ DanhGiaThang + tiêu_chi_chungs + cong_chuc + don_vi."""
    if not danh_gia_ids:
        return []
    stmt = (
        select(DanhGiaThang)
        .where(DanhGiaThang.id.in_(danh_gia_ids))
        .options(
            selectinload(DanhGiaThang.cong_chuc),
            selectinload(DanhGiaThang.tieu_chi_chungs).selectinload(
                TieuChiChungDanhGia.tieu_chi
            ),
        )
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


def print_don_summary(idx: int, total: int, don: DanhGiaThang) -> None:
    cc = don.cong_chuc
    ho_ten = getattr(cc, "ho_ten", "?") if cc else "?"
    ma_cc = getattr(cc, "ma_cc", "?") if cc else "?"
    print(
        f"\n[{idx}/{total}] {ma_cc} - {ho_ten} | Tháng {don.thang}/{don.nam} "
        f"| trang_thai_tc = {don.trang_thai_tc.value if don.trang_thai_tc else None}"
    )

    # Tổng kết theo TC
    so_tc_co_diem_pd = 0
    so_tc_se_reset = 0
    diem_pd_truoc = Decimal("0")
    diem_pd_sau = Decimal("0")
    for tc in don.tieu_chi_chungs:
        diem_max = Decimal(str(tc.tieu_chi.diem_toi_da))
        if tc.diem_phe_duyet is not None:
            so_tc_co_diem_pd += 1
            diem_pd_truoc += tc.diem_phe_duyet
        # Tiêu chí bị duyệt sai theo điều kiện gốc
        if (
            tc.diem_tu_cham is not None
            and tc.diem_tu_cham > 0
            and tc.diem_tu_cham < diem_max
            and tc.diem_phe_duyet is not None
            and abs(tc.diem_phe_duyet - tc.diem_tu_cham) > Decimal("0.01")
        ):
            so_tc_se_reset += 1

    print(
        f"    - Tổng TC trong đơn: {len(don.tieu_chi_chungs)} "
        f"| TC có diem_phe_duyet: {so_tc_co_diem_pd} "
        f"| TC khớp pattern sai: {so_tc_se_reset}"
    )
    print(
        f"    - Tổng diem_phe_duyet trước revert: {diem_pd_truoc} "
        f"→ Sau revert: 0 (toàn bộ NULL)"
    )


def revert_one_don(don: DanhGiaThang) -> tuple[int, Decimal]:
    """Reset 1 đơn về CHO_PHE_DUYET. Trả về (so_tc_reset, tong_diem_pd_truoc)."""
    so_tc = 0
    tong_diem_pd = Decimal("0")
    for tc in don.tieu_chi_chungs:
        if tc.diem_phe_duyet is not None:
            tong_diem_pd += tc.diem_phe_duyet
        tc.is_achieved_ld = None
        tc.diem_phe_duyet = None
        tc.ly_do_dieu_chinh = None
        tc.ghi_chu_ld = None
        tc.ngay_phe_duyet = None
        tc.trang_thai = TrangThaiTieuChi.CHO_PHE_DUYET
        so_tc += 1

    # Reset trạng thái đơn
    don.trang_thai_tc = TrangThaiTieuChi.CHO_PHE_DUYET
    don.nguoi_phe_duyet_tc_cap1_id = None
    don.ngay_phe_duyet_tc_cap1 = None
    don.diem_tc_cap1 = None
    don.nguoi_phe_duyet_tc_cap2_id = None
    don.ngay_phe_duyet_tc_cap2 = None
    don.diem_tc_cap2 = None
    don.diem_tieu_chi_chung = None
    # is_khoa: giữ nguyên (chưa khóa, không liên quan)

    return so_tc, tong_diem_pd


# =============================================================================
# MAIN
# =============================================================================

async def run(commit: bool) -> int:
    mode = "COMMIT" if commit else "DRY-RUN"
    print(f"=== REVERT TIÊU CHÍ CHUNG DUYỆT SAI ===  [{mode}]\n")

    async with AsyncSessionLocal() as session:
        # 1. Tìm danh sách đơn sai
        danh_gia_ids = await find_don_can_revert(session)
        print(f"Tìm thấy {len(danh_gia_ids)} đơn cần revert.")

        if not danh_gia_ids:
            print("Không có đơn nào cần xử lý.")
            return 0

        # 2. Load full
        don_list = await load_don_full(session, danh_gia_ids)

        # 3. Sort theo (đơn vị, tháng, mã CC)
        don_list.sort(
            key=lambda d: (
                getattr(d.cong_chuc, "ma_cc", "") if d.cong_chuc else "",
                d.thang,
                d.nam,
            )
        )

        # 4. Print preview + revert in-memory
        tong_tc_reset = 0
        tong_diem_pd_truoc = Decimal("0")
        for idx, don in enumerate(don_list, start=1):
            print_don_summary(idx, len(don_list), don)
            so_tc, diem_pd = revert_one_don(don)
            tong_tc_reset += so_tc
            tong_diem_pd_truoc += diem_pd

        print(
            f"\n--- TỔNG KẾT ---"
            f"\n  Đơn sẽ revert       : {len(don_list)}"
            f"\n  Tiêu chí sẽ reset   : {tong_tc_reset}"
            f"\n  Tổng diem_phe_duyet trước revert: {tong_diem_pd_truoc}"
        )

        # 5. Commit hoặc rollback
        if commit:
            await session.commit()
            print("\n✅ ĐÃ COMMIT vào DB.")
        else:
            await session.rollback()
            print(
                "\n[DRY-RUN] KHÔNG commit. "
                "Chạy lại với --commit để áp dụng."
            )

    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Revert các đơn tiêu chí chung bị duyệt SAI (logic cũ tick box)"
    )
    parser.add_argument(
        "--commit",
        action="store_true",
        help="Thực sự ghi DB. Mặc định là --dry-run (chỉ in preview).",
    )
    args = parser.parse_args()

    if args.commit:
        print(
            "⚠️  CẢNH BÁO: SẼ GHI VÀO PRODUCTION DB.\n"
            "    Nhập 'YES' để xác nhận, bất cứ gì khác để hủy: ",
            end="",
        )
        confirm = input().strip()
        if confirm != "YES":
            print("Đã hủy.")
            return 1

    return asyncio.run(run(commit=args.commit))


if __name__ == "__main__":
    sys.exit(main())
