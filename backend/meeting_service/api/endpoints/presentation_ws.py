"""WebSocket endpoint cho Phase 4.1 — Page-Sync.

WS /ws/hop-khong-giay/cuoc-hop/{cuoc_hop_id}/presentation?token=<jwt>

Threat model:
- Auth qua query token (FastAPI WebSocket không hỗ trợ Authorization header
  reliable cross-browser). Token JWT scope=meeting:{id} tránh cross-meeting
  injection.
- Validate cuoc_hop.trang_thai IN (DA_THONG_BAO, DANG_DIEN_RA) — close 1008
  cho status khác.
- Heartbeat ping mỗi 30s; client phải reply pong (hoặc bất kỳ message) để
  giữ kết nối. Idle >120s → server close.
- Host disconnect detection: khi host WS disconnect, schedule task delay 30s
  rồi broadcast host_disconnected. Reconnect trong 30s → cancel + broadcast
  host_reconnected (graceful).
- Inbound events delegate sang PresentationManager (đã test ở BE_P4).
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from meeting_service.dependencies import get_db
from meeting_service.models.cuoc_hop import CuocHop
from meeting_service.models.trang_thai_trinh_chieu import TrangThaiTrinhChieu
from meeting_service.services.presentation_manager import channel_for
from meeting_service.services.presentation_singletons import (
    backend,
    host_disconnect_timers,
    manager,
)
from meeting_service.services.ws_token_service import verify_ws_token


logger = logging.getLogger("hkg.ws")

router = APIRouter()

# WS close codes (RFC 6455 + custom)
WS_CLOSE_AUTH = 1008  # Policy violation — token invalid / wrong state
WS_CLOSE_NORMAL = 1000

HEARTBEAT_INTERVAL_S = 30
IDLE_TIMEOUT_S = 120
HOST_RECONNECT_GRACE_S = 30

_VALID_STATES = ("DA_THONG_BAO", "DANG_DIEN_RA")


@router.websocket("/cuoc-hop/{cuoc_hop_id}/presentation")
async def presentation_ws(
    websocket: WebSocket,
    cuoc_hop_id: UUID,
    token: str = Query(...),
    db: AsyncSession = Depends(get_db),
) -> None:
    # 1. Verify token (scope=meeting:{cuoc_hop_id}, type=ws_presentation)
    try:
        user_id = verify_ws_token(token, cuoc_hop_id)
    except Exception:
        await websocket.close(code=WS_CLOSE_AUTH)
        return

    # 2. Load + validate cuoc_hop state
    res = await db.execute(
        select(CuocHop).where(
            CuocHop.id == cuoc_hop_id,
            CuocHop.is_deleted.is_(False),
        )
    )
    ch = res.scalar_one_or_none()
    if ch is None or ch.trang_thai not in _VALID_STATES:
        await websocket.close(code=WS_CLOSE_AUTH)
        return

    is_host = ch.chu_toa_id == user_id
    channel = channel_for(cuoc_hop_id)

    # 3. Accept + add to pool
    await websocket.accept()
    await backend.add_client(channel, websocket, is_host=is_host)

    # 4. Host reconnect grace: cancel pending host_disconnected task, broadcast reconnect
    if is_host:
        timer = host_disconnect_timers.pop(channel, None)
        if timer and not timer.done():
            timer.cancel()
            await backend.broadcast(
                channel, {"type": "host_reconnected"}, exclude=websocket
            )

    # 5. Send initial state_sync
    state = await _load_state(db, cuoc_hop_id)
    host_online = await backend.host_count(channel) > 0
    await websocket.send_json(_build_state_sync(state, host_online))

    # 6. Heartbeat task
    last_pong_at = datetime.now(timezone.utc)

    async def heartbeat_loop():
        while True:
            await asyncio.sleep(HEARTBEAT_INTERVAL_S)
            try:
                await websocket.send_json({"type": "ping"})
            except Exception:
                break
            # Idle check — last activity (any incoming message) trong IDLE_TIMEOUT_S
            idle = (datetime.now(timezone.utc) - last_pong_at).total_seconds()
            if idle > IDLE_TIMEOUT_S:
                logger.info("WS idle timeout for %s", channel)
                try:
                    await websocket.close(code=WS_CLOSE_NORMAL)
                except Exception:
                    pass
                break

    hb_task = asyncio.create_task(heartbeat_loop())

    # 7. Receive loop
    try:
        while True:
            data = await websocket.receive_json()
            last_pong_at = datetime.now(timezone.utc)

            event_type = data.get("type")
            if event_type == "pong":
                continue  # client keepalive ack
            await manager.handle_inbound_event(
                db, cuoc_hop_id, user_id, data, websocket
            )
    except WebSocketDisconnect:
        pass
    except Exception as exc:
        logger.warning("WS error %s: %s", channel, exc)
    finally:
        hb_task.cancel()
        await backend.remove_client(channel, websocket)

        # 8. Host disconnect → schedule broadcast sau grace 30s
        if is_host:
            await _schedule_host_disconnected(channel)


# ──────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────

async def _load_state(db: AsyncSession, cuoc_hop_id: UUID):
    """Load row trang_thai_trinh_chieu (có thể NULL nếu chưa init)."""
    res = await db.execute(
        select(TrangThaiTrinhChieu).where(
            TrangThaiTrinhChieu.cuoc_hop_id == cuoc_hop_id
        )
    )
    return res.scalar_one_or_none()


def _build_state_sync(state, host_online: bool) -> dict:
    """Build state_sync event payload (serializable JSON)."""
    if state is None:
        return {
            "type": "state_sync",
            "is_active": False,
            "tai_lieu_hien_tai_id": None,
            "trang_hien_tai": 1,
            "zoom_level": "1.00",
            "host_online": host_online,
        }
    return {
        "type": "state_sync",
        "is_active": state.is_active,
        "tai_lieu_hien_tai_id": str(state.tai_lieu_hien_tai_id)
        if state.tai_lieu_hien_tai_id
        else None,
        "trang_hien_tai": state.trang_hien_tai,
        "zoom_level": str(Decimal(state.zoom_level).quantize(Decimal("0.01"))),
        "host_online": host_online,
    }


async def _schedule_host_disconnected(channel: str) -> None:
    """Schedule task delay 30s rồi broadcast host_disconnected."""
    # Cancel timer cũ (nếu có) — phòng double-disconnect
    prior = host_disconnect_timers.pop(channel, None)
    if prior and not prior.done():
        prior.cancel()

    async def _runner():
        try:
            await asyncio.sleep(HOST_RECONNECT_GRACE_S)
            # Re-check: nếu host đã reconnect (task này không bị cancel kịp),
            # broadcast vẫn OK — client xử lý idempotent.
            await backend.broadcast(channel, {"type": "host_disconnected"})
        except asyncio.CancelledError:
            pass
        finally:
            if host_disconnect_timers.get(channel) is asyncio.current_task():
                host_disconnect_timers.pop(channel, None)

    host_disconnect_timers[channel] = asyncio.create_task(_runner())
