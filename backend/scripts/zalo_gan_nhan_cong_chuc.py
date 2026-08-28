"""
scripts/zalo_gan_nhan_cong_chuc.py
===================================
Gắn nhãn Zalo OA cho công chức Chi cục, để kịch bản chatbot chỉ gửi tin ôn tập
cho người trong cơ quan — không gửi cho người dân đang theo dõi OA.

VÌ SAO CẦN
==========
OA có 758 người theo dõi (28/08/2026) nhưng chỉ ~327 là công chức. Quy tắc hẹn
giờ của chatbot lọc được người nhận theo NHÃN, nên phải gắn nhãn cho đúng nhóm
công chức thì hơn 400 người dân mới không bị làm phiền mỗi sáng.

VÌ SAO CHIA NHIỀU NHÃN
======================
Zalo giới hạn MỖI NHÃN tối đa 200 người. Vượt quá thì hệ thống TỰ GỠ nhãn của
người được gắn lâu nhất — âm thầm, không báo gì. Người bị gỡ sẽ lặng lẽ không
nhận được câu hỏi nữa. Vì vậy chia thành nhiều nhãn, mỗi nhãn giữ dưới ngưỡng
`SUC_CHUA_MOI_NHAN` để còn chỗ cho người follow thêm về sau.

VÌ SAO CHIA BẰNG SỐ DƯ CỦA user_id
==================================
Chia theo thứ tự danh sách thì chỉ cần thêm một người ở đầu là toàn bộ những
người sau bị dồn sang nhãn khác. Chia bằng `int(user_id) % số_nhãn` thì mỗi
người luôn rơi vào cùng một nhãn qua mọi lần chạy, miễn là số nhãn không đổi.

CHẠY
====
    cd backend && source venv/bin/activate

    python scripts/zalo_gan_nhan_cong_chuc.py            # chỉ xem, KHÔNG ghi
    python scripts/zalo_gan_nhan_cong_chuc.py --ghi      # gắn nhãn thật

Chạy lại được nhiều lần: gắn lại nhãn cũ cho cùng một người là thao tác vô hại,
nên cứ chạy định kỳ để nhặt công chức mới follow OA. Đặt cron hằng tuần:

    0 6 * * 1  cd /opt/kpi-prod/backend && venv/bin/python \
               scripts/zalo_gan_nhan_cong_chuc.py --ghi >> /var/log/zalo-nhan.log 2>&1

⚠️ GHI RA NGOÀI: script này thay đổi dữ liệu trên OA thật (gắn nhãn cho người
   dùng Zalo). Không phải thao tác chỉ-đọc như `zalo_tra_uid.py`. Gỡ được bằng
   API `rmfollowerfromtag` nếu cần.

⚠️ CHƯA XỬ LÝ: công chức nghỉ/chuyển đi vẫn giữ nhãn cũ. Muốn gỡ thì bổ sung
   nhánh gọi `rmfollowerfromtag` cho người có `is_active = false`.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from collections import Counter, defaultdict
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select  # noqa: E402

from shared.database import create_db_engine, create_session_factory  # noqa: E402

from common_service.config import settings  # noqa: E402
from common_service.models.zalo import ZaloLienKet  # noqa: E402
from common_service.services.zalo.token_store import lay_access_token  # noqa: E402

_URL_GAN_NHAN = "https://openapi.zalo.me/v2.0/oa/tag/tagfollower"

# Trần cứng của Zalo là 200/nhãn. Giữ 150 để còn chỗ cho người follow thêm
# giữa hai lần chạy — chạm trần là Zalo âm thầm gỡ người cũ ra.
SUC_CHUA_MOI_NHAN = 150

TIEN_TO_NHAN = "CC_HQKV08"

# Zalo chặn tần suất; 0.3s/lần cũng là nhịp `zalo_tra_uid.py` đang dùng
_NHIP_GIAY = 0.3


def _ten_nhan(user_id: str, so_nhan: int) -> str:
    """Người nào vào nhãn nào — ổn định qua các lần chạy."""
    try:
        thu_tu = int(user_id) % so_nhan
    except ValueError:
        # user_id không phải số (chưa gặp) — vẫn phải xếp vào đâu đó
        thu_tu = sum(ord(c) for c in user_id) % so_nhan
    return f"{TIEN_TO_NHAN}_{thu_tu + 1}"


async def _gan_mot(
    client: httpx.AsyncClient, token: str, user_id: str, nhan: str
) -> tuple[bool, str]:
    """Trả về (thành công, mô tả). Không ném lỗi."""
    try:
        r = await client.post(
            _URL_GAN_NHAN,
            headers={"access_token": token, "Content-Type": "application/json"},
            json={"user_id": user_id, "tag_name": nhan},
        )
        d = r.json()
    except (httpx.HTTPError, ValueError) as e:
        return False, str(e)[:100]

    if d.get("error") == 0:
        return True, "ok"
    return False, f"error={d.get('error')} {str(d.get('message'))[:80]}"


async def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description="Gắn nhãn Zalo cho công chức")
    p.add_argument("--ghi", action="store_true", help="GẮN NHÃN THẬT trên OA")
    p.add_argument(
        "--suc-chua",
        type=int,
        default=SUC_CHUA_MOI_NHAN,
        help=f"Số người tối đa mỗi nhãn (mặc định {SUC_CHUA_MOI_NHAN}, trần Zalo là 200)",
    )
    a = p.parse_args(argv)

    if a.suc_chua > 200:
        print("⛔ Zalo giới hạn 200 người/nhãn. Đặt --suc-chua ≤ 200.")
        return 1

    engine = create_db_engine(settings.database_url)
    session_factory = create_session_factory(engine)

    try:
        async with session_factory() as db:
            token = await lay_access_token(db)

            ds = list(
                (
                    await db.scalars(
                        select(ZaloLienKet)
                        .where(ZaloLienKet.zalo_user_id.isnot(None))
                        .order_by(ZaloLienKet.created_at)
                    )
                ).all()
            )

        if not ds:
            print("Chưa có user_id nào. Chạy scripts/zalo_tra_uid.py --tat-ca --ghi trước.")
            return 1

        so_nhan = max(1, -(-len(ds) // a.suc_chua))  # làm tròn lên
        nhom: dict[str, list[str]] = defaultdict(list)
        for lk in ds:
            nhom[_ten_nhan(lk.zalo_user_id, so_nhan)].append(lk.zalo_user_id)

        print(f"{len(ds)} công chức có user_id → chia {so_nhan} nhãn "
              f"(tối đa {a.suc_chua}/nhãn, trần Zalo 200)")
        for ten in sorted(nhom):
            print(f"   {ten:<16} {len(nhom[ten])} người")
        print("─" * 72)

        if not a.ghi:
            print("Chế độ chỉ xem — KHÔNG gắn nhãn. Thêm --ghi để gắn thật.")
            return 0

        dem: Counter[str] = Counter()
        loi_dau: dict[str, str] = {}
        async with httpx.AsyncClient(timeout=25.0) as client:
            for ten in sorted(nhom):
                for i, uid in enumerate(nhom[ten], 1):
                    ok, mo_ta = await _gan_mot(client, token, uid, ten)
                    dem["ok" if ok else "loi"] += 1
                    if not ok and mo_ta not in loi_dau:
                        loi_dau[mo_ta] = uid
                    if i % 25 == 0:
                        print(f"   {ten}: {i}/{len(nhom[ten])}")
                    await asyncio.sleep(_NHIP_GIAY)
                print(f"✔ {ten}: xong {len(nhom[ten])} người")

        print("─" * 72)
        print(f"Thành công: {dem['ok']}   Lỗi: {dem['loi']}")
        for mo_ta in loi_dau:
            print(f"   lỗi: {mo_ta}")
        return 0 if dem["loi"] == 0 else 2

    finally:
        await engine.dispose()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main(sys.argv[1:])))
