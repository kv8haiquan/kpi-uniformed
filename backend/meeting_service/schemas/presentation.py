"""Pydantic schemas cho Phase 4.1 — Page-Sync (REST + WS payloads).

Threat model:
- WS inbound payloads dùng discriminated union để FastAPI/TypeAdapter auto-validate
  theo `type`, tránh lỗ hổng "client gửi field thừa" hoặc "type confusion".
- Validator zoom range [0.5, 4.0] + page > 0 ở schema để chặn payload xấu
  TRƯỚC khi vào DB CHECK constraint (defense in depth).
- WS token KHÔNG nằm trong response body khi cuộc họp HOAN_THANH/HUY (xử lý
  ở endpoint level, không phải schema).
- Decimal round 2 chữ số thập phân để client gửi 1.234567 không break NUMERIC(4,2).
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Annotated, Literal, Optional, Union
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ════════════════════════════════════════════════════════════════════
# Enums
# ════════════════════════════════════════════════════════════════════

class WSInboundEventType(str, Enum):
    """Events client → server. Chỉ chu_toa được gửi (server reject nếu khác)."""
    PRESENTATION_START = "presentation_start"
    PRESENTATION_END = "presentation_end"
    DOCUMENT_OPEN = "document_open"
    PAGE_CHANGE = "page_change"
    ZOOM_CHANGE = "zoom_change"


class WSOutboundEventType(str, Enum):
    """Events server → client (broadcast)."""
    STATE_SYNC = "state_sync"
    PRESENTATION_STARTED = "presentation_started"
    PRESENTATION_ENDED = "presentation_ended"
    DOCUMENT_CHANGED = "document_changed"
    PAGE_CHANGED = "page_changed"
    ZOOM_CHANGED = "zoom_changed"
    HOST_DISCONNECTED = "host_disconnected"
    HOST_RECONNECTED = "host_reconnected"
    MEETING_ENDED = "meeting_ended"
    ERROR = "error"


# ════════════════════════════════════════════════════════════════════
# Helpers — zoom validator dùng chung
# ════════════════════════════════════════════════════════════════════

def _validate_zoom(v: Decimal | float | int | str) -> Decimal:
    """Round về 2 chữ số thập phân (match NUMERIC(4,2)) + range check."""
    d = Decimal(str(v)).quantize(Decimal("0.01"))
    if d < Decimal("0.5") or d > Decimal("4.0"):
        raise ValueError("zoom_level phải nằm trong [0.5, 4.0]")
    return d


# ════════════════════════════════════════════════════════════════════
# REST schemas
# ════════════════════════════════════════════════════════════════════

class PresentationStateResponse(BaseModel):
    """Response của GET /presentation/state — state hiện tại + WS token."""
    model_config = ConfigDict(from_attributes=True)

    cuoc_hop_id: UUID
    is_active: bool
    tai_lieu_hien_tai_id: Optional[UUID] = None
    trang_hien_tai: int = Field(default=1, ge=1)
    zoom_level: Decimal = Field(default=Decimal("1.00"))
    bat_dau_luc: Optional[datetime] = None
    ket_thuc_luc: Optional[datetime] = None
    cap_nhat_luc: datetime
    cap_nhat_boi_id: Optional[UUID] = None

    # Token cho WebSocket connection
    ws_token: str
    ws_token_expires_at: datetime

    # User context cho FE quyết định UI
    is_chu_toa: bool
    is_thu_ky: bool


# ════════════════════════════════════════════════════════════════════
# WS Inbound payloads (discriminated by `type`)
# ════════════════════════════════════════════════════════════════════

class PresentationStartPayload(BaseModel):
    type: Literal["presentation_start"]
    tai_lieu_id: UUID
    page: int = Field(default=1, ge=1)


class PresentationEndPayload(BaseModel):
    type: Literal["presentation_end"]


class DocumentOpenPayload(BaseModel):
    type: Literal["document_open"]
    tai_lieu_id: UUID
    page: int = Field(default=1, ge=1)


class PageChangePayload(BaseModel):
    type: Literal["page_change"]
    page: int = Field(..., ge=1)


class ZoomChangePayload(BaseModel):
    type: Literal["zoom_change"]
    zoom: Decimal

    @field_validator("zoom", mode="before")
    @classmethod
    def _round_and_validate(cls, v):
        return _validate_zoom(v)


# Discriminated union — FastAPI/TypeAdapter parse đúng subclass theo `type`.
WSInboundEvent = Annotated[
    Union[
        PresentationStartPayload,
        PresentationEndPayload,
        DocumentOpenPayload,
        PageChangePayload,
        ZoomChangePayload,
    ],
    Field(discriminator="type"),
]


# ════════════════════════════════════════════════════════════════════
# WS Outbound events (server → client)
# ════════════════════════════════════════════════════════════════════

class StateSyncEvent(BaseModel):
    """Sync state đầy đủ — gửi lúc connect hoặc reconnect."""
    type: Literal["state_sync"] = "state_sync"
    is_active: bool
    tai_lieu_hien_tai_id: Optional[UUID] = None
    trang_hien_tai: int = 1
    zoom_level: Decimal = Decimal("1.00")
    host_online: bool


class PresentationStartedEvent(BaseModel):
    type: Literal["presentation_started"] = "presentation_started"
    tai_lieu_id: UUID
    page: int = 1
    bat_dau_luc: datetime


class PresentationEndedEvent(BaseModel):
    type: Literal["presentation_ended"] = "presentation_ended"
    ket_thuc_luc: datetime


class DocumentChangedEvent(BaseModel):
    type: Literal["document_changed"] = "document_changed"
    tai_lieu_id: UUID
    page: int = 1


class PageChangedEvent(BaseModel):
    type: Literal["page_changed"] = "page_changed"
    page: int = Field(..., ge=1)


class ZoomChangedEvent(BaseModel):
    type: Literal["zoom_changed"] = "zoom_changed"
    zoom: Decimal


class HostDisconnectedEvent(BaseModel):
    type: Literal["host_disconnected"] = "host_disconnected"


class HostReconnectedEvent(BaseModel):
    type: Literal["host_reconnected"] = "host_reconnected"


class MeetingEndedEvent(BaseModel):
    """Cuộc họp kết thúc/hủy → đóng tất cả WS."""
    type: Literal["meeting_ended"] = "meeting_ended"
    reason: Literal["completed", "cancelled"]


class WSErrorEvent(BaseModel):
    """Error event từ server (kèm code để FE handle)."""
    type: Literal["error"] = "error"
    code: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)
