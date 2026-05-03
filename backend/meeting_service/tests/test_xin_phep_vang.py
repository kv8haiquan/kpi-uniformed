"""
Test Module 5 — Xin phép vắng + APScheduler auto-approve logic.

Tests:
- CBCC trong thành phần gửi đơn → 201 + audit REQUEST_LEAVE
- CBCC ngoài thành phần → 403
- Chu_toa list cho-duyet → thấy đơn của mình
- Chu_toa duyệt → trạng thái DA_DUYET + thong_bao
- Auto-approve logic: tạo đơn cũ (created_at < now-4h) → gọi
  service.auto_approve_overdue() → đơn chuyển TU_DONG_DUYET
"""

from datetime import datetime, timedelta, timezone
from uuid import UUID

import pytest
from httpx import AsyncClient
from sqlalchemy import text as sa_text
from sqlalchemy.ext.asyncio import AsyncSession


BASE_CH = "/api/v1/hop-khong-giay/cuoc-hop"
BASE_XP = "/api/v1/hop-khong-giay/xin-phep-vang"


def _meeting_payload(don_vi_id, chu_toa_id, thanh_phan):
    return {
        "tieu_de": "Test G3 — Họp xin vắng",
        "khoi": "CHUYEN_MON",
        "hinh_thuc": "TRUC_TIEP",
        "ngay_hop": "2026-05-22",
        "gio_bat_dau": "08:30",
        "don_vi_to_chuc_id": str(don_vi_id),
        "chu_toa_id": str(chu_toa_id),
        "thanh_phan": thanh_phan,
    }


def _make_thu_ky(don_vi_id):
    from datetime import datetime, timedelta, timezone
    from shared.auth import TokenPayload
    return TokenPayload(
        sub="aaaaaaaa-0002-0000-0000-000000000002",
        ma_cc="TEST-G3-002", ho_ten="TK",
        vai_tro="CC", don_vi_id=str(don_vi_id),
        platform_roles=["THU_KY_HOP"],
        exp=int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()),
        type="access",
    )


@pytest.mark.asyncio
async def test_create_xin_phep_audit_request_leave(
    client: AsyncClient, chu_toa_user, seed_test_users,
    db_session: AsyncSession,
):
    """thu_ky là thành phần → gửi đơn OK + audit."""
    thu_ky = _make_thu_ky(seed_test_users["don_vi_a"])

    create = await client.post(BASE_CH + "/", json=_meeting_payload(
        seed_test_users["don_vi_a"], chu_toa_user.sub,
        thanh_phan=[{"cong_chuc_id": thu_ky.sub, "loai_tham_du": "BAT_BUOC"}],
    ))
    ch_id = create.json()["data"]["id"]

    # Switch sang thu_ky
    from meeting_service.dependencies import get_current_user
    from meeting_service.main import app as fastapi_app
    async def _override():
        return thu_ky
    fastapi_app.dependency_overrides[get_current_user] = _override

    resp = await client.post(BASE_XP + "/", json={
        "cuoc_hop_id": ch_id,
        "ly_do": "Đi công tác Hà Nội",
    })
    assert resp.status_code == 201, resp.text
    xpv_id = resp.json()["data"]["id"]
    assert resp.json()["data"]["trang_thai"] == "CHO_DUYET"

    res = await db_session.execute(sa_text("""
        SELECT COUNT(*) FROM common.audit_log
         WHERE module='MEETING' AND hanh_dong='REQUEST_LEAVE'
           AND doi_tuong_id=:xpv_id
    """), {"xpv_id": xpv_id})
    assert res.scalar() == 1


@pytest.mark.asyncio
async def test_create_xin_phep_not_invited_403(
    client: AsyncClient, chu_toa_user, seed_test_users,
):
    from datetime import datetime, timedelta, timezone
    from shared.auth import TokenPayload

    outsider = TokenPayload(
        sub="aaaaaaaa-0004-0000-0000-000000000004",
        ma_cc="TEST-G3-004", ho_ten="Outsider",
        vai_tro="CC",
        don_vi_id=str(seed_test_users["don_vi_b"]),
        platform_roles=[],
        exp=int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()),
        type="access",
    )

    create = await client.post(BASE_CH + "/", json=_meeting_payload(
        seed_test_users["don_vi_a"], chu_toa_user.sub, thanh_phan=[],
    ))
    ch_id = create.json()["data"]["id"]

    from meeting_service.dependencies import get_current_user
    from meeting_service.main import app as fastapi_app
    async def _override():
        return outsider
    fastapi_app.dependency_overrides[get_current_user] = _override

    resp = await client.post(BASE_XP + "/", json={
        "cuoc_hop_id": ch_id, "ly_do": "Bận",
    })
    assert resp.status_code == 403
    assert resp.json()["detail"]["error"]["code"] == "NOT_INVITED"


@pytest.mark.asyncio
async def test_chu_toa_list_and_duyet(
    client: AsyncClient, chu_toa_user, seed_test_users,
):
    """thu_ky gửi đơn → chu_toa list cho-duyet thấy → duyệt → trạng thái DA_DUYET."""
    thu_ky = _make_thu_ky(seed_test_users["don_vi_a"])

    create = await client.post(BASE_CH + "/", json=_meeting_payload(
        seed_test_users["don_vi_a"], chu_toa_user.sub,
        thanh_phan=[{"cong_chuc_id": thu_ky.sub, "loai_tham_du": "BAT_BUOC"}],
    ))
    ch_id = create.json()["data"]["id"]

    # thu_ky gửi đơn
    from meeting_service.dependencies import get_current_user
    from meeting_service.main import app as fastapi_app
    async def _override_tk():
        return thu_ky
    fastapi_app.dependency_overrides[get_current_user] = _override_tk

    create_xp = await client.post(BASE_XP + "/", json={
        "cuoc_hop_id": ch_id, "ly_do": "Bệnh",
    })
    xpv_id = create_xp.json()["data"]["id"]

    # Switch về chu_toa
    async def _override_ct():
        return chu_toa_user
    fastapi_app.dependency_overrides[get_current_user] = _override_ct

    # Chu_toa list
    list_resp = await client.get(BASE_XP + "/cho-duyet")
    assert list_resp.status_code == 200
    items = list_resp.json()["data"]
    assert any(it["id"] == xpv_id for it in items)

    # Chu_toa duyệt
    duyet = await client.post(f"{BASE_XP}/{xpv_id}/duyet", json={
        "quyet_dinh": "DA_DUYET",
    })
    assert duyet.status_code == 200, duyet.text
    assert duyet.json()["data"]["trang_thai"] == "DA_DUYET"


@pytest.mark.asyncio
async def test_auto_approve_overdue_logic(
    client: AsyncClient, chu_toa_user, seed_test_users,
    db_session: AsyncSession,
):
    """
    Tạo đơn rồi rewind created_at → gọi service.auto_approve_overdue() trực tiếp
    để verify logic không cần đợi 4h thật.
    """
    thu_ky = _make_thu_ky(seed_test_users["don_vi_a"])

    create = await client.post(BASE_CH + "/", json=_meeting_payload(
        seed_test_users["don_vi_a"], chu_toa_user.sub,
        thanh_phan=[{"cong_chuc_id": thu_ky.sub, "loai_tham_du": "BAT_BUOC"}],
    ))
    ch_id = create.json()["data"]["id"]

    # thu_ky gửi đơn
    from meeting_service.dependencies import get_current_user
    from meeting_service.main import app as fastapi_app
    async def _override():
        return thu_ky
    fastapi_app.dependency_overrides[get_current_user] = _override

    create_xp = await client.post(BASE_XP + "/", json={
        "cuoc_hop_id": ch_id, "ly_do": "Đột xuất",
    })
    xpv_id = create_xp.json()["data"]["id"]

    # Rewind created_at → 5h trước
    five_hours_ago = datetime.now(timezone.utc) - timedelta(hours=5)
    await db_session.execute(sa_text("""
        UPDATE meeting.xin_phep_vang
           SET created_at = :ts
         WHERE id = :id
    """), {"ts": five_hours_ago, "id": xpv_id})
    await db_session.flush()

    # Gọi logic trực tiếp (không qua scheduler)
    from meeting_service.services.xin_phep_vang_service import XinPhepVangService
    service = XinPhepVangService(db_session)
    count = await service.auto_approve_overdue()
    assert count == 1, "Phải auto-duyệt được 1 đơn"

    # Verify trạng thái
    res = await db_session.execute(sa_text("""
        SELECT trang_thai, auto_approved FROM meeting.xin_phep_vang
         WHERE id = :id
    """), {"id": xpv_id})
    row = res.fetchone()
    assert row[0] == "TU_DONG_DUYET"
    assert row[1] is True

    # Verify audit AUTO_APPROVE_LEAVE
    audit = await db_session.execute(sa_text("""
        SELECT COUNT(*) FROM common.audit_log
         WHERE module='MEETING' AND hanh_dong='AUTO_APPROVE_LEAVE'
           AND doi_tuong_id=:xpv_id
    """), {"xpv_id": xpv_id})
    assert audit.scalar() == 1


@pytest.mark.asyncio
async def test_auto_approve_does_not_touch_recent(
    client: AsyncClient, chu_toa_user, seed_test_users,
    db_session: AsyncSession,
):
    """Đơn mới (< 4h) không bị auto-duyệt."""
    thu_ky = _make_thu_ky(seed_test_users["don_vi_a"])

    create = await client.post(BASE_CH + "/", json=_meeting_payload(
        seed_test_users["don_vi_a"], chu_toa_user.sub,
        thanh_phan=[{"cong_chuc_id": thu_ky.sub, "loai_tham_du": "BAT_BUOC"}],
    ))
    ch_id = create.json()["data"]["id"]

    from meeting_service.dependencies import get_current_user
    from meeting_service.main import app as fastapi_app
    async def _override():
        return thu_ky
    fastapi_app.dependency_overrides[get_current_user] = _override
    await client.post(BASE_XP + "/", json={"cuoc_hop_id": ch_id, "ly_do": "x"})

    # KHÔNG rewind created_at — đơn mới
    from meeting_service.services.xin_phep_vang_service import XinPhepVangService
    service = XinPhepVangService(db_session)
    count = await service.auto_approve_overdue()
    assert count == 0
