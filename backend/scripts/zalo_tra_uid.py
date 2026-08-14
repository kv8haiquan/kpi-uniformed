"""
scripts/zalo_tra_uid.py
========================
Tra `zalo_user_id` của công chức từ SỐ ĐIỆN THOẠI đã có trong
`common.zalo_lien_ket`, dùng API `oa/getprofile` của Zalo.

VÌ SAO LÀM ĐƯỢC (đính chính hiểu nhầm trước 14/08/2026): `oa/getprofile` nhận
tham số `phone` chứ không chỉ `user_id`. Zalo trả về hồ sơ đầy đủ NẾU số đó
đã follow Official Account. Không phải đoán tên, không phải nhìn avatar —
số điện thoại chính là khóa tra, nên kết quả khớp là CHÍNH XÁC.

Ba trạng thái Zalo trả về:
    error = 0     → đã follow OA, lấy được user_id
    error = -213  → có Zalo nhưng CHƯA follow OA
    error = -201  → số không hợp lệ / không có tài khoản Zalo

LỢI ÍCH: gửi ZNS theo user_id giá 560đ thay vì 800đ theo số điện thoại —
rẻ hơn 30%. Ngoài ra kết quả -201 chỉ ra luôn những số sai trong danh sách.

    cd backend && source venv/bin/activate

    python scripts/zalo_tra_uid.py                  # thử 20 số, KHÔNG ghi DB
    python scripts/zalo_tra_uid.py --gioi-han 100   # thử 100 số
    python scripts/zalo_tra_uid.py --tat-ca         # quét hết, vẫn KHÔNG ghi
    python scripts/zalo_tra_uid.py --tat-ca --ghi   # quét hết VÀ ghi user_id

⚠️ DỮ LIỆU CÁ NHÂN (Nghị định 13/2023/NĐ-CP): script gửi số điện thoại thật
   của công chức sang máy chủ VNG. Chỉ chạy khi có sự đồng ý của lãnh đạo.
   Số điện thoại LUÔN bị che khi in ra màn hình. Tên hiển thị Zalo chỉ in để
   người vận hành đối chiếu bằng mắt, KHÔNG lưu vào cơ sở dữ liệu — chỉ
   `zalo_user_id` được lưu, đúng nguyên tắc tối thiểu hóa dữ liệu.

⚠️ Chỉ ĐỌC từ Zalo, không gửi tin, KHÔNG tốn phí. Bảng duy nhất bị ghi là
   `common.zalo_lien_ket` (cột `zalo_user_id`) và chỉ khi có cờ `--ghi`.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Optional

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select, update  # noqa: E402

from shared.database import create_db_engine, create_session_factory  # noqa: E402

from common_service.config import settings  # noqa: E402
from common_service.models.zalo import ZaloLienKet  # noqa: E402
from common_service.services.zalo.phone import che_giau  # noqa: E402
from common_service.services.zalo.token_store import lay_access_token  # noqa: E402

_URL_PROFILE = "https://openapi.zalo.me/v2.0/oa/getprofile"

# Nhịp gọi: Zalo giới hạn tần suất, và 543 lần gọi liên tiếp dễ bị chặn tạm.
# 0.3s/lần ⇒ ~3 phút cho toàn bộ danh sách, đủ chậm để không bị coi là quét.
_NHIP_GIAY = 0.3

DA_FOLLOW = "DA_FOLLOW"
CHUA_FOLLOW = "CHUA_FOLLOW"
SO_HONG = "SO_HONG"
LOI_KHAC = "LOI_KHAC"


async def _tra_mot_so(
    client: httpx.AsyncClient, token: str, so: str
) -> tuple[str, Optional[dict[str, Any]]]:
    """Trả về (trạng thái, hồ sơ). Không ném lỗi — mọi sự cố quy về LOI_KHAC."""
    try:
        r = await client.get(
            _URL_PROFILE,
            headers={"access_token": token},
            params={"data": json.dumps({"phone": so})},
        )
        d = r.json()
    except (httpx.HTTPError, ValueError) as e:
        return LOI_KHAC, {"message": str(e)[:120]}

    ma = d.get("error")
    if ma == 0:
        return DA_FOLLOW, d.get("data") or {}
    if ma == -213:
        return CHUA_FOLLOW, None
    if ma == -201:
        return SO_HONG, None
    return LOI_KHAC, {"error": ma, "message": str(d.get("message"))[:120]}


async def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description="Tra zalo_user_id từ số điện thoại")
    p.add_argument("--gioi-han", type=int, default=20, help="Số bản ghi tra (mặc định 20)")
    p.add_argument("--tat-ca", action="store_true", help="Tra toàn bộ danh sách")
    p.add_argument("--ghi", action="store_true", help="GHI zalo_user_id vào DB")
    p.add_argument(
        "--tra-lai",
        action="store_true",
        help="Tra cả những người ĐÃ có user_id (mặc định bỏ qua)",
    )
    a = p.parse_args(argv)

    engine = create_db_engine(settings.database_url)
    session_factory = create_session_factory(engine)

    try:
        async with session_factory() as db:
            token = await lay_access_token(db)

            q = select(ZaloLienKet).where(ZaloLienKet.so_dien_thoai.isnot(None))
            if not a.tra_lai:
                q = q.where(ZaloLienKet.zalo_user_id.is_(None))
            q = q.order_by(ZaloLienKet.created_at)
            if not a.tat_ca:
                q = q.limit(a.gioi_han)

            ds = list((await db.scalars(q)).all())

            print(f"Sẽ tra {len(ds)} số điện thoại"
                  f"{' — CÓ GHI vào DB' if a.ghi else ' — chỉ xem, KHÔNG ghi'}")
            print(f"Nhịp {_NHIP_GIAY}s/lần ⇒ khoảng "
                  f"{int(len(ds) * _NHIP_GIAY // 60)} phút {int(len(ds) * _NHIP_GIAY % 60)} giây")
            print("─" * 72)

            dem: Counter[str] = Counter()
            so_ghi = 0

            async with httpx.AsyncClient(timeout=20.0) as client:
                for i, lk in enumerate(ds, 1):
                    tt, ho_so = await _tra_mot_so(client, token, lk.so_dien_thoai)
                    dem[tt] += 1

                    if tt == DA_FOLLOW and ho_so:
                        uid = str(ho_so.get("user_id") or "")
                        ten = ho_so.get("display_name") or "(không tên)"
                        print(f"{i:>4}. ✅ {che_giau(lk.so_dien_thoai):<14} "
                              f"uid={uid:<20} Zalo: {ten}")
                        if a.ghi and uid:
                            await db.execute(
                                update(ZaloLienKet)
                                .where(ZaloLienKet.id == lk.id)
                                .values(zalo_user_id=uid)
                            )
                            so_ghi += 1
                    elif tt == CHUA_FOLLOW:
                        print(f"{i:>4}. ○  {che_giau(lk.so_dien_thoai):<14} chưa follow OA")
                    elif tt == SO_HONG:
                        print(f"{i:>4}. ❌ {che_giau(lk.so_dien_thoai):<14} "
                              f"số không hợp lệ / không có Zalo")
                    else:
                        print(f"{i:>4}. ⚠️  {che_giau(lk.so_dien_thoai):<14} {ho_so}")

                    if i < len(ds):
                        await asyncio.sleep(_NHIP_GIAY)

            if a.ghi and so_ghi:
                await db.commit()
                print(f"\nĐã ghi {so_ghi} user_id vào common.zalo_lien_ket")
            elif a.ghi:
                print("\nKhông có user_id nào để ghi")

    finally:
        await engine.dispose()

    tong = sum(dem.values())
    print("─" * 72)
    print(f"TỔNG KẾT trên {tong} số:")
    for nhan, ten in [
        (DA_FOLLOW, "Đã follow OA — dùng được user_id"),
        (CHUA_FOLLOW, "Chưa follow OA — vẫn phải gửi theo SĐT"),
        (SO_HONG, "Số hỏng — cần đơn vị rà lại"),
        (LOI_KHAC, "Lỗi khác"),
    ]:
        n = dem[nhan]
        pc = f"{100.0 * n / tong:.1f}%" if tong else "—"
        print(f"  {ten:<42} {n:>4}  ({pc})")

    if dem[DA_FOLLOW]:
        tiet_kiem = dem[DA_FOLLOW] * (800 - 560)
        print(f"\nNếu gửi cho nhóm đã follow theo user_id (560đ thay vì 800đ):")
        print(f"  tiết kiệm {tiet_kiem:,}đ cho MỖI lượt gửi tới toàn bộ nhóm này"
              .replace(",", "."))
    if not a.ghi and dem[DA_FOLLOW]:
        print("\nChưa ghi gì vào DB. Thêm cờ --ghi khi muốn lưu lại.")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main(sys.argv[1:])))
