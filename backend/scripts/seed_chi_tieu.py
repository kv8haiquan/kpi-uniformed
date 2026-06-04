#!/usr/bin/env python3
"""
scripts/seed_chi_tieu.py
========================
Nap danh muc khoi tao cho module Chi tieu don vi: 7 linh vuc + bo chi tieu mau.

CACH CHAY (CO GUARD AN TOAN):
    cd backend
    python scripts/seed_chi_tieu.py --confirm

YEU CAU:
    - Migration create_chi_tieu_schema_20260604 da chay (schema chi_tieu ton tai)
    - .env tro DUNG database muc tieu

⚠️ AN TOAN: script GHI du lieu. Bat buoc co co --confirm. Truoc khi ghi se in ro
   DB host/name de ban kiem tra — KHONG vo tinh seed nham production neu chua muon.

IDEMPOTENT: ON CONFLICT DO UPDATE theo ma_linh_vuc / ma_chi_tieu — chay lai se
cap nhat ten/don vi tinh/... cua cac ma da co (dung de sua noi dung danh muc mau).

Nguon: docs/Chi Tieu/CHI_TIEU_BUSINESS_RULES.md muc 1.1 + 2.2.
"""

import argparse
import asyncio
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from chi_tieu_service.config import settings


# 7 lĩnh vực (ma, tên, văn bản kế hoạch, thứ tự)
LINH_VUC = [
    ("GSQL", "Giám sát quản lý", "KH 24/KH-HQKV8", 1),
    ("THUE", "Thuế XNK", "KH 306, KH 1342", 2),
    ("KTSTQ", "Kiểm tra sau thông quan", "KH 251, CV 851", 3),
    ("DAOTAO", "Đào tạo, tập huấn", "KH 91", 4),
    ("QLRR", "Quản lý rủi ro", "QĐ 51, QĐ 56", 5),
    ("CBL", "Kiểm soát chống buôn lậu", "KH 15", 6),
    ("TRUYENTHONG", "Truyền thông", None, 7),
]

# Bộ chỉ tiêu mẫu (ma_linh_vuc, ma_chi_tieu, tên, đơn vị tính, kiểu dữ liệu, có phấn đấu, thứ tự)
CHI_TIEU = [
    ("GSQL", "GSQL_01", "Kim ngạch XNK (không gồm KNQ, TNTX)", "triệu USD", "THAP_PHAN", False, 1),
    ("GSQL", "GSQL_02", "Số tờ khai", "tờ khai", "SO_NGUYEN", False, 2),
    ("GSQL", "GSQL_03", "Số doanh nghiệp làm thủ tục", "doanh nghiệp", "SO_NGUYEN", False, 3),
    ("THUE", "THUE_01", "Số thu thuế XNK", "tỷ đồng", "THAP_PHAN", True, 1),
    ("KTSTQ", "KTSTQ_01", "Số thu KTSTQ", "triệu đồng", "THAP_PHAN", True, 1),
    ("KTSTQ", "KTSTQ_02", "Số cuộc KTSTQ", "cuộc", "SO_NGUYEN", False, 2),
    ("DAOTAO", "DAOTAO_01", "Số hội nghị/lớp tập huấn", "hội nghị", "SO_NGUYEN", False, 1),
    ("QLRR", "QLRR_01", "Tỷ lệ tờ khai luồng xanh", "%", "PHAN_TRAM", False, 1),
    ("CBL", "CBL_01", "Số vụ vi phạm phát hiện", "vụ", "SO_NGUYEN", False, 1),
    ("CBL", "CBL_02", "Trị giá hàng vi phạm", "triệu đồng", "THAP_PHAN", False, 2),
    ("TRUYENTHONG", "TT_01", "Số tin/bài truyền thông", "tin bài", "SO_NGUYEN", False, 1),
]


async def seed():
    engine = create_async_engine(settings.database_url, echo=False)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as db:
        # Linh vuc
        n_lv = 0
        for ma, ten, vb, tt in LINH_VUC:
            res = await db.execute(text("""
                INSERT INTO chi_tieu.linh_vuc (ma_linh_vuc, ten_linh_vuc, van_ban_ke_hoach, thu_tu)
                VALUES (:ma, :ten, :vb, :tt)
                ON CONFLICT (ma_linh_vuc) DO UPDATE SET
                    ten_linh_vuc = EXCLUDED.ten_linh_vuc,
                    van_ban_ke_hoach = EXCLUDED.van_ban_ke_hoach,
                    thu_tu = EXCLUDED.thu_tu,
                    updated_at = CURRENT_TIMESTAMP
            """), {"ma": ma, "ten": ten, "vb": vb, "tt": tt})
            n_lv += res.rowcount or 0

        # Map ma_linh_vuc -> id
        rows = (await db.execute(text("SELECT id, ma_linh_vuc FROM chi_tieu.linh_vuc"))).fetchall()
        lv_map = {r[1]: r[0] for r in rows}

        # Chi tieu
        n_ct = 0
        for ma_lv, ma_ct, ten, dvt, kdl, cpd, tt in CHI_TIEU:
            lv_id = lv_map.get(ma_lv)
            if not lv_id:
                print(f"  ! Bo qua {ma_ct}: chua co linh vuc {ma_lv}")
                continue
            res = await db.execute(text("""
                INSERT INTO chi_tieu.danh_muc_chi_tieu
                    (linh_vuc_id, ma_chi_tieu, ten_chi_tieu, don_vi_tinh, kieu_du_lieu, co_phan_dau, thu_tu)
                VALUES (:lv, :ma, :ten, :dvt, :kdl, :cpd, :tt)
                ON CONFLICT (ma_chi_tieu) DO UPDATE SET
                    ten_chi_tieu = EXCLUDED.ten_chi_tieu,
                    don_vi_tinh = EXCLUDED.don_vi_tinh,
                    kieu_du_lieu = EXCLUDED.kieu_du_lieu,
                    co_phan_dau = EXCLUDED.co_phan_dau,
                    thu_tu = EXCLUDED.thu_tu,
                    updated_at = CURRENT_TIMESTAMP
            """), {"lv": lv_id, "ma": ma_ct, "ten": ten, "dvt": dvt, "kdl": kdl, "cpd": cpd, "tt": tt})
            n_ct += res.rowcount or 0

        await db.commit()
    await engine.dispose()
    print(f"✓ Seed xong: xử lý {n_lv} lĩnh vực, {n_ct} chỉ tiêu (insert mới hoặc cập nhật theo mã).")


def main():
    parser = argparse.ArgumentParser(description="Seed danh muc Chi tieu don vi")
    parser.add_argument("--confirm", action="store_true", help="Bat buoc — xac nhan GHI vao DB")
    args = parser.parse_args()

    host = settings.db_host
    name = settings.db_name
    print("=" * 60)
    print(f"  DB muc tieu: host={host}  db={name}")
    print("=" * 60)
    if not args.confirm:
        print("⛔ Chua co --confirm. Script GHI du lieu nen can xac nhan.")
        print(f"   Neu host={host} la PRODUCTION, KHONG seed neu chua duoc duyet.")
        print("   Chay lai voi:  python scripts/seed_chi_tieu.py --confirm")
        sys.exit(1)

    asyncio.run(seed())


if __name__ == "__main__":
    main()
