"""
app/core/login_protection.py
============================
Chống brute-force đăng nhập (đợt vá bảo mật 31/07/2026).

Hai lớp bảo vệ cho POST /api/v1/auth/login:

1. Rate limit theo IP (slowapi): 30 lần/phút/IP.
   - Key ưu tiên header X-Real-IP do nginx set (backend đứng sau proxy nên
     request.client.host luôn là 127.0.0.1).
   - Đặt rộng vì toàn cơ quan có thể ra Internet qua 1 IP NAT chung —
     giờ cao điểm nhiều người đăng nhập cùng lúc không được chặn oan.

2. Khóa tạm theo tài khoản: sai mật khẩu 10 lần liên tiếp → khóa 15 phút.
   - Đếm in-memory (kpi-backend chạy 1 worker uvicorn duy nhất qua PM2;
     restart service = reset bộ đếm, chấp nhận được).
   - Đăng nhập thành công thì reset bộ đếm.

Sự kiện chặn ghi qua logger `app.security` (ra PM2 log) để tra soát.
Tests tắt bằng env DISABLE_LOGIN_RATE_LIMIT=true.
"""

import logging
import os
import time

from slowapi import Limiter
from slowapi.util import get_remote_address

logger = logging.getLogger("app.security")

# =============================================================================
# 1. RATE LIMIT THEO IP
# =============================================================================

LOGIN_RATE_LIMIT = "30/minute"


def get_client_ip(request) -> str:
    """Lấy IP thật của client: X-Real-IP (nginx set) → fallback remote address."""
    return request.headers.get("x-real-ip") or get_remote_address(request) or "unknown"


limiter = Limiter(
    key_func=lambda request: f"login-ip:{get_client_ip(request)}",
    enabled=os.getenv("DISABLE_LOGIN_RATE_LIMIT") != "true",
    default_limits=[],  # KHÔNG global limit — chỉ áp per-endpoint qua decorator
)

# =============================================================================
# 2. KHÓA TẠM THEO TÀI KHOẢN
# =============================================================================

MAX_FAILED_ATTEMPTS = 10          # số lần sai liên tiếp trước khi khóa
LOCKOUT_SECONDS = 15 * 60         # thời gian khóa tạm

# username (đã lowercase) -> {"count": int, "lock_until": epoch seconds}
_failed_logins: dict[str, dict] = {}


def _enabled() -> bool:
    return os.getenv("DISABLE_LOGIN_RATE_LIMIT") != "true"


def seconds_until_unlock(username: str) -> int:
    """Còn bao nhiêu giây nữa tài khoản được thử lại (0 = không bị khóa)."""
    if not _enabled():
        return 0
    entry = _failed_logins.get(username)
    if not entry:
        return 0
    remaining = int(entry.get("lock_until", 0) - time.monotonic())
    if remaining <= 0 and entry.get("lock_until"):
        # Hết hạn khóa — cho thử lại từ đầu
        _failed_logins.pop(username, None)
        return 0
    return max(remaining, 0)


def record_failed_login(username: str, ip: str) -> None:
    """Ghi nhận 1 lần đăng nhập sai; kích hoạt khóa tạm khi đủ ngưỡng."""
    if not _enabled():
        return
    entry = _failed_logins.setdefault(username, {"count": 0, "lock_until": 0})
    entry["count"] += 1
    if entry["count"] >= MAX_FAILED_ATTEMPTS:
        entry["lock_until"] = time.monotonic() + LOCKOUT_SECONDS
        entry["count"] = 0
        logger.warning(
            "LOGIN LOCKOUT: tài khoản '%s' bị khóa tạm %d phút sau %d lần sai liên tiếp (IP: %s)",
            username, LOCKOUT_SECONDS // 60, MAX_FAILED_ATTEMPTS, ip,
        )
    else:
        logger.info(
            "LOGIN FAILED: tài khoản '%s' sai lần %d/%d (IP: %s)",
            username, entry["count"], MAX_FAILED_ATTEMPTS, ip,
        )


def reset_failed_login(username: str) -> None:
    """Đăng nhập thành công — xóa bộ đếm."""
    _failed_logins.pop(username, None)
