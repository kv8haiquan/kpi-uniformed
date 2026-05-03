"""
short_lived_token.py
=====================
JWT short-lived token cho:
1. View/download tài liệu (Module 3) — TTL 1h
2. QR điểm danh (Module 4) — TTL ngắn hơn (mặc định 1h, gắn với cuộc họp)

Dùng cùng SECRET_KEY với main JWT auth — encode/decode bằng `jose.jwt`.
Subject + custom claim "purpose" để phân biệt loại token.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from fastapi import HTTPException, status
from jose import JWTError, jwt

from meeting_service.config import settings


PURPOSE_VIEW_DOC = "view_doc"
PURPOSE_DOWNLOAD_DOC = "download_doc"
PURPOSE_QR_DIEM_DANH = "qr_diem_danh"


def issue_token(
    *,
    purpose: str,
    subject: str,
    extra_claims: Optional[dict[str, Any]] = None,
    ttl_seconds: int = 3600,
) -> str:
    """Sinh token TTL ngắn cho 1 mục đích cụ thể (view/download/qr-diem-danh)."""
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": subject,
        "purpose": purpose,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=ttl_seconds)).timestamp()),
        "type": "short_lived",
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def verify_token(token: str, *, expected_purpose: str) -> dict[str, Any]:
    """Decode + verify token. Raise 401 nếu invalid/expired/wrong purpose."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"success": False, "error": {"code": "TOKEN_INVALID",
                    "message": "Token không hợp lệ hoặc đã hết hạn"}},
        )
    if payload.get("type") != "short_lived":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"success": False, "error": {"code": "TOKEN_TYPE",
                    "message": "Sai loại token"}},
        )
    if payload.get("purpose") != expected_purpose:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"success": False, "error": {"code": "TOKEN_PURPOSE",
                    "message": "Token không dùng cho mục đích này"}},
        )
    return payload
