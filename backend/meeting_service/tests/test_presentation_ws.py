"""Test WebSocket endpoint (Phase 4.1 BE_P5).

Strategy: gọi `presentation_ws()` handler trực tiếp với mock WebSocket
(tránh phải mở real WS server). Pattern đã verify ở BE_P4.

Coverage:
- 1. test_connect_with_valid_token — accept + state_sync
- 2. test_connect_with_invalid_token — close 1008
- 3. test_connect_wrong_scope — token cuoc_hop khác → close 1008
- 4. test_connect_meeting_len_ke_hoach_close — LEN_KE_HOACH → close 1008
- 5. test_connect_meeting_da_thong_bao_ok — DA_THONG_BAO accept (v3.1)
- 6. test_chu_toa_send_event_broadcasts — chu_toa send page_change → broadcast
- 7. test_dai_bieu_send_event_silent_reject — non-host → no broadcast
- 8. test_disconnect_removes_from_pool — disconnect → pool count giảm
- 9. test_host_reconnect_cancels_disconnect_timer — reconnect trong grace → cancel
- 10. test_host_disconnect_broadcasts_after_grace — wait grace → host_disconnected
- 11. test_close_channel_meeting_ended — manager.close_channel → all WS receive
"""

import asyncio
from datetime import date, time
from typing import Any
from uuid import UUID, uuid4

import pytest
from fastapi import WebSocketDisconnect
from sqlalchemy import text as sa_text
from sqlalchemy.ext.asyncio import AsyncSession

from meeting_service.api.endpoints import presentation_ws as ws_module
from meeting_service.api.endpoints.presentation_ws import presentation_ws
from meeting_service.models import CuocHop
from meeting_service.services.presentation_manager import channel_for
from meeting_service.services.presentation_singletons import (
    backend,
    host_disconnect_timers,
    manager,
)
from meeting_service.services.ws_token_service import create_ws_token


class MockWS:
    """Mock WebSocket — feed/disconnect cho receive_json loop."""

    def __init__(self):
        self.incoming: asyncio.Queue = asyncio.Queue()
        self.sent: list[Any] = []
        self.accepted = False
        self.closed_with: int | None = None
        self._disconnect = False

    async def accept(self) -> None:
        self.accepted = True

    async def send_json(self, data: Any) -> None:
        self.sent.append(data)

    async def close(self, code: int = 1000) -> None:
        if self.closed_with is None:
            self.closed_with = code

    async def receive_json(self) -> Any:
        # Lấy message tiếp theo; nếu disconnect signaled → raise
        while True:
            if self._disconnect and self.incoming.empty():
                raise WebSocketDisconnect(code=1000)
            try:
                return await asyncio.wait_for(self.incoming.get(), timeout=0.1)
            except asyncio.TimeoutError:
                continue

    def feed(self, data: Any) -> None:
        self.incoming.put_nowait(data)

    def disconnect(self) -> None:
        self._disconnect = True


# Helpers ─────────────────────────────────────────────────────────────

async def _seed_meeting(
    db_session: AsyncSession,
    seed_test_users,
    *,
    chu_toa_ma_cc: str = "TEST-G3-001",
    trang_thai: str = "DANG_DIEN_RA",
) -> CuocHop:
    from meeting_service.tests.conftest import TEST_USERS
    chu_toa_id = TEST_USERS[chu_toa_ma_cc]
    ch = CuocHop(
        tieu_de="Test BE_P5 ws",
        ngay_hop=date(2026, 5, 15),
        gio_bat_dau=time(8, 30),
        gio_ket_thuc=time(10, 0),
        don_vi_to_chuc_id=seed_test_users["don_vi_a"],
        chu_toa_id=chu_toa_id,
        created_by=chu_toa_id,
        trang_thai=trang_thai,
    )
    db_session.add(ch)
    await db_session.flush()
    await db_session.refresh(ch)
    return ch


async def _run_handler(ws: MockWS, ch_id: UUID, token: str, db: AsyncSession,
                       wait_for_state_sync: bool = True):
    """Spawn handler task, đợi state_sync gửi xong (nếu accept)."""
    task = asyncio.create_task(
        presentation_ws(websocket=ws, cuoc_hop_id=ch_id, token=token, db=db)
    )
    if wait_for_state_sync:
        # Poll tối đa 0.3s đợi state_sync
        for _ in range(30):
            if any(m.get("type") == "state_sync" for m in ws.sent):
                break
            await asyncio.sleep(0.01)
    return task


@pytest.fixture(autouse=True)
async def _cleanup_singletons():
    """Reset singleton state giữa các test (pool, timers)."""
    yield
    # Cancel any leftover host disconnect timers
    for t in list(host_disconnect_timers.values()):
        t.cancel()
    host_disconnect_timers.clear()
    # Reset pool
    backend._pools.clear()
    backend._host_conns.clear()
    backend._locks.clear()
    # Cancel any debounce tasks in manager
    for t in list(manager._debounce_tasks.values()):
        t.cancel()
    manager._debounce_tasks.clear()


# ════════════════════════════════════════════════════════════════════
# AUTH / SCOPE
# ════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_connect_with_valid_token(db_session: AsyncSession, seed_test_users):
    """1: token hợp lệ + meeting DANG_DIEN_RA → accept + state_sync."""
    ch = await _seed_meeting(db_session, seed_test_users)
    token, _ = create_ws_token(ch.chu_toa_id, ch.id, ch)
    ws = MockWS()
    task = await _run_handler(ws, ch.id, token, db_session)

    assert ws.accepted is True
    sync_events = [m for m in ws.sent if m.get("type") == "state_sync"]
    assert len(sync_events) == 1
    assert sync_events[0]["host_online"] is True

    ws.disconnect()
    await asyncio.wait_for(task, timeout=1.0)


@pytest.mark.asyncio
async def test_connect_with_invalid_token(db_session: AsyncSession, seed_test_users):
    """2: token bịa → close 1008, KHÔNG accept."""
    ch = await _seed_meeting(db_session, seed_test_users)
    ws = MockWS()
    await presentation_ws(
        websocket=ws, cuoc_hop_id=ch.id, token="not.a.valid.jwt", db=db_session
    )
    assert ws.accepted is False
    assert ws.closed_with == 1008


@pytest.mark.asyncio
async def test_connect_wrong_scope(db_session: AsyncSession, seed_test_users):
    """3: token cấp cho meeting A, connect meeting B → close 1008."""
    ch_a = await _seed_meeting(db_session, seed_test_users)
    ch_b = await _seed_meeting(db_session, seed_test_users)
    token_a, _ = create_ws_token(ch_a.chu_toa_id, ch_a.id, ch_a)

    ws = MockWS()
    await presentation_ws(
        websocket=ws, cuoc_hop_id=ch_b.id, token=token_a, db=db_session
    )
    assert ws.closed_with == 1008


@pytest.mark.asyncio
async def test_connect_meeting_len_ke_hoach_close(
    db_session: AsyncSession, seed_test_users
):
    """4: meeting LEN_KE_HOACH → close 1008 (v3.1 scope rule)."""
    ch = await _seed_meeting(db_session, seed_test_users, trang_thai="LEN_KE_HOACH")
    token, _ = create_ws_token(ch.chu_toa_id, ch.id, ch)
    ws = MockWS()
    await presentation_ws(
        websocket=ws, cuoc_hop_id=ch.id, token=token, db=db_session
    )
    assert ws.closed_with == 1008


@pytest.mark.asyncio
async def test_connect_meeting_da_thong_bao_ok(
    db_session: AsyncSession, seed_test_users
):
    """5: meeting DA_THONG_BAO → accept (v3.1 cho phép pre-connect)."""
    ch = await _seed_meeting(db_session, seed_test_users, trang_thai="DA_THONG_BAO")
    token, _ = create_ws_token(ch.chu_toa_id, ch.id, ch)
    ws = MockWS()
    task = await _run_handler(ws, ch.id, token, db_session)
    assert ws.accepted is True
    ws.disconnect()
    await asyncio.wait_for(task, timeout=1.0)


# ════════════════════════════════════════════════════════════════════
# EVENT DISPATCH
# ════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_chu_toa_send_event_broadcasts(
    db_session: AsyncSession, seed_test_users
):
    """6: chu_toa send presentation_end → broadcast presentation_ended tới đại biểu."""
    ch = await _seed_meeting(db_session, seed_test_users)
    # Tài liệu test (CHECK chk_ttc_active_has_doc yêu cầu tai_lieu_hien_tai_id
    # khi is_active=TRUE)
    tl_id = (await db_session.execute(sa_text("""
        INSERT INTO meeting.tai_lieu
            (cuoc_hop_id, ten_tai_lieu, minio_key, file_size, created_by)
        VALUES (:ch, 'test.pdf', 'test/k.pdf', 1024, :uid)
        RETURNING id
    """), {"ch": str(ch.id), "uid": str(ch.chu_toa_id)})).scalar_one()
    # Setup state đang active để presentation_end có gì để end
    await db_session.execute(sa_text("""
        INSERT INTO meeting.trang_thai_trinh_chieu
            (cuoc_hop_id, tai_lieu_hien_tai_id, is_active, bat_dau_luc)
        VALUES (:ch, :tl, TRUE, NOW())
    """), {"ch": str(ch.id), "tl": str(tl_id)})
    await db_session.flush()

    token, _ = create_ws_token(ch.chu_toa_id, ch.id, ch)
    chu_toa_ws = MockWS()
    other_ws = MockWS()

    chu_task = await _run_handler(chu_toa_ws, ch.id, token, db_session)

    # Add đại biểu trực tiếp vào pool (skip auth flow cho speed)
    await backend.add_client(channel_for(ch.id), other_ws, is_host=False)

    # Chu_toa send presentation_end
    chu_toa_ws.feed({"type": "presentation_end"})
    await asyncio.sleep(0.1)  # cho handle_inbound_event chạy

    ended = [m for m in other_ws.sent if m.get("type") == "presentation_ended"]
    assert len(ended) >= 1, f"Đại biểu phải nhận presentation_ended. Got: {other_ws.sent}"

    chu_toa_ws.disconnect()
    await asyncio.wait_for(chu_task, timeout=1.0)


@pytest.mark.asyncio
async def test_dai_bieu_send_event_silent_reject(
    db_session: AsyncSession, seed_test_users
):
    """7: đại biểu (non-host) send page_change → server KHÔNG broadcast."""
    from meeting_service.tests.conftest import TEST_USERS

    ch = await _seed_meeting(db_session, seed_test_users)
    dai_bieu_id = TEST_USERS["TEST-G3-002"]  # KHÔNG phải chu_toa
    token, _ = create_ws_token(dai_bieu_id, ch.id, ch)

    dai_bieu_ws = MockWS()
    listener_ws = MockWS()
    task = await _run_handler(dai_bieu_ws, ch.id, token, db_session)

    await backend.add_client(channel_for(ch.id), listener_ws, is_host=False)

    dai_bieu_ws.feed({"type": "page_change", "page": 99})
    await asyncio.sleep(0.25)

    page_events = [m for m in listener_ws.sent if m.get("type") == "page_changed"]
    assert page_events == [], f"Non-host event KHÔNG được broadcast. Got: {page_events}"

    dai_bieu_ws.disconnect()
    await asyncio.wait_for(task, timeout=1.0)


# ════════════════════════════════════════════════════════════════════
# DISCONNECT / HOST LIFECYCLE
# ════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_disconnect_removes_from_pool(
    db_session: AsyncSession, seed_test_users
):
    """8: WS disconnect → backend.client_count giảm."""
    ch = await _seed_meeting(db_session, seed_test_users)
    token, _ = create_ws_token(ch.chu_toa_id, ch.id, ch)
    ws = MockWS()
    task = await _run_handler(ws, ch.id, token, db_session)

    channel = channel_for(ch.id)
    assert await backend.client_count(channel) == 1

    ws.disconnect()
    await asyncio.wait_for(task, timeout=1.0)

    assert await backend.client_count(channel) == 0


@pytest.mark.asyncio
async def test_host_reconnect_cancels_disconnect_timer(
    db_session: AsyncSession, seed_test_users, monkeypatch
):
    """9: host disconnect → 1s sau reconnect → timer bị cancel + host_reconnected broadcast."""
    # Speed-up grace period cho test deterministic
    monkeypatch.setattr(ws_module, "HOST_RECONNECT_GRACE_S", 1.0)

    ch = await _seed_meeting(db_session, seed_test_users)
    token, _ = create_ws_token(ch.chu_toa_id, ch.id, ch)
    listener_ws = MockWS()
    channel = channel_for(ch.id)
    await backend.add_client(channel, listener_ws, is_host=False)

    # Lần 1: chu_toa connect rồi disconnect → schedule timer
    ws1 = MockWS()
    task1 = await _run_handler(ws1, ch.id, token, db_session)
    ws1.disconnect()
    await asyncio.wait_for(task1, timeout=1.0)
    assert channel in host_disconnect_timers

    # Lần 2: chu_toa reconnect trong grace → cancel timer
    await asyncio.sleep(0.2)
    ws2 = MockWS()
    task2 = await _run_handler(ws2, ch.id, token, db_session)
    assert channel not in host_disconnect_timers

    reconnect_events = [m for m in listener_ws.sent if m.get("type") == "host_reconnected"]
    assert len(reconnect_events) == 1

    ws2.disconnect()
    await asyncio.wait_for(task2, timeout=1.0)


@pytest.mark.asyncio
async def test_host_disconnect_broadcasts_after_grace(
    db_session: AsyncSession, seed_test_users, monkeypatch
):
    """10: host disconnect → sau grace 0.2s → broadcast host_disconnected."""
    monkeypatch.setattr(ws_module, "HOST_RECONNECT_GRACE_S", 0.2)

    ch = await _seed_meeting(db_session, seed_test_users)
    token, _ = create_ws_token(ch.chu_toa_id, ch.id, ch)
    listener_ws = MockWS()
    channel = channel_for(ch.id)
    await backend.add_client(channel, listener_ws, is_host=False)

    ws = MockWS()
    task = await _run_handler(ws, ch.id, token, db_session)
    ws.disconnect()
    await asyncio.wait_for(task, timeout=1.0)

    # Đợi qua grace period
    await asyncio.sleep(0.4)

    disc_events = [m for m in listener_ws.sent if m.get("type") == "host_disconnected"]
    assert len(disc_events) == 1


# ════════════════════════════════════════════════════════════════════
# CLOSE CHANNEL (hook cho BE_P6)
# ════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_close_channel_meeting_ended(
    db_session: AsyncSession, seed_test_users
):
    """11: manager.close_channel → all WS nhận meeting_ended + closed code 1000."""
    ch = await _seed_meeting(db_session, seed_test_users)
    channel = channel_for(ch.id)
    a, b = MockWS(), MockWS()
    await backend.add_client(channel, a)
    await backend.add_client(channel, b)

    await manager.close_channel(ch.id, reason="completed")

    for w in (a, b):
        ended = [m for m in w.sent if m.get("type") == "meeting_ended"]
        assert ended == [{"type": "meeting_ended", "reason": "completed"}]
        assert w.closed_with == 1000
