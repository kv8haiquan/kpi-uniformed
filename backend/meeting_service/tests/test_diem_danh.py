"""
Test Module 4 — Điểm danh.

Tests:
- Sinh QR token + CBCC quét (mời + token đúng cuộc họp) → CO_MAT
- Bấm tay multi-CBCC + audit CHECKIN_MANUAL
- Tổng hợp summary đếm đúng
- Permission: CBCC ngoài thành phần quét QR → 403
- Idempotent: quét 2 lần → 409
"""

import pytest
from httpx import AsyncClient
from sqlalchemy import text as sa_text
from sqlalchemy.ext.asyncio import AsyncSession


BASE_CH = "/api/v1/hop-khong-giay/cuoc-hop"
BASE_DD = "/api/v1/hop-khong-giay/diem-danh"


def _create_meeting_payload(don_vi_id, chu_toa_id, thanh_phan):
    """G4-fix-7: dùng today + gio = now-1m để in window cho QR submit test."""
    from datetime import date, datetime, timedelta
    today = date.today().isoformat()
    gio_now = (datetime.now() - timedelta(minutes=1)).time().strftime("%H:%M")
    return {
        "tieu_de": "Test G3 — Họp điểm danh",
        "khoi": "CHUYEN_MON",
        "hinh_thuc": "TRUC_TIEP",
        "ngay_hop": today,
        "gio_bat_dau": gio_now,
        "don_vi_to_chuc_id": str(don_vi_id),
        "chu_toa_id": str(chu_toa_id),
        "thanh_phan": thanh_phan,
    }


@pytest.mark.asyncio
async def test_qr_flow_co_mat(
    client: AsyncClient, chu_toa_user, seed_test_users,
    db_session: AsyncSession,
):
    """chu_toa sinh QR token → thu_ky_phong_a quét → CO_MAT.

    NOTE: KHÔNG dùng fixture thu_ky_phong_a để tránh override get_current_user.
    Tạo TokenPayload thu_ky inline thay thế.
    """
    from datetime import datetime, timedelta, timezone
    from shared.auth import TokenPayload

    thu_ky_payload = TokenPayload(
        sub="aaaaaaaa-0002-0000-0000-000000000002",
        ma_cc="TEST-G3-002",
        ho_ten="Test Thư ký",
        vai_tro="CC",
        don_vi_id=str(seed_test_users["don_vi_a"]),
        platform_roles=["THU_KY_HOP"],
        exp=int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()),
        type="access",
    )

    # 1. chu_toa_user (đang active) tạo cuộc họp mời thu_ky
    create = await client.post(BASE_CH + "/", json=_create_meeting_payload(
        seed_test_users["don_vi_a"], chu_toa_user.sub,
        thanh_phan=[{"cong_chuc_id": thu_ky_payload.sub, "loai_tham_du": "BAT_BUOC"}],
    ))
    ch_id = create.json()["data"]["id"]

    # 2. chu_toa sinh QR token
    qr = await client.post(f"{BASE_DD}/qr-token/{ch_id}")
    assert qr.status_code == 200, qr.text
    token = qr.json()["data"]["token"]

    # 3. Switch → thu_ky quét
    from meeting_service.dependencies import get_current_user
    from meeting_service.main import app as fastapi_app
    async def _override():
        return thu_ky_payload
    fastapi_app.dependency_overrides[get_current_user] = _override

    resp = await client.post(BASE_DD + "/quet", json={"token": token})
    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]
    assert data["hinh_thuc"] == "QR"
    # Trạng thái CO_MAT hoặc DEN_MUON tùy vào timing test (ngay_hop=2026-05-20 future)
    assert data["trang_thai"] in ("CO_MAT", "DEN_MUON")

    # Verify audit CHECKIN_QR
    res = await db_session.execute(sa_text("""
        SELECT COUNT(*) FROM common.audit_log
         WHERE module='MEETING' AND hanh_dong='CHECKIN_QR'
           AND doi_tuong_id=:dd_id
    """), {"dd_id": data["id"]})
    assert res.scalar() == 1


@pytest.mark.asyncio
async def test_qr_quet_2_lan_409(
    client: AsyncClient, chu_toa_user, seed_test_users,
):
    from datetime import datetime, timedelta, timezone
    from shared.auth import TokenPayload

    thu_ky_payload = TokenPayload(
        sub="aaaaaaaa-0002-0000-0000-000000000002",
        ma_cc="TEST-G3-002",
        ho_ten="TK", vai_tro="CC",
        don_vi_id=str(seed_test_users["don_vi_a"]),
        platform_roles=["THU_KY_HOP"],
        exp=int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()),
        type="access",
    )

    create = await client.post(BASE_CH + "/", json=_create_meeting_payload(
        seed_test_users["don_vi_a"], chu_toa_user.sub,
        thanh_phan=[{"cong_chuc_id": thu_ky_payload.sub, "loai_tham_du": "BAT_BUOC"}],
    ))
    ch_id = create.json()["data"]["id"]
    qr = await client.post(f"{BASE_DD}/qr-token/{ch_id}")
    token = qr.json()["data"]["token"]

    from meeting_service.dependencies import get_current_user
    from meeting_service.main import app as fastapi_app
    async def _override():
        return thu_ky_payload
    fastapi_app.dependency_overrides[get_current_user] = _override

    r1 = await client.post(BASE_DD + "/quet", json={"token": token})
    assert r1.status_code == 200
    r2 = await client.post(BASE_DD + "/quet", json={"token": token})
    assert r2.status_code == 409
    assert r2.json()["detail"]["error"]["code"] == "ALREADY_CHECKED_IN"


@pytest.mark.asyncio
async def test_qr_quet_not_invited_403(
    client: AsyncClient, chu_toa_user, seed_test_users,
):
    """User không có trong thành phần → quét QR fail."""
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

    create = await client.post(BASE_CH + "/", json=_create_meeting_payload(
        seed_test_users["don_vi_a"], chu_toa_user.sub, thanh_phan=[],
    ))
    ch_id = create.json()["data"]["id"]
    qr = await client.post(f"{BASE_DD}/qr-token/{ch_id}")
    token = qr.json()["data"]["token"]

    from meeting_service.dependencies import get_current_user
    from meeting_service.main import app as fastapi_app
    async def _override():
        return outsider
    fastapi_app.dependency_overrides[get_current_user] = _override

    resp = await client.post(BASE_DD + "/quet", json={"token": token})
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_bam_tay_bulk(
    client: AsyncClient, chu_toa_user, seed_test_users, db_session: AsyncSession,
):
    create = await client.post(BASE_CH + "/", json=_create_meeting_payload(
        seed_test_users["don_vi_a"], chu_toa_user.sub,
        thanh_phan=[
            {"cong_chuc_id": "aaaaaaaa-0002-0000-0000-000000000002", "loai_tham_du": "BAT_BUOC"},
            {"cong_chuc_id": "aaaaaaaa-0003-0000-0000-000000000003", "loai_tham_du": "BAT_BUOC"},
        ],
    ))
    ch_id = create.json()["data"]["id"]

    payload = {
        "cuoc_hop_id": ch_id,
        "diem_danh": [
            {"cong_chuc_id": "aaaaaaaa-0002-0000-0000-000000000002", "trang_thai": "CO_MAT"},
            {"cong_chuc_id": "aaaaaaaa-0003-0000-0000-000000000003", "trang_thai": "VANG_KHONG_PHEP"},
        ],
    }
    resp = await client.post(BASE_DD + "/bam-tay", json=payload)
    assert resp.status_code == 200, resp.text
    assert resp.json()["data"]["so_diem_danh"] == 2

    # Audit CHECKIN_MANUAL (1 row cho whole batch)
    res = await db_session.execute(sa_text("""
        SELECT COUNT(*) FROM common.audit_log
         WHERE module='MEETING' AND hanh_dong='CHECKIN_MANUAL'
           AND doi_tuong_id=:ch_id
    """), {"ch_id": ch_id})
    assert res.scalar() == 1


@pytest.mark.asyncio
async def test_summary_count(
    client: AsyncClient, chu_toa_user, seed_test_users,
):
    create = await client.post(BASE_CH + "/", json=_create_meeting_payload(
        seed_test_users["don_vi_a"], chu_toa_user.sub,
        thanh_phan=[
            {"cong_chuc_id": "aaaaaaaa-0002-0000-0000-000000000002", "loai_tham_du": "BAT_BUOC"},
            {"cong_chuc_id": "aaaaaaaa-0003-0000-0000-000000000003", "loai_tham_du": "BAT_BUOC"},
            {"cong_chuc_id": "aaaaaaaa-0004-0000-0000-000000000004", "loai_tham_du": "THAM_KHAO"},
        ],
    ))
    ch_id = create.json()["data"]["id"]

    await client.post(BASE_DD + "/bam-tay", json={
        "cuoc_hop_id": ch_id,
        "diem_danh": [
            {"cong_chuc_id": "aaaaaaaa-0002-0000-0000-000000000002", "trang_thai": "CO_MAT"},
            {"cong_chuc_id": "aaaaaaaa-0003-0000-0000-000000000003", "trang_thai": "VANG_KHONG_PHEP"},
        ],
    })

    resp = await client.get(f"{BASE_CH}/{ch_id}/diem-danh")
    assert resp.status_code == 200
    s = resp.json()["data"]
    assert s["tong_so"] == 3
    assert s["co_mat"] == 1
    assert s["vang_khong_phep"] == 1
    assert s["chua_diem_danh"] == 1


@pytest.mark.asyncio
async def test_diem_danh_cua_toi_not_invited_403(
    client: AsyncClient, chu_toa_user, seed_test_users,
):
    """Fix 30/07/2026: /diem-danh-cua-toi phải chặn user ngoài cuộc họp.

    Trước fix endpoint này không có require_can_view_meeting nên trả 200 cho
    mọi user đăng nhập, lệch với các endpoint cùng trang (đều 403).
    """
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

    create = await client.post(BASE_CH + "/", json=_create_meeting_payload(
        seed_test_users["don_vi_a"], chu_toa_user.sub, thanh_phan=[],
    ))
    ch_id = create.json()["data"]["id"]

    # Chủ tọa vẫn xem được trạng thái của mình
    resp_ct = await client.get(f"{BASE_CH}/{ch_id}/diem-danh-cua-toi")
    assert resp_ct.status_code == 200

    from meeting_service.dependencies import get_current_user
    from meeting_service.main import app as fastapi_app
    async def _override():
        return outsider
    fastapi_app.dependency_overrides[get_current_user] = _override

    resp = await client.get(f"{BASE_CH}/{ch_id}/diem-danh-cua-toi")
    assert resp.status_code == 403
    assert resp.json()["detail"]["error"]["code"] == "NO_PERMISSION"
