"""Test PresentationManager (Phase 4.1 BE_P4).

Coverage còn lại của 12 test trong PROMPT_2 §4.4 (6 đã ở test_broadcast_backend.py):
- 7. test_debounce_page_change — 10 events 100ms → 1 broadcast
- 8. test_debounce_per_user_isolation — user A không ảnh hưởng user B
- 9. test_handle_event_non_host_silent_reject — non-chu_toa silent
- 10. test_handle_presentation_start_upsert_db — DB UPSERT đúng
- 11. test_handle_document_open_validates_tai_lieu — sai cuoc_hop reject
- (close_channel test đã ở test_broadcast_backend.py)
"""

import asyncio
from datetime import date, time
from typing import Any
from uuid import UUID, uuid4

import pytest
from sqlalchemy import text as sa_text
from sqlalchemy.ext.asyncio import AsyncSession

from meeting_service.models import CuocHop, TrangThaiTrinhChieu
from meeting_service.services.broadcast_backend import InMemoryBackend
from meeting_service.services.presentation_manager import (
    PresentationManager,
    channel_for,
)


class MockWS:
    """Mock WebSocket cho manager tests."""

    def __init__(self):
        self.sent: list[Any] = []

    async def send_json(self, data):
        self.sent.append(data)

    async def close(self, code: int = 1000):
        pass


async def _seed_meeting(
    db_session: AsyncSession,
    seed_test_users,
    *,
    chu_toa_ma_cc: str = "TEST-G3-001",
    trang_thai: str = "DANG_DIEN_RA",
) -> UUID:
    """Tạo cuoc_hop test trong session, return id."""
    from meeting_service.tests.conftest import TEST_USERS
    chu_toa_id = TEST_USERS[chu_toa_ma_cc]
    ch = CuocHop(
        tieu_de="Test BE_P4 manager",
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
    return ch.id


async def _seed_tai_lieu(
    db_session: AsyncSession, cuoc_hop_id: UUID, chu_toa_id: UUID
) -> UUID:
    return (await db_session.execute(sa_text("""
        INSERT INTO meeting.tai_lieu
            (cuoc_hop_id, ten_tai_lieu, minio_key, file_size, created_by)
        VALUES (:ch, 'test.pdf', 'test/key.pdf', 1024, :uid)
        RETURNING id
    """), {"ch": str(cuoc_hop_id), "uid": str(chu_toa_id)})).scalar_one()


# ════════════════════════════════════════════════════════════════════
# 7. Debounce
# ════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_debounce_page_change(db_session: AsyncSession, seed_test_users):
    """7/12: 10 page_change events trong 100ms → chỉ 1 broadcast cuối cùng."""
    from meeting_service.tests.conftest import TEST_USERS
    chu_toa_id = TEST_USERS["TEST-G3-001"]
    ch_id = await _seed_meeting(db_session, seed_test_users)
    # State row tồn tại để UPDATE work
    db_session.add(TrangThaiTrinhChieu(cuoc_hop_id=ch_id))
    await db_session.flush()

    backend = InMemoryBackend()
    manager = PresentationManager(backend)
    ws = MockWS()

    # Add 1 client để verify broadcast
    listener = MockWS()
    await backend.add_client(channel_for(ch_id), listener)

    # Spam 10 events trong ~50ms
    for page in range(1, 11):
        await manager.handle_inbound_event(
            db_session, ch_id, chu_toa_id,
            {"type": "page_change", "page": page}, ws,
        )
        await asyncio.sleep(0.005)

    # Đợi debounce window 150ms + buffer
    await asyncio.sleep(0.25)

    page_events = [e for e in listener.sent if e.get("type") == "page_changed"]
    assert len(page_events) == 1, f"Debounce sai — broadcast {len(page_events)} events thay vì 1"
    assert page_events[0]["page"] == 10, "Phải broadcast event CUỐI CÙNG"


@pytest.mark.asyncio
async def test_debounce_per_user_isolation(
    db_session: AsyncSession, seed_test_users
):
    """8/12: 2 host (giả lập 2 user khác nhau cùng channel) debounce độc lập.

    Note: theo D1 chỉ chu_toa được broadcast, nhưng tests _internal_
    của debounce key tách theo user_id — verify mechanic.
    """
    from meeting_service.tests.conftest import TEST_USERS

    chu_toa_id = TEST_USERS["TEST-G3-001"]
    other_id = TEST_USERS["TEST-G3-002"]  # Sẽ bị silent reject (non-host)

    ch_id = await _seed_meeting(db_session, seed_test_users)
    db_session.add(TrangThaiTrinhChieu(cuoc_hop_id=ch_id))
    await db_session.flush()

    backend = InMemoryBackend()
    manager = PresentationManager(backend)
    listener = MockWS()
    await backend.add_client(channel_for(ch_id), listener)
    ws = MockWS()

    # User non-host gửi → silent reject (không tạo debounce task)
    await manager.handle_inbound_event(
        db_session, ch_id, other_id,
        {"type": "page_change", "page": 99}, ws,
    )
    await asyncio.sleep(0.05)

    # Chu toa gửi event hợp lệ → debounce task tạo
    await manager.handle_inbound_event(
        db_session, ch_id, chu_toa_id,
        {"type": "page_change", "page": 5}, ws,
    )
    await asyncio.sleep(0.25)

    page_events = [e for e in listener.sent if e.get("type") == "page_changed"]
    assert len(page_events) == 1
    assert page_events[0]["page"] == 5
    # Verify non-host KHÔNG broadcast
    assert all(e.get("page") != 99 for e in page_events)


# ════════════════════════════════════════════════════════════════════
# 9. Permission
# ════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_handle_event_non_host_silent_reject(
    db_session: AsyncSession, seed_test_users
):
    """9/12: user KHÔNG phải chu_toa → silent reject (không broadcast, không error)."""
    from meeting_service.tests.conftest import TEST_USERS

    ch_id = await _seed_meeting(db_session, seed_test_users)
    other_id = TEST_USERS["TEST-G3-002"]

    backend = InMemoryBackend()
    manager = PresentationManager(backend)
    listener = MockWS()
    await backend.add_client(channel_for(ch_id), listener)
    ws = MockWS()

    await manager.handle_inbound_event(
        db_session, ch_id, other_id,
        {"type": "presentation_end"}, ws,
    )
    # Không broadcast
    assert listener.sent == []
    # Không send error tới WS (silent)
    assert ws.sent == []


# ════════════════════════════════════════════════════════════════════
# 10. presentation_start UPSERT DB
# ════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_handle_presentation_start_upsert_db(
    db_session: AsyncSession, seed_test_users
):
    """10/12: presentation_start → UPSERT row đúng (is_active=TRUE, page, tai_lieu)."""
    from meeting_service.tests.conftest import TEST_USERS

    chu_toa_id = TEST_USERS["TEST-G3-001"]
    ch_id = await _seed_meeting(db_session, seed_test_users)
    tai_lieu_id = await _seed_tai_lieu(db_session, ch_id, chu_toa_id)

    backend = InMemoryBackend()
    manager = PresentationManager(backend)
    listener = MockWS()
    await backend.add_client(channel_for(ch_id), listener)
    ws = MockWS()

    await manager.handle_inbound_event(
        db_session, ch_id, chu_toa_id,
        {"type": "presentation_start", "tai_lieu_id": str(tai_lieu_id), "page": 3},
        ws,
    )

    # Verify DB
    row = (await db_session.execute(sa_text("""
        SELECT is_active, tai_lieu_hien_tai_id, trang_hien_tai, bat_dau_luc
          FROM meeting.trang_thai_trinh_chieu
         WHERE cuoc_hop_id = :ch
    """), {"ch": str(ch_id)})).one()
    assert row.is_active is True
    assert row.tai_lieu_hien_tai_id == tai_lieu_id
    assert row.trang_hien_tai == 3
    assert row.bat_dau_luc is not None

    # Verify broadcast
    started = [e for e in listener.sent if e.get("type") == "presentation_started"]
    assert len(started) == 1
    assert started[0]["tai_lieu_id"] == str(tai_lieu_id)
    assert started[0]["page"] == 3


# ════════════════════════════════════════════════════════════════════
# 11. document_open validates tai_lieu thuộc cuoc_hop
# ════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_handle_document_open_validates_tai_lieu(
    db_session: AsyncSession, seed_test_users
):
    """11/12: document_open với tai_lieu KHÁC cuoc_hop → error event, KHÔNG broadcast."""
    from meeting_service.tests.conftest import TEST_USERS

    chu_toa_id = TEST_USERS["TEST-G3-001"]
    ch_id_a = await _seed_meeting(db_session, seed_test_users)
    ch_id_b = await _seed_meeting(db_session, seed_test_users)
    # Tài liệu thuộc cuoc_hop B
    foreign_tl = await _seed_tai_lieu(db_session, ch_id_b, chu_toa_id)

    backend = InMemoryBackend()
    manager = PresentationManager(backend)
    listener = MockWS()
    await backend.add_client(channel_for(ch_id_a), listener)
    ws = MockWS()

    await manager.handle_inbound_event(
        db_session, ch_id_a, chu_toa_id,
        {"type": "document_open", "tai_lieu_id": str(foreign_tl), "page": 1},
        ws,
    )

    # Phải có error event tới ws (chu_toa)
    assert any(
        e.get("type") == "error" and e.get("code") == "DOCUMENT_DELETED"
        for e in ws.sent
    ), f"Phải gửi DOCUMENT_DELETED error. Got: {ws.sent}"
    # KHÔNG broadcast document_changed
    assert all(e.get("type") != "document_changed" for e in listener.sent)
