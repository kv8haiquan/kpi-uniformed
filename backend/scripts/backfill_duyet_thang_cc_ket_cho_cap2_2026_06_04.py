#!/usr/bin/env python3
"""
backfill_duyet_thang_cc_ket_cho_cap2_2026_06_04.py
===================================================

Backfill các đơn TIÊU CHÍ CHUNG bị KẸT ở CHO_CAP2 do bug endpoint
`phe-duyet-tieu-chi-bulk` thiếu case "ĐT (TRUONG_DON_VI) duyệt thẳng CC thường".

BUG (đã fix trong danh_gia.py 04/06/2026):
    Khi CC thường chọn "Đội trưởng - duyệt thẳng" lúc gửi (cap1_id = chính ĐT),
    rồi ĐT bấm "Duyệt hàng loạt" (bulk), nhánh `is_duyet_thang` của endpoint
    bulk KHÔNG nhận ra trường hợp này → rơi xuống nhánh "Cấp 1":
        - set ngay_phe_duyet_tc_cap1, trang_thai_tc = CHO_CAP2
        - gán cap2_id = TRUONG_DON_VI cùng đơn vị = CHÍNH ĐT đó
    => deadlock: cap1_id == cap2_id, đơn kẹt CHO_CAP2 hiển thị "chờ cấp 2".

    Endpoint single (phe-duyet-tieu-chi) xử lý đúng ở nhánh đặc biệt nên các
    đơn duyệt-từng-đơn không dính. Chỉ đơn duyệt-hàng-loạt mới kẹt.

CHỮ KÝ ĐƠN KẸT (chỉ backfill đúng các đơn này — KHÔNG đụng đơn 2-cấp hợp lệ
cap1=PDV ≠ cap2=TDV):
    trang_thai_tc = 'CHO_CAP2'
    AND nguoi_phe_duyet_tc_cap1_id IS NOT NULL
    AND nguoi_phe_duyet_tc_cap2_id = nguoi_phe_duyet_tc_cap1_id   (cùng 1 người)
    AND ngay_phe_duyet_tc_cap1 IS NOT NULL
    AND ngay_phe_duyet_tc_cap2 IS NULL

FINALIZE (giống đúng nhánh "Cấp 2" của endpoint bulk — đồng ý quyết định cấp 1,
GIỮ NGUYÊN diem_phe_duyet đã có):
    - Mỗi TC con: trang_thai = DA_PHE_DUYET, ngay_phe_duyet = ngay_phe_duyet_tc_cap1
    - Đơn: trang_thai_tc = DA_PHE_DUYET
           ngay_phe_duyet_tc_cap2 = ngay_phe_duyet_tc_cap1
           diem_tc_cap2 = diem_tc_cap1
           diem_tieu_chi_chung = diem_tc_cap1

Usage:
    python3 backend/scripts/backfill_duyet_thang_cc_ket_cho_cap2_2026_06_04.py            # dry-run (default)
    python3 backend/scripts/backfill_duyet_thang_cc_ket_cho_cap2_2026_06_04.py --commit   # apply

⚠️ DB localhost:5432 LÀ PRODUCTION. Dry-run trước, COMMIT chỉ khi đã xác nhận.

Date: 2026-06-04
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

# Path setup
BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.session import AsyncSessionLocal
from app.models.kpi_assessment import (
    DanhGiaThang,
    TieuChiChungDanhGia,
    TrangThaiTieuChi,
)


async def find_don_ket(session) -> list[DanhGiaThang]:
    """Tìm các đơn kẹt CHO_CAP2 với cap1_id == cap2_id (deadlock duyệt thẳng).

    Bắt CẢ 2 nhóm:
      - Nhóm chưa duyệt cấp 2 (ngay_phe_duyet_tc_cap2 IS NULL): TC con còn
        CHO_PHE_DUYET → finalize đầy đủ.
      - Nhóm đã có đủ ngày + điểm 2 cấp nhưng nhãn trang_thai_tc còn kẹt
        CHO_CAP2 (TC con đã DA_PHE_DUYET): chỉ sửa nhãn đơn cha, KHÔNG ghi đè
        ngày/điểm cấp 2 đã có (finalize idempotent).
    """
    stmt = (
        select(DanhGiaThang)
        .where(
            DanhGiaThang.trang_thai_tc == TrangThaiTieuChi.CHO_CAP2,
            DanhGiaThang.is_deleted == False,  # noqa: E712
            DanhGiaThang.nguoi_phe_duyet_tc_cap1_id.is_not(None),
            DanhGiaThang.nguoi_phe_duyet_tc_cap2_id
            == DanhGiaThang.nguoi_phe_duyet_tc_cap1_id,
            DanhGiaThang.ngay_phe_duyet_tc_cap1.is_not(None),
        )
        .options(
            selectinload(DanhGiaThang.cong_chuc),
            selectinload(DanhGiaThang.nguoi_phe_duyet_tc_cap1),
            selectinload(DanhGiaThang.tieu_chi_chungs),
        )
        .order_by(DanhGiaThang.nam, DanhGiaThang.thang)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


def finalize_don(don: DanhGiaThang) -> None:
    """Hoàn tất đơn = đồng ý cấp 1, set DA_PHE_DUYET (giữ nguyên điểm).

    Idempotent: chỉ điền ngày/điểm cấp 2 khi CHƯA có — KHÔNG ghi đè dữ liệu
    cấp 2 đã tồn tại (nhóm đơn cũ đã duyệt đủ 2 cấp, chỉ kẹt nhãn đơn cha).
    """
    now_cap1 = don.ngay_phe_duyet_tc_cap1
    for tc in don.tieu_chi_chungs:
        tc.trang_thai = TrangThaiTieuChi.DA_PHE_DUYET
        if tc.ngay_phe_duyet is None:
            tc.ngay_phe_duyet = now_cap1

    don.trang_thai_tc = TrangThaiTieuChi.DA_PHE_DUYET
    if don.ngay_phe_duyet_tc_cap2 is None:
        don.ngay_phe_duyet_tc_cap2 = now_cap1
    if don.diem_tc_cap2 is None and don.diem_tc_cap1 is not None:
        don.diem_tc_cap2 = don.diem_tc_cap1
    if don.diem_tieu_chi_chung is None and don.diem_tc_cap1 is not None:
        don.diem_tieu_chi_chung = don.diem_tc_cap1


async def main(commit: bool) -> None:
    async with AsyncSessionLocal() as session:
        dons = await find_don_ket(session)

        print("=" * 78)
        print(f"TÌM THẤY {len(dons)} đơn KẸT CHO_CAP2 (cap1_id == cap2_id):")
        print("=" * 78)
        if not dons:
            print("Không có đơn nào cần backfill. Kết thúc.")
            return

        for d in dons:
            cc = d.cong_chuc.ho_ten if d.cong_chuc else "?"
            pd = d.nguoi_phe_duyet_tc_cap1.ho_ten if d.nguoi_phe_duyet_tc_cap1 else "?"
            diem = d.diem_tc_cap1
            nhom = (
                "[nhãn-only: TC con đã duyệt]"
                if d.ngay_phe_duyet_tc_cap2 is not None
                else "[hoàn tất cấp 2]"
            )
            print(
                f"  - {d.thang:02d}/{d.nam} | CC: {cc:<28} | "
                f"cap1=cap2: {pd:<22} | diem_cap1={diem} | {len(d.tieu_chi_chungs)} TC "
                f"{nhom}"
            )

        print("-" * 78)
        if not commit:
            print("DRY-RUN (mặc định). KHÔNG ghi gì. Chạy lại với --commit để áp dụng.")
            return

        for d in dons:
            finalize_don(d)
        await session.commit()
        print(f"✅ ĐÃ COMMIT: backfill {len(dons)} đơn → DA_PHE_DUYET.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--commit", action="store_true", help="Áp dụng thay đổi (mặc định dry-run)")
    args = parser.parse_args()
    asyncio.run(main(args.commit))
