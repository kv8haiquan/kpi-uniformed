#!/usr/bin/env python3
"""
scripts/fix_ngay_dieu_chuyen_2026.py
====================================
Sửa `lich_su_dieu_chuyen.ngay_hieu_luc` cho đúng NGÀY HIỆU LỰC của quyết định,
theo file `docs/Fix-dieu-chuyen-don-vi/BANG THEO DOI DIEU DONG 2026.xls`.

GỐC RỄ được vá:
    Form điều chuyển điền sẵn `ngay_hieu_luc = hôm nay`, và backend còn
    `payload.ngay_hieu_luc or date.today()` → 92/95 bản ghi có
    ngay_hieu_luc = created_at (NGÀY NHẬP LIỆU), không phải ngày QĐ.
    Đợt 15/5/2026 bị ghi thành 01–06/6; đợt 03/6 bị ghi thành 13–14/7;
    đợt 04/02 không có bản ghi nào.

BỐN THAO TÁC (theo đúng thứ tự):
    1. GỘP KHỨ HỒI  — người bị nhập sai rồi sửa bằng cách chuyển đi/chuyển lại
                      (2 dòng cùng chiều QĐ + 1 dòng chiều ngược) → giữ 1 dòng.
    2. SỬA NGÀY     — UPDATE ngay_hieu_luc về ngày trong QĐ.
    3. THÊM MỚI     — INSERT bản ghi cho đợt chưa từng vào hệ thống.
    4. (không đổi `cong_chuc.don_vi_id` — đơn vị hiện tại đã đúng 142/142)

Chạy:
    # xem trước, KHÔNG ghi gì (mặc định)
    python scripts/fix_ngay_dieu_chuyen_2026.py

    # ghi thật — LUÔN thử trên DB test trước
    DB_NAME=kpi_haiquan_test python scripts/fix_ngay_dieu_chuyen_2026.py --apply

⚠️ Script IDEMPOTENT: chạy lại lần 2 sẽ báo "không có gì để làm".
⚠️ Mọi thao tác nằm trong MỘT transaction; lỗi giữa đường là rollback sạch.
"""

import argparse
import asyncio
import re
import sys
import unicodedata
from datetime import date
from pathlib import Path
from typing import Optional

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.config import settings
from app.models import CongChuc, DonVi
from app.models.admin import LichSuDieuChuyen

# =============================================================================
# CẤU HÌNH — nguồn dữ liệu và các bảng tra
# =============================================================================

FILE_EXCEL = PROJECT_ROOT.parent / "docs" / "Fix-dieu-chuyen-don-vi" / "BANG THEO DOI DIEU DONG 2026.xls"
SHEET = "Lam QD 2026"

# Viết tắt đơn vị trong Excel → ma_don_vi trong DB
ABBR_TO_MA_DON_VI = {
    "TCCB": "TCCB",
    "VP": "VP",
    "CNTT": "CNTT",
    "NV": "NVHQ",
    "QLRR": "QLRR",
    "CP": "HQCK-CP",
    "HG": "HQCK-HG",
    "MC": "HQCK-MC",
    "HM": "HQCK-HM",
    "BPS": "HQCK-BPS",
    "VG": "HQCK-VG",
    "KTSTQ": "PTSTQ",
    "KS": "KSHQ",
}

# Chuỗi ngày trong Excel → ngày hiệu lực thật
NGAY_HIEU_LUC = {
    "04/02/2026": date(2026, 2, 4),
    "15/5/2026": date(2026, 5, 15),
    "03/06/2026": date(2026, 6, 3),
    "03/07/2026": date(2026, 7, 3),
}

# Người trùng tên: DB gắn hậu tố năm sinh, Excel ghi tên trần → chốt cứng theo STT.
# Căn cứ tra: snapshot đơn vị + người duyệt của kê khai theo tháng (xem PLAN §Sai #3).
MA_CC_THEO_STT = {
    7: "20ZZ-0220",    # Nguyễn Viết Cường 1971 — KK T1 ở HQCK-CP, người duyệt PĐT CP
    24: "20ZZ-0483",   # Nguyễn Đức Tuệ 1985   — KK T1,T2 ở HQCK-HG → T4 TCCB
    29: "20ZZ-0298",   # Phạm Thị Lan Hương 1987 — KK T1 ở HQCK-BPS → T4 HQCK-MC
    110: "20ZZ-0261",  # Nguyễn Mạnh Cường 1970 — KK T5 rơi vào CẢ KSHQ và HQCK-MC
    141: "20ZZ-0176",  # Nguyễn Văn Hoàn 1995
}

# `ly_do` ghi tạm — chưa có số quyết định, TCCB bổ sung sau qua
# trang /admin/lich-su-dieu-chuyen.
def ly_do_cho_dot(ngay: date) -> str:
    return f"Đợt điều động {ngay.strftime('%d/%m/%Y')}"


# =============================================================================
# CHUẨN HÓA TÊN
# =============================================================================

def nfc(s) -> str:
    """Chuẩn hóa Unicode + gom khoảng trắng, GIỮ dấu (dùng để khớp chính xác)."""
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", str(s)).strip())


# =============================================================================
# ĐỌC EXCEL
# =============================================================================

class DongQD:
    """Một dòng quyết định trong Excel."""

    def __init__(self, stt: int, ho_ten: str, ma_di: str, ma_den: str, ngay: date):
        self.stt = stt
        self.ho_ten = ho_ten
        self.ma_di = ma_di
        self.ma_den = ma_den
        self.ngay = ngay

    def __repr__(self) -> str:
        return f"STT{self.stt} {self.ho_ten} {self.ma_di}->{self.ma_den} {self.ngay}"


def doc_excel() -> list[DongQD]:
    if not FILE_EXCEL.exists():
        raise SystemExit(f"❌ Không thấy file Excel: {FILE_EXCEL}")

    df = pd.ExcelFile(FILE_EXCEL).parse(SHEET, header=0)
    df = df[df["STT"].notna()]

    ket_qua: list[DongQD] = []
    for _, r in df.iterrows():
        abbr_di = str(r["Đơn vị đi (viết tắt)"]).strip()
        abbr_den = str(r["Đơn vị đến (viết tắt)"]).strip()
        chuoi_ngay = str(r["Ngày hiệu lực"]).strip()

        if abbr_di not in ABBR_TO_MA_DON_VI:
            raise SystemExit(f"❌ STT {r['STT']}: viết tắt đơn vị đi lạ: {abbr_di!r}")
        if abbr_den not in ABBR_TO_MA_DON_VI:
            raise SystemExit(f"❌ STT {r['STT']}: viết tắt đơn vị đến lạ: {abbr_den!r}")
        if chuoi_ngay not in NGAY_HIEU_LUC:
            raise SystemExit(f"❌ STT {r['STT']}: ngày hiệu lực lạ: {chuoi_ngay!r}")

        ket_qua.append(DongQD(
            stt=int(r["STT"]),
            ho_ten=nfc(r["Họ và tên"]),
            ma_di=ABBR_TO_MA_DON_VI[abbr_di],
            ma_den=ABBR_TO_MA_DON_VI[abbr_den],
            ngay=NGAY_HIEU_LUC[chuoi_ngay],
        ))
    return ket_qua


# =============================================================================
# LẬP KẾ HOẠCH — so QĐ với DB, sinh danh sách thao tác
# =============================================================================

class KeHoach:
    def __init__(self):
        self.xoa: list[tuple] = []     # (id, ma_cc, ho_ten, ngay, di, den, vi_sao)
        self.sua: list[tuple] = []     # (id, ma_cc, ho_ten, ngay_cu, ngay_moi, di, den)
        self.them: list[tuple] = []    # (cc_id, ma_cc, ho_ten, ngay, di, den, cv)
        self.da_dung: list[tuple] = [] # (ma_cc, ho_ten, ngay, di, den)
        self.canh_bao: list[str] = []


async def lap_ke_hoach(db: AsyncSession, cac_dong: list[DongQD]) -> KeHoach:
    kh = KeHoach()

    # --- Bảng tra đơn vị ---
    don_vi_rows = (await db.execute(select(DonVi))).scalars().all()
    ma_to_id = {d.ma_don_vi: d.id for d in don_vi_rows}
    id_to_ma = {d.id: d.ma_don_vi for d in don_vi_rows}

    # --- Bảng tra công chức ---
    cc_rows = (await db.execute(
        select(CongChuc).where(CongChuc.is_deleted == False)
    )).scalars().all()
    cc_theo_ma = {c.ma_cc: c for c in cc_rows}
    cc_theo_ten: dict[str, list[CongChuc]] = {}
    for c in cc_rows:
        cc_theo_ten.setdefault(nfc(c.ho_ten), []).append(c)

    for dong in cac_dong:
        # ---- 1. Xác định công chức ----
        if dong.stt in MA_CC_THEO_STT:
            ma_cc = MA_CC_THEO_STT[dong.stt]
            cc = cc_theo_ma.get(ma_cc)
            if cc is None:
                kh.canh_bao.append(f"{dong}: không thấy ma_cc chốt cứng {ma_cc} → BỎ QUA")
                continue
        else:
            ung_vien = cc_theo_ten.get(dong.ho_ten, [])
            if len(ung_vien) == 0:
                kh.canh_bao.append(
                    f"{dong}: không khớp họ tên trong DB → BỎ QUA "
                    f"(nếu do trùng tên có hậu tố năm sinh, thêm vào MA_CC_THEO_STT)"
                )
                continue
            if len(ung_vien) > 1:
                kh.canh_bao.append(
                    f"{dong}: {len(ung_vien)} người cùng tên "
                    f"({', '.join(u.ma_cc for u in ung_vien)}) → BỎ QUA, phải chốt cứng ma_cc"
                )
                continue
            cc = ung_vien[0]

        id_di = ma_to_id.get(dong.ma_di)
        id_den = ma_to_id.get(dong.ma_den)
        if id_di is None or id_den is None:
            kh.canh_bao.append(f"{dong}: không tra được id đơn vị → BỎ QUA")
            continue

        # ---- 2. Lấy các bản ghi ĐIỀU CHUYỂN hiện có của người này ----
        rows = (await db.execute(
            select(LichSuDieuChuyen)
            .where(
                LichSuDieuChuyen.cong_chuc_id == cc.id,
                LichSuDieuChuyen.loai == "DIEU_CHUYEN",
            )
            .order_by(LichSuDieuChuyen.created_at)
        )).scalars().all()

        cung_chieu = [r for r in rows if r.don_vi_cu_id == id_di and r.don_vi_moi_id == id_den]
        nguoc_chieu = [r for r in rows if r.don_vi_cu_id == id_den and r.don_vi_moi_id == id_di]

        # ---- 3. GỘP KHỨ HỒI ----
        # Dấu hiệu nhập sai rồi sửa bằng cách chuyển đi/chuyển lại:
        #   ≥2 bản ghi CÙNG chiều QĐ. Khi đó bản ghi NGƯỢC chiều là thao tác
        #   hoàn tác, không phải quyết định thật → xóa.
        # Chỉ xóa khi có ≥2 bản cùng chiều, để không đụng vào ca chuyển đi rồi
        # thực sự chuyển về sau này.
        if len(cung_chieu) >= 2:
            giu = cung_chieu[-1]  # mới nhất theo created_at
            for r in cung_chieu[:-1]:
                kh.xoa.append((r.id, cc.ma_cc, cc.ho_ten, r.ngay_hieu_luc,
                               dong.ma_di, dong.ma_den, "trùng cùng chiều QĐ"))
            for r in nguoc_chieu:
                kh.xoa.append((r.id, cc.ma_cc, cc.ho_ten, r.ngay_hieu_luc,
                               dong.ma_den, dong.ma_di, "hoàn tác của lần nhập sai"))
            cung_chieu = [giu]

        # ---- 4. SỬA NGÀY / THÊM MỚI ----
        if len(cung_chieu) == 1:
            r = cung_chieu[0]
            if r.ngay_hieu_luc != dong.ngay:
                kh.sua.append((r.id, cc.ma_cc, cc.ho_ten, r.ngay_hieu_luc,
                               dong.ngay, dong.ma_di, dong.ma_den))
            else:
                kh.da_dung.append((cc.ma_cc, cc.ho_ten, r.ngay_hieu_luc,
                                   dong.ma_di, dong.ma_den))
        else:
            kh.them.append((cc.id, cc.ma_cc, cc.ho_ten, dong.ngay,
                            dong.ma_di, dong.ma_den, cc.chuc_vu))

        # ---- 5. Đối chiếu đơn vị hiện tại (chỉ cảnh báo, không tự sửa) ----
        if id_to_ma.get(cc.don_vi_id) != dong.ma_den:
            kh.canh_bao.append(
                f"{cc.ma_cc} {cc.ho_ten}: đơn vị hiện tại "
                f"{id_to_ma.get(cc.don_vi_id)} ≠ đơn vị đến của QĐ {dong.ma_den} "
                f"→ cần TCCB xác nhận, script KHÔNG tự đổi don_vi_id"
            )

    return kh


# =============================================================================
# IN KẾ HOẠCH
# =============================================================================

def in_ke_hoach(kh: KeHoach) -> None:
    print()
    print("=" * 100)
    print(f"1) GỘP KHỨ HỒI — xóa {len(kh.xoa)} bản ghi")
    print("=" * 100)
    for _id, ma_cc, ho_ten, ngay, di, den, vi_sao in kh.xoa:
        print(f"   {ma_cc}  {ho_ten:<26} {str(ngay):<12} {di:>9} -> {den:<9}  ({vi_sao})")

    print()
    print("=" * 100)
    print(f"2) SỬA NGÀY HIỆU LỰC — {len(kh.sua)} bản ghi")
    print("=" * 100)
    for _id, ma_cc, ho_ten, ngay_cu, ngay_moi, di, den in kh.sua:
        print(f"   {ma_cc}  {ho_ten:<26} {str(ngay_cu):<12} -> {str(ngay_moi):<12} "
              f"{di:>9} -> {den}")

    print()
    print("=" * 100)
    print(f"3) THÊM MỚI — {len(kh.them)} bản ghi")
    print("=" * 100)
    for _cc_id, ma_cc, ho_ten, ngay, di, den, _cv in kh.them:
        print(f"   {ma_cc}  {ho_ten:<26} {str(ngay):<12} {di:>9} -> {den}")

    print()
    print(f"4) ĐÃ ĐÚNG SẴN — {len(kh.da_dung)} bản ghi (không đụng)")
    for ma_cc, ho_ten, ngay, di, den in kh.da_dung:
        print(f"   {ma_cc}  {ho_ten:<26} {str(ngay):<12} {di:>9} -> {den}")

    if kh.canh_bao:
        print()
        print("=" * 100)
        print(f"⚠️  CẢNH BÁO — {len(kh.canh_bao)} mục cần người xem")
        print("=" * 100)
        for c in kh.canh_bao:
            print(f"   • {c}")

    print()
    print("-" * 100)
    print(f"TỔNG: xóa {len(kh.xoa)} · sửa {len(kh.sua)} · thêm {len(kh.them)} · "
          f"đã đúng {len(kh.da_dung)} · cảnh báo {len(kh.canh_bao)}")
    print("-" * 100)


# =============================================================================
# GHI
# =============================================================================

async def ghi(db: AsyncSession, kh: KeHoach) -> None:
    ma_to_id = {
        d.ma_don_vi: d.id
        for d in (await db.execute(select(DonVi))).scalars().all()
    }

    # 1. XÓA
    for _id, *_ in kh.xoa:
        await db.execute(delete(LichSuDieuChuyen).where(LichSuDieuChuyen.id == _id))

    # 2. SỬA
    for _id, _ma_cc, _ho_ten, _ngay_cu, ngay_moi, _di, _den in kh.sua:
        r = (await db.execute(
            select(LichSuDieuChuyen).where(LichSuDieuChuyen.id == _id)
        )).scalar_one()
        r.ngay_hieu_luc = ngay_moi
        if not (r.ly_do or "").strip() or r.ly_do == "Điều chuyển nhân sự":
            r.ly_do = ly_do_cho_dot(ngay_moi)

    # 3. THÊM
    for cc_id, _ma_cc, _ho_ten, ngay, di, den, chuc_vu in kh.them:
        db.add(LichSuDieuChuyen(
            loai="DIEU_CHUYEN",
            cong_chuc_id=cc_id,
            don_vi_cu_id=ma_to_id[di],
            don_vi_moi_id=ma_to_id[den],
            # vai_tro/chức vụ: không suy được từ QĐ → giữ nguyên hiện tại ở cả
            # hai đầu, để bản ghi không khẳng định sai điều gì.
            vai_tro_cu_id=None,
            vai_tro_moi_id=None,
            chuc_vu_cu=chuc_vu,
            chuc_vu_moi=chuc_vu,
            ly_do=ly_do_cho_dot(ngay),
            ngay_hieu_luc=ngay,
            nguoi_thuc_hien_id=None,  # di trú dữ liệu, không phải hành động của admin
        ))

    await db.flush()


# =============================================================================
# MAIN
# =============================================================================

async def main(apply: bool) -> int:
    print(f"📄 Excel : {FILE_EXCEL}")
    print(f"🗄️  DB    : {settings.db_name} @ {settings.db_host}:{settings.db_port}")
    print(f"🔧 Chế độ: {'GHI THẬT (--apply)' if apply else 'XEM TRƯỚC (dry-run)'}")

    if apply and settings.db_name == "kpi_haiquan":
        print()
        print("🚨 ĐANG NHẮM VÀO DATABASE PRODUCTION `kpi_haiquan`.")
        print("   Hãy chạy thử trên `kpi_haiquan_test` trước:")
        print("   DB_NAME=kpi_haiquan_test python scripts/fix_ngay_dieu_chuyen_2026.py --apply")
        tra_loi = input("   Gõ đúng chữ  GHI VAO PROD  để tiếp tục: ").strip()
        if tra_loi != "GHI VAO PROD":
            print("   → Đã hủy, không ghi gì.")
            return 1

    cac_dong = doc_excel()
    print(f"✅ Đọc được {len(cac_dong)} dòng quyết định từ Excel")

    engine = create_async_engine(settings.database_url, echo=False)
    Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    ma_ket_thuc = 0
    async with Session() as db:
        kh = await lap_ke_hoach(db, cac_dong)
        in_ke_hoach(kh)

        tong_thao_tac = len(kh.xoa) + len(kh.sua) + len(kh.them)

        if not apply:
            print()
            print("ℹ️  Chế độ xem trước — KHÔNG ghi gì vào DB.")
            print("   Thêm --apply để ghi thật.")
        elif tong_thao_tac == 0:
            print()
            print("✅ Không có gì để làm — dữ liệu đã khớp quyết định.")
        else:
            try:
                await ghi(db, kh)
                await db.commit()
                print()
                print(f"✅ ĐÃ GHI: xóa {len(kh.xoa)} · sửa {len(kh.sua)} · thêm {len(kh.them)}")
            except Exception as e:
                await db.rollback()
                print()
                print(f"❌ LỖI — đã rollback, DB không đổi: {e}")
                ma_ket_thuc = 1

    await engine.dispose()
    return ma_ket_thuc


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Sửa ngay_hieu_luc trong lich_su_dieu_chuyen theo QĐ điều động 2026"
    )
    parser.add_argument(
        "--apply", action="store_true",
        help="Ghi thật vào DB (mặc định chỉ xem trước)"
    )
    args = parser.parse_args()
    sys.exit(asyncio.run(main(args.apply)))
