#!/usr/bin/env python3
"""
scripts/zalo_import_sdt.py
===========================
Import danh sách số điện thoại công chức để gửi thông báo Zalo.

MẶC ĐỊNH LÀ CHẠY KHÔ (dry-run): chỉ đọc file, chuẩn hóa, đối chiếu với
public.cong_chuc và in báo cáo. KHÔNG ghi gì vào database.
Muốn ghi thật phải thêm cờ --ghi.

GHI VÀO ĐÂU
===========
Chỉ ghi vào `common.zalo_lien_ket`. KHÔNG đụng `public.cong_chuc.so_dien_thoai`
— theo quy tắc trong CLAUDE.md, module mới chỉ được ĐỌC bảng schema public.
Nếu sau này muốn điền số vào hồ sơ công chức cho mục đích khác thì đó là một
quyết định riêng, cần đội KPI thực hiện.

ĐỊNH DẠNG FILE ĐẦU VÀO
======================
Excel (.xlsx) hoặc CSV, có 2 cột (tên cột không phân biệt hoa thường, tự dò):
    - Cột mã: ma_cc | ma | ma_cong_chuc | maccl | "Mã CC"
    - Cột số: so_dien_thoai | sdt | dien_thoai | phone | "Số điện thoại"

Ví dụ:
    ma_cc      | so_dien_thoai
    20ZZ-0224  | 0913 048 358
    20ZZ-0097  | +84936719858

CÁCH DÙNG
=========
    cd backend && source venv/bin/activate

    # 1. Chạy khô, xem báo cáo
    PYTHONPATH=$PWD python scripts/zalo_import_sdt.py danh_sach.xlsx

    # 2. Xuất các dòng có vấn đề để đơn vị rà lại
    PYTHONPATH=$PWD python scripts/zalo_import_sdt.py danh_sach.xlsx \
        --xuat-loi loi_can_ra_soat.csv

    # 3. Ghi thật (sau khi đã xem báo cáo và đồng ý)
    PYTHONPATH=$PWD python scripts/zalo_import_sdt.py danh_sach.xlsx --ghi
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Optional

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from sqlalchemy import select, text  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: E402

from shared.database import create_db_engine, create_session_factory  # noqa: E402

from common_service.config import settings  # noqa: E402
from common_service.models.zalo import LK_CHUA_XAC_MINH, ZaloLienKet  # noqa: E402
from common_service.services.zalo.phone import chuan_hoa, hien_thi  # noqa: E402

_TEN_COT_MA = {"ma_cc", "ma", "ma_cong_chuc", "macc", "ma cc", "mã cc", "mã"}
_TEN_COT_SDT = {
    "so_dien_thoai", "sdt", "dien_thoai", "phone", "so dien thoai",
    "số điện thoại", "sđt", "điện thoại", "so_dt",
}


def _chuan_ten_cot(ten: Any) -> str:
    return str(ten or "").strip().lower().replace("\n", " ")


def doc_file(duong_dan: Path) -> list[dict[str, str]]:
    """Đọc Excel/CSV → list {ma_cc, so_dien_thoai}. Tự dò tên cột."""
    if not duong_dan.exists():
        raise SystemExit(f"Không tìm thấy file: {duong_dan}")

    if duong_dan.suffix.lower() in (".xlsx", ".xlsm", ".xls"):
        import pandas as pd

        df = pd.read_excel(duong_dan, dtype=str)
        ban_ghi = df.to_dict("records")
    elif duong_dan.suffix.lower() == ".csv":
        with duong_dan.open(encoding="utf-8-sig", newline="") as f:
            ban_ghi = list(csv.DictReader(f))
    else:
        raise SystemExit(f"Định dạng không hỗ trợ: {duong_dan.suffix}")

    if not ban_ghi:
        raise SystemExit("File rỗng, không có dòng dữ liệu nào")

    # Dò tên cột từ dòng đầu
    cot = {_chuan_ten_cot(k): k for k in ban_ghi[0].keys()}
    cot_ma = next((cot[c] for c in cot if c in _TEN_COT_MA), None)
    cot_sdt = next((cot[c] for c in cot if c in _TEN_COT_SDT), None)
    if not cot_ma or not cot_sdt:
        raise SystemExit(
            f"Không dò được cột. Cột đang có: {list(ban_ghi[0].keys())}\n"
            f"Cần 1 cột mã ({sorted(_TEN_COT_MA)}) và "
            f"1 cột số ({sorted(_TEN_COT_SDT)})."
        )

    ket_qua = []
    for r in ban_ghi:
        ma = str(r.get(cot_ma) or "").strip()
        sdt = str(r.get(cot_sdt) or "").strip()
        if ma.lower() in ("", "nan", "none"):
            continue
        ket_qua.append({"ma_cc": ma, "so_dien_thoai": "" if sdt.lower() in ("nan", "none") else sdt})
    return ket_qua


async def _nap_cong_chuc(db: AsyncSession) -> dict[str, dict[str, Any]]:
    """Đọc toàn bộ công chức đang hoạt động → tra theo mã (viết hoa)."""
    kq = await db.execute(
        text(
            "SELECT id, ma_cc, ho_ten FROM public.cong_chuc "
            "WHERE is_active = true AND COALESCE(is_deleted, false) = false"
        )
    )
    return {r.ma_cc.strip().upper(): dict(r._mapping) for r in kq}


async def chay(duong_dan: Path, ghi: bool, xuat_loi: Optional[Path]) -> int:
    engine = create_db_engine(settings.database_url)
    session_factory = create_session_factory(engine)

    dong = doc_file(duong_dan)
    print(f"Đọc {len(dong)} dòng từ {duong_dan.name}\n")

    async with session_factory() as db:
        cong_chuc = await _nap_cong_chuc(db)
        print(f"Đối chiếu với {len(cong_chuc)} công chức đang hoạt động\n")

        # Liên kết đã có sẵn
        kq = await db.execute(select(ZaloLienKet))
        da_co = {str(lk.cong_chuc_id): lk for lk in kq.scalars().all()}

        thong_ke: Counter = Counter()
        loi: list[dict[str, str]] = []
        theo_so: defaultdict[str, list[str]] = defaultdict(list)
        se_ghi: list[tuple[dict[str, Any], Any]] = []

        for r in dong:
            ma = r["ma_cc"].strip().upper()
            cc = cong_chuc.get(ma)
            if cc is None:
                thong_ke["khong_tim_thay_ma"] += 1
                loi.append({"ma_cc": r["ma_cc"], "so": r["so_dien_thoai"],
                            "loi": "Không tìm thấy mã công chức (hoặc đã nghỉ)"})
                continue

            kq_ch = chuan_hoa(r["so_dien_thoai"])
            if not kq_ch.hop_le:
                thong_ke[f"so_loi_{kq_ch.trang_thai}"] += 1
                loi.append({"ma_cc": ma, "so": r["so_dien_thoai"],
                            "loi": f"{kq_ch.trang_thai}: {kq_ch.ghi_chu}"})
                continue

            theo_so[kq_ch.so_chuan].append(ma)  # type: ignore[arg-type]
            thong_ke["hop_le"] += 1
            if kq_ch.trang_thai == "OK_SO_CU":
                thong_ke["so_cu_da_quy_doi"] += 1
            se_ghi.append((cc, kq_ch))

        # Số trùng — 2 người khai cùng 1 số là dấu hiệu nhập nhầm
        trung = {s: m for s, m in theo_so.items() if len(m) > 1}
        for so, ma_list in trung.items():
            loi.append({"ma_cc": ", ".join(ma_list), "so": hien_thi(so),
                        "loi": f"Số trùng giữa {len(ma_list)} người"})

        # ---------------- Báo cáo ----------------
        print("=" * 62)
        print("KẾT QUẢ ĐỐI CHIẾU")
        print("=" * 62)
        print(f"  Hợp lệ, sẵn sàng gửi        : {thong_ke['hop_le']:>4}")
        if thong_ke["so_cu_da_quy_doi"]:
            print(f"    (trong đó số 11 số cũ đã quy đổi: {thong_ke['so_cu_da_quy_doi']})")
        print(f"  Không tìm thấy mã công chức : {thong_ke['khong_tim_thay_ma']:>4}")
        for k, v in sorted(thong_ke.items()):
            if k.startswith("so_loi_"):
                print(f"  Số không dùng được [{k[7:]:<14}]: {v:>4}")
        print(f"  Số bị trùng giữa nhiều người: {len(trung):>4}")

        phu = (thong_ke["hop_le"] / len(cong_chuc) * 100) if cong_chuc else 0
        print(f"\n  ĐỘ PHỦ: {thong_ke['hop_le']}/{len(cong_chuc)} công chức = {phu:.1f}%")
        if phu < 70:
            print("  ⚠️  Độ phủ dưới 70% — nhiều người sẽ không nhận được tin.")

        chua_co = len(cong_chuc) - thong_ke["hop_le"]
        if chua_co > 0:
            print(f"  Còn {chua_co} công chức chưa có số điện thoại dùng được.")

        if xuat_loi and loi:
            with xuat_loi.open("w", encoding="utf-8-sig", newline="") as f:
                w = csv.DictWriter(f, fieldnames=["ma_cc", "so", "loi"])
                w.writeheader()
                w.writerows(loi)
            print(f"\n  Đã xuất {len(loi)} dòng cần rà soát → {xuat_loi}")

        # ---------------- Ghi ----------------
        if not ghi:
            print("\n" + "=" * 62)
            print("ĐANG CHẠY KHÔ — KHÔNG GHI GÌ VÀO DATABASE.")
            print("Xem kỹ báo cáo trên, nếu đồng ý thì chạy lại với cờ --ghi")
            print("=" * 62)
            await engine.dispose()
            return 0

        them, cap_nhat = 0, 0
        for cc, kq_ch in se_ghi:
            cc_id = str(cc["id"])
            lk = da_co.get(cc_id)
            if lk is None:
                db.add(
                    ZaloLienKet(
                        cong_chuc_id=cc["id"],
                        so_dien_thoai=kq_ch.so_chuan,
                        so_goc=kq_ch.so_goc[:30],
                        trang_thai=LK_CHUA_XAC_MINH,
                        nguon="IMPORT_EXCEL",
                    )
                )
                them += 1
            elif lk.so_dien_thoai != kq_ch.so_chuan:
                lk.so_dien_thoai = kq_ch.so_chuan
                lk.so_goc = kq_ch.so_goc[:30]
                lk.nguon = "IMPORT_EXCEL"
                # Số đổi → xóa cờ lỗi cũ để thử lại
                if lk.trang_thai == "SO_LOI":
                    lk.trang_thai = LK_CHUA_XAC_MINH
                cap_nhat += 1

        await db.commit()
        print(f"\n✅ Đã ghi: thêm mới {them}, cập nhật {cap_nhat} liên kết.")

    await engine.dispose()
    return 0


def main() -> int:
    p = argparse.ArgumentParser(
        description="Import số điện thoại cho kênh thông báo Zalo (mặc định chạy khô)"
    )
    p.add_argument("file", type=Path, help="File .xlsx hoặc .csv")
    p.add_argument("--ghi", action="store_true",
                   help="GHI THẬT vào common.zalo_lien_ket (mặc định chỉ chạy khô)")
    p.add_argument("--xuat-loi", type=Path, default=None,
                   help="Xuất CSV các dòng cần rà soát")
    a = p.parse_args()

    print(f"DB: {settings.db_name} @ {settings.db_host}:{settings.db_port}")
    if a.ghi:
        print("⚠️  CHẾ ĐỘ GHI THẬT\n")
    return asyncio.run(chay(a.file, a.ghi, a.xuat_loi))


if __name__ == "__main__":
    raise SystemExit(main())
