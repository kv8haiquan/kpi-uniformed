"""
backend/scripts/migrate_kq_diem_to_percent.py
================================================
Migration mot lan: chuan hoa `lms.ket_qua_bai_kiem_tra.diem` tu DIEM THO ve %.

Ly do:
  - Code cu (bai_kiem_tra_service.py:734) luu `kq.diem = tong_diem` (raw),
    vd: bai 30 cau x 1d, hoc vien dung 25 cau → kq.diem = 25 (thay vi 83.33).
  - Code da fix → tu nay kq.diem = phan_tram (thang 100).
  - Du lieu cu can backfill: tinh lai phan_tram tu chi_tiet_tra_loi (JSONB) —
    mỗi cau co `diem_dat` va `diem_toi_da` san — sum ra ty le %.

Pham vi:
  - Chi tac dong KQ co `chi_tiet_tra_loi NOT NULL` (= bai trac nghiem da nop tu cham).
  - Bo qua bai THUC_HANH (giang vien cham tay, da nhap %).
  - Sau khi update KQ, tinh lai chung_chi.diem_dat = max(KQ.diem) tuong ung khoa hoc.

Usage (chay tu thu muc backend/):
    venv/bin/python -m scripts.migrate_kq_diem_to_percent              # dry-run
    venv/bin/python -m scripts.migrate_kq_diem_to_percent --apply      # thuc su UPDATE DB

Backup truoc khi --apply:
    pg_dump --schema=lms ... > backups/lms_schema_<ts>.sql
"""

import argparse
import asyncio
import sys
from collections import defaultdict
from decimal import Decimal

from sqlalchemy import select, update, func

from lms_service.config import settings
from lms_service.models.bai_kiem_tra import BaiKiemTra
from lms_service.models.chung_chi import ChungChi
from lms_service.models.dang_ky_khoa_hoc import DangKyKhoaHoc
from lms_service.models.ket_qua_bai_kiem_tra import KetQuaBaiKiemTra
from lms_service.models.khoa_hoc import KhoaHoc
from shared.database import create_db_engine, create_session_factory


def percent_from_chi_tiet(chi_tiet) -> Decimal | None:
    """Tinh phan tram tu chi_tiet_tra_loi (JSONB list of {diem_dat, diem_toi_da})."""
    if not chi_tiet or not isinstance(chi_tiet, list):
        return None
    sum_dat = Decimal("0")
    sum_max = Decimal("0")
    for c in chi_tiet:
        try:
            sum_dat += Decimal(str(c.get("diem_dat", 0) or 0))
            sum_max += Decimal(str(c.get("diem_toi_da", 0) or 0))
        except Exception:
            continue
    if sum_max == 0:
        return None
    return (sum_dat / sum_max * Decimal("100")).quantize(Decimal("0.01"))


async def main():
    parser = argparse.ArgumentParser(description="Chuan hoa kq.diem ve %.")
    parser.add_argument("--apply", action="store_true", help="Thuc su UPDATE DB.")
    args = parser.parse_args()
    apply_mode = args.apply

    print("=" * 70)
    print(f"  MODE:  {'APPLY (UPDATE DB)' if apply_mode else 'DRY-RUN (read-only)'}")
    print(f"  DB:    {settings.db_host}:{settings.db_port}/{settings.db_name}")
    print("=" * 70)

    if apply_mode:
        print("\nCANH BAO: Sap UPDATE production DB.")
        print("Hay chac chan ban da pg_dump backup truoc.\n")

    engine = create_db_engine(settings.database_url)
    factory = create_session_factory(engine)

    kq_changed = 0
    kq_unchanged = 0
    kq_skipped_no_chi_tiet = 0
    kq_skipped_thuc_hanh = 0
    cc_changed = 0
    cc_unchanged = 0

    try:
        async with factory() as db:
            # ===================================================================
            # PHAN 1: KetQuaBaiKiemTra trac nghiem
            # ===================================================================
            print("\n[1/2] KetQuaBaiKiemTra — chuan hoa diem...")

            stmt = (
                select(
                    KetQuaBaiKiemTra.id,
                    KetQuaBaiKiemTra.diem,
                    KetQuaBaiKiemTra.chi_tiet_tra_loi,
                    BaiKiemTra.loai_bai_kiem_tra,
                    BaiKiemTra.tieu_de,
                )
                .join(BaiKiemTra, KetQuaBaiKiemTra.bai_kiem_tra_id == BaiKiemTra.id)
                .order_by(KetQuaBaiKiemTra.lan_thu.asc())
            )
            rows = (await db.execute(stmt)).all()
            print(f"  Tong ket qua: {len(rows)}")

            updates = []  # list of (id, new_diem) for chung_chi step
            for r in rows:
                if r.loai_bai_kiem_tra == "THUC_HANH":
                    kq_skipped_thuc_hanh += 1
                    continue
                if not r.chi_tiet_tra_loi:
                    kq_skipped_no_chi_tiet += 1
                    continue

                new_diem = percent_from_chi_tiet(r.chi_tiet_tra_loi)
                if new_diem is None:
                    kq_skipped_no_chi_tiet += 1
                    continue

                old_diem = r.diem
                if old_diem is not None and abs(Decimal(old_diem) - new_diem) < Decimal("0.01"):
                    kq_unchanged += 1
                    continue

                updates.append((r.id, new_diem))
                kq_changed += 1
                if kq_changed <= 10 or kq_changed % 20 == 0:
                    print(f"    KQ {r.id}: diem {old_diem} → {new_diem}  ({r.tieu_de[:40]})")

            print(f"\n  Will update: {kq_changed}")
            print(f"  Unchanged:   {kq_unchanged}")
            print(f"  Skipped (THUC_HANH): {kq_skipped_thuc_hanh}")
            print(f"  Skipped (no chi_tiet): {kq_skipped_no_chi_tiet}")

            # Update KQ trong transaction (du dry-run hay apply) — de phan 2 thay state moi.
            # Cuoi cung rollback neu dry-run, commit neu apply.
            if updates:
                print(f"\n  Updating {len(updates)} KQ trong transaction...")
                for kq_id, new_diem in updates:
                    await db.execute(
                        update(KetQuaBaiKiemTra)
                        .where(KetQuaBaiKiemTra.id == kq_id)
                        .values(diem=new_diem)
                    )
                await db.flush()

            # ===================================================================
            # PHAN 2: chung_chi.diem_dat = max(kq.diem) tuong ung khoa
            # ===================================================================
            print("\n[2/2] chung_chi.diem_dat — tinh lai tu max(KQ.diem) moi...")

            # Lay tat ca cert + dang_ky de biet hoc vien nao
            cc_stmt = (
                select(
                    ChungChi.id,
                    ChungChi.cong_chuc_id,
                    ChungChi.khoa_hoc_id,
                    ChungChi.ma_chung_chi,
                    ChungChi.diem_dat,
                )
                .order_by(ChungChi.ngay_cap.asc())
            )
            certs = (await db.execute(cc_stmt)).all()
            print(f"  Tong cert: {len(certs)}")

            for cc in certs:
                # Kiem tra khoa co BKT khong
                bkt_count = (await db.execute(
                    select(func.count(BaiKiemTra.id)).where(
                        BaiKiemTra.khoa_hoc_id == cc.khoa_hoc_id,
                        BaiKiemTra.is_active == True,  # noqa: E712
                    )
                )).scalar() or 0

                if bkt_count == 0:
                    # Khoa khong co BKT → diem_tong_ket = 100 (giu nguyen)
                    new_diem = Decimal("100")
                else:
                    best = (await db.execute(
                        select(func.max(KetQuaBaiKiemTra.diem))
                        .join(BaiKiemTra, KetQuaBaiKiemTra.bai_kiem_tra_id == BaiKiemTra.id)
                        .where(
                            KetQuaBaiKiemTra.cong_chuc_id == cc.cong_chuc_id,
                            BaiKiemTra.khoa_hoc_id == cc.khoa_hoc_id,
                            KetQuaBaiKiemTra.dat_yeu_cau == True,  # noqa: E712
                        )
                    )).scalar()
                    new_diem = best if best is not None else cc.diem_dat or Decimal("0")

                old_diem = cc.diem_dat or Decimal("0")
                new_diem = Decimal(str(new_diem)).quantize(Decimal("0.01"))

                if abs(old_diem - new_diem) < Decimal("0.01"):
                    cc_unchanged += 1
                    continue

                cc_changed += 1
                if cc_changed <= 20 or cc_changed % 10 == 0:
                    print(f"    CC {cc.ma_chung_chi}: diem_dat {old_diem} → {new_diem}")

                # Always update trong transaction; rollback neu dry-run.
                await db.execute(
                    update(ChungChi)
                    .where(ChungChi.id == cc.id)
                    .values(diem_dat=new_diem)
                )

            print(f"\n  Will update: {cc_changed}")
            print(f"  Unchanged:   {cc_unchanged}")

            # ===================================================================
            # COMMIT
            # ===================================================================
            if apply_mode:
                await db.commit()
                print("\n✓ COMMITTED.")
            else:
                await db.rollback()
                print("\n(Dry-run — rolled back.)")

    finally:
        await engine.dispose()

    print()
    print("=" * 70)
    print(f"  KetQuaBaiKiemTra:  changed={kq_changed}  unchanged={kq_unchanged}")
    print(f"                     skipped THUC_HANH={kq_skipped_thuc_hanh}, no_chi_tiet={kq_skipped_no_chi_tiet}")
    print(f"  chung_chi:         changed={cc_changed}  unchanged={cc_unchanged}")
    if not apply_mode:
        print("\n  (DRY-RUN — DB khong bi UPDATE.)")
        print("  De thuc hien, chay lai voi --apply.")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
