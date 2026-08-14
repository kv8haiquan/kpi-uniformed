"""
scripts/zalo_gui_thu.py
========================
Gửi THỬ một tin ZNS tới đúng MỘT số điện thoại do người chạy chỉ định.

Vì sao cần script riêng thay vì bật worker lên cho nó chạy:
  - Worker quét bảng common.thong_bao và gửi cho CẢ danh sách thành phần họp.
    Bật lên để thử là nhắn nhầm vào hàng trăm số thật.
  - Script này KHÔNG đụng common.zalo_outbox và common.zalo_lien_ket: không tạo
    hàng đợi, không đổi trạng thái ai cả. Bảng duy nhất có thể bị ghi là
    common.zalo_token, khi access_token hết hạn và phải refresh — đó là cơ chế
    bình thường của hệ thống.
  - Nó dựng tham số bằng CHÍNH code chạy thật (DANH_MUC_MAU), nên cái gì gửi
    được ở đây thì worker cũng gửi được y hệt.

MẶC ĐỊNH chạy ở chế độ development của Zalo: MIỄN PHÍ, và Zalo chỉ chấp nhận
số điện thoại của quản trị viên Official Account. Đây là hàng rào an toàn —
lỡ gõ nhầm số của người khác thì Zalo từ chối chứ không gửi đi.

    cd backend && source venv/bin/activate

    # Gửi thử miễn phí (số phải là QTV của OA)
    python scripts/zalo_gui_thu.py 0912345678

    # Chọn loại tin khác
    python scripts/zalo_gui_thu.py 0912345678 --loai HUY_HOP

    # Gửi thật, CÓ TÍNH PHÍ, gửi được tới số bất kỳ
    python scripts/zalo_gui_thu.py 0912345678 --that

Script luôn in nguyên văn tham số sắp gửi và hỏi xác nhận trước khi gọi API.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
import uuid
from datetime import date, datetime, time, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from shared.database import create_db_engine, create_session_factory  # noqa: E402

from common_service.config import settings  # noqa: E402
from common_service.services.zalo.client import gui_zns  # noqa: E402
from common_service.services.zalo.phone import chuan_hoa, hien_thi  # noqa: E402
from common_service.services.zalo.templates import (  # noqa: E402
    DANH_MUC_MAU,
    ThongTinGui,
)


def _doi_so(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Gửi thử 1 tin ZNS")
    p.add_argument("so_dien_thoai", help="Số nhận tin, ví dụ 0912345678")
    p.add_argument(
        "--loai",
        default="GIAY_MOI_HOP",
        choices=sorted(DANH_MUC_MAU),
        help="Loại thông báo (mặc định GIAY_MOI_HOP)",
    )
    p.add_argument("--ho-ten", default="Nguyễn Văn A", help="Tên hiển thị trong tin")
    p.add_argument(
        "--that",
        action="store_true",
        help="Gửi THẬT (có tính phí, gửi được tới số bất kỳ). "
        "Mặc định là chế độ development miễn phí.",
    )
    p.add_argument(
        "--khong-hoi", action="store_true", help="Bỏ qua bước hỏi xác nhận"
    )
    return p.parse_args(argv)


async def main(argv: list[str]) -> int:
    a = _doi_so(argv)

    kq_so = chuan_hoa(a.so_dien_thoai)
    if not kq_so.so_chuan:
        print(f"❌ Số không hợp lệ: {a.so_dien_thoai} — {kq_so.trang_thai} "
              f"{kq_so.ghi_chu}".rstrip())
        return 1

    mau = DANH_MUC_MAU[a.loai]
    template_id = getattr(settings, mau.khoa_config, "")
    if not template_id:
        print(f"❌ Chưa đặt {mau.khoa_config.upper()} trong .env")
        return 1

    # Dữ liệu họp giả lập: ngày mai, 14h00. cuoc_hop_id là UUID ngẫu nhiên nên
    # nút bấm trong tin sẽ dẫn tới cuộc họp không tồn tại — đúng ý đồ, vì đây
    # là tin thử, không được trỏ vào cuộc họp thật của đơn vị.
    mai = date.today() + timedelta(days=1)
    tt = ThongTinGui(
        doi_tuong_type=a.loai,
        ho_ten=a.ho_ten,
        ngay_hop=mai,
        gio_bat_dau=time(14, 0),
        link_url=None,
        cuoc_hop_id=uuid.uuid4(),
    )
    tham_so = mau.tham_so(tt)

    che_do_thu = not a.that
    print("─" * 68)
    print(f"  Loại tin     : {a.loai} — {mau.mo_ta}")
    print(f"  Template ID  : {template_id}")
    print(f"  Gửi tới      : {hien_thi(kq_so.so_chuan)}  ({kq_so.so_chuan})")
    print(f"  Tham số      : {tham_so}")
    if che_do_thu:
        print("  Chế độ       : DEVELOPMENT — miễn phí, Zalo chỉ nhận số QTV của OA")
    else:
        print("  Chế độ       : THẬT — CÓ TÍNH PHÍ, trừ vào ví ZBS của đơn vị")
    if settings.zalo_dry_run:
        print("  Ghi chú      : .env đang bật ZALO_DRY_RUN — script này tự bỏ qua")
        print("                 cờ đó CHỈ trong tiến trình của nó. File .env và")
        print("                 worker đang chạy KHÔNG bị đụng tới.")
    print("─" * 68)

    if not a.khong_hoi:
        tra_loi = input("Gõ 'gui' để xác nhận: ").strip().lower()
        if tra_loi != "gui":
            print("Đã hủy, không gửi gì cả.")
            return 1

    # Cố tình ghi đè sau khi đã xác nhận: mục đích của script LÀ gửi thật một
    # tin. Bắt người dùng sửa .env rồi nhớ sửa lại là cách chắc chắn có ngày
    # quên, để worker chạy khô mà tưởng đang gửi.
    settings.zalo_dry_run = False

    engine = create_db_engine(settings.database_url)
    session_factory = create_session_factory(engine)
    try:
        async with session_factory() as db:
            kq = await gui_zns(
                db,
                so_dien_thoai=kq_so.so_chuan,
                template_id=template_id,
                template_data=tham_so,
                tracking_id=f"guithu-{datetime.now():%Y%m%d%H%M%S}",
                che_do_thu_nghiem=che_do_thu,
            )
    finally:
        await engine.dispose()

    print()
    if kq.thanh_cong:
        print(f"✅ Zalo nhận tin. msg_id = {kq.message_id}")
        print("   Kiểm điện thoại: tin ZNS về trong vòng vài giây.")
        print("   KHÔNG thấy tin mà msg_id vẫn có → xem lại Nhật ký gửi trong ZBS.")
        return 0

    print(f"❌ Gửi hỏng — mã lỗi {kq.ma_loi}: {kq.mo_ta_loi}")
    print(f"   Thử lại được: {kq.thu_lai_duoc}")
    if str(kq.ma_loi) == "-133":
        print("   → Tham số template không khớp. Chạy:")
        print("     python scripts/zalo_xem_template.py --doi-chieu")
    if str(kq.ma_loi) in {"-124", "-216", "-217"}:
        print("   → Lỗi token. Chạy lại scripts/zalo_nap_token.py.")
    return 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main(sys.argv[1:])))
