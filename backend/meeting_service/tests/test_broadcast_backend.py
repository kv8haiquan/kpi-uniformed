"""Test InMemoryBackend (Phase 4.1 BE_P4 — pool/broadcast/close).

Threat model focus:
- Async lock protect pool state khi concurrent add/remove
- 1 client lỗi không được break broadcast cho clients khác
- close_channel cleanup pool + close all WS với code 1000
"""

import asyncio
from typing import Any
from uuid import uuid4

import pytest

from meeting_service.services.broadcast_backend import InMemoryBackend


class MockWS:
    """Mock WebSocket — tracking gửi/đóng cho test."""

    def __init__(self, name: str = "ws", fail_send: bool = False):
        self.name = name
        self.sent: list[Any] = []
        self.closed_with: list[int] = []
        self.fail_send = fail_send

    async def send_json(self, data: Any) -> None:
        if self.fail_send:
            raise RuntimeError(f"{self.name}: simulated send failure")
        self.sent.append(data)

    async def close(self, code: int = 1000) -> None:
        self.closed_with.append(code)


@pytest.mark.asyncio
async def test_add_remove_client():
    """1/12: pool tracking đúng add/remove + cleanup khi empty."""
    backend = InMemoryBackend()
    ch = "meeting:" + str(uuid4())
    a, b = MockWS("a"), MockWS("b")

    await backend.add_client(ch, a)
    await backend.add_client(ch, b, is_host=True)
    assert await backend.client_count(ch) == 2
    assert await backend.host_count(ch) == 1

    await backend.remove_client(ch, a)
    assert await backend.client_count(ch) == 1

    await backend.remove_client(ch, b)
    assert await backend.client_count(ch) == 0


@pytest.mark.asyncio
async def test_broadcast_to_all_clients():
    """2/12: broadcast → tất cả client trong channel nhận event."""
    backend = InMemoryBackend()
    ch = "meeting:" + str(uuid4())
    clients = [MockWS(f"c{i}") for i in range(5)]
    for c in clients:
        await backend.add_client(ch, c)

    await backend.broadcast(ch, {"type": "ping"})
    for c in clients:
        assert c.sent == [{"type": "ping"}]


@pytest.mark.asyncio
async def test_broadcast_excludes_sender():
    """3/12: exclude param → sender KHÔNG nhận lại event."""
    backend = InMemoryBackend()
    ch = "meeting:" + str(uuid4())
    sender = MockWS("sender")
    others = [MockWS(f"o{i}") for i in range(3)]
    await backend.add_client(ch, sender)
    for o in others:
        await backend.add_client(ch, o)

    await backend.broadcast(ch, {"type": "x"}, exclude=sender)
    assert sender.sent == []
    for o in others:
        assert o.sent == [{"type": "x"}]


@pytest.mark.asyncio
async def test_broadcast_handles_client_error():
    """4/12: 1 client raise → broadcast vẫn tới các client khác."""
    backend = InMemoryBackend()
    ch = "meeting:" + str(uuid4())
    bad = MockWS("bad", fail_send=True)
    good1, good2 = MockWS("g1"), MockWS("g2")
    for c in [bad, good1, good2]:
        await backend.add_client(ch, c)

    await backend.broadcast(ch, {"type": "ping"})
    assert good1.sent == [{"type": "ping"}]
    assert good2.sent == [{"type": "ping"}]
    # bad client không có gì sent (raise)
    assert bad.sent == []


@pytest.mark.asyncio
async def test_host_count_tracking():
    """5/12: host_count đúng theo is_host flag."""
    backend = InMemoryBackend()
    ch = "meeting:" + str(uuid4())
    h, c1, c2 = MockWS("host"), MockWS("c1"), MockWS("c2")
    await backend.add_client(ch, h, is_host=True)
    await backend.add_client(ch, c1)
    await backend.add_client(ch, c2)
    assert await backend.host_count(ch) == 1
    assert await backend.client_count(ch) == 3

    await backend.remove_client(ch, h)
    assert await backend.host_count(ch) == 0
    assert await backend.client_count(ch) == 2


@pytest.mark.asyncio
async def test_concurrent_add_remove():
    """6/12: concurrent add/remove 50 clients → no race, count chính xác."""
    backend = InMemoryBackend()
    ch = "meeting:" + str(uuid4())

    async def cycle(i: int):
        ws = MockWS(f"c{i}")
        await backend.add_client(ch, ws)
        await asyncio.sleep(0)  # cooperative yield
        await backend.remove_client(ch, ws)

    await asyncio.gather(*(cycle(i) for i in range(50)))
    assert await backend.client_count(ch) == 0


@pytest.mark.asyncio
async def test_close_channel_broadcasts_meeting_ended():
    """12/12: close_channel send reason event + close all WS với code 1000."""
    backend = InMemoryBackend()
    ch = "meeting:" + str(uuid4())
    clients = [MockWS(f"c{i}") for i in range(3)]
    for c in clients:
        await backend.add_client(ch, c)

    reason = {"type": "meeting_ended", "reason": "completed"}
    await backend.close_channel(ch, reason)

    # Tất cả client nhận reason event
    for c in clients:
        assert c.sent == [reason]
        assert c.closed_with == [1000]

    # Pool đã clean
    assert await backend.client_count(ch) == 0
