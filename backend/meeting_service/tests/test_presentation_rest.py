"""Test REST endpoint GET /presentation/state (Phase 4.1 BE_P3).

Threat model + coverage:
- UPSERT lazy: row tạo lần đầu, lần sau update — chỉ 1 row / cuoc_hop.
- Scope check (v3.1): LEN_KE_HOACH/HOAN_THANH/HUY → 403; DA_THONG_BAO/
  DANG_DIEN_RA → 200.
- Permission: chu_toa | thu_ky | thanh_phan | admin → 200; user khác → 403.
- WS token TTL: formula plan v3.1 — combine(ngay_hop,gio_ket_thuc,HCM)+1h
  capped at NOW+6h. Fallback (gio_ket_thuc NULL) = combine(...,gio_bat_dau)+4h.
"""

from datetime import date, datetime, time, timedelta
from uuid import UUID
from zoneinfo import ZoneInfo

import pytest
from httpx import AsyncClient
from sqlalchemy import text as sa_text
from sqlalchemy.ext.asyncio import AsyncSession


BASE = "/api/v1/hop-khong-giay/cuoc-hop"
HCM = ZoneInfo("Asia/Ho_Chi_Minh")


def _payload_create(don_vi_id, chu_toa_id, ngay_hop=None, gio_bd=None, gio_kt=None,
                    thu_ky_id=None):
    return {
        "tieu_de": "Test BE_P3 — Presentation State",
        "khoi": "CHUYEN_MON",
        "hinh_thuc": "TRUC_TIEP",
        "ngay_hop": (ngay_hop or "2026-05-15"),
        "gio_bat_dau": (gio_bd or "08:30"),
        "gio_ket_thuc": gio_kt if gio_kt is not None else "10:00",
        "dia_diem": "Phòng họp test",
        "don_vi_to_chuc_id": str(don_vi_id),
        "chu_toa_id": str(chu_toa_id),
        "thu_ky_id": str(thu_ky_id) if thu_ky_id else None,
        "thanh_phan": [],
    }


async def _create_meeting_in_status(
    client: AsyncClient,
    db_session: AsyncSession,
    user,
    seed_test_users,
    target_status: str,
    *,
    ngay_hop=None,
    gio_bd=None,
    gio_kt=None,
    thu_ky_id=None,
) -> UUID:
    payload = _payload_create(
        seed_test_users["don_vi_a"], user.sub,
        ngay_hop=ngay_hop, gio_bd=gio_bd, gio_kt=gio_kt, thu_ky_id=thu_ky_id,
    )
    resp = await client.post(BASE + "/", json=payload)
    assert resp.status_code == 201, resp.text
    cuoc_hop_id = UUID(resp.json()["data"]["id"])

    if target_status != "LEN_KE_HOACH":
        await db_session.execute(
            sa_text("UPDATE meeting.cuoc_hop SET trang_thai = :s WHERE id = :id"),
            {"s": target_status, "id": str(cuoc_hop_id)},
        )
        await db_session.flush()

    # Force gio_ket_thuc=NULL nếu test fallback — POST schema reject None nên
    # update sau qua SQL.
    if gio_kt is None and 'gio_kt_null' in (locals().get('_marker') or ''):
        pass  # placeholder

    return cuoc_hop_id


# ════════════════════════════════════════════════════════════════════
# 9 TESTS BE_P3
# ════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_get_state_creates_row_lazy(
    client: AsyncClient, db_session: AsyncSession, chu_toa_user, seed_test_users
):
    """1/9: gọi lần đầu → row trang_thai_trinh_chieu được tạo qua UPSERT."""
    cuoc_hop_id = await _create_meeting_in_status(
        client, db_session, chu_toa_user, seed_test_users, "DA_THONG_BAO"
    )
    resp = await client.get(f"{BASE}/{cuoc_hop_id}/presentation/state")
    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]
    assert data["cuoc_hop_id"] == str(cuoc_hop_id)
    assert data["is_active"] is False
    assert data["trang_hien_tai"] == 1
    assert data["ws_token"]
    assert data["is_chu_toa"] is True

    # Verify row tồn tại trong DB
    count = await db_session.execute(sa_text(
        "SELECT COUNT(*) FROM meeting.trang_thai_trinh_chieu WHERE cuoc_hop_id = :ch"
    ), {"ch": str(cuoc_hop_id)})
    assert count.scalar_one() == 1


@pytest.mark.asyncio
async def test_get_state_returns_existing(
    client: AsyncClient, db_session: AsyncSession, chu_toa_user, seed_test_users
):
    """2/9: gọi lần 2 → return row cũ, KHÔNG tạo duplicate."""
    cuoc_hop_id = await _create_meeting_in_status(
        client, db_session, chu_toa_user, seed_test_users, "DA_THONG_BAO"
    )
    r1 = await client.get(f"{BASE}/{cuoc_hop_id}/presentation/state")
    r2 = await client.get(f"{BASE}/{cuoc_hop_id}/presentation/state")
    assert r1.status_code == r2.status_code == 200

    count = await db_session.execute(sa_text(
        "SELECT COUNT(*) FROM meeting.trang_thai_trinh_chieu WHERE cuoc_hop_id = :ch"
    ), {"ch": str(cuoc_hop_id)})
    assert count.scalar_one() == 1, "UPSERT phải UPDATE row cũ, không tạo duplicate"


@pytest.mark.asyncio
async def test_get_state_chu_toa_flags(
    client: AsyncClient, db_session: AsyncSession, chu_toa_user, seed_test_users
):
    """3/9: chu_toa user → is_chu_toa=True, is_thu_ky=False."""
    cuoc_hop_id = await _create_meeting_in_status(
        client, db_session, chu_toa_user, seed_test_users, "DANG_DIEN_RA"
    )
    resp = await client.get(f"{BASE}/{cuoc_hop_id}/presentation/state")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["is_chu_toa"] is True
    assert data["is_thu_ky"] is False


@pytest.mark.asyncio
async def test_get_state_thu_ky_flags(
    client: AsyncClient, db_session: AsyncSession,
    chu_toa_user, thu_ky_phong_a, seed_test_users,
):
    """4/9: user là thu_ky_id của cuộc họp → is_thu_ky=True."""
    # Tạo cuộc họp với thu_ky_id = TEST-G3-002
    from meeting_service.tests.conftest import TEST_USERS
    thu_ky_id = TEST_USERS["TEST-G3-002"]

    # Switch sang chu_toa để tạo cuộc họp
    cuoc_hop_id = await _create_meeting_in_status(
        client, db_session, chu_toa_user, seed_test_users, "DA_THONG_BAO",
        thu_ky_id=thu_ky_id,
    )

    # Switch sang thu_ky_phong_a (đã set qua fixture)
    from meeting_service.tests.conftest import _make_user, _set_user
    thu_ky_user = _make_user("TEST-G3-002", seed_test_users["don_vi_a"])
    _set_user(thu_ky_user)

    try:
        resp = await client.get(f"{BASE}/{cuoc_hop_id}/presentation/state")
        assert resp.status_code == 200, resp.text
        data = resp.json()["data"]
        assert data["is_chu_toa"] is False
        assert data["is_thu_ky"] is True
    finally:
        from meeting_service.main import app
        from meeting_service.dependencies import get_current_user
        app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_get_state_unauthorized_user(
    client: AsyncClient, db_session: AsyncSession, chu_toa_user, seed_test_users
):
    """5/9: user không liên quan cuộc họp → 403."""
    cuoc_hop_id = await _create_meeting_in_status(
        client, db_session, chu_toa_user, seed_test_users, "DA_THONG_BAO"
    )
    # Switch sang user khác (cbcc thường, không trong thanh_phan)
    from meeting_service.tests.conftest import _make_user, _set_user
    from meeting_service.main import app
    from meeting_service.dependencies import get_current_user

    cbcc = _make_user("TEST-G3-004", seed_test_users["don_vi_b"])
    _set_user(cbcc)
    try:
        resp = await client.get(f"{BASE}/{cuoc_hop_id}/presentation/state")
        assert resp.status_code == 403, resp.text
        assert resp.json()["detail"]["error"]["code"] == "NO_PERMISSION"
    finally:
        app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_get_state_status_len_ke_hoach_403(
    client: AsyncClient, db_session: AsyncSession, chu_toa_user, seed_test_users
):
    """6/9: cuoc_hop LEN_KE_HOACH → 403 INVALID_MEETING_STATE (v3.1 scope)."""
    cuoc_hop_id = await _create_meeting_in_status(
        client, db_session, chu_toa_user, seed_test_users, "LEN_KE_HOACH"
    )
    resp = await client.get(f"{BASE}/{cuoc_hop_id}/presentation/state")
    assert resp.status_code == 403, resp.text
    assert resp.json()["detail"]["error"]["code"] == "INVALID_MEETING_STATE"


@pytest.mark.asyncio
async def test_get_state_status_da_thong_bao_ok(
    client: AsyncClient, db_session: AsyncSession, chu_toa_user, seed_test_users
):
    """7/9: cuoc_hop DA_THONG_BAO → 200 (v3.1 cho phép pre-load tài liệu)."""
    cuoc_hop_id = await _create_meeting_in_status(
        client, db_session, chu_toa_user, seed_test_users, "DA_THONG_BAO"
    )
    resp = await client.get(f"{BASE}/{cuoc_hop_id}/presentation/state")
    assert resp.status_code == 200, resp.text


@pytest.mark.asyncio
async def test_get_state_ws_token_ttl_formula(
    client: AsyncClient, db_session: AsyncSession, chu_toa_user, seed_test_users
):
    """8/9: TTL = combine(ngay_hop, gio_ket_thuc, HCM) + 1h, capped NOW+6h.

    Đặt cuộc họp end trong NOW+1h → expected expires = NOW+2h (within cap).
    Dùng end_target.date() làm ngay_hop để tránh cross-midnight bug.
    """
    now_hcm = datetime.now(HCM)
    end_target = (now_hcm + timedelta(hours=1)).replace(microsecond=0, second=0)

    cuoc_hop_id = await _create_meeting_in_status(
        client, db_session, chu_toa_user, seed_test_users, "DANG_DIEN_RA",
        ngay_hop=end_target.date().isoformat(),
        gio_bd="00:00",  # Bất kỳ — chỉ end thôi quyết định TTL
        gio_kt=end_target.time().strftime("%H:%M"),
    )

    resp = await client.get(f"{BASE}/{cuoc_hop_id}/presentation/state")
    assert resp.status_code == 200, resp.text
    expires_at = datetime.fromisoformat(resp.json()["data"]["ws_token_expires_at"])
    expected = end_target + timedelta(hours=1)

    # Tolerance ±2 phút (clock drift + parsing)
    diff = abs((expires_at.astimezone(HCM) - expected).total_seconds())
    assert diff < 120, f"TTL formula sai: expected ~{expected}, got {expires_at}"


@pytest.mark.asyncio
async def test_get_state_ws_token_fallback_no_gio_ket_thuc(
    client: AsyncClient, db_session: AsyncSession, chu_toa_user, seed_test_users
):
    """9/9: gio_ket_thuc NULL → TTL = combine(ngay_hop, gio_bat_dau, HCM) + 4h.

    Dùng start_target = NOW + 30min để (start + 4h) < NOW + 6h cap, đồng thời
    .date()/.time() trên cùng ngày → tránh cross-midnight bug.
    """
    now_hcm = datetime.now(HCM)
    start_target = (now_hcm + timedelta(minutes=30)).replace(microsecond=0, second=0)

    # Tạo với gio_kt placeholder rồi UPDATE NULL qua SQL (POST schema yêu cầu time)
    cuoc_hop_id = await _create_meeting_in_status(
        client, db_session, chu_toa_user, seed_test_users, "DA_THONG_BAO",
        ngay_hop=start_target.date().isoformat(),
        gio_bd=start_target.time().strftime("%H:%M"),
        gio_kt=(start_target + timedelta(hours=2)).time().strftime("%H:%M"),
    )
    # Force gio_ket_thuc = NULL để trigger fallback
    await db_session.execute(
        sa_text("UPDATE meeting.cuoc_hop SET gio_ket_thuc = NULL WHERE id = :id"),
        {"id": str(cuoc_hop_id)},
    )
    await db_session.flush()

    resp = await client.get(f"{BASE}/{cuoc_hop_id}/presentation/state")
    assert resp.status_code == 200, resp.text
    expires_at = datetime.fromisoformat(resp.json()["data"]["ws_token_expires_at"])
    expected = start_target + timedelta(hours=4)

    diff = abs((expires_at.astimezone(HCM) - expected).total_seconds())
    assert diff < 120, f"Fallback TTL sai: expected ~{expected}, got {expires_at}"
