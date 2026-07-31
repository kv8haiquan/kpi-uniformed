#!/usr/bin/env python3
"""
scripts/zalo_nap_token.py
==========================
Nạp refresh_token ban đầu của Zalo OA vào common.zalo_token.

CHẠY 1 LẦN lúc cài đặt. Sau đó hệ thống tự refresh và tự ghi đè token mới.

LẤY refresh_token Ở ĐÂU
=======================
1. Vào Zalo Developers (developers.zalo.me) → chọn ứng dụng đã gắn với OA
2. Mục Official Account API → thực hiện luồng ủy quyền (OAuth) cho OA
3. Đổi authorization code lấy cặp access_token + refresh_token
4. Dán refresh_token vào lệnh dưới

CÁCH DÙNG
=========
    cd backend && source venv/bin/activate
    PYTHONPATH=$PWD python scripts/zalo_nap_token.py --refresh-token "xxxxx"

Không truyền token qua tham số dòng lệnh trên máy dùng chung được thì dùng:
    PYTHONPATH=$PWD python scripts/zalo_nap_token.py --hoi
(sẽ hỏi nhập ẩn, không lưu vào lịch sử shell)

⚠️ refresh_token XOAY VÒNG: mỗi lần hệ thống refresh, Zalo cấp token mới và
vô hiệu cái cũ. Vì vậy token dán vào đây chỉ dùng được ĐÚNG MỘT LẦN. Nếu chạy
lại script với token cũ sau khi hệ thống đã refresh, sẽ lỗi và phải lấy token
mới từ Zalo dashboard.
"""

from __future__ import annotations

import argparse
import asyncio
import getpass
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from shared.database import create_db_engine, create_session_factory  # noqa: E402

from common_service.config import settings  # noqa: E402
from common_service.services.zalo.token_store import (  # noqa: E402
    khoi_tao_token,
    lay_access_token,
)


async def chay(refresh_token: str, thu_ngay: bool) -> int:
    engine = create_db_engine(settings.database_url)
    session_factory = create_session_factory(engine)

    async with session_factory() as db:
        await khoi_tao_token(db, refresh_token=refresh_token)
        print("✅ Đã lưu refresh_token vào common.zalo_token")

        if thu_ngay:
            print("\nThử refresh để lấy access_token...")
            try:
                token = await lay_access_token(db)
                print(f"✅ Lấy được access_token (dài {len(token)} ký tự)")
                print("   Token mới đã được ghi đè vào DB.")
            except Exception as e:
                print(f"❌ Refresh thất bại: {e}")
                print("   Kiểm tra lại ZALO_APP_ID / ZALO_OA_SECRET trong .env")
                await engine.dispose()
                return 1

    await engine.dispose()
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description="Nạp refresh_token Zalo OA")
    p.add_argument("--refresh-token", default=None)
    p.add_argument("--hoi", action="store_true", help="Nhập token ẩn qua bàn phím")
    p.add_argument("--khong-thu", action="store_true",
                   help="Chỉ lưu, không thử refresh ngay")
    a = p.parse_args()

    token = a.refresh_token
    if a.hoi or not token:
        token = getpass.getpass("Dán refresh_token của OA: ").strip()
    if not token:
        print("Chưa nhập token.")
        return 1

    if not settings.zalo_app_id or not settings.zalo_oa_secret:
        print("⚠️  Chưa có ZALO_APP_ID / ZALO_OA_SECRET trong .env — "
              "vẫn lưu được refresh_token nhưng chưa refresh được.")

    print(f"DB: {settings.db_name} @ {settings.db_host}:{settings.db_port}\n")
    return asyncio.run(chay(token, thu_ngay=not a.khong_thu))


if __name__ == "__main__":
    raise SystemExit(main())
