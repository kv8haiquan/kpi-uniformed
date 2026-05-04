"""Test endpoints lifecycle bat-dau / ket-thuc (Phase 4.1 BE_P2).

Threat model:
- State machine: chỉ cho transition đúng (DA_THONG_BAO→DANG_DIEN_RA,
  DANG_DIEN_RA→HOAN_THANH). Status sai → 400, không leak info.
- Permission: dùng require_can_edit_meeting (chu_toa | thu_ky | admin |
  TRUONG_CNTT). User khác → 403.
- Audit log: ghi 2 hanh_dong CUOC_HOP_BAT_DAU/KET_THUC vào common.audit_log
  để trace ai bắt đầu/kết thúc cuộc họp nào.
- ket-thuc cleanup state: phòng case cuộc họp kết thúc giữa lúc đang
  trình chiếu — tránh row trang_thai_trinh_chieu kẹt is_active=TRUE.
"""

from datetime import date, time
from uuid import UUID

import pytest
from httpx import AsyncClient
from sqlalchemy import text as sa_text
from sqlalchemy.ext.asyncio import AsyncSession

from meeting_service.models import TrangThaiTrinhChieu


BASE = "/api/v1/hop-khong-giay/cuoc-hop"


def _payload_create(don_vi_id, chu_toa_id):
    return {
        "tieu_de": "Test BE_P2 — Lifecycle",
        "khoi": "CHUYEN_MON",
        "hinh_thuc": "TRUC_TIEP",
        "ngay_hop": "2026-05-15",
        "gio_bat_dau": "08:30",
        "gio_ket_thuc": "10:00",
        "dia_diem": "Phòng họp test",
        "don_vi_to_chuc_id": str(don_vi_id),
        "chu_toa_id": str(chu_toa_id),
        "thanh_phan": [],
    }


async def _create_meeting_in_status(
    client: AsyncClient,
    db_session: AsyncSession,
    user,
    seed_test_users,
    target_status: str,
) -> UUID:
    """Helper: tạo cuộc họp + force trạng thái mong muốn qua SQL."""
    resp = await client.post(
        BASE + "/",
        json=_payload_create(seed_test_users["don_vi_a"], user.sub),
    )
    assert resp.status_code == 201, resp.text
    cuoc_hop_id = UUID(resp.json()["data"]["id"])

    if target_status != "LEN_KE_HOACH":
        await db_session.execute(
            sa_text("UPDATE meeting.cuoc_hop SET trang_thai = :s WHERE id = :id"),
            {"s": target_status, "id": str(cuoc_hop_id)},
        )
        await db_session.flush()
    return cuoc_hop_id


# ════════════════════════════════════════════════════════════════════
# 5 TESTS BE_P2
# ════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_bat_dau_valid_transition(
    client: AsyncClient, db_session: AsyncSession, chu_toa_user, seed_test_users
):
    """1/5: DA_THONG_BAO → POST /bat-dau → 200, status=DANG_DIEN_RA."""
    cuoc_hop_id = await _create_meeting_in_status(
        client, db_session, chu_toa_user, seed_test_users, "DA_THONG_BAO"
    )
    resp = await client.post(f"{BASE}/{cuoc_hop_id}/bat-dau")
    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]
    assert data["trang_thai"] == "DANG_DIEN_RA"


@pytest.mark.asyncio
async def test_bat_dau_invalid_transition(
    client: AsyncClient, db_session: AsyncSession, chu_toa_user, seed_test_users
):
    """2/5: LEN_KE_HOACH → POST /bat-dau → 400 INVALID_STATE_TRANSITION."""
    cuoc_hop_id = await _create_meeting_in_status(
        client, db_session, chu_toa_user, seed_test_users, "LEN_KE_HOACH"
    )
    resp = await client.post(f"{BASE}/{cuoc_hop_id}/bat-dau")
    assert resp.status_code == 400, resp.text
    body = resp.json()
    assert body["detail"]["error"]["code"] == "INVALID_STATE_TRANSITION"
    assert "DA_THONG_BAO" in body["detail"]["error"]["message"]


@pytest.mark.asyncio
async def test_bat_dau_permission_required(
    client: AsyncClient, db_session: AsyncSession,
    chu_toa_user, seed_test_users,
):
    """3/5: user không phải chu_toa/thu_ky/admin → 403 (qua require_can_edit_meeting)."""
    # Tạo cuộc họp dưới quyền chu_toa
    cuoc_hop_id = await _create_meeting_in_status(
        client, db_session, chu_toa_user, seed_test_users, "DA_THONG_BAO"
    )
    # Switch sang user khác (cbcc thường, không liên quan cuộc họp)
    from meeting_service.tests.conftest import _make_user, _set_user
    from meeting_service.main import app
    from meeting_service.dependencies import get_current_user

    cbcc = _make_user("TEST-G3-004", seed_test_users["don_vi_b"])
    _set_user(cbcc)
    try:
        resp = await client.post(f"{BASE}/{cuoc_hop_id}/bat-dau")
        assert resp.status_code == 403, resp.text
    finally:
        app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_ket_thuc_cleanup_presentation_state(
    client: AsyncClient, db_session: AsyncSession, chu_toa_user, seed_test_users
):
    """4/5: DANG_DIEN_RA + trang_thai_trinh_chieu(is_active=TRUE) → ket-thuc →
    state is_active=FALSE + ket_thuc_luc set."""
    cuoc_hop_id = await _create_meeting_in_status(
        client, db_session, chu_toa_user, seed_test_users, "DANG_DIEN_RA"
    )

    # Lấy 1 tài liệu hợp lệ — bypass: tạo trực tiếp via SQL với cuoc_hop_id
    # (tránh phải upload file qua API)
    tai_lieu_id = (await db_session.execute(sa_text("""
        INSERT INTO meeting.tai_lieu
            (cuoc_hop_id, ten_tai_lieu, minio_key, file_size, created_by)
        VALUES (:ch, 'test.pdf', 'test/key.pdf', 1024, :uid)
        RETURNING id
    """), {"ch": str(cuoc_hop_id), "uid": chu_toa_user.sub})).scalar_one()

    # Tạo state đang active
    db_session.add(TrangThaiTrinhChieu(
        cuoc_hop_id=cuoc_hop_id,
        tai_lieu_hien_tai_id=tai_lieu_id,
        is_active=True,
    ))
    await db_session.flush()

    resp = await client.post(f"{BASE}/{cuoc_hop_id}/ket-thuc")
    assert resp.status_code == 200, resp.text
    assert resp.json()["data"]["trang_thai"] == "HOAN_THANH"

    # Verify state cleanup
    row = await db_session.execute(sa_text("""
        SELECT is_active, ket_thuc_luc FROM meeting.trang_thai_trinh_chieu
         WHERE cuoc_hop_id = :ch
    """), {"ch": str(cuoc_hop_id)})
    state = row.one()
    assert state.is_active is False, "ket-thuc phải set is_active=FALSE"
    assert state.ket_thuc_luc is not None, "ket-thuc phải set ket_thuc_luc=NOW"


@pytest.mark.asyncio
async def test_audit_log_recorded(
    client: AsyncClient, db_session: AsyncSession, chu_toa_user, seed_test_users
):
    """5/5: sau bat-dau → audit_log có row hanh_dong=CUOC_HOP_BAT_DAU."""
    cuoc_hop_id = await _create_meeting_in_status(
        client, db_session, chu_toa_user, seed_test_users, "DA_THONG_BAO"
    )
    resp = await client.post(f"{BASE}/{cuoc_hop_id}/bat-dau")
    assert resp.status_code == 200

    row = await db_session.execute(sa_text("""
        SELECT module, hanh_dong, doi_tuong_loai, doi_tuong_id, nguoi_thuc_hien_id
          FROM common.audit_log
         WHERE module = 'MEETING'
           AND hanh_dong = 'CUOC_HOP_BAT_DAU'
           AND doi_tuong_id = :ch
         ORDER BY created_at DESC
         LIMIT 1
    """), {"ch": str(cuoc_hop_id)})
    audit = row.one_or_none()
    assert audit is not None, "Phải có audit row CUOC_HOP_BAT_DAU"
    assert audit.module == "MEETING"
    assert audit.doi_tuong_loai == "cuoc_hop"
    assert str(audit.nguoi_thuc_hien_id) == chu_toa_user.sub
