"""WebSocket token service cho Phase 4.1 — Page-Sync.

Threat model:
- WS token là JWT short-lived gắn scope `meeting:{cuoc_hop_id}` để client
  kết nối WS endpoint `/ws/.../cuoc-hop/{id}/presentation`.
- Verify scope match path → chống cross-meeting injection (token cuộc họp A
  không kết nối được WS cuộc họp B).
- TTL bounded: tối đa NOW+6h, không auto-refresh — nếu cần dùng tiếp,
  client gọi lại REST `GET /presentation/state`.
- Plan v3.1 §3.2 formula:
    end_dt = combine(ngay_hop, gio_ket_thuc, tz=Asia/HCM)
    candidate = end_dt + 1h
    fallback (gio_ket_thuc NULL) = combine(ngay_hop, gio_bat_dau, tz=HCM) + 4h
    cap = NOW + 6h
    TTL = min(candidate, cap); TTL <= 0 → 410 Gone.

KHÔNG reuse short_lived_token vì:
- TTL động theo cuoc_hop, không cố định 3600s
- Scope binding (meeting_id) bắt buộc verify
- "type" = "ws_presentation" để tách khỏi token tài liệu
"""

from __future__ import annotations

import zoneinfo
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from fastapi import HTTPException, status
from jose import JWTError, jwt

from meeting_service.config import settings


HCM_TZ = zoneinfo.ZoneInfo("Asia/Ho_Chi_Minh")
TOKEN_TYPE = "ws_presentation"
TOKEN_MAX_TTL_HOURS = 6
DEFAULT_BUFFER_AFTER_END_HOURS = 1
FALLBACK_DURATION_HOURS = 4


def calculate_ws_token_expiry(cuoc_hop) -> datetime:
    """Tính WS token expiration theo formula plan v3.1.

    Args:
        cuoc_hop: ORM object có ngay_hop (date), gio_bat_dau (time),
                  gio_ket_thuc (time, có thể NULL).

    Returns:
        timezone-aware datetime in Asia/Ho_Chi_Minh, đã apply cap NOW+6h.
        Có thể trả về thời điểm trong quá khứ nếu cuộc họp đã kết thúc lâu —
        caller phải kiểm `expires_at <= now()` để raise 410.
    """
    if cuoc_hop.gio_ket_thuc is not None:
        end_naive = datetime.combine(cuoc_hop.ngay_hop, cuoc_hop.gio_ket_thuc)
        end_aware = end_naive.replace(tzinfo=HCM_TZ)
        candidate = end_aware + timedelta(hours=DEFAULT_BUFFER_AFTER_END_HOURS)
    else:
        # Fallback: ngay_hop + gio_bat_dau + 4h (giả định cuộc họp ~4h)
        start_naive = datetime.combine(cuoc_hop.ngay_hop, cuoc_hop.gio_bat_dau)
        start_aware = start_naive.replace(tzinfo=HCM_TZ)
        candidate = start_aware + timedelta(hours=FALLBACK_DURATION_HOURS)

    cap = datetime.now(HCM_TZ) + timedelta(hours=TOKEN_MAX_TTL_HOURS)
    return min(candidate, cap)


def create_ws_token(
    user_id: UUID,
    cuoc_hop_id: UUID,
    cuoc_hop,
) -> tuple[str, datetime]:
    """Tạo short-lived JWT cho WebSocket connection.

    JWT payload: sub, scope, type, iat, exp.
    Returns: (token_string, expires_at_datetime).
    Raise HTTPException 410 nếu cuộc họp đã hết hạn (TTL <= 0).
    """
    expires_at = calculate_ws_token_expiry(cuoc_hop)
    now = datetime.now(HCM_TZ)
    if expires_at <= now:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail={
                "success": False,
                "error": {
                    "code": "MEETING_EXPIRED",
                    "message": "Cuộc họp đã kết thúc — không thể cấp WS token mới.",
                },
            },
        )

    payload: dict[str, Any] = {
        "sub": str(user_id),
        "scope": f"meeting:{cuoc_hop_id}",
        "type": TOKEN_TYPE,
        "iat": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
    }
    token = jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)
    return token, expires_at


def verify_ws_token(token: str, cuoc_hop_id: UUID) -> UUID:
    """Verify WS token + return user_id.

    Raise HTTPException 401 nếu: invalid signature, expired, wrong type,
    wrong scope (token cuộc họp khác).
    """
    err = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={
            "success": False,
            "error": {"code": "WS_TOKEN_INVALID", "message": "Token không hợp lệ"},
        },
    )
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    except JWTError:
        raise err

    if payload.get("type") != TOKEN_TYPE:
        raise err

    expected_scope = f"meeting:{cuoc_hop_id}"
    if payload.get("scope") != expected_scope:
        raise err

    sub = payload.get("sub")
    if not sub:
        raise err
    try:
        return UUID(sub)
    except (ValueError, TypeError):
        raise err
