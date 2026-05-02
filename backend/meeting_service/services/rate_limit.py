"""Rate limiter dùng chung cho meeting_service (Phase 4.1 P0 Hardening).

Threat model:
- Chống abuse upload tài liệu (file lớn, spam upload) — giới hạn theo IP
  (fallback) hoặc user_id (nếu middleware populate `request.state.user_id`).
- Limit MVP: 10 upload / 5 phút. Tune ở `tai_lieu.upload` decorator.
- Tests bypass bằng env `HKG_DISABLE_RATE_LIMIT=true` (conftest set sẵn).
"""

import os

from slowapi import Limiter
from slowapi.util import get_remote_address


def _key_func(request) -> str:
    """Ưu tiên user_id (nếu middleware populate), fallback IP."""
    user_id = getattr(request.state, "user_id", None)
    if user_id:
        return f"user:{user_id}"
    return f"ip:{get_remote_address(request)}"


limiter = Limiter(
    key_func=_key_func,
    enabled=os.getenv("HKG_DISABLE_RATE_LIMIT") != "true",
    default_limits=[],  # KHÔNG global limit, chỉ apply per-endpoint
)
