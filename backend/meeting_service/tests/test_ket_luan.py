"""
Test Module 10 — Kết luận + Dashboard.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy import text as sa_text
from sqlalchemy.ext.asyncio import AsyncSession


BASE_CH = "/api/v1/hop-khong-giay/cuoc-hop"
BASE_KL = "/api/v1/hop-khong-giay/ket-luan"
BASE_TK = "/api/v1/hop-khong-giay/thong-ke"


def _meeting_payload(don_vi_id, chu_toa_id):
    return {
        "tieu_de": "Test G3b — họp giao việc",
        "khoi": "CHUYEN_MON",
        "hinh_thuc": "TRUC_TIEP",
        "ngay_hop": "2026-05-25",
        "gio_bat_dau": "08:30",
        "don_vi_to_chuc_id": str(don_vi_id),
        "chu_toa_id": str(chu_toa_id),
        "thanh_phan": [],
    }


@pytest.mark.asyncio
async def test_create_ket_luan_audit(
    client: AsyncClient, chu_toa_user, seed_test_users, db_session: AsyncSession,
):
    create = await client.post(BASE_CH + "/", json=_meeting_payload(
        seed_test_users["don_vi_a"], chu_toa_user.sub,
    ))
    ch_id = create.json()["data"]["id"]

    resp = await client.post(f"{BASE_CH}/{ch_id}/ket-luan", json={
        "noi_dung": "Báo cáo tiến độ dự án X trước 30/05",
        "nguoi_phu_trach_id": "aaaaaaaa-0002-0000-0000-000000000002",
        "han_hoan_thanh": "2026-05-30",
        "muc_uu_tien": "CAO",
    })
    assert resp.status_code == 201, resp.text
    kl_id = resp.json()["data"]["id"]
    assert resp.json()["data"]["trang_thai"] == "CHUA_BAT_DAU"

    # Audit
    audit = await db_session.execute(sa_text("""
        SELECT COUNT(*) FROM common.audit_log
         WHERE module='MEETING' AND hanh_dong='CREATE_TASK'
           AND doi_tuong_id=:kl_id
    """), {"kl_id": kl_id})
    assert audit.scalar() == 1

    # Notification gửi cho nguoi_phu_trach
    notif = await db_session.execute(sa_text("""
        SELECT COUNT(*) FROM common.thong_bao
         WHERE loai='MEETING' AND doi_tuong_type='KET_LUAN_GIAO'
           AND doi_tuong_id=:kl_id
    """), {"kl_id": kl_id})
    assert notif.scalar() == 1


@pytest.mark.asyncio
async def test_tien_do_auto_status(
    client: AsyncClient, chu_toa_user, seed_test_users, db_session: AsyncSession,
):
    """Update tiến độ → auto trang_thai."""
    create = await client.post(BASE_CH + "/", json=_meeting_payload(
        seed_test_users["don_vi_a"], chu_toa_user.sub,
    ))
    ch_id = create.json()["data"]["id"]

    # Tạo nhiệm vụ giao chu_toa_user
    kl_resp = await client.post(f"{BASE_CH}/{ch_id}/ket-luan", json={
        "noi_dung": "Self task", "nguoi_phu_trach_id": chu_toa_user.sub,
    })
    kl_id = kl_resp.json()["data"]["id"]

    # Tiến độ 30% → DANG_LAM
    r1 = await client.post(f"{BASE_KL}/{kl_id}/tien-do", json={
        "phan_tram_sau": 30, "mo_ta": "Đã làm 30%",
    })
    assert r1.status_code == 201

    res = await db_session.execute(sa_text(
        "SELECT trang_thai, tien_do_phan_tram FROM meeting.ket_luan WHERE id=:id"
    ), {"id": kl_id})
    row = res.fetchone()
    assert row[0] == "DANG_LAM"
    assert row[1] == 30

    # Tiến độ 100% → HOAN_THANH
    r2 = await client.post(f"{BASE_KL}/{kl_id}/tien-do", json={
        "phan_tram_sau": 100, "mo_ta": "Xong",
    })
    assert r2.status_code == 201

    res = await db_session.execute(sa_text(
        "SELECT trang_thai, tien_do_phan_tram FROM meeting.ket_luan WHERE id=:id"
    ), {"id": kl_id})
    row = res.fetchone()
    assert row[0] == "HOAN_THANH"
    assert row[1] == 100


@pytest.mark.asyncio
async def test_cua_toi_filter(
    client: AsyncClient, chu_toa_user, seed_test_users,
):
    create = await client.post(BASE_CH + "/", json=_meeting_payload(
        seed_test_users["don_vi_a"], chu_toa_user.sub,
    ))
    ch_id = create.json()["data"]["id"]

    # Tạo 2 nhiệm vụ giao chu_toa_user
    for i in range(2):
        await client.post(f"{BASE_CH}/{ch_id}/ket-luan", json={
            "noi_dung": f"Task {i}", "nguoi_phu_trach_id": chu_toa_user.sub,
        })

    resp = await client.get(BASE_KL + "/cua-toi")
    assert resp.status_code == 200
    items = resp.json()["data"]
    assert len(items) >= 2


@pytest.mark.asyncio
async def test_dashboard_ca_nhan(
    client: AsyncClient, chu_toa_user, seed_test_users,
):
    """Dashboard cá nhân — count đúng nhiệm vụ + cuộc họp."""
    resp = await client.get(BASE_TK + "/ca-nhan")
    assert resp.status_code == 200
    d = resp.json()["data"]
    # Tất cả field phải có
    for k in ("so_cuoc_hop_thang_nay", "so_cuoc_hop_tham_du", "so_lan_vang",
              "ty_le_tham_du", "nhiem_vu_dang_lam", "nhiem_vu_qua_han"):
        assert k in d


@pytest.mark.asyncio
async def test_dashboard_don_vi_lanh_dao_only(
    client: AsyncClient, chu_toa_user, seed_test_users,
):
    """LĐ ĐV xem được dashboard đơn vị mình."""
    don_vi_a = seed_test_users["don_vi_a"]
    resp = await client.get(f"{BASE_TK}/don-vi/{don_vi_a}")
    # chu_toa_user is_lanh_dao=True và don_vi_id=don_vi_a → OK
    assert resp.status_code == 200, resp.text
    d = resp.json()["data"]
    for k in ("so_cuoc_hop", "so_nhiem_vu_giao", "so_nhiem_vu_hoan_thanh",
              "so_nhiem_vu_qua_han", "ty_le_hoan_thanh"):
        assert k in d


@pytest.mark.asyncio
async def test_dashboard_don_vi_other_403(
    client: AsyncClient, chu_toa_user, seed_test_users,
):
    """LĐ ĐV phòng A KHÔNG xem được dashboard phòng B."""
    don_vi_b = seed_test_users["don_vi_b"]
    resp = await client.get(f"{BASE_TK}/don-vi/{don_vi_b}")
    assert resp.status_code == 403
