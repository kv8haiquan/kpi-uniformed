"""Singletons cho Phase 4.1 page-sync.

Backend pool + manager phải share giữa các WS connection trong cùng process.
Module-level singleton là pattern đơn giản nhất; swap RedisPubSubBackend khi
cần multi-worker (Phase sau).
"""

from __future__ import annotations

import asyncio
from typing import Dict

from meeting_service.services.broadcast_backend import InMemoryBackend
from meeting_service.services.presentation_manager import PresentationManager


backend = InMemoryBackend()
manager = PresentationManager(backend)

# Theo dõi task gửi `host_disconnected` sau 30s (cho phép reconnect grace).
# Key: channel str. Value: asyncio.Task chờ delay.
host_disconnect_timers: Dict[str, asyncio.Task] = {}
