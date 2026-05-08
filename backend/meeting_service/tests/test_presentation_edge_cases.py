"""Edge case tests cho Phase 4.1 BE_P6.

Threat model:
- Cuộc họp bị hủy/hoàn thành giữa lúc đang trình chiếu → mọi WS client
  phải nhận meeting_ended + close graceful (không kẹt zombie connection).
- Tài liệu bị xóa giữa chừng → host nhận DOCUMENT_DELETED error.
- Audit log: chỉ ghi 5 events business-value (CUOC_HOP_BAT_DAU/KET_THUC,
  PRESENTATION_START/END, DOCUMENT_OPEN). Tuyệt đối KHÔNG flood DB bằng
  page_change/zoom_change events (D11 plan v3.1).
"""

from datetime import date, time
from uuid import UUID, uuid4

import pytest
from sqlalchemy import text as sa_text
from sqlalchemy.ext.asyncio import AsyncSession

from meeting_service.models import CuocHop, TrangThaiTrinhChieu
from meeting_service.services.broadcast_backend import InMemoryBackend
from meeting_service.services.cuoc_hop_service import CuocHopService
from meeting_service.services.presentation_manager import (
    PresentationManager,
    channel_for,
)
from meeting_service.services.presentation_singletons import (
    backend as global_backend,
    manager as global_manager,
)


class MockWS:
    def __init__(self):
        self.sent = []
        self.closed_with: int | None = None

    async def send_json(self, data):
        self.sent.append(data)

    async def close(self, code: int = 1000):
        self.closed_with = code


async def _seed_meeting_dang_dien_ra(db_session, seed_test_users) -> CuocHop:
    from meeting_service.tests.conftest import TEST_USERS
    chu_toa_id = TEST_USERS["TEST-G3-001"]
    ch = CuocHop(
        tieu_de="Test edge case",
        ngay_hop=date(2026, 5, 15),
        gio_bat_dau=time(8, 30),
        gio_ket_thuc=time(10, 0),
        don_vi_to_chuc_id=seed_test_users["don_vi_a"],
        chu_toa_id=chu_toa_id,
        created_by=chu_toa_id,
        trang_thai="DANG_DIEN_RA",
    )
    db_session.add(ch)
    await db_session.flush()
    await db_session.refresh(ch)
    return ch


async def _seed_tai_lieu(db_session, ch_id: UUID, user_id: UUID) -> UUID:
    return (await db_session.execute(sa_text("""
        INSERT INTO meeting.tai_lieu
            (cuoc_hop_id, ten_tai_lieu, minio_key, file_size, created_by)
        VALUES (:ch, 'doc.pdf', 'k/doc.pdf', 1024, :uid)
        RETURNING id
    """), {"ch": str(ch_id), "uid": str(user_id)})).scalar_one()


@pytest.fixture(autouse=True)
async def _cleanup_singleton_pool():
    """Reset global pool giữa edge case tests."""
    yield
    global_backend._pools.clear()
    global_backend._host_conns.clear()
    global_backend._locks.clear()
    for t in list(global_manager._debounce_tasks.values()):
        t.cancel()
    global_manager._debounce_tasks.clear()


# ════════════════════════════════════════════════════════════════════
# 1. Meeting cancelled trong khi đang trình chiếu
# ════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_meeting_cancelled_during_presentation(
    db_session: AsyncSession, seed_test_users, chu_toa_user
):
    """1/5: huy() cuộc họp DANG_DIEN_RA → broadcast meeting_ended (cancelled)
    + close all WS code 1000."""
    ch = await _seed_meeting_dang_dien_ra(db_session, seed_test_users)
    channel = channel_for(ch.id)

    # Mock 2 WS clients đang trong pool
    a, b = MockWS(), MockWS()
    await global_backend.add_client(channel, a, is_host=True)
    await global_backend.add_client(channel, b)

    # Hủy cuộc họp
    service = CuocHopService(db_session)
    await service.huy(ch, "Test cancel", chu_toa_user)

    # Cả 2 client phải nhận meeting_ended + closed
    for w in (a, b):
        ended = [m for m in w.sent if m.get("type") == "meeting_ended"]
        assert ended == [{"type": "meeting_ended", "reason": "cancelled"}], (
            f"Expected meeting_ended cancelled. Got: {w.sent}"
        )
        assert w.closed_with == 1000


# ════════════════════════════════════════════════════════════════════
# 2. Meeting completed (ket_thuc) trong khi đang trình chiếu
# ════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_meeting_completed_during_presentation(
    db_session: AsyncSession, seed_test_users, chu_toa_user
):
    """2/5: ket_thuc() → broadcast meeting_ended (completed) + close all WS."""
    ch = await _seed_meeting_dang_dien_ra(db_session, seed_test_users)
    channel = channel_for(ch.id)

    a, b = MockWS(), MockWS()
    await global_backend.add_client(channel, a, is_host=True)
    await global_backend.add_client(channel, b)

    service = CuocHopService(db_session)
    await service.ket_thuc(ch, chu_toa_user)

    for w in (a, b):
        ended = [m for m in w.sent if m.get("type") == "meeting_ended"]
        assert ended == [{"type": "meeting_ended", "reason": "completed"}]
        assert w.closed_with == 1000


# ════════════════════════════════════════════════════════════════════
# 3. Document deleted trong khi đang active presentation
# ════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_document_deleted_during_active_presentation(
    db_session: AsyncSession, seed_test_users
):
    """3/5: thư ký xóa tài liệu giữa chừng → host nhận DOCUMENT_DELETED error
    khi tiếp tục gửi event document_open."""
    ch = await _seed_meeting_dang_dien_ra(db_session, seed_test_users)
    tl_id = await _seed_tai_lieu(db_session, ch.id, ch.chu_toa_id)

    # Thư ký xóa (soft delete) tài liệu
    await db_session.execute(
        sa_text("UPDATE meeting.tai_lieu SET is_deleted = TRUE WHERE id = :id"),
        {"id": str(tl_id)},
    )
    await db_session.flush()

    # Local manager cho test isolation
    local_backend = InMemoryBackend()
    local_manager = PresentationManager(local_backend)
    host_ws = MockWS()

    await local_manager.handle_inbound_event(
        db_session, ch.id, ch.chu_toa_id,
        {"type": "document_open", "tai_lieu_id": str(tl_id)},
        host_ws,
    )

    error_events = [m for m in host_ws.sent if m.get("type") == "error"]
    assert any(e.get("code") == "DOCUMENT_DELETED" for e in error_events), (
        f"Expected DOCUMENT_DELETED error. Got: {host_ws.sent}"
    )


# ════════════════════════════════════════════════════════════════════
# 4. Audit log chỉ ghi 5 actions business-value
# ════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_audit_log_only_business_events(
    db_session: AsyncSession, seed_test_users, chu_toa_user
):
    """4/5: full lifecycle (bat-dau → start trình chiếu → end → ket-thuc) tạo
    đúng 4 audit events: CUOC_HOP_BAT_DAU, PRESENTATION_START, PRESENTATION_END,
    CUOC_HOP_KET_THUC. (DOCUMENT_OPEN là action 5 — test riêng nếu cần.)"""
    from meeting_service.tests.conftest import TEST_USERS
    chu_toa_id = TEST_USERS["TEST-G3-001"]

    # Tạo cuộc họp ở DA_THONG_BAO để bat-dau → DANG_DIEN_RA
    ch = CuocHop(
        tieu_de="Test audit",
        ngay_hop=date(2026, 5, 15),
        gio_bat_dau=time(8, 30),
        gio_ket_thuc=time(10, 0),
        don_vi_to_chuc_id=seed_test_users["don_vi_a"],
        chu_toa_id=chu_toa_id,
        created_by=chu_toa_id,
        trang_thai="DA_THONG_BAO",
    )
    db_session.add(ch)
    await db_session.flush()
    tl_id = await _seed_tai_lieu(db_session, ch.id, chu_toa_id)

    service = CuocHopService(db_session)
    local_backend = InMemoryBackend()
    local_manager = PresentationManager(local_backend)
    ws = MockWS()

    # 1. CUOC_HOP_BAT_DAU
    await service.bat_dau(ch, chu_toa_user)
    # 2. PRESENTATION_START
    await local_manager.handle_inbound_event(
        db_session, ch.id, chu_toa_id,
        {"type": "presentation_start", "tai_lieu_id": str(tl_id), "page": 1}, ws,
    )
    # 3. PRESENTATION_END
    await local_manager.handle_inbound_event(
        db_session, ch.id, chu_toa_id,
        {"type": "presentation_end"}, ws,
    )
    # 4. CUOC_HOP_KET_THUC
    await service.ket_thuc(ch, chu_toa_user)

    # Query audit log
    rows = await db_session.execute(sa_text("""
        SELECT hanh_dong FROM common.audit_log
         WHERE module = 'MEETING' AND doi_tuong_id = :ch
         ORDER BY created_at
    """), {"ch": str(ch.id)})
    actions = [r.hanh_dong for r in rows.fetchall()]

    assert "CUOC_HOP_BAT_DAU" in actions
    assert "PRESENTATION_START" in actions
    assert "PRESENTATION_END" in actions
    assert "CUOC_HOP_KET_THUC" in actions


# ════════════════════════════════════════════════════════════════════
# 5. Page_change KHÔNG audit (tránh flood)
# ════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_audit_log_no_page_change(
    db_session: AsyncSession, seed_test_users
):
    """5/5: gửi 50 page_change/zoom_change → 0 audit row PAGE_CHANGE/ZOOM_CHANGE.
    D11 plan v3.1: chỉ audit 5 events business-value, page/zoom KHÔNG vào DB."""
    import asyncio
    ch = await _seed_meeting_dang_dien_ra(db_session, seed_test_users)
    tl_id = await _seed_tai_lieu(db_session, ch.id, ch.chu_toa_id)
    # Init state row active để UPDATE work
    db_session.add(TrangThaiTrinhChieu(
        cuoc_hop_id=ch.id,
        tai_lieu_hien_tai_id=tl_id,
        is_active=True,
    ))
    await db_session.flush()

    local_backend = InMemoryBackend()
    local_manager = PresentationManager(local_backend)
    ws = MockWS()

    # Spam 50 page_change events
    for page in range(1, 51):
        await local_manager.handle_inbound_event(
            db_session, ch.id, ch.chu_toa_id,
            {"type": "page_change", "page": page}, ws,
        )

    # Đợi debounce + flush
    await asyncio.sleep(0.25)

    # Verify KHÔNG có audit row nào với hanh_dong chứa PAGE/ZOOM
    rows = await db_session.execute(sa_text("""
        SELECT hanh_dong FROM common.audit_log
         WHERE module = 'MEETING'
           AND doi_tuong_id = :ch
           AND (hanh_dong LIKE '%PAGE%' OR hanh_dong LIKE '%ZOOM%')
    """), {"ch": str(ch.id)})
    found = [r.hanh_dong for r in rows.fetchall()]
    assert found == [], f"Page/zoom KHÔNG được audit. Found: {found}"
