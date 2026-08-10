#!/usr/bin/env python3
"""
scripts/zalo_doi_code.py
=========================
Đổi `code` từ URL callback của Zalo lấy access_token + refresh_token,
rồi lưu vào common.zalo_token.

⏰ KHẨN: `code` chỉ sống vài phút. Chạy ngay sau khi lấy được URL callback.
Hết hạn thì phải bấm ủy quyền lại trên Zalo để lấy code mới.

CÁCH DÙNG
=========
    cd backend && source venv/bin/activate

    PYTHONPATH=$PWD python scripts/zalo_doi_code.py \
        --app-id 1234567890 \
        --secret  <APP_SECRET_KEY> \
        --code    <chuoi code trong URL callback>

Nếu luồng ủy quyền có dùng PKCE thì thêm:
        --code-verifier <chuoi code_verifier đã dùng lúc tạo URL>

Chỉ thử đổi mà chưa muốn ghi DB:
        --khong-luu

SAU KHI CHẠY XONG
=================
Script chỉ lưu token vào DB. Vẫn phải điền vào backend/.env:
    ZALO_APP_ID=<app id>
    ZALO_OA_SECRET=<secret>
vì mỗi lần làm mới token, hệ thống cần hai giá trị này để gọi Zalo.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from urllib.parse import parse_qs, urlparse

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

import httpx  # noqa: E402

from shared.database import create_db_engine, create_session_factory  # noqa: E402

from common_service.config import settings  # noqa: E402

OAUTH_URL = "https://oauth.zaloapp.com/v4/oa/access_token"


def tach_code(chuoi: str) -> str:
    """Nhận cả URL callback đầy đủ lẫn chuỗi code trần."""
    if chuoi.startswith("http://") or chuoi.startswith("https://"):
        q = parse_qs(urlparse(chuoi).query)
        code = (q.get("code") or [""])[0]
        if not code:
            raise SystemExit("URL không có tham số ?code=")
        return code
    return chuoi.strip()


async def doi_code(
    app_id: str, secret: str, code: str, code_verifier: str | None, luu: bool
) -> int:
    du_lieu = {
        "app_id": app_id,
        "grant_type": "authorization_code",
        "code": code,
    }
    if code_verifier:
        du_lieu["code_verifier"] = code_verifier

    print(f"→ POST {OAUTH_URL}")
    print(f"  app_id={app_id}  code={code[:24]}...({len(code)} ký tự)")
    if code_verifier:
        print("  có kèm code_verifier (PKCE)")
    print()

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                OAUTH_URL,
                headers={
                    "secret_key": secret,
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                data=du_lieu,
            )
    except httpx.HTTPError as e:
        print(f"❌ Lỗi mạng: {e}")
        return 1

    print(f"HTTP {resp.status_code}")
    try:
        kq = resp.json()
    except ValueError:
        print("❌ Zalo trả về không phải JSON:")
        print(resp.text[:1000])
        return 1

    # In nguyên văn phản hồi (che bớt token) để dễ chẩn đoán khi lỗi
    hien_thi = dict(kq)
    for k in ("access_token", "refresh_token"):
        if hien_thi.get(k):
            hien_thi[k] = f"<{len(hien_thi[k])} ký tự>"
    print(json.dumps(hien_thi, ensure_ascii=False, indent=2))
    print()

    access_token = kq.get("access_token")
    refresh_token = kq.get("refresh_token")

    if not access_token or not refresh_token:
        print("❌ KHÔNG lấy được token.")
        loi = str(kq.get("error") or "")
        mo_ta = kq.get("error_description") or kq.get("error_name") or kq.get("message")
        if mo_ta:
            print(f"   Zalo báo: {mo_ta}")
        print()
        print("Nguyên nhân thường gặp:")
        print("  • code đã hết hạn (chỉ sống vài phút) → bấm ủy quyền lại lấy code mới")
        print("  • code đã dùng rồi (chỉ dùng được MỘT lần)")
        print("  • sai app_id hoặc secret_key")
        print("  • luồng có PKCE nhưng thiếu --code-verifier")
        return 1

    try:
        het_han = int(kq.get("expires_in") or 3600)
    except (TypeError, ValueError):
        het_han = 3600

    print("✅ Đổi code thành công")
    print(f"   access_token : {len(access_token)} ký tự, hạn {het_han}s")
    print(f"   refresh_token: {len(refresh_token)} ký tự")

    if not luu:
        print("\n(--khong-luu: KHÔNG ghi vào DB)")
        _in_token_du_phong(refresh_token)
        return 0

    engine = create_db_engine(settings.database_url)
    session_factory = create_session_factory(engine)
    try:
        async with session_factory() as db:
            from common_service.services.zalo.token_store import khoi_tao_token

            await khoi_tao_token(
                db,
                refresh_token=refresh_token,
                access_token=access_token,
                het_han_giay=het_han,
            )
        print(f"\n✅ Đã lưu vào common.zalo_token (DB: {settings.db_name})")
        print("\nBước tiếp theo — điền vào backend/.env:")
        print(f"   ZALO_APP_ID={app_id}")
        print("   ZALO_OA_SECRET=<secret key vừa dùng>")
    except Exception as e:
        # BÀI HỌC 09/08/2026: lần đầu chạy script này, đổi code THÀNH CÔNG nhưng
        # bảng common.zalo_token chưa tồn tại trên prod → ghi hỏng, token mất
        # trắng. Mà `code` chỉ dùng được MỘT lần nên phải đi xin code mới.
        # Từ nay: ghi hỏng thì in token ra để cứu, không nuốt mất nữa.
        print(f"\n❌ ĐỔI CODE THÀNH CÔNG nhưng LƯU DB THẤT BẠI: {e}")
        _in_token_du_phong(refresh_token)
        print("\n⚠️  `code` đã bị tiêu thụ — KHÔNG đổi lại được bằng code cũ.")
        print("   Hãy chép refresh_token ở trên, sửa lỗi DB, rồi nạp lại bằng:")
        print("      python scripts/zalo_nap_token.py --hoi")
        return 1
    finally:
        await engine.dispose()
    return 0


def _in_token_du_phong(refresh_token: str) -> None:
    """In refresh_token đầy đủ ra màn hình để cứu khi không ghi được DB."""
    print("\n" + "=" * 68)
    print("refresh_token ĐẦY ĐỦ — chép ngay và cất chỗ an toàn:")
    print("=" * 68)
    print(refresh_token)
    print("=" * 68)


def main() -> int:
    p = argparse.ArgumentParser(description="Đổi code Zalo lấy token")
    p.add_argument("--app-id", required=True)
    p.add_argument("--secret", required=True, help="App Secret Key")
    p.add_argument("--code", required=True, help="Chuỗi code, hoặc dán cả URL callback")
    p.add_argument("--code-verifier", default=None, help="Nếu luồng dùng PKCE")
    p.add_argument("--khong-luu", action="store_true", help="Chỉ thử, không ghi DB")
    a = p.parse_args()

    code = tach_code(a.code)
    return asyncio.run(
        doi_code(a.app_id, a.secret, code, a.code_verifier, luu=not a.khong_luu)
    )


if __name__ == "__main__":
    raise SystemExit(main())
