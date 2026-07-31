"""
common_service/services/zalo/token_store.py
============================================
Quản lý OAuth token của Zalo OA, lưu trong common.zalo_token.

⚠️ ĐIỂM CHẾT NGƯỜI: refresh_token của Zalo XOAY VÒNG.
Mỗi lần gọi refresh, Zalo trả về refresh_token MỚI và vô hiệu hóa cái cũ.
Nếu quá trình ghi đè thất bại (crash, rollback, ghi vào .env thay vì DB) thì
refresh_token trong tay đã chết → không lấy được access_token nào nữa →
phải vào Zalo dashboard ủy quyền lại BẰNG TAY.

Vì vậy ở đây:
  - Token lưu ở DB (ghi đè được), KHÔNG lưu ở .env
  - COMMIT NGAY sau khi nhận token mới, trước khi dùng nó gửi bất cứ tin nào
  - Nếu commit lỗi thì coi như refresh thất bại, không dùng token vừa nhận
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from common_service.config import settings
from common_service.models.zalo import ZaloToken

logger = logging.getLogger("zalo.token")

# Refresh sớm hơn hạn 5 phút để tránh tin gửi đúng lúc token hết hạn
_DEM_TRUOC = timedelta(minutes=5)


class LoiTokenZalo(Exception):
    """Không lấy được access_token dùng được."""


async def _doc_ban_ghi(db: AsyncSession) -> Optional[ZaloToken]:
    kq = await db.execute(select(ZaloToken).where(ZaloToken.ten == "OA"))
    return kq.scalar_one_or_none()


async def khoi_tao_token(
    db: AsyncSession, refresh_token: str, access_token: str = "", het_han_giay: int = 0
) -> ZaloToken:
    """Nạp lần đầu bộ token lấy từ Zalo dashboard (chạy 1 lần lúc cài đặt).

    Dùng qua script `scripts/zalo_nap_token.py`, không gọi từ API để tránh
    lộ token qua HTTP.
    """
    ban_ghi = await _doc_ban_ghi(db)
    het_han = (
        datetime.now(timezone.utc) + timedelta(seconds=het_han_giay)
        if het_han_giay
        else None
    )
    if ban_ghi is None:
        ban_ghi = ZaloToken(ten="OA")
        db.add(ban_ghi)
    ban_ghi.refresh_token = refresh_token
    ban_ghi.access_token = access_token or None
    ban_ghi.het_han_luc = het_han
    ban_ghi.updated_at = datetime.now(timezone.utc)
    await db.commit()
    logger.info("Đã nạp refresh_token ban đầu cho OA")
    return ban_ghi


async def lay_access_token(db: AsyncSession) -> str:
    """Trả access_token còn hạn, tự refresh khi cần.

    Raise LoiTokenZalo nếu chưa nạp token hoặc refresh thất bại.
    """
    ban_ghi = await _doc_ban_ghi(db)
    if ban_ghi is None or not ban_ghi.refresh_token:
        raise LoiTokenZalo(
            "Chưa nạp refresh_token cho OA. Chạy scripts/zalo_nap_token.py trước."
        )

    con_han = (
        ban_ghi.access_token
        and ban_ghi.het_han_luc
        and ban_ghi.het_han_luc - _DEM_TRUOC > datetime.now(timezone.utc)
    )
    if con_han:
        return ban_ghi.access_token  # type: ignore[return-value]

    return await _refresh(db, ban_ghi)


async def _refresh(db: AsyncSession, ban_ghi: ZaloToken) -> str:
    """Gọi Zalo lấy access_token mới và GHI ĐÈ refresh_token xoay vòng."""
    if not settings.zalo_app_id or not settings.zalo_oa_secret:
        raise LoiTokenZalo(
            "Thiếu ZALO_APP_ID hoặc ZALO_OA_SECRET trong .env"
        )

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(
                settings.zalo_oauth_url,
                headers={
                    "secret_key": settings.zalo_oa_secret,
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                data={
                    "app_id": settings.zalo_app_id,
                    "grant_type": "refresh_token",
                    "refresh_token": ban_ghi.refresh_token,
                },
            )
    except httpx.HTTPError as e:
        raise LoiTokenZalo(f"Lỗi mạng khi refresh token: {e}") from e

    try:
        du_lieu = resp.json()
    except ValueError as e:
        raise LoiTokenZalo(f"Zalo trả về không phải JSON (HTTP {resp.status_code})") from e

    access_token = du_lieu.get("access_token")
    refresh_token_moi = du_lieu.get("refresh_token")
    if not access_token or not refresh_token_moi:
        raise LoiTokenZalo(
            f"Zalo không trả token: {du_lieu.get('error')} — "
            f"{du_lieu.get('error_description') or du_lieu.get('message')}"
        )

    try:
        het_han_giay = int(du_lieu.get("expires_in") or 3600)
    except (TypeError, ValueError):
        het_han_giay = 3600

    now = datetime.now(timezone.utc)
    ban_ghi.access_token = access_token
    ban_ghi.refresh_token = refresh_token_moi  # BẮT BUỘC ghi đè
    ban_ghi.het_han_luc = now + timedelta(seconds=het_han_giay)
    ban_ghi.lan_refresh_cuoi = now
    ban_ghi.updated_at = now

    # Commit TRƯỚC khi trả token ra dùng — nếu ghi hỏng thì thà coi như
    # refresh thất bại còn hơn dùng token mà refresh_token mới đã mất.
    try:
        await db.commit()
    except Exception as e:  # pragma: no cover — phụ thuộc lỗi DB
        await db.rollback()
        raise LoiTokenZalo(
            f"Nhận được token mới nhưng KHÔNG ghi được vào DB: {e}. "
            "Không dùng token này để tránh mất refresh_token."
        ) from e

    logger.info("Đã refresh access_token Zalo, hạn %s", ban_ghi.het_han_luc)
    return access_token
