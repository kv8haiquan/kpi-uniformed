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

IDEMPOTENT: ON CONFLICT DO NOTHING theo ma_linh_vuc / ma_chi_tieu — chay nhieu lan an toan.

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


# 7 linh vuc (ma, ten, van ban ke hoach, thu tu)
LINH_VUC = [
    ("GSQL", "Giam sat quan ly", "KH 24/KH-HQKV8", 1),
    ("THUE", "Thue XNK", "KH 306, KH 1342", 2),
    ("KTSTQ", "Kiem tra sau thong quan", "KH 251, CV 851", 3),
    ("DAOTAO", "Dao tao, tap huan", "KH 91", 4),
    ("QLRR", "Quan ly rui ro", "QD 51, QD 56", 5),
    ("CBL", "Kiem soat chong buon lau", "KH 15", 6),
    ("TRUYENTHONG", "Truyen thong", None, 7),
]

# Bo chi tieu mau (ma_linh_vuc, ma_chi_tieu, ten, don_vi_tinh, kieu_du_lieu, co_phan_dau, thu_tu)
CHI_TIEU = [
    ("GSQL", "GSQL_01", "Kim ngach XNK (khong gom KNQ, TNTX)", "trieu USD", "THAP_PHAN", False, 1),
    ("GSQL", "GSQL_02", "So to khai", "to khai", "SO_NGUYEN", False, 2),
    ("GSQL", "GSQL_03", "So doanh nghiep lam thu tuc", "doanh nghiep", "SO_NGUYEN", False, 3),
    ("THUE", "THUE_01", "So thu thue XNK", "ty dong", "THAP_PHAN", True, 1),
    ("KTSTQ", "KTSTQ_01", "So thu KTSTQ", "trieu dong", "THAP_PHAN", True, 1),
    ("KTSTQ", "KTSTQ_02", "So cuoc KTSTQ", "cuoc", "SO_NGUYEN", False, 2),
    ("DAOTAO", "DAOTAO_01", "So hoi nghi/lop tap huan", "hoi nghi", "SO_NGUYEN", False, 1),
    ("QLRR", "QLRR_01", "Ty le to khai luong xanh", "%", "PHAN_TRAM", False, 1),
    ("CBL", "CBL_01", "So vu vi pham phat hien", "vu", "SO_NGUYEN", False, 1),
    ("CBL", "CBL_02", "Tri gia hang vi pham", "trieu dong", "THAP_PHAN", False, 2),
    ("TRUYENTHONG", "TT_01", "So tin/bai truyen thong", "tin bai", "SO_NGUYEN", False, 1),
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
                ON CONFLICT (ma_linh_vuc) DO NOTHING
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
                ON CONFLICT (ma_chi_tieu) DO NOTHING
            """), {"lv": lv_id, "ma": ma_ct, "ten": ten, "dvt": dvt, "kdl": kdl, "cpd": cpd, "tt": tt})
            n_ct += res.rowcount or 0

        await db.commit()
    await engine.dispose()
    print(f"✓ Seed xong: them moi {n_lv} linh vuc, {n_ct} chi tieu (cac ma da co bi bo qua).")


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
