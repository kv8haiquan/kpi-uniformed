"""
Test G4-fix-6:
- PUT /thanh-phan: add/remove diff, block remove chu_toa, notify added khi DA_THONG_BAO
- POST /tu-diem-danh: self checkin happy + idempotent + not-invited 403
"""

from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy import text as sa_text
from sqlalchemy.ext.asyncio import AsyncSession


BASE = "/api/v1/hop-khong-giay/cuoc-hop"


def _payload(don_vi_id, chu_toa_id, thu_ky_id=None, thanh_phan=None):
    """G4-fix-7: today + gio_bd = now-1m → in checkin window cho self-checkin tests."""
    from datetime import date as _date, datetime as _dt, timedelta as _td
    today = _date.today().isoformat()
    gio_now = (_dt.now() - _td(minutes=1)).time().strftime("%H:%M")
    return {
        "tieu_de": "Test G4-fix-6",
        "khoi": "CHUYEN_MON",
        "hinh_thuc": "TRUC_TIEP",
        "ngay_hop": today,
        "gio_bat_dau": gio_now,
        "don_vi_to_chuc_id": str(don_vi_id),
        "chu_toa_id": str(chu_toa_id),
        "thu_ky_id": str(thu_ky_id) if thu_ky_id else None,
        "thanh_phan": thanh_phan or [],
    }


# ════════════════════════════════════════════════════════════════════
# PUT /thanh-phan
# ════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_sua_thanh_phan_add_remove(
    client: AsyncClient, chu_toa_user, seed_test_users, db_session: AsyncSession,
):
    """PUT replace list → đúng 2 added, 1 removed."""
    create = await client.post(BASE + "/", json=_payload(
        seed_test_users["don_vi_a"], chu_toa_user.sub,
        thanh_phan=[
            {"cong_chuc_id": "aaaaaaaa-0002-0000-0000-000000000002", "loai_tham_du": "BAT_BUOC"},
            {"cong_chuc_id": "aaaaaaaa-0003-0000-0000-000000000003", "loai_tham_du": "BAT_BUOC"},
        ],
    ))
    ch_id = create.json()["data"]["id"]

    # Replace: bỏ 0003, thêm 0004 → diff add=1 remove=1
    new_list = [
        {"cong_chuc_id": "aaaaaaaa-0002-0000-0000-000000000002", "loai_tham_du": "BAT_BUOC"},
        {"cong_chuc_id": "aaaaaaaa-0004-0000-0000-000000000004", "loai_tham_du": "BAT_BUOC"},
    ]
    resp = await client.put(f"{BASE}/{ch_id}/thanh-phan", json={"thanh_phan": new_list})
    assert resp.status_code == 200, resp.text
    summary = resp.json()["data"]
    assert summary["so_them"] == 1
    assert summary["so_bo"] == 1
    assert summary["tong_thanh_phan"] == 2

    # Verify DB
    result = await db_session.execute(sa_text(
        "SELECT cong_chuc_id::text FROM meeting.thanh_phan WHERE cuoc_hop_id = :id ORDER BY cong_chuc_id"
    ), {"id": ch_id})
    ids = sorted([r[0] for r in result.fetchall()])
    assert "aaaaaaaa-0002-0000-0000-000000000002" in ids
    assert "aaaaaaaa-0004-0000-0000-000000000004" in ids
    assert "aaaaaaaa-0003-0000-0000-000000000003" not in ids


@pytest.mark.asyncio
async def test_sua_thanh_phan_block_remove_chu_toa(
    client: AsyncClient, chu_toa_user, seed_test_users,
):
    """KHÔNG cho remove chu_toa khỏi thành phần → 409."""
    # Tạo họp, sau đó thêm chu_toa_user vào thanh_phan
    create = await client.post(BASE + "/", json=_payload(
        seed_test_users["don_vi_a"], chu_toa_user.sub,
        thanh_phan=[{"cong_chuc_id": chu_toa_user.sub, "loai_tham_du": "BAT_BUOC"}],
    ))
    ch_id = create.json()["data"]["id"]

    # Thử PUT empty list → bỏ chu_toa
    resp = await client.put(f"{BASE}/{ch_id}/thanh-phan", json={"thanh_phan": []})
    assert resp.status_code == 409
    assert resp.json()["detail"]["error"]["code"] == "CANNOT_REMOVE_CORE"


@pytest.mark.asyncio
async def test_sua_thanh_phan_notify_added_when_da_thong_bao(
    client: AsyncClient, chu_toa_user, seed_test_users, db_session: AsyncSession,
):
    """Khi cuộc họp DA_THONG_BAO → người mới thêm nhận GIAY_MOI_HOP."""
    create = await client.post(BASE + "/", json=_payload(
        seed_test_users["don_vi_a"], chu_toa_user.sub,
        thanh_phan=[{"cong_chuc_id": "aaaaaaaa-0002-0000-0000-000000000002", "loai_tham_du": "BAT_BUOC"}],
    ))
    ch_id = create.json()["data"]["id"]
    # Set DA_THONG_BAO
    await db_session.execute(sa_text(
        "UPDATE meeting.cuoc_hop SET trang_thai='DA_THONG_BAO' WHERE id=:id"
    ), {"id": ch_id})
    await db_session.flush()

    # Thêm 0004 vào list
    new_list = [
        {"cong_chuc_id": "aaaaaaaa-0002-0000-0000-000000000002", "loai_tham_du": "BAT_BUOC"},
        {"cong_chuc_id": "aaaaaaaa-0004-0000-0000-000000000004", "loai_tham_du": "BAT_BUOC"},
    ]
    await client.put(f"{BASE}/{ch_id}/thanh-phan", json={"thanh_phan": new_list})

    # Verify GIAY_MOI_HOP gửi cho 0004
    res = await db_session.execute(sa_text("""
        SELECT COUNT(*) FROM common.thong_bao
         WHERE doi_tuong_id = :id
           AND doi_tuong_type = 'GIAY_MOI_HOP'
           AND nguoi_nhan_id = 'aaaaaaaa-0004-0000-0000-000000000004'
    """), {"id": ch_id})
    assert res.scalar() == 1


# ════════════════════════════════════════════════════════════════════
# POST /tu-diem-danh
# ════════════════════════════════════════════════════════════════════

def _make_cbcc_token(sub: str, don_vi_id):
    from shared.auth import TokenPayload
    return TokenPayload(
        sub=sub,
        ma_cc="TEST-G3-CBCC", ho_ten="CBCC",
        vai_tro="CC", don_vi_id=str(don_vi_id),
        platform_roles=[],
        exp=int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()),
        type="access",
    )


@pytest.mark.asyncio
async def test_tu_diem_danh_happy(
    client: AsyncClient, chu_toa_user, seed_test_users, db_session: AsyncSession,
):
    """CBCC trong thành phần tự điểm danh → CO_MAT/DEN_MUON."""
    invitee_id = "aaaaaaaa-0002-0000-0000-000000000002"
    create = await client.post(BASE + "/", json=_payload(
        seed_test_users["don_vi_a"], chu_toa_user.sub,
        thanh_phan=[{"cong_chuc_id": invitee_id, "loai_tham_du": "BAT_BUOC"}],
    ))
    ch_id = create.json()["data"]["id"]

    # Switch sang CBCC invitee
    from meeting_service.dependencies import get_current_user
    from meeting_service.main import app as fastapi_app
    cbcc_token = _make_cbcc_token(invitee_id, seed_test_users["don_vi_a"])
    async def _o():
        return cbcc_token
    fastapi_app.dependency_overrides[get_current_user] = _o

    resp = await client.post(f"{BASE}/{ch_id}/tu-diem-danh")
    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]
    assert data["hinh_thuc"] == "TU_DIEM_DANH"
    assert data["trang_thai"] in ("CO_MAT", "DEN_MUON")

    # Verify audit CHECKIN_SELF
    res = await db_session.execute(sa_text("""
        SELECT COUNT(*) FROM common.audit_log
         WHERE module='MEETING' AND hanh_dong='CHECKIN_SELF'
           AND doi_tuong_id=:dd_id
    """), {"dd_id": data["id"]})
    assert res.scalar() == 1


@pytest.mark.asyncio
async def test_tu_diem_danh_idempotent_409(
    client: AsyncClient, chu_toa_user, seed_test_users,
):
    """Click "Tôi có mặt" lần 2 → 409 ALREADY_CHECKED_IN."""
    invitee_id = "aaaaaaaa-0002-0000-0000-000000000002"
    create = await client.post(BASE + "/", json=_payload(
        seed_test_users["don_vi_a"], chu_toa_user.sub,
        thanh_phan=[{"cong_chuc_id": invitee_id, "loai_tham_du": "BAT_BUOC"}],
    ))
    ch_id = create.json()["data"]["id"]

    from meeting_service.dependencies import get_current_user
    from meeting_service.main import app as fastapi_app
    cbcc = _make_cbcc_token(invitee_id, seed_test_users["don_vi_a"])
    async def _o():
        return cbcc
    fastapi_app.dependency_overrides[get_current_user] = _o

    r1 = await client.post(f"{BASE}/{ch_id}/tu-diem-danh")
    assert r1.status_code == 200
    r2 = await client.post(f"{BASE}/{ch_id}/tu-diem-danh")
    assert r2.status_code == 409
    assert r2.json()["detail"]["error"]["code"] == "ALREADY_CHECKED_IN"


@pytest.mark.asyncio
async def test_tu_diem_danh_not_invited_403(
    client: AsyncClient, chu_toa_user, seed_test_users,
):
    """User KHÔNG trong thành phần → 403 NOT_INVITED."""
    create = await client.post(BASE + "/", json=_payload(
        seed_test_users["don_vi_a"], chu_toa_user.sub, thanh_phan=[],
    ))
    ch_id = create.json()["data"]["id"]

    from meeting_service.dependencies import get_current_user
    from meeting_service.main import app as fastapi_app
    outsider = _make_cbcc_token(
        "aaaaaaaa-0004-0000-0000-000000000004",
        seed_test_users["don_vi_b"],
    )
    async def _o():
        return outsider
    fastapi_app.dependency_overrides[get_current_user] = _o

    resp = await client.post(f"{BASE}/{ch_id}/tu-diem-danh")
    assert resp.status_code == 403
    assert resp.json()["detail"]["error"]["code"] == "NOT_INVITED"


@pytest.mark.asyncio
async def test_diem_danh_cua_toi_status(
    client: AsyncClient, chu_toa_user, seed_test_users,
):
    """GET diem-danh-cua-toi → trả status đúng cho FE biết hiện nút hay không."""
    invitee_id = "aaaaaaaa-0002-0000-0000-000000000002"
    create = await client.post(BASE + "/", json=_payload(
        seed_test_users["don_vi_a"], chu_toa_user.sub,
        thanh_phan=[{"cong_chuc_id": invitee_id, "loai_tham_du": "BAT_BUOC"}],
    ))
    ch_id = create.json()["data"]["id"]

    from meeting_service.dependencies import get_current_user
    from meeting_service.main import app as fastapi_app
    cbcc = _make_cbcc_token(invitee_id, seed_test_users["don_vi_a"])
    async def _o():
        return cbcc
    fastapi_app.dependency_overrides[get_current_user] = _o

    # Trước khi điểm danh
    r1 = await client.get(f"{BASE}/{ch_id}/diem-danh-cua-toi")
    assert r1.status_code == 200
    assert r1.json()["data"]["is_invited"] is True
    assert r1.json()["data"]["da_diem_danh"] is False

    # Tự điểm danh
    await client.post(f"{BASE}/{ch_id}/tu-diem-danh")

    # Sau
    r2 = await client.get(f"{BASE}/{ch_id}/diem-danh-cua-toi")
    assert r2.json()["data"]["da_diem_danh"] is True
    assert r2.json()["data"]["hinh_thuc"] == "TU_DIEM_DANH"
