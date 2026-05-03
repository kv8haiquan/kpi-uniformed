"""
Test G4-fix-7.2 — checkin window guard.

Window: gio_bat_dau − 30p → gio_ket_thuc + 60p (hoặc gio_bd + 4h nếu thiếu)
- Trước window → 409 NOT_YET_OPEN
- Sau window → 409 CHECKIN_CLOSED
- Trong window → OK (CO_MAT/DEN_MUON theo threshold 5p)
"""

from datetime import date, datetime, time, timedelta, timezone

import pytest
from httpx import AsyncClient
from shared.auth import TokenPayload


BASE = "/api/v1/hop-khong-giay/cuoc-hop"


def _meeting_payload(don_vi_id, chu_toa_id, ngay_hop: str, gio_bat_dau: str,
                       gio_ket_thuc: str | None = None,
                       thanh_phan: list | None = None):
    return {
        "tieu_de": "Test G4-fix-7 window",
        "khoi": "CHUYEN_MON",
        "hinh_thuc": "TRUC_TIEP",
        "ngay_hop": ngay_hop,
        "gio_bat_dau": gio_bat_dau,
        "gio_ket_thuc": gio_ket_thuc,
        "don_vi_to_chuc_id": str(don_vi_id),
        "chu_toa_id": str(chu_toa_id),
        "thanh_phan": thanh_phan or [],
    }


def _make_cbcc_token(sub: str, don_vi_id):
    return TokenPayload(
        sub=sub, ma_cc="TEST-G3-CBCC", ho_ten="CBCC",
        vai_tro="CC", don_vi_id=str(don_vi_id),
        platform_roles=[],
        exp=int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()),
        type="access",
    )


def _override(user):
    from meeting_service.dependencies import get_current_user
    from meeting_service.main import app
    async def _o():
        return user
    app.dependency_overrides[get_current_user] = _o


@pytest.mark.asyncio
async def test_not_yet_open_409(client: AsyncClient, chu_toa_user, seed_test_users):
    """Cuộc họp ngày mai 9h → CBCC tự điểm danh hôm nay → 409 NOT_YET_OPEN."""
    invitee_id = "aaaaaaaa-0002-0000-0000-000000000002"
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    create = await client.post(BASE + "/", json=_meeting_payload(
        seed_test_users["don_vi_a"], chu_toa_user.sub,
        ngay_hop=tomorrow, gio_bat_dau="09:00",
        thanh_phan=[{"cong_chuc_id": invitee_id, "loai_tham_du": "BAT_BUOC"}],
    ))
    ch_id = create.json()["data"]["id"]

    _override(_make_cbcc_token(invitee_id, seed_test_users["don_vi_a"]))
    resp = await client.post(f"{BASE}/{ch_id}/tu-diem-danh")
    assert resp.status_code == 409
    err = resp.json()["detail"]["error"]
    assert err["code"] == "NOT_YET_OPEN"
    assert "open_at" in err
    assert "close_at" in err


@pytest.mark.asyncio
async def test_checkin_closed_409(client: AsyncClient, chu_toa_user, seed_test_users):
    """Cuộc họp hôm qua → 409 CHECKIN_CLOSED."""
    invitee_id = "aaaaaaaa-0002-0000-0000-000000000002"
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    create = await client.post(BASE + "/", json=_meeting_payload(
        seed_test_users["don_vi_a"], chu_toa_user.sub,
        ngay_hop=yesterday, gio_bat_dau="09:00",
        thanh_phan=[{"cong_chuc_id": invitee_id, "loai_tham_du": "BAT_BUOC"}],
    ))
    ch_id = create.json()["data"]["id"]

    _override(_make_cbcc_token(invitee_id, seed_test_users["don_vi_a"]))
    resp = await client.post(f"{BASE}/{ch_id}/tu-diem-danh")
    assert resp.status_code == 409
    assert resp.json()["detail"]["error"]["code"] == "CHECKIN_CLOSED"


@pytest.mark.asyncio
async def test_in_window_ok(client: AsyncClient, chu_toa_user, seed_test_users):
    """Cuộc họp hôm nay, giờ bắt đầu = now-1m → window mở → điểm danh OK CO_MAT."""
    invitee_id = "aaaaaaaa-0002-0000-0000-000000000002"
    today = date.today().isoformat()
    # gio_bat_dau = now - 1 minute (chắc chắn trong window và dưới threshold 5p → CO_MAT)
    gio_now = (datetime.now() - timedelta(minutes=1)).time().strftime("%H:%M")
    create = await client.post(BASE + "/", json=_meeting_payload(
        seed_test_users["don_vi_a"], chu_toa_user.sub,
        ngay_hop=today, gio_bat_dau=gio_now,
        thanh_phan=[{"cong_chuc_id": invitee_id, "loai_tham_du": "BAT_BUOC"}],
    ))
    ch_id = create.json()["data"]["id"]

    _override(_make_cbcc_token(invitee_id, seed_test_users["don_vi_a"]))
    resp = await client.post(f"{BASE}/{ch_id}/tu-diem-danh")
    assert resp.status_code == 200, resp.text
    assert resp.json()["data"]["trang_thai"] == "CO_MAT"


@pytest.mark.asyncio
async def test_my_status_returns_window_info(
    client: AsyncClient, chu_toa_user, seed_test_users,
):
    """GET diem-danh-cua-toi trả window_status + open_at + close_at."""
    invitee_id = "aaaaaaaa-0002-0000-0000-000000000002"
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    create = await client.post(BASE + "/", json=_meeting_payload(
        seed_test_users["don_vi_a"], chu_toa_user.sub,
        ngay_hop=tomorrow, gio_bat_dau="09:00",
        thanh_phan=[{"cong_chuc_id": invitee_id, "loai_tham_du": "BAT_BUOC"}],
    ))
    ch_id = create.json()["data"]["id"]

    _override(_make_cbcc_token(invitee_id, seed_test_users["don_vi_a"]))
    resp = await client.get(f"{BASE}/{ch_id}/diem-danh-cua-toi")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["window_status"] == "NOT_YET_OPEN"
    assert "open_at" in data
    assert "close_at" in data
