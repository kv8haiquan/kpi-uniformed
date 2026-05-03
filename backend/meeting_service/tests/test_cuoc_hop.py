"""
Test Module 1 (cuộc họp).

Methodology:
- Tx-rollback per test (không persist DB)
- TEST-G2-* dedicated accounts (không pick user thật)
- Verify side effects (audit_log, thong_bao) qua query trong session

Coverage:
- 7 happy path (1/endpoint)
- 3 permission-denied
- 3 cross-cutting (audit, thong_bao bulk, CASCADE)
"""

from datetime import date, time
from uuid import UUID

import pytest
from httpx import AsyncClient
from sqlalchemy import text as sa_text
from sqlalchemy.ext.asyncio import AsyncSession


BASE = "/api/v1/hop-khong-giay/cuoc-hop"


def _payload_create(don_vi_id, chu_toa_id, thu_ky_id=None, thanh_phan=None):
    return {
        "tieu_de": "Test G2 — Giao ban tuần",
        "mo_ta": "Cuộc họp test G2",
        "khoi": "CHUYEN_MON",
        "hinh_thuc": "TRUC_TIEP",
        "ngay_hop": "2026-05-15",
        "gio_bat_dau": "08:30",
        "gio_ket_thuc": "10:00",
        "dia_diem": "Phòng họp test",
        "don_vi_to_chuc_id": str(don_vi_id),
        "chu_toa_id": str(chu_toa_id),
        "thu_ky_id": str(thu_ky_id) if thu_ky_id else None,
        "thanh_phan": thanh_phan or [],
    }


# ════════════════════════════════════════════════════════════════════
# HAPPY PATH (7)
# ════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_create_cuoc_hop(client: AsyncClient, chu_toa_user, seed_test_users):
    """1/7: POST / — tạo cuộc họp."""
    resp = await client.post(BASE + "/", json=_payload_create(
        seed_test_users["don_vi_a"],
        chu_toa_user.sub,
    ))
    assert resp.status_code == 201, resp.text
    data = resp.json()["data"]
    assert data["tieu_de"] == "Test G2 — Giao ban tuần"
    assert data["trang_thai"] == "LEN_KE_HOACH"
    assert data["khoi"] == "CHUYEN_MON"


@pytest.mark.asyncio
async def test_list_cuoc_hop(client: AsyncClient, admin_user, seed_test_users):
    """2/7: GET / — list + pagination."""
    # Create 1 trước rồi list
    await client.post(BASE + "/", json=_payload_create(
        seed_test_users["don_vi_a"], admin_user.sub,
    ))
    resp = await client.get(BASE + "/?page=1&limit=20")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["success"] is True
    assert body["pagination"]["page"] == 1
    assert body["pagination"]["limit"] == 20


@pytest.mark.asyncio
async def test_get_detail(client: AsyncClient, chu_toa_user, seed_test_users):
    """3/7: GET /{id} — chi tiết. Chu_toa của họp xem được."""
    create = await client.post(BASE + "/", json=_payload_create(
        seed_test_users["don_vi_a"], chu_toa_user.sub,
    ))
    ch_id = create.json()["data"]["id"]

    resp = await client.get(f"{BASE}/{ch_id}")
    assert resp.status_code == 200, resp.text
    assert resp.json()["data"]["id"] == ch_id


@pytest.mark.asyncio
async def test_update_cuoc_hop(client: AsyncClient, chu_toa_user, seed_test_users):
    """4/7: PATCH /{id} — cập nhật."""
    create = await client.post(BASE + "/", json=_payload_create(
        seed_test_users["don_vi_a"], chu_toa_user.sub,
    ))
    ch_id = create.json()["data"]["id"]

    resp = await client.patch(f"{BASE}/{ch_id}", json={"dia_diem": "Phòng họp số 2"})
    assert resp.status_code == 200, resp.text
    assert resp.json()["data"]["dia_diem"] == "Phòng họp số 2"


@pytest.mark.asyncio
async def test_huy_cuoc_hop(client: AsyncClient, chu_toa_user, seed_test_users):
    """5/7: POST /{id}/huy."""
    create = await client.post(BASE + "/", json=_payload_create(
        seed_test_users["don_vi_a"], chu_toa_user.sub,
    ))
    ch_id = create.json()["data"]["id"]

    resp = await client.post(f"{BASE}/{ch_id}/huy", json={"ly_do": "Lãnh đạo bận"})
    assert resp.status_code == 200, resp.text
    assert resp.json()["data"]["trang_thai"] == "HUY"


@pytest.mark.asyncio
async def test_gui_giay_moi(
    client: AsyncClient, chu_toa_user, seed_test_users, db_session: AsyncSession
):
    """6/7: POST /{id}/gui-giay-moi — N notification."""
    # Tạo họp với 2 thành phần
    payload = _payload_create(
        seed_test_users["don_vi_a"], chu_toa_user.sub,
        thanh_phan=[
            {"cong_chuc_id": "aaaaaaaa-0002-0000-0000-000000000002", "loai_tham_du": "BAT_BUOC"},
            {"cong_chuc_id": "aaaaaaaa-0003-0000-0000-000000000003", "loai_tham_du": "BAT_BUOC"},
        ],
    )
    create = await client.post(BASE + "/", json=payload)
    ch_id = create.json()["data"]["id"]

    resp = await client.post(f"{BASE}/{ch_id}/gui-giay-moi")
    assert resp.status_code == 200, resp.text
    assert resp.json()["data"]["so_giay_moi_da_gui"] == 2

    # Verify thong_bao có 2 row
    result = await db_session.execute(sa_text("""
        SELECT COUNT(*) FROM common.thong_bao
         WHERE loai = 'MEETING'
           AND doi_tuong_type = 'GIAY_MOI_HOP'
           AND doi_tuong_id = :ch_id
    """), {"ch_id": ch_id})
    assert result.scalar() == 2


@pytest.mark.asyncio
async def test_xac_nhan_tham_du(
    client: AsyncClient, chu_toa_user, thu_ky_phong_a, seed_test_users
):
    """7/7: POST /{id}/xac-nhan — CBCC tự xác nhận."""
    # admin/chu_toa tạo họp với thu_ky_phong_a là 1 thành phần
    create = await client.post(BASE + "/", json=_payload_create(
        seed_test_users["don_vi_a"], chu_toa_user.sub,
        thanh_phan=[
            {"cong_chuc_id": thu_ky_phong_a.sub, "loai_tham_du": "BAT_BUOC"},
        ],
    ))
    ch_id = create.json()["data"]["id"]

    # switch user → thu_ky_phong_a tự xác nhận
    from meeting_service.dependencies import get_current_user
    from meeting_service.main import app as fastapi_app
    async def _override():
        return thu_ky_phong_a
    fastapi_app.dependency_overrides[get_current_user] = _override

    resp = await client.post(f"{BASE}/{ch_id}/xac-nhan", json={"xac_nhan": "THAM_DU"})
    assert resp.status_code == 200, resp.text
    assert resp.json()["data"]["xac_nhan"] == "THAM_DU"


# ════════════════════════════════════════════════════════════════════
# PERMISSION DENIED (3)
# ════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_perm_cbcc_not_invited_get_403(
    client: AsyncClient, admin_user, seed_test_users, cbcc_user,
):
    """CBCC không invited GET /{id} → 403.

    admin tạo cuộc họp Phòng A (không mời cbcc_user ở Phòng B),
    rồi switch sang cbcc_user GET → phải 403.
    """
    create = await client.post(BASE + "/", json=_payload_create(
        seed_test_users["don_vi_a"], admin_user.sub,
    ))
    ch_id = create.json()["data"]["id"]

    # Switch → cbcc_user (Phòng B)
    from meeting_service.dependencies import get_current_user
    from meeting_service.main import app as fastapi_app
    async def _override():
        return cbcc_user
    fastapi_app.dependency_overrides[get_current_user] = _override

    resp = await client.get(f"{BASE}/{ch_id}")
    assert resp.status_code == 403, resp.text


@pytest.mark.asyncio
async def test_perm_thu_ky_phong_b_cannot_edit_phong_a(
    client: AsyncClient, admin_user, seed_test_users, thu_ky_phong_b,
):
    """THU_KY_HOP Phòng B PATCH cuộc họp Phòng A → 403."""
    create = await client.post(BASE + "/", json=_payload_create(
        seed_test_users["don_vi_a"], admin_user.sub,
    ))
    ch_id = create.json()["data"]["id"]

    # Switch → thu_ky_phong_b
    from meeting_service.dependencies import get_current_user
    from meeting_service.main import app as fastapi_app
    async def _override():
        return thu_ky_phong_b
    fastapi_app.dependency_overrides[get_current_user] = _override

    resp = await client.patch(f"{BASE}/{ch_id}", json={"dia_diem": "Hack"})
    assert resp.status_code == 403, resp.text


@pytest.mark.asyncio
async def test_perm_non_chu_toa_cannot_huy(
    client: AsyncClient, admin_user, seed_test_users, cbcc_user,
):
    """CBCC không phải chu_toa POST /huy → 403."""
    create = await client.post(BASE + "/", json=_payload_create(
        seed_test_users["don_vi_a"], admin_user.sub,
    ))
    ch_id = create.json()["data"]["id"]

    # Switch → cbcc_user
    from meeting_service.dependencies import get_current_user
    from meeting_service.main import app as fastapi_app
    async def _override():
        return cbcc_user
    fastapi_app.dependency_overrides[get_current_user] = _override

    resp = await client.post(f"{BASE}/{ch_id}/huy", json={"ly_do": "Hack"})
    assert resp.status_code == 403, resp.text


# ════════════════════════════════════════════════════════════════════
# CROSS-CUTTING (3)
# ════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_audit_log_after_create(
    client: AsyncClient, chu_toa_user, seed_test_users, db_session: AsyncSession,
):
    """Mutation → 1 row trong common.audit_log."""
    create = await client.post(BASE + "/", json=_payload_create(
        seed_test_users["don_vi_a"], chu_toa_user.sub,
    ))
    ch_id = create.json()["data"]["id"]

    result = await db_session.execute(sa_text("""
        SELECT hanh_dong, doi_tuong_loai, chi_tiet
          FROM common.audit_log
         WHERE module = 'MEETING'
           AND doi_tuong_id = :ch_id
           AND hanh_dong = 'CREATE_MEETING'
    """), {"ch_id": ch_id})
    row = result.fetchone()
    assert row is not None
    assert row[0] == "CREATE_MEETING"
    assert row[1] == "cuoc_hop"
    assert row[2]["khoi"] == "CHUYEN_MON"


@pytest.mark.asyncio
async def test_send_invitation_creates_n_thong_bao(
    client: AsyncClient, chu_toa_user, seed_test_users, db_session: AsyncSession,
):
    """gui-giay-moi tạo N row thong_bao."""
    create = await client.post(BASE + "/", json=_payload_create(
        seed_test_users["don_vi_a"], chu_toa_user.sub,
        thanh_phan=[
            {"cong_chuc_id": "aaaaaaaa-0002-0000-0000-000000000002", "loai_tham_du": "BAT_BUOC"},
            {"cong_chuc_id": "aaaaaaaa-0003-0000-0000-000000000003", "loai_tham_du": "THAM_KHAO"},
            {"cong_chuc_id": "aaaaaaaa-0004-0000-0000-000000000004", "loai_tham_du": "BAT_BUOC"},
        ],
    ))
    ch_id = create.json()["data"]["id"]

    await client.post(f"{BASE}/{ch_id}/gui-giay-moi")

    result = await db_session.execute(sa_text("""
        SELECT COUNT(*) FROM common.thong_bao
         WHERE loai = 'MEETING'
           AND doi_tuong_type = 'GIAY_MOI_HOP'
           AND doi_tuong_id = :ch_id
    """), {"ch_id": ch_id})
    assert result.scalar() == 3


@pytest.mark.asyncio
async def test_cascade_delete_thanh_phan(
    client: AsyncClient, chu_toa_user, seed_test_users, db_session: AsyncSession,
):
    """Hard delete cuoc_hop → thanh_phan CASCADE clean.

    Note: API soft delete; ở đây test ON DELETE CASCADE qua hard DELETE.
    """
    create = await client.post(BASE + "/", json=_payload_create(
        seed_test_users["don_vi_a"], chu_toa_user.sub,
        thanh_phan=[
            {"cong_chuc_id": "aaaaaaaa-0002-0000-0000-000000000002", "loai_tham_du": "BAT_BUOC"},
        ],
    ))
    ch_id = create.json()["data"]["id"]

    pre = await db_session.execute(sa_text(
        "SELECT COUNT(*) FROM meeting.thanh_phan WHERE cuoc_hop_id = :ch_id"
    ), {"ch_id": ch_id})
    assert pre.scalar() == 1

    await db_session.execute(sa_text(
        "DELETE FROM meeting.cuoc_hop WHERE id = :ch_id"
    ), {"ch_id": ch_id})

    post = await db_session.execute(sa_text(
        "SELECT COUNT(*) FROM meeting.thanh_phan WHERE cuoc_hop_id = :ch_id"
    ), {"ch_id": ch_id})
    assert post.scalar() == 0
