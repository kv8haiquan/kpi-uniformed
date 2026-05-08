"""Unit test cho ws_token_service (Phase 4.1 BE_P3).

Tách khỏi test_presentation_rest.py để cover:
- verify_ws_token: invalid/expired/wrong-scope/wrong-type → 401
- create_ws_token: meeting đã hết hạn → 410
"""

from datetime import date, datetime, time, timedelta, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException

from meeting_service.services.ws_token_service import (
    HCM_TZ,
    TOKEN_TYPE,
    create_ws_token,
    verify_ws_token,
    calculate_ws_token_expiry,
)


def _fake_meeting(*, ngay_hop, gio_bat_dau, gio_ket_thuc=None):
    return SimpleNamespace(
        ngay_hop=ngay_hop,
        gio_bat_dau=gio_bat_dau,
        gio_ket_thuc=gio_ket_thuc,
    )


@pytest.mark.asyncio
async def test_create_and_verify_ws_token_roundtrip():
    """Token tạo → verify ra đúng user_id + scope match."""
    user_id = uuid4()
    cuoc_hop_id = uuid4()
    now_hcm = datetime.now(HCM_TZ)
    ch = _fake_meeting(
        ngay_hop=now_hcm.date(),
        gio_bat_dau=time(8, 0),
        gio_ket_thuc=(now_hcm + timedelta(hours=1)).time(),
    )
    token, expires_at = create_ws_token(user_id, cuoc_hop_id, ch)
    assert token
    assert expires_at > now_hcm

    decoded_user_id = verify_ws_token(token, cuoc_hop_id)
    assert decoded_user_id == user_id


@pytest.mark.asyncio
async def test_verify_rejects_wrong_scope():
    """Token cấp cho cuộc họp A → verify với cuộc họp B raise 401."""
    user_id = uuid4()
    cuoc_hop_a = uuid4()
    cuoc_hop_b = uuid4()
    now_hcm = datetime.now(HCM_TZ)
    ch = _fake_meeting(
        ngay_hop=now_hcm.date(),
        gio_bat_dau=time(8, 0),
        gio_ket_thuc=(now_hcm + timedelta(hours=1)).time(),
    )
    token, _ = create_ws_token(user_id, cuoc_hop_a, ch)

    with pytest.raises(HTTPException) as exc_info:
        verify_ws_token(token, cuoc_hop_b)
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_verify_rejects_invalid_signature():
    """Token bịa → 401."""
    with pytest.raises(HTTPException) as exc_info:
        verify_ws_token("not.a.valid.token", uuid4())
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_create_token_raises_410_for_expired_meeting():
    """Cuộc họp đã end + 1h vẫn trong quá khứ → TTL <= 0 → raise 410."""
    user_id = uuid4()
    cuoc_hop_id = uuid4()
    yesterday = (datetime.now(HCM_TZ) - timedelta(days=2)).date()
    ch = _fake_meeting(
        ngay_hop=yesterday,
        gio_bat_dau=time(8, 0),
        gio_ket_thuc=time(10, 0),
    )
    with pytest.raises(HTTPException) as exc_info:
        create_ws_token(user_id, cuoc_hop_id, ch)
    assert exc_info.value.status_code == 410


@pytest.mark.asyncio
async def test_calculate_expiry_caps_at_now_plus_6h():
    """Cuộc họp xa tương lai (1 tháng sau) → cap NOW+6h activate."""
    future_date = (datetime.now(HCM_TZ) + timedelta(days=30)).date()
    ch = _fake_meeting(
        ngay_hop=future_date,
        gio_bat_dau=time(8, 0),
        gio_ket_thuc=time(10, 0),
    )
    expires_at = calculate_ws_token_expiry(ch)
    cap_expected = datetime.now(HCM_TZ) + timedelta(hours=6)
    diff = abs((expires_at - cap_expected).total_seconds())
    assert diff < 60, f"Cap NOW+6h không apply: expires_at={expires_at}, expected~{cap_expected}"
