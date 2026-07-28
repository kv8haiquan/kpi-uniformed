"""
Clear (xoa mem) + Import bo de DGNL moi cho 11 linh vuc so "1" -> "11".
========================================================================
- Doc 11 file "(viet lai)" trong docs/Bo de DGNL/.
- Ghi de cot linh_vuc theo THU MUC (so 1..11) -> ma_linh_vuc chinh thuc trong DB.
- Che do:
    DRY-RUN (mac dinh): chi doc, in bang doi chieu, KHONG ghi DB.
    EXECUTE (EXEC=1):    trong 1 transaction:
        1) xoa mem (is_active=false) toan bo cau active thuoc 11 linh vuc dich
        2) insert cau hoi moi
        3) verify roi COMMIT.

Chay DRY-RUN:  cd backend && ./venv/bin/python scripts/import_bo_de_dgnl_2026.py
Chay EXECUTE:  cd backend && EXEC=1 ./venv/bin/python scripts/import_bo_de_dgnl_2026.py
"""

import asyncio
import glob
import os
import re
import uuid
from decimal import Decimal

import openpyxl
from sqlalchemy import select, func, update, insert

from lms_service.dependencies import session_factory
from lms_service.models.cau_hoi_dgnl import CauHoiDgnl
from lms_service.models.linh_vuc import LinhVuc
from lms_service.services.cau_hoi_dgnl_service import CauHoiDgnlService

BODE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "docs", "Bộ đề DGNL")

# Thu muc so N -> ma_linh_vuc dich trong DB (bo chinh thuc "1"->"11")
FOLDER_TO_MA = {
    1: "1. LHQ", 2: "2. LTXNK", 3: "3. LQLT", 4: "4. LXLVPHC", 5: "5. LCBCC",
    6: "6. QCLV", 7: "7. QCCV", 8: "8. LCDS", 9: "9. STVB", 10: "10.TA", 11: "11. TT",
}

LOAI_VALID = {"TRAC_NGHIEM_1", "TRAC_NGHIEM_NHIEU", "DUNG_SAI", "TU_LUAN"}
DO_KHO_VALID = {"DE", "TRUNG_BINH", "KHO"}

EXEC = os.getenv("EXEC") == "1"


def _folder_num(name: str):
    m = re.match(r"\s*(\d+)", name)
    return int(m.group(1)) if m else None


def _read_vietlai(folder_path: str):
    """Tra ve list dict (moi dong 1 cau hoi) tu file '(viet lai)' trong folder."""
    cands = [f for f in glob.glob(os.path.join(folder_path, "*viết lại*.xlsx"))
             if "~$" not in os.path.basename(f)]
    if not cands:
        return None, []
    fpath = sorted(cands)[0]
    wb = openpyxl.load_workbook(fpath, read_only=True, data_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    wb.close()
    if not rows:
        return fpath, []
    headers = [str(h).strip().lower().replace(" ", "_") if h is not None else f"col_{i}"
               for i, h in enumerate(rows[0])]
    out = []
    for r in rows[1:]:
        d = {headers[i]: (str(v).strip() if v is not None else "")
             for i, v in enumerate(r) if i < len(headers)}
        if any(v for v in d.values()):
            out.append(d)
    return fpath, out


def _parse_row(row: dict, ma_lv_target: str, lv_id: uuid.UUID):
    """Validate + build 1 dict san sang insert. Raise ValueError neu loi."""
    noi_dung = (row.get("noi_dung") or "").strip()
    if not noi_dung:
        raise ValueError("thiếu noi_dung")
    loai = (row.get("loai") or "TRAC_NGHIEM_1").strip().upper()
    if loai not in LOAI_VALID:
        raise ValueError(f"loai '{loai}' không hợp lệ")
    do_kho = (row.get("do_kho") or "TRUNG_BINH").strip().upper()
    if do_kho not in DO_KHO_VALID:
        raise ValueError(f"do_kho '{do_kho}' không hợp lệ")
    # dung dung logic parse cua service de format dap_an giong het app
    dap_an = CauHoiDgnlService._parse_dap_an(None, row, loai)
    try:
        diem = Decimal(str(float(row.get("diem") or 1)))
    except Exception:
        diem = Decimal("1")
    giai_thich = (row.get("giai_thich") or "").strip() or None
    return {
        "linh_vuc_id": lv_id,
        "noi_dung": noi_dung,
        "giai_thich": giai_thich,
        "loai": loai,
        "dap_an": dap_an,
        "diem": diem,
        "do_kho": do_kho,
        "nguoi_tao_id": None,  # import he thong
        "is_active": True,
    }


async def main():
    async with session_factory() as db:
        # 1) Resolve linh_vuc_id cho 11 ma dich
        lv_rows = (await db.execute(select(LinhVuc))).scalars().all()
        ma_to_id = {lv.ma_linh_vuc: lv.id for lv in lv_rows}
        missing = [ma for ma in FOLDER_TO_MA.values() if ma not in ma_to_id]
        if missing:
            print("❌ Thiếu lĩnh vực trong DB:", missing)
            return

        target_ids = [ma_to_id[ma] for ma in FOLDER_TO_MA.values()]

        # 2) Doc + parse 11 file
        folders = sorted(
            [d for d in os.listdir(BODE_DIR) if os.path.isdir(os.path.join(BODE_DIR, d))],
            key=lambda x: (_folder_num(x) or 999),
        )
        all_new = []
        print(f"{'Lĩnh vực dích':<28}{'File':<8}{'Parse OK':>9}{'Lỗi':>6}{'Cũ(active)':>12}")
        print("-" * 70)
        total_ok = total_err = total_old = 0
        errors_sample = []
        for fname in folders:
            num = _folder_num(fname)
            if num not in FOLDER_TO_MA:
                continue
            ma_target = FOLDER_TO_MA[num]
            lv_id = ma_to_id[ma_target]
            fpath, rows = _read_vietlai(os.path.join(BODE_DIR, fname))
            ok = err = 0
            for i, row in enumerate(rows, 2):
                try:
                    all_new.append(_parse_row(row, ma_target, lv_id))
                    ok += 1
                except ValueError as e:
                    err += 1
                    if len(errors_sample) < 10:
                        errors_sample.append(f"  [{fname}] dòng {i}: {e}")
            old_active = (await db.execute(
                select(func.count(CauHoiDgnl.id)).where(
                    CauHoiDgnl.linh_vuc_id == lv_id, CauHoiDgnl.is_active == True
                )
            )).scalar() or 0
            total_ok += ok; total_err += err; total_old += old_active
            fbase = os.path.basename(fpath) if fpath else "(KHÔNG THẤY FILE)"
            print(f"{ma_target:<28}{'':<8}{ok:>9}{err:>6}{old_active:>12}   {fbase[:40]}")
        print("-" * 70)
        print(f"{'TỔNG':<28}{'':<8}{total_ok:>9}{total_err:>6}{total_old:>12}")
        if errors_sample:
            print("\nMẫu lỗi:")
            print("\n".join(errors_sample))

        print(f"\n➡️  Sẽ XÓA MỀM {total_old} câu cũ (active) và THÊM {total_ok} câu mới vào 11 lĩnh vực.")

        if not EXEC:
            print("\n🔸 DRY-RUN — KHÔNG ghi DB. Chạy lại với EXEC=1 để thực thi.")
            return

        # 3) EXECUTE trong 1 transaction
        print("\n⏳ Đang ghi DB (transaction)...")
        # 3a) Xoa mem cau cu active
        res_del = await db.execute(
            update(CauHoiDgnl)
            .where(CauHoiDgnl.linh_vuc_id.in_(target_ids), CauHoiDgnl.is_active == True)
            .values(is_active=False)
            .execution_options(synchronize_session=False)
        )
        so_xoa = res_del.rowcount or 0
        # 3b) Insert cau moi
        if all_new:
            await db.execute(insert(CauHoiDgnl), all_new)
        # 3c) Verify truoc khi commit
        so_active_moi = (await db.execute(
            select(func.count(CauHoiDgnl.id)).where(
                CauHoiDgnl.linh_vuc_id.in_(target_ids), CauHoiDgnl.is_active == True
            )
        )).scalar() or 0
        print(f"   Đã xóa mềm: {so_xoa} | Thêm mới: {len(all_new)} | Active sau (11 lĩnh vực): {so_active_moi}")
        if so_active_moi != len(all_new):
            print("❌ Số active sau khác số thêm mới → ROLLBACK để an toàn.")
            await db.rollback()
            return
        await db.commit()
        print("✅ COMMIT thành công.")


if __name__ == "__main__":
    asyncio.run(main())
