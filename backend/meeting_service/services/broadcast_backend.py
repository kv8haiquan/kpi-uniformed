"""BroadcastBackend abstraction cho Phase 4.1 — Page-Sync.

Threat model + design notes:
- Tách Protocol khỏi InMemoryBackend implementation để có thể swap sang
  Redis Pub/Sub khi cần multi-worker (sau Phase 4.1).
- InMemoryBackend phù hợp single-process PM2 fork mode hiện tại — pool
  state local, restart service → mất pool nhưng client tự reconnect
  + state DB phục hồi.
- Async lock per channel để add/remove/broadcast đồng thời an toàn.
- broadcast: dùng asyncio.gather(return_exceptions=True) để 1 client lỗi
  (vd connection broken) không break broadcast cho clients còn lại.
"""

from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from typing import Any, Optional, Protocol, Set


logger = logging.getLogger("hkg.broadcast")


class WebSocketLike(Protocol):
    """Minimum interface từ FastAPI WebSocket cần thiết cho broadcast."""

    async def send_json(self, data: Any) -> None: ...

    async def close(self, code: int = 1000) -> None: ...


class BroadcastBackend(Protocol):
    """Abstract pool — InMemoryBackend cho MVP, RedisPubSub cho multi-worker sau."""

    async def add_client(
        self, channel: str, ws: WebSocketLike, is_host: bool = False
    ) -> None: ...

    async def remove_client(self, channel: str, ws: WebSocketLike) -> None: ...

    async def broadcast(
        self,
        channel: str,
        event: dict,
        exclude: Optional[WebSocketLike] = None,
    ) -> None: ...

    async def host_count(self, channel: str) -> int: ...

    async def client_count(self, channel: str) -> int: ...

    async def close_channel(self, channel: str, reason: dict) -> None: ...


class InMemoryBackend:
    """In-memory pool cho single PM2 process.

    Pros: 0 dependency, latency 5-20ms.
    Cons: KHÔNG scale multi-worker — restart service → mất pool, client
    tự reconnect (state đã lưu DB).
    """

    def __init__(self) -> None:
        self._pools: dict[str, Set[WebSocketLike]] = defaultdict(set)
        self._host_conns: dict[str, Set[WebSocketLike]] = defaultdict(set)
        self._locks: dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)

    async def add_client(
        self, channel: str, ws: WebSocketLike, is_host: bool = False
    ) -> None:
        async with self._locks[channel]:
            self._pools[channel].add(ws)
            if is_host:
                self._host_conns[channel].add(ws)

    async def remove_client(self, channel: str, ws: WebSocketLike) -> None:
        async with self._locks[channel]:
            self._pools[channel].discard(ws)
            self._host_conns[channel].discard(ws)
            # Cleanup empty pools để khỏi giữ lock vô hạn
            if not self._pools[channel]:
                self._pools.pop(channel, None)
                self._host_conns.pop(channel, None)

    async def broadcast(
        self,
        channel: str,
        event: dict,
        exclude: Optional[WebSocketLike] = None,
    ) -> None:
        # Snapshot pool dưới lock, gửi ngoài lock để tránh giữ lock khi I/O.
        async with self._locks[channel]:
            targets = [c for c in self._pools.get(channel, set()) if c is not exclude]

        if not targets:
            return

        async def _safe_send(ws: WebSocketLike) -> None:
            try:
                await ws.send_json(event)
            except Exception as exc:
                # 1 client lỗi không được break các client khác.
                logger.warning("broadcast send failed on channel=%s: %s", channel, exc)

        await asyncio.gather(*(_safe_send(t) for t in targets), return_exceptions=True)

    async def host_count(self, channel: str) -> int:
        async with self._locks[channel]:
            return len(self._host_conns.get(channel, set()))

    async def client_count(self, channel: str) -> int:
        async with self._locks[channel]:
            return len(self._pools.get(channel, set()))

    async def close_channel(self, channel: str, reason: dict) -> None:
        """Gửi reason event rồi close all WS với code 1000 (normal closure)."""
        async with self._locks[channel]:
            targets = list(self._pools.get(channel, set()))
            self._pools.pop(channel, None)
            self._host_conns.pop(channel, None)

        async def _close_one(ws: WebSocketLike) -> None:
            try:
                await ws.send_json(reason)
            except Exception:
                pass
            try:
                await ws.close(code=1000)
            except Exception:
                pass

        if targets:
            await asyncio.gather(*(_close_one(t) for t in targets), return_exceptions=True)
