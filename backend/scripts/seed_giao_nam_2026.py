#!/usr/bin/env python3
"""
scripts/seed_giao_nam_2026.py
=============================
Nap DANH MUC CHI TIEU THAT (tu Excel ra soat) + GIAO NAM 2026 vao schema chi_tieu.

Nguon: scripts/dumps/chi_tieu_giao_nam_preview.csv (tao boi extract_chi_tieu_excel.py)
Quy tac chinh sua (theo xac nhan nguoi dung):
  - "Tang doanh nghiep": lay so dau (Mong Cai 2227, Cam Pha 151).
  - Kim ngach "Tang 11%" (Hon Gai): BO QUA (de trong).
  - Cac o khong phai so khac (vd "Khong dang ky"): BO QUA.

Chay:
    cd backend
    python scripts/seed_giao_nam_2026.py            # DRY-RUN (chi in, khong ghi)
    python scripts/seed_giao_nam_2026.py --confirm  # GHI vao DB

An toan: dry-run mac dinh. --confirm moi ghi; in ro DB dich truoc khi ghi.
Idempotent: danh muc upsert theo ma_chi_tieu; giao_nam upsert theo
(don_vi, chi_tieu, nam, loai_muc).
"""

import argparse
import asyncio
import csv
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR.parent))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from chi_tieu_service.config import settings

CSV = SCRIPT_DIR / "dumps" / "chi_tieu_giao_nam_preview.csv"
NAM = 2026

# ---- Danh muc chi tieu that: ma -> (linh_vuc_ma, ten, don_vi_tinh, kieu, co_phan_dau) ----
# kieu: SO_NGUYEN | THAP_PHAN | PHAN_TRAM
CATALOG = {
    # Giam sat quan ly (GSQL)
    "GSQL_KNXNK":  ("GSQL", "Tăng kim ngạch XNK (không gồm KNQ, TNTX)", "triệu USD", "THAP_PHAN", False),
    "GSQL_TANGDN": ("GSQL", "Tăng doanh nghiệp làm thủ tục", "doanh nghiệp", "SO_NGUYEN", False),
    "GSQL_HNDT":   ("GSQL", "Hội nghị đối thoại, tham vấn", "hội nghị", "SO_NGUYEN", False),
    "GSQL_RSTTHC": ("GSQL", "Rà soát, đề xuất cắt giảm TTHC", "đề xuất", "SO_NGUYEN", False),
    "GSQL_SHTT":   ("GSQL", "Phát hiện vi phạm SHTT/hàng giả", "vụ", "SO_NGUYEN", False),
    "GSQL_CCKTSTQ":("GSQL", "Đề xuất cung cấp thông tin KTSTQ", "đề xuất", "SO_NGUYEN", False),
    # Thue XNK (THUE) — 2 muc
    "THUE_STHU":   ("THUE", "Số thu thuế XNK", "tỷ đồng", "THAP_PHAN", True),
    # KTSTQ
    "KTSTQ_SOCUOC":("KTSTQ", "Số cuộc kiểm tra STQ", "cuộc", "SO_NGUYEN", False),
    "KTSTQ_STHU":  ("KTSTQ", "Số thu NSNN (KTSTQ)", "triệu đồng", "THAP_PHAN", True),  # 2 muc
    "KTSTQ_TLVP":  ("KTSTQ", "Tỷ lệ phát hiện vi phạm KTSTQ", "tỷ lệ", "THAP_PHAN", False),
    "KTSTQ_PHIEU": ("KTSTQ", "Phiếu cung cấp thông tin KTSTQ", "phiếu", "SO_NGUYEN", False),
    # Dao tao (DAOTAO)
    "DAOTAO_SOLOP":("DAOTAO", "Số lớp tập huấn", "lớp", "SO_NGUYEN", False),
    "DAOTAO_LUOT": ("DAOTAO", "Số lượt người tham gia tập huấn", "lượt", "SO_NGUYEN", False),
    # QLRR
    "QLRR_HOSO":   ("QLRR", "Số hồ sơ DN trọng điểm", "hồ sơ", "SO_NGUYEN", False),
    "QLRR_TCDN":   ("QLRR", "Số tiêu chí phân tích (doanh nghiệp)", "tiêu chí", "SO_NGUYEN", False),
    "QLRR_TCMH":   ("QLRR", "Số tiêu chí phân tích (mặt hàng)", "tiêu chí", "SO_NGUYEN", False),
    "QLRR_DNCUC":  ("QLRR", "Số lượng DN được giao thu (Cục HQ giao)", "doanh nghiệp", "SO_NGUYEN", False),
    "QLRR_DNCC":   ("QLRR", "Số lượng DN giao thu (Chi cục giao)", "doanh nghiệp", "SO_NGUYEN", False),
    # CBL
    "CBL_CHUTRI":  ("CBL", "Số vụ chủ trì bắt giữ", "vụ", "SO_NGUYEN", False),
    "CBL_PHOIHOP": ("CBL", "Số vụ phối hợp bắt giữ", "vụ", "SO_NGUYEN", False),
    "CBL_TRIGIA":  ("CBL", "Tổng trị giá chủ trì bắt giữ", "triệu đồng", "THAP_PHAN", False),
    "CBL_XUPHAT":  ("CBL", "Số thu NSNN từ xử phạt VPHC", "triệu đồng", "THAP_PHAN", False),
    "CBL_KHOITO":  ("CBL", "HQ khởi tố", "vụ", "SO_NGUYEN", False),
    # Truyen thong (TRUYENTHONG)
    "TT_TTDT":     ("TRUYENTHONG", "Tin/bài - Cổng TTĐT Chi cục", "tin bài", "SO_NGUYEN", False),
    "TT_DDCIQN":   ("TRUYENTHONG", "Tin/bài - Fanpage DDCI Quảng Ninh", "tin bài", "SO_NGUYEN", False),
    "TT_DDCICC":   ("TRUYENTHONG", "Tin/bài - Fanpage DDCI Chi cục", "tin bài", "SO_NGUYEN", False),
    "TT_ISEC":     ("TRUYENTHONG", "Tin/bài - ISEC", "tin bài", "SO_NGUYEN", False),
}

# Ten chi tieu trong CSV -> ma_chi_tieu (cac muc PD cua Thue/KTSTQ deu tro ve 1 ma)
TEN_CSV_TO_MA = {
    "Tăng kim ngạch XNK (không gồm KNQ, TNTX)": "GSQL_KNXNK",
    "Tăng doanh nghiệp làm thủ tục": "GSQL_TANGDN",
    "Hội nghị đối thoại, tham vấn": "GSQL_HNDT",
    "Rà soát, đề xuất cắt giảm TTHC": "GSQL_RSTTHC",
    "Phát hiện vi phạm SHTT/hàng giả": "GSQL_SHTT",
    "Đề xuất cung cấp thông tin KTSTQ": "GSQL_CCKTSTQ",
    "Số thu thuế XNK (pháp lệnh 18.300 tỷ)": "THUE_STHU",
    "Số thu thuế XNK (phấn đấu 25.000 tỷ)": "THUE_STHU",
    "Số cuộc kiểm tra STQ": "KTSTQ_SOCUOC",
    "Số thu NSNN (KTSTQ)": "KTSTQ_STHU",
    "Tỷ lệ phát hiện vi phạm KTSTQ": "KTSTQ_TLVP",
    "Phiếu cung cấp thông tin KTSTQ": "KTSTQ_PHIEU",
    "Số lớp tập huấn": "DAOTAO_SOLOP",
    "Số lượt người tham gia tập huấn": "DAOTAO_LUOT",
    "Số hồ sơ DN trọng điểm": "QLRR_HOSO",
    "Số tiêu chí phân tích (doanh nghiệp)": "QLRR_TCDN",
    "Số tiêu chí phân tích (mặt hàng)": "QLRR_TCMH",
    "Số lượng DN được giao thu (Cục HQ giao)": "QLRR_DNCUC",
    "Số lượng DN giao thu (Chi cục giao)": "QLRR_DNCC",
    "Số vụ chủ trì bắt giữ": "CBL_CHUTRI",
    "Số vụ phối hợp bắt giữ": "CBL_PHOIHOP",
    "Tổng trị giá chủ trì bắt giữ": "CBL_TRIGIA",
    "Số thu NSNN từ xử phạt VPHC": "CBL_XUPHAT",
    "HQ khởi tố (vụ)": "CBL_KHOITO",
    "Tin/bài - Cổng TTĐT Chi cục": "TT_TTDT",
    "Tin/bài - Fanpage DDCI Quảng Ninh": "TT_DDCIQN",
    "Tin/bài - Fanpage DDCI Chi cục": "TT_DDCICC",
    "Tin/bài - ISEC": "TT_ISEC",
}

# Danh muc MAU cu can vo hieu hoa
MA_MAU_CU = ["GSQL_01", "GSQL_02", "GSQL_03", "THUE_01", "KTSTQ_01", "KTSTQ_02",
             "DAOTAO_01", "QLRR_01", "CBL_01", "CBL_02", "TT_01"]


def gia_tri_tu_row(row) -> float | None:
    """Lay gia tri giao nam tu 1 dong CSV, ap dung quy tac chinh sua."""
    num = row["gia_tri_giao_num"].strip()
    if num:
        return float(num)
    raw = row["gia_tri_giao_raw"].strip()
    # "Tang doanh nghiep": lay so dau (2227 DN..., 151 DN...)
    if row["chi_tieu"] == "Tăng doanh nghiệp làm thủ tục":
        m = re.match(r"^\s*([0-9]+(?:[.,][0-9]+)?)", raw)
        if m:
            return float(m.group(1).replace(",", "."))
    # con lai (Tang 11%, Khong dang ky, ...) -> bo qua
    return None


async def run(confirm: bool):
    rows = list(csv.DictReader(open(CSV, encoding="utf-8-sig")))

    # Gom giao_nam: (ma_chi_tieu, ma_don_vi, loai_muc) -> gia tri
    giao = []
    bo_qua = []
    for r in rows:
        ma_ct = TEN_CSV_TO_MA.get(r["chi_tieu"])
        ma_dv = r["ma_don_vi"].strip()
        if not ma_ct or not ma_dv:
            bo_qua.append((r["chi_tieu"], r["don_vi_excel"], "thiếu mã")); continue
        val = gia_tri_tu_row(r)
        if val is None:
            bo_qua.append((r["chi_tieu"], r["don_vi_excel"], f'bỏ "{r["gia_tri_giao_raw"]}"')); continue
        giao.append((ma_ct, ma_dv, r["loai_muc"], val))

    print(f"Danh mục chỉ tiêu: {len(CATALOG)} | giao_nam hợp lệ: {len(giao)} | bỏ qua: {len(bo_qua)}")
    if bo_qua:
        print("  Bỏ qua:")
        for ct, dv, ly in bo_qua:
            print(f"    - [{dv}] {ct[:38]} → {ly}")

    if not confirm:
        print("\n⚠️ DRY-RUN (chưa ghi). Chạy lại với --confirm để nạp vào DB.")
        print(f"   DB đích: host={settings.db_host} db={settings.db_name}")
        return

    engine = create_async_engine(settings.database_url, echo=False)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as db:
        # 1. Map ma_linh_vuc -> id ; ma_don_vi -> id
        lv = {r[1]: r[0] for r in (await db.execute(text(
            "SELECT id, ma_linh_vuc FROM chi_tieu.linh_vuc"))).fetchall()}
        dv = {r[1]: r[0] for r in (await db.execute(text(
            "SELECT id, ma_don_vi FROM public.don_vi"))).fetchall()}

        # 2. Vo hieu hoa danh muc mau cu
        await db.execute(text("""
            UPDATE chi_tieu.danh_muc_chi_tieu SET is_active = FALSE, updated_at = CURRENT_TIMESTAMP
            WHERE ma_chi_tieu = ANY(:ma)
        """), {"ma": MA_MAU_CU})

        # 3. Upsert danh muc that
        for ma, (lv_ma, ten, dvt, kieu, cpd) in CATALOG.items():
            await db.execute(text("""
                INSERT INTO chi_tieu.danh_muc_chi_tieu
                    (linh_vuc_id, ma_chi_tieu, ten_chi_tieu, don_vi_tinh, kieu_du_lieu, co_phan_dau, is_active)
                VALUES (:lv, :ma, :ten, :dvt, :kieu, :cpd, TRUE)
                ON CONFLICT (ma_chi_tieu) DO UPDATE SET
                    linh_vuc_id = EXCLUDED.linh_vuc_id, ten_chi_tieu = EXCLUDED.ten_chi_tieu,
                    don_vi_tinh = EXCLUDED.don_vi_tinh, kieu_du_lieu = EXCLUDED.kieu_du_lieu,
                    co_phan_dau = EXCLUDED.co_phan_dau, is_active = TRUE, updated_at = CURRENT_TIMESTAMP
            """), {"lv": lv[lv_ma], "ma": ma, "ten": ten, "dvt": dvt, "kieu": kieu, "cpd": cpd})

        # map ma_chi_tieu -> id (sau upsert)
        ct = {r[1]: r[0] for r in (await db.execute(text(
            "SELECT id, ma_chi_tieu FROM chi_tieu.danh_muc_chi_tieu"))).fetchall()}

        # 4. Upsert giao_nam
        n = 0
        for ma_ct, ma_dv, loai, val in giao:
            if ma_dv not in dv:
                continue
            await db.execute(text("""
                INSERT INTO chi_tieu.giao_nam
                    (don_vi_id, chi_tieu_id, nam, loai_muc, gia_tri_giao, ghi_chu)
                VALUES (:dv, :ct, :nam, :loai, :val, 'Seed từ Excel rà soát T4.2026')
                ON CONFLICT (don_vi_id, chi_tieu_id, nam, loai_muc) DO UPDATE SET
                    gia_tri_giao = EXCLUDED.gia_tri_giao, is_deleted = FALSE,
                    updated_at = CURRENT_TIMESTAMP
            """), {"dv": dv[ma_dv], "ct": ct[ma_ct], "nam": NAM, "loai": loai, "val": val})
            n += 1
        await db.commit()
    await engine.dispose()
    print(f"\n✓ Đã nạp: {len(CATALOG)} chỉ tiêu (vô hiệu {len(MA_MAU_CU)} mẫu cũ) + {n} dòng giao_nam.")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--confirm", action="store_true", help="GHI vào DB (mặc định dry-run)")
    args = p.parse_args()
    asyncio.run(run(args.confirm))


if __name__ == "__main__":
    main()
