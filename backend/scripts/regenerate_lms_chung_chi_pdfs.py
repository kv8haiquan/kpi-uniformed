"""
backend/scripts/regenerate_lms_chung_chi_pdfs.py
==================================================
Re-sinh PDF chung chi LMS de fix bug "KHONG DAT" tren cert da cap.

Bug cu (da fix):
  - lms_service/services/chung_chi_pdf.py: ham xep_loai_label() tra "KHÔNG ĐẠT"
    cho diem < 50 → cert co diem 30 (vd: BKT thuc hanh threshold 30) hien thi sai.
  - lms_service/schemas/chung_chi.py: tinh_xep_loai() tuong tu.
Fix da apply: tier thap nhat la "ĐẠT" (cert chi cap khi hoc vien da pass).

Script nay re-sinh PDF cho TAT CA cert da cap, dung lai logic moi (import truc tiep
generate_certificate_pdf — so co ban update). Khong update DB (diem_dat khong doi).

Usage (chay tu thu muc backend/):
    venv/bin/python -m scripts.regenerate_lms_chung_chi_pdfs                # dry-run
    venv/bin/python -m scripts.regenerate_lms_chung_chi_pdfs --apply        # ghi de that
    venv/bin/python -m scripts.regenerate_lms_chung_chi_pdfs --apply --limit 1
    venv/bin/python -m scripts.regenerate_lms_chung_chi_pdfs --apply --ma CC-2026-000020

Khuyen cao: backup truoc khi chay --apply
    cp -r uploads/lms/chung-chi uploads/lms/chung-chi.bak.$(date +%Y%m%d-%H%M%S)
"""

import argparse
import asyncio
import os
import sys
from typing import Optional

from sqlalchemy import select

from lms_service.config import settings
from lms_service.models.base import CongChucRef, DonViRef
from lms_service.models.chung_chi import ChungChi
from lms_service.models.khoa_hoc import KhoaHoc
from lms_service.services.chung_chi_pdf import generate_certificate_pdf
from shared.database import create_db_engine, create_session_factory


async def fetch_certs(db, ma_filter: Optional[str] = None):
    cc = CongChucRef.__table__.alias("cc")
    dv = DonViRef.__table__.alias("dv")

    stmt = (
        select(
            ChungChi.id,
            ChungChi.ma_chung_chi,
            ChungChi.diem_dat,
            ChungChi.ngay_cap,
            ChungChi.file_url,
            cc.c.ho_ten,
            cc.c.ma_cc,
            dv.c.ten_don_vi,
            KhoaHoc.ten_khoa_hoc,
        )
        .join(cc, ChungChi.cong_chuc_id == cc.c.id)
        .outerjoin(dv, cc.c.don_vi_id == dv.c.id)
        .join(KhoaHoc, ChungChi.khoa_hoc_id == KhoaHoc.id)
        .order_by(ChungChi.ngay_cap.asc())
    )
    if ma_filter:
        stmt = stmt.where(ChungChi.ma_chung_chi == ma_filter)

    res = await db.execute(stmt)
    return res.all()


def cert_path(year: int, ma_chung_chi: str) -> str:
    rel = f"chung-chi/{year}/{ma_chung_chi}.pdf"
    return os.path.join(settings.upload_dir, rel)


async def main():
    parser = argparse.ArgumentParser(
        description="Re-sinh PDF chung chi LMS (fix bug KHONG DAT).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Thuc su ghi de PDF (mac dinh la dry-run, KHONG ghi).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Chi xu ly N cert dau tien (test).",
    )
    parser.add_argument(
        "--ma",
        type=str,
        default=None,
        help="Chi xu ly mot cert co ma cu the (vd: CC-2026-000020).",
    )
    args = parser.parse_args()

    apply_mode = args.apply

    print("=" * 70)
    print(f"  MODE:   {'APPLY (SE GHI DE FILE)' if apply_mode else 'DRY-RUN (khong ghi)'}")
    print(f"  DB:     {settings.db_host}:{settings.db_port}/{settings.db_name}")
    print(f"  DIR:    {os.path.abspath(settings.upload_dir)}")
    print(f"  CWD:    {os.getcwd()}")
    if args.ma:
        print(f"  FILTER: ma_chung_chi = {args.ma}")
    if args.limit:
        print(f"  LIMIT:  {args.limit} cert dau tien")
    print("=" * 70)

    if apply_mode:
        print("\nCANH BAO: Sap ghi de file PDF chung chi tren disk.")
        print("Hay chac chan ban da backup folder uploads/lms/chung-chi/")
        print("    cp -r uploads/lms/chung-chi uploads/lms/chung-chi.bak.$(date +%s)")
        print()

    engine = create_db_engine(settings.database_url)
    factory = create_session_factory(engine)

    ok = 0
    fail = 0
    failures = []
    total = 0

    try:
        async with factory() as db:
            rows = await fetch_certs(db, args.ma)
            if args.limit:
                rows = rows[: args.limit]
            total = len(rows)

            if total == 0:
                print("Khong tim thay cert nao.")
                return

            print(f"Tim thay {total} cert. Bat dau xu ly...\n")

            for i, row in enumerate(rows, 1):
                ma = row.ma_chung_chi
                ngay = row.ngay_cap
                year = ngay.year if ngay else 2026
                path = cert_path(year, ma)
                head = f"[{i:>3}/{total}] {ma} | diem={row.diem_dat} | {row.ho_ten}"

                try:
                    pdf_bytes = generate_certificate_pdf(
                        ma_chung_chi=ma,
                        ho_ten=row.ho_ten or "",
                        ma_cc=row.ma_cc or "",
                        ten_khoa_hoc=row.ten_khoa_hoc or "",
                        diem_dat=row.diem_dat or 0,
                        ngay_cap=ngay,
                        don_vi=row.ten_don_vi,
                    )

                    if apply_mode:
                        os.makedirs(os.path.dirname(path), exist_ok=True)
                        with open(path, "wb") as f:
                            f.write(pdf_bytes)
                        print(f"{head} -> WRITTEN ({len(pdf_bytes):>6} B)  {path}")
                    else:
                        print(f"{head} -> WOULD WRITE ({len(pdf_bytes):>6} B)  {path}")
                    ok += 1
                except Exception as e:
                    fail += 1
                    failures.append((ma, str(e)))
                    print(f"{head} -> FAILED: {e}")
    finally:
        await engine.dispose()

    print()
    print("=" * 70)
    print(f"  DONE.  OK={ok}  FAILED={fail}  TOTAL={total}")
    if failures:
        print("\n  Failures:")
        for ma, err in failures:
            print(f"    - {ma}: {err}")
    if not apply_mode:
        print()
        print("  (DRY-RUN — khong file nao bi ghi de.)")
        print("  De thuc hien, chay lai voi flag --apply.")
    print("=" * 70)

    if fail > 0:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
