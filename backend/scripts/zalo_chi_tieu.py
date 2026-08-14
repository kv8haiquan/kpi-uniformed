"""
scripts/zalo_chi_tieu.py
=========================
Xem kênh Zalo đã tiêu bao nhiêu tiền, còn bao nhiêu hạn mức.

    cd backend && source venv/bin/activate

    python scripts/zalo_chi_tieu.py              # hôm nay + tháng này
    python scripts/zalo_chi_tieu.py --thang 6    # tháng 6 năm nay
    python scripts/zalo_chi_tieu.py --lich-su    # 6 tháng gần nhất
    python scripts/zalo_chi_tieu.py --quota      # hỏi thêm hạn mức từ Zalo

CHỈ ĐỌC. Không gửi tin, không ghi gì vào cơ sở dữ liệu.

Số liệu lấy từ `common.zalo_outbox` — mỗi bản ghi DA_GUI là một tin đã tính
phí. Tin THAT_BAI/BO_QUA không tính tiền nên không đếm.

⚠️ Ví ZBS trên trang quản trị Zalo KHÔNG phải thước đo tin cậy: đã ghi nhận
   trường hợp ví không đổi số trong khi hạn mức (`message/quota`) trừ đúng
   từng tin. Bảng outbox và quota mới là hai nguồn đáng tin.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text  # noqa: E402

from shared.database import create_db_engine, create_session_factory  # noqa: E402

from common_service.config import settings  # noqa: E402
from common_service.models.zalo import OB_DA_GUI  # noqa: E402
from common_service.services.zalo.tran_chi import (  # noqa: E402
    dinh_dang_tien,
    khong_gioi_han,
    tinh_hinh_chi,
)
from common_service.services.zalo.token_store import lay_access_token  # noqa: E402

_URL_QUOTA = "https://business.openapi.zalo.me/message/quota"

# Chia theo doi_tuong_type của thông báo gốc — cho biết tiền đi vào loại tin
# nào (giấy mời / nhắc họp / thay đổi / hủy). Đây là số liệu để quyết định
# có nên bớt mốc nhắc hay không.
_SQL_THEO_LOAI = text(
    """
    SELECT COALESCE(tb.doi_tuong_type, '(không rõ)') AS loai_tin,
           count(*)                                  AS so_tin
      FROM common.zalo_outbox ob
      JOIN common.thong_bao tb ON tb.id = ob.thong_bao_id
     WHERE ob.trang_thai = :da_gui
       AND ob.ngay_gui IS NOT NULL
       AND date_trunc('month', ob.ngay_gui AT TIME ZONE 'Asia/Ho_Chi_Minh')
           = make_date(:nam, :thang, 1)
     GROUP BY 1
     ORDER BY 2 DESC
    """
)

_SQL_LICH_SU = text(
    """
    SELECT to_char(
               date_trunc('month', ngay_gui AT TIME ZONE 'Asia/Ho_Chi_Minh'),
               'MM/YYYY') AS ky,
           count(*)        AS so_tin
      FROM common.zalo_outbox
     WHERE trang_thai = :da_gui
       AND ngay_gui IS NOT NULL
     GROUP BY 1
     ORDER BY min(ngay_gui) DESC
     LIMIT 6
    """
)

# Tin không gửi được / bị bỏ — không tốn tiền nhưng cho biết kênh có khỏe không
_SQL_TRANG_THAI = text(
    """
    SELECT trang_thai,
           COALESCE(ly_do_bo_qua, '—') AS ly_do,
           count(*)                    AS so
      FROM common.zalo_outbox
     GROUP BY 1, 2
     ORDER BY 3 DESC
    """
)


async def _hoi_quota(token: str) -> str:
    """Hạn mức Zalo còn lại. Lỗi thì trả về mô tả, không làm hỏng báo cáo."""
    try:
        async with httpx.AsyncClient(timeout=15.0) as c:
            r = await c.get(_URL_QUOTA, headers={"access_token": token})
            d = r.json()
    except (httpx.HTTPError, ValueError) as e:
        return f"không hỏi được ({str(e)[:60]})"
    if d.get("error") != 0:
        return f"Zalo báo lỗi {d.get('error')}: {d.get('message')}"
    return json.dumps(d.get("data") or {}, ensure_ascii=False)


def _thanh(nhan: str, tin: int, tran_tin: int, don_gia: int) -> str:
    tien = dinh_dang_tien(tin * don_gia)
    if khong_gioi_han(tran_tin):
        return f"  {nhan:<12} {tin:>6} tin   {tien:>14}   (chưa đặt trần)"
    if tran_tin == 0:
        return f"  {nhan:<12} {tin:>6} tin   {tien:>14}   ⛔ TRẦN 0 — CHẶN HẾT"
    pc = int(100 * tin / tran_tin)
    o = int(round(pc / 5))
    thanh = "█" * min(o, 20) + "░" * max(0, 20 - o)
    return (
        f"  {nhan:<12} {tin:>6}/{tran_tin:<6} tin  {tien:>14}"
        f" / {dinh_dang_tien(tran_tin * don_gia):<14} {thanh} {pc}%"
    )


async def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description="Báo cáo chi tiêu kênh Zalo")
    p.add_argument("--thang", type=int, default=None, help="Xem chi tiết tháng nào")
    p.add_argument("--nam", type=int, default=None, help="Năm (mặc định năm nay)")
    p.add_argument("--lich-su", action="store_true", help="6 tháng gần nhất")
    p.add_argument("--quota", action="store_true", help="Hỏi thêm hạn mức từ Zalo")
    a = p.parse_args(argv)

    engine = create_db_engine(settings.database_url)
    session_factory = create_session_factory(engine)

    try:
        async with session_factory() as db:
            th = await tinh_hinh_chi(db)

            print("═" * 78)
            print("CHI TIÊU KÊNH ZALO")
            print("═" * 78)
            print(f"  Đơn giá áp dụng: {dinh_dang_tien(th.don_gia)}/tin")
            print()
            print(_thanh("Hôm nay", th.tin_ngay, th.tran_ngay_tin, th.don_gia))
            print(_thanh("Tháng này", th.tin_thang, th.tran_thang_tin, th.don_gia))
            print()
            if th.con_lai is None:
                print("  ⚠️  CHƯA ĐẶT TRẦN NÀO — không có gì chặn nếu gửi nhầm hàng loạt.")
                print("     Đặt ZALO_TRAN_NGAY_DONG / ZALO_TRAN_THANG_DONG trong .env.")
            elif th.cham_tran:
                print("  ⛔ ĐÃ CHẠM TRẦN — worker đang tạm ngừng gửi.")
            else:
                print(
                    f"  Còn gửi được {th.con_lai} tin "
                    f"({dinh_dang_tien(th.con_lai * th.don_gia)}) trước khi chạm trần."
                )

            # Bóc tách theo loại tin của tháng đang xét
            now_row = await db.execute(
                text(
                    "SELECT EXTRACT(YEAR FROM now() AT TIME ZONE 'Asia/Ho_Chi_Minh')::int,"
                    "       EXTRACT(MONTH FROM now() AT TIME ZONE 'Asia/Ho_Chi_Minh')::int"
                )
            )
            nam_nay, thang_nay = now_row.one()
            nam = a.nam or nam_nay
            thang = a.thang or thang_nay

            rows = (
                await db.execute(
                    _SQL_THEO_LOAI,
                    {"da_gui": OB_DA_GUI, "nam": nam, "thang": thang},
                )
            ).mappings().all()

            print()
            print("─" * 78)
            print(f"THÁNG {thang:02d}/{nam} — TIỀN ĐI VÀO LOẠI TIN NÀO")
            print("─" * 78)
            tong = sum(r["so_tin"] for r in rows) or 0
            if not tong:
                print("  (chưa gửi tin nào trong tháng này)")
            for r in rows:
                pc = 100.0 * r["so_tin"] / tong
                print(
                    f"  {r['loai_tin']:<22} {r['so_tin']:>6} tin  "
                    f"{dinh_dang_tien(r['so_tin'] * th.don_gia):>14}  {pc:>5.1f}%"
                )
            if tong:
                print(
                    f"  {'TỔNG':<22} {tong:>6} tin  "
                    f"{dinh_dang_tien(tong * th.don_gia):>14}"
                )

            if a.lich_su:
                print()
                print("─" * 78)
                print("6 KỲ GẦN NHẤT")
                print("─" * 78)
                for r in (
                    await db.execute(_SQL_LICH_SU, {"da_gui": OB_DA_GUI})
                ).mappings():
                    print(
                        f"  {r['ky']:<10} {r['so_tin']:>6} tin  "
                        f"{dinh_dang_tien(r['so_tin'] * th.don_gia):>14}"
                    )

            print()
            print("─" * 78)
            print("TÌNH TRẠNG HÀNG ĐỢI (mọi thời kỳ)")
            print("─" * 78)
            for r in (await db.execute(_SQL_TRANG_THAI)).mappings():
                print(f"  {r['trang_thai']:<12} {r['ly_do']:<18} {r['so']:>6}")

            if a.quota:
                token = await lay_access_token(db)
                print()
                print(f"  Hạn mức Zalo còn lại: {await _hoi_quota(token)}")

            print("═" * 78)
    finally:
        await engine.dispose()

    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main(sys.argv[1:])))
