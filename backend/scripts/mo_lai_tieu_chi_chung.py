#!/usr/bin/env python3
"""
scripts/mo_lai_tieu_chi_chung.py
================================
Mở lại phần TIÊU CHÍ CHUNG của một tháng cho MỘT công chức, để người đó tự chấm
lại và lãnh đạo ĐƠN VỊ HIỆN TẠI duyệt lại.

Dùng khi nào: công chức được điều chuyển với ngày hiệu lực LÙI VỀ QUÁ KHỨ, nên
tháng đó đã bị đơn vị CŨ chấm và duyệt xong trước khi việc điều chuyển được nhập
vào hệ thống. Ca đầu tiên: `20ZZ-0529` Nguyễn Đức Quang, QĐ 03/7/2026 chuyển
HQCK-MC → KSHQ nhưng chỉ được nhập ngày 25/08, khi T7 đã `DA_PHE_DUYET` bởi
PĐT HQCK-MC.

Vì sao KHÔNG dùng endpoint "mở khóa" của CCT: endpoint đó mở khóa CẢ ĐƠN VỊ trong
tháng đó (`xep_loai_moi.py`), quá rộng cho một người.

Việc script làm:
    1. `danh_gia_thang`  — bỏ khóa, trả `trang_thai_tc` về NHAP, xóa mọi dấu vết
       phê duyệt của đơn vị cũ (người duyệt, ngày duyệt, điểm cấp 1/cấp 2, điểm
       tiêu chí chung tổng).
    2. `don_vi_id_snapshot` — dời về đơn vị HIỆN TẠI của công chức (tùy chọn
       `--giu-snapshot` để không dời).
    3. `tieu_chi_chung_danh_gia` — trả từng dòng về NHAP và xóa phần chấm của
       lãnh đạo. GIỮ `is_achieved_cc` / `diem_tu_cham` để công chức mở ra còn
       thấy bản mình đã chấm; endpoint `POST /danh-gia/tieu-chi-chung` khi gửi
       lại sẽ tự XÓA HẾT dòng cũ rồi tạo mới, nên phần này chỉ là trạng thái
       trung gian (xem `danh_gia.py`, đoạn "Xóa bản cũ" → "Tạo mới").

Script KHÔNG làm:
    • Không đụng `ke_khai_cong_viec` (ca 20ZZ-0529 không có kê khai T7).
    • Không đụng `bao_cao_xep_loai` / `chi_tiet_xep_loai`. Sau khi chạy, hai đơn
      vị liên quan phải bấm "cập nhật chi tiết từ dữ liệu" cho báo cáo tháng đó
      để người này rời danh sách đơn vị cũ và vào danh sách đơn vị mới.

Chạy:
    # xem trước, KHÔNG ghi gì (mặc định)
    python scripts/mo_lai_tieu_chi_chung.py --ma-cc 20ZZ-0529 --thang 7 --nam 2026

    # ghi thật — LUÔN thử trên DB test trước
    DB_NAME=kpi_haiquan_test python scripts/mo_lai_tieu_chi_chung.py \
        --ma-cc 20ZZ-0529 --thang 7 --nam 2026 --apply

⚠️ Mọi thao tác nằm trong MỘT transaction; lỗi giữa đường là rollback sạch.
"""

import argparse
import asyncio
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.config import settings
from app.models import CongChuc, DonVi
from app.models.kpi_assessment import DanhGiaThang, TieuChiChungDanhGia, TrangThaiTieuChi


def _in_dong(nhan: str, truoc, sau=None) -> None:
    if sau is None:
        print(f"   {nhan:<34} {truoc}")
    else:
        print(f"   {nhan:<34} {str(truoc):<24} ->  {sau}")


async def main(ma_cc: str, thang: int, nam: int, apply: bool, giu_snapshot: bool) -> int:
    print(f"🗄️  DB    : {settings.db_name} @ {settings.db_host}:{settings.db_port}")
    print(f"🎯 Mục tiêu: {ma_cc} — tiêu chí chung tháng {thang}/{nam}")
    print(f"🔧 Chế độ : {'GHI THẬT (--apply)' if apply else 'XEM TRƯỚC (dry-run)'}")

    if apply and settings.db_name == "kpi_haiquan":
        print()
        print("🚨 ĐANG NHẮM VÀO DATABASE PRODUCTION `kpi_haiquan`.")
        tra_loi = input("   Gõ đúng chữ  GHI VAO PROD  để tiếp tục: ").strip()
        if tra_loi != "GHI VAO PROD":
            print("   → Đã hủy, không ghi gì.")
            return 1

    engine = create_async_engine(settings.database_url, echo=False)
    Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    ma_ket_thuc = 0
    async with Session() as db:
        cc = (await db.execute(
            select(CongChuc).where(CongChuc.ma_cc == ma_cc, CongChuc.is_deleted == False)
        )).scalar_one_or_none()
        if cc is None:
            print(f"❌ Không thấy công chức {ma_cc}")
            await engine.dispose()
            return 1

        dg = (await db.execute(
            select(DanhGiaThang).where(
                DanhGiaThang.cong_chuc_id == cc.id,
                DanhGiaThang.thang == thang,
                DanhGiaThang.nam == nam,
                DanhGiaThang.is_deleted == False,
            )
        )).scalar_one_or_none()
        if dg is None:
            print(f"❌ Không thấy đánh giá tháng {thang}/{nam} của {ma_cc}")
            await engine.dispose()
            return 1

        ma_don_vi_theo_id = {
            d.id: d.ma_don_vi for d in (await db.execute(select(DonVi))).scalars().all()
        }
        ho_ten_theo_id = {
            c.id: c.ma_cc for c in (await db.execute(select(CongChuc))).scalars().all()
        }

        tc_rows = (await db.execute(
            select(TieuChiChungDanhGia)
            .where(TieuChiChungDanhGia.danh_gia_thang_id == dg.id)
        )).scalars().all()

        dv_moi_id = cc.don_vi_id if not giu_snapshot else dg.don_vi_id_snapshot

        # ------------------------------------------------------------------
        # IN RÕ TỪNG CỘT SẼ ĐỔI
        # ------------------------------------------------------------------
        print()
        print("=" * 92)
        print(f"1) danh_gia_thang  (id={dg.id})")
        print("=" * 92)
        _in_dong("trang_thai_tc", dg.trang_thai_tc.value if dg.trang_thai_tc else None, "NHAP")
        _in_dong("is_khoa", dg.is_khoa, False)
        _in_dong("diem_tieu_chi_chung", dg.diem_tieu_chi_chung, None)
        _in_dong("diem_tc_cap1", dg.diem_tc_cap1, None)
        _in_dong("diem_tc_cap2", dg.diem_tc_cap2, None)
        _in_dong("nguoi_phe_duyet_tc_cap1_id",
                 ho_ten_theo_id.get(dg.nguoi_phe_duyet_tc_cap1_id), None)
        _in_dong("nguoi_phe_duyet_tc_cap2_id",
                 ho_ten_theo_id.get(dg.nguoi_phe_duyet_tc_cap2_id), None)
        _in_dong("ngay_phe_duyet_tc_cap1", dg.ngay_phe_duyet_tc_cap1, None)
        _in_dong("ngay_phe_duyet_tc_cap2", dg.ngay_phe_duyet_tc_cap2, None)
        _in_dong("don_vi_id_snapshot",
                 ma_don_vi_theo_id.get(dg.don_vi_id_snapshot),
                 ma_don_vi_theo_id.get(dv_moi_id) + (" (giữ nguyên)" if giu_snapshot else ""))
        print()
        _in_dong("KHÔNG đổi — trang_thai", dg.trang_thai.value if dg.trang_thai else None)

        print()
        print("=" * 92)
        print(f"2) tieu_chi_chung_danh_gia — {len(tc_rows)} dòng")
        print("=" * 92)
        print("   Mỗi dòng:  trang_thai -> NHAP · is_achieved_ld -> NULL · "
              "diem_phe_duyet -> NULL")
        print("              nguoi_phe_duyet_id -> NULL · ngay_gui -> NULL · "
              "ngay_phe_duyet -> NULL")
        print("   GIỮ NGUYÊN: is_achieved_cc, diem_tu_cham, ghi_chu_cc")
        print()
        tong_tu_cham = sum(float(r.diem_tu_cham or 0) for r in tc_rows)
        tong_phe_duyet = sum(float(r.diem_phe_duyet or 0) for r in tc_rows)
        print(f"   Tổng điểm tự chấm  (GIỮ) : {tong_tu_cham}")
        print(f"   Tổng điểm phê duyệt (XÓA): {tong_phe_duyet}")
        trang_thai_hien = sorted({
            r.trang_thai.value if r.trang_thai else None for r in tc_rows
        }, key=str)
        print(f"   Trạng thái hiện tại      : {trang_thai_hien}")

        if not apply:
            print()
            print("ℹ️  Chế độ xem trước — KHÔNG ghi gì vào DB.")
            print("   Thêm --apply để ghi thật.")
            await engine.dispose()
            return 0

        # ------------------------------------------------------------------
        # GHI
        # ------------------------------------------------------------------
        try:
            dg.trang_thai_tc = TrangThaiTieuChi.NHAP
            dg.is_khoa = False
            dg.diem_tieu_chi_chung = None
            dg.diem_tc_cap1 = None
            dg.diem_tc_cap2 = None
            dg.nguoi_phe_duyet_tc_cap1_id = None
            dg.nguoi_phe_duyet_tc_cap2_id = None
            dg.ngay_phe_duyet_tc_cap1 = None
            dg.ngay_phe_duyet_tc_cap2 = None
            if not giu_snapshot:
                dg.don_vi_id_snapshot = dv_moi_id

            for r in tc_rows:
                r.trang_thai = TrangThaiTieuChi.NHAP
                r.is_achieved_ld = None
                r.diem_phe_duyet = None
                r.nguoi_phe_duyet_id = None
                r.ngay_gui = None
                r.ngay_phe_duyet = None

            await db.flush()

            # --- Kiểm chứng TRƯỚC khi commit ---
            loi: list[str] = []
            if dg.is_khoa:
                loi.append("is_khoa vẫn True")
            if dg.trang_thai_tc != TrangThaiTieuChi.NHAP:
                loi.append(f"trang_thai_tc = {dg.trang_thai_tc}")
            if dg.nguoi_phe_duyet_tc_cap1_id or dg.nguoi_phe_duyet_tc_cap2_id:
                loi.append("còn người phê duyệt cũ")
            con_duyet = [r for r in tc_rows if r.trang_thai != TrangThaiTieuChi.NHAP
                         or r.diem_phe_duyet is not None or r.nguoi_phe_duyet_id is not None]
            if con_duyet:
                loi.append(f"{len(con_duyet)} dòng tiêu chí chưa sạch")
            if loi:
                raise RuntimeError("Kiểm chứng thất bại: " + "; ".join(loi))

            await db.commit()
            print()
            print(f"✅ ĐÃ GHI — {ma_cc} có thể tự chấm lại tiêu chí chung tháng {thang}/{nam}")
            print("   Việc tiếp theo (làm trên giao diện, KHÔNG bằng SQL):")
            print(f"   1. {ma_cc} đăng nhập → tự đánh giá tiêu chí chung tháng {thang} → gửi phê duyệt")
            print("   2. Lãnh đạo đơn vị hiện tại duyệt cấp 1 rồi cấp 2")
            print(f"   3. Hai đơn vị liên quan bấm 'cập nhật chi tiết từ dữ liệu' cho báo cáo xếp loại tháng {thang}")
        except Exception as e:
            await db.rollback()
            print()
            print(f"❌ LỖI — đã rollback, DB không đổi: {e}")
            ma_ket_thuc = 1

    await engine.dispose()
    return ma_ket_thuc


if __name__ == "__main__":
    p = argparse.ArgumentParser(
        description="Mở lại tiêu chí chung một tháng cho một công chức (ca điều chuyển lùi ngày)"
    )
    p.add_argument("--ma-cc", required=True, help="Mã công chức, VD 20ZZ-0529")
    p.add_argument("--thang", required=True, type=int)
    p.add_argument("--nam", required=True, type=int)
    p.add_argument("--apply", action="store_true", help="Ghi thật (mặc định chỉ xem trước)")
    p.add_argument("--giu-snapshot", action="store_true",
                   help="KHÔNG dời don_vi_id_snapshot về đơn vị hiện tại")
    args = p.parse_args()
    sys.exit(asyncio.run(main(args.ma_cc, args.thang, args.nam, args.apply, args.giu_snapshot)))
