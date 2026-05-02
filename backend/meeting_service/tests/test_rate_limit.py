"""Smoke test cho rate_limit module (Phase 4.1 P0).

Verify config + key_func behavior. Manual load test (11 upload → 429)
documented trong scripts/INSTALL_CRON.md §3.1.
"""

import os
from unittest.mock import MagicMock

import pytest


@pytest.mark.asyncio
async def test_limiter_disabled_in_test_env():
    """Conftest set HKG_DISABLE_RATE_LIMIT=true → limiter.enabled=False."""
    # Conftest đã set env ở module top, nhưng limiter init xảy ra khi import.
    # Verify env đúng giá trị.
    assert os.getenv("HKG_DISABLE_RATE_LIMIT") == "true"

    from meeting_service.services.rate_limit import limiter
    assert limiter.enabled is False, (
        "Limiter phải DISABLED trong test env để tránh 429 false positive"
    )


@pytest.mark.asyncio
async def test_key_func_prefers_user_id_over_ip():
    """key_func: ưu tiên request.state.user_id, fallback IP."""
    from meeting_service.services.rate_limit import _key_func

    # Mock request có user_id
    req_with_user = MagicMock()
    req_with_user.state.user_id = "abc-123"
    assert _key_func(req_with_user) == "user:abc-123"

    # Mock request KHÔNG có user_id → fallback IP
    req_no_user = MagicMock()
    req_no_user.state = MagicMock(spec=[])  # không có attr user_id
    req_no_user.client.host = "192.168.1.10"
    req_no_user.headers = {}
    key = _key_func(req_no_user)
    assert key.startswith("ip:"), f"Expected ip: prefix, got {key}"


@pytest.mark.asyncio
async def test_app_has_limiter_state():
    """main.py wire app.state.limiter + exception handler."""
    from meeting_service.main import app
    from meeting_service.services.rate_limit import limiter as expected_limiter

    assert hasattr(app.state, "limiter")
    assert app.state.limiter is expected_limiter
