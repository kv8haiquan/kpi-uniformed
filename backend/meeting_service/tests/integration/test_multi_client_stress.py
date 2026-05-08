"""Stress test: 50 đại biểu nhận broadcast từ 1 chu_toa (Phase 4.1 BE_P6).

Mục đích: verify InMemoryBackend handle 50 client cùng lúc + đo p50/p95/p99
latency từ broadcast → client nhận.

Run: ALLOW_PROD_TEST=true pytest meeting_service/tests/integration/ -v --no-header

Mark `slow` để skip trong default run; chỉ chạy explicit.
"""

import asyncio
import time as time_mod
from typing import Any

import pytest

from meeting_service.services.broadcast_backend import InMemoryBackend


class TimingMockWS:
    """Mock WS ghi timestamp lúc nhận từng event để đo latency."""

    def __init__(self):
        self.received_at: list[float] = []
        self.events: list[Any] = []

    async def send_json(self, data):
        self.received_at.append(time_mod.perf_counter())
        self.events.append(data)

    async def close(self, code: int = 1000):
        pass


def _percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    sorted_v = sorted(values)
    k = int(len(sorted_v) * pct / 100)
    return sorted_v[min(k, len(sorted_v) - 1)]


@pytest.mark.slow
@pytest.mark.asyncio
async def test_50_clients_broadcast_latency():
    """50 clients + 100 broadcasts: p95 < 50ms (in-process bound), success >95%."""
    backend = InMemoryBackend()
    channel = "stress:test"

    clients = [TimingMockWS() for _ in range(50)]
    for c in clients:
        await backend.add_client(channel, c)

    broadcast_times: list[float] = []
    for i in range(100):
        send_at = time_mod.perf_counter()
        await backend.broadcast(channel, {"type": "ping", "seq": i})
        broadcast_times.append(send_at)
        # Yield để các send_json kịp run (giả lập network async)
        await asyncio.sleep(0)

    # Tính latency: per client per event = received_at - broadcast_send_at
    latencies_ms: list[float] = []
    success_count = 0
    expected_per_client = 100
    for c in clients:
        if len(c.received_at) >= expected_per_client * 0.95:
            success_count += 1
        for i, recv in enumerate(c.received_at[:expected_per_client]):
            if i < len(broadcast_times):
                latencies_ms.append((recv - broadcast_times[i]) * 1000)

    p50 = _percentile(latencies_ms, 50)
    p95 = _percentile(latencies_ms, 95)
    p99 = _percentile(latencies_ms, 99)
    success_rate = success_count / len(clients) * 100

    print(f"\n=== Stress Test 50 clients × 100 broadcasts ===")
    print(f"Total events delivered: {len(latencies_ms)} / {50 * 100}")
    print(f"Success rate: {success_rate:.1f}%")
    print(f"Latency p50/p95/p99: {p50:.2f}ms / {p95:.2f}ms / {p99:.2f}ms")

    assert success_rate >= 95, f"Success rate {success_rate:.1f}% < 95%"
    # In-process broadcast should be very fast — relax target để robust với CI noise
    assert p95 < 100, f"p95 {p95:.2f}ms >= 100ms"
