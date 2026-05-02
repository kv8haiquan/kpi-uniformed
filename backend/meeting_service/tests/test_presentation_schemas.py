"""Test Pydantic schemas cho Phase 4.1 — Page-Sync.

Threat model:
- Discriminated union: client gửi {type: 'page_change', page: 0} phải fail
  (page validator), không leak vào WS handler.
- Zoom round 2 decimal: client gửi 1.234567 → 1.23, tránh break NUMERIC(4,2).
- Range validator chặn zoom ngoài [0.5, 4.0] ở schema layer (defense in depth
  trước CHECK constraint DB).
"""

from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest
from pydantic import TypeAdapter, ValidationError

from meeting_service.schemas.presentation import (
    DocumentOpenPayload,
    PageChangePayload,
    PresentationStartPayload,
    PresentationStateResponse,
    WSInboundEvent,
    ZoomChangePayload,
)


_inbound_adapter: TypeAdapter = TypeAdapter(WSInboundEvent)


@pytest.mark.asyncio
async def test_presentation_state_response_serialize():
    """1/5: PresentationStateResponse model_dump phải ra JSON đúng schema."""
    now = datetime.now(timezone.utc)
    resp = PresentationStateResponse(
        cuoc_hop_id=uuid4(),
        is_active=True,
        tai_lieu_hien_tai_id=uuid4(),
        trang_hien_tai=5,
        zoom_level=Decimal("1.50"),
        bat_dau_luc=now,
        ket_thuc_luc=None,
        cap_nhat_luc=now,
        cap_nhat_boi_id=uuid4(),
        ws_token="dummy.jwt.token",
        ws_token_expires_at=now,
        is_chu_toa=True,
        is_thu_ky=False,
    )
    dumped = resp.model_dump(mode="json")
    assert dumped["is_active"] is True
    assert dumped["trang_hien_tai"] == 5
    assert dumped["zoom_level"] == "1.50"  # Decimal → str trong mode="json"
    assert dumped["ws_token"] == "dummy.jwt.token"
    assert dumped["is_chu_toa"] is True
    assert dumped["is_thu_ky"] is False


@pytest.mark.asyncio
async def test_inbound_event_discriminated_union():
    """2/5: TypeAdapter parse đúng subclass theo `type` discriminator."""
    tai_lieu_id = uuid4()

    # presentation_start → PresentationStartPayload
    e1 = _inbound_adapter.validate_python({
        "type": "presentation_start",
        "tai_lieu_id": str(tai_lieu_id),
        "page": 3,
    })
    assert isinstance(e1, PresentationStartPayload)
    assert e1.tai_lieu_id == tai_lieu_id
    assert e1.page == 3

    # page_change → PageChangePayload
    e2 = _inbound_adapter.validate_python({"type": "page_change", "page": 7})
    assert isinstance(e2, PageChangePayload)
    assert e2.page == 7

    # zoom_change → ZoomChangePayload (Decimal)
    e3 = _inbound_adapter.validate_python({"type": "zoom_change", "zoom": "2.0"})
    assert isinstance(e3, ZoomChangePayload)
    assert e3.zoom == Decimal("2.00")

    # document_open → DocumentOpenPayload (page mặc định 1)
    e4 = _inbound_adapter.validate_python({
        "type": "document_open",
        "tai_lieu_id": str(tai_lieu_id),
    })
    assert isinstance(e4, DocumentOpenPayload)
    assert e4.page == 1

    # type sai → ValidationError (discriminator reject)
    with pytest.raises(ValidationError):
        _inbound_adapter.validate_python({"type": "unknown_event"})


@pytest.mark.asyncio
async def test_zoom_validation_range():
    """3/5: zoom ngoài [0.5, 4.0] → ValidationError ở schema."""
    # Quá max
    with pytest.raises(ValidationError) as exc_info:
        ZoomChangePayload(type="zoom_change", zoom=Decimal("5.0"))
    assert "[0.5, 4.0]" in str(exc_info.value)

    # Dưới min
    with pytest.raises(ValidationError):
        ZoomChangePayload(type="zoom_change", zoom=Decimal("0.3"))

    # Boundary ok
    ZoomChangePayload(type="zoom_change", zoom=Decimal("0.5"))
    ZoomChangePayload(type="zoom_change", zoom=Decimal("4.0"))


@pytest.mark.asyncio
async def test_page_validation_positive():
    """4/5: page <= 0 → ValidationError."""
    with pytest.raises(ValidationError):
        PageChangePayload(type="page_change", page=0)

    with pytest.raises(ValidationError):
        PageChangePayload(type="page_change", page=-1)

    # page=1 OK
    p = PageChangePayload(type="page_change", page=1)
    assert p.page == 1

    # PresentationStart cũng phải reject page=0 (Field ge=1)
    with pytest.raises(ValidationError):
        PresentationStartPayload(
            type="presentation_start",
            tai_lieu_id=uuid4(),
            page=0,
        )


@pytest.mark.asyncio
async def test_zoom_rounded_to_2_decimal():
    """5/5: zoom 1.234567 → 1.23 (Decimal quantize 0.01)."""
    e = ZoomChangePayload(type="zoom_change", zoom="1.234567")
    assert e.zoom == Decimal("1.23")

    # Float input cũng quantize đúng
    e2 = _inbound_adapter.validate_python({
        "type": "zoom_change",
        "zoom": 2.789,
    })
    assert e2.zoom == Decimal("2.79")  # bankers rounding làm tròn lên

    # Integer 2 → "2.00"
    e3 = ZoomChangePayload(type="zoom_change", zoom=2)
    assert e3.zoom == Decimal("2.00")
