"""
Test G4-fix-5.a — guard 409 cho cuộc họp đã HUY.

Cases:
1. PATCH cuộc họp HUY → 409 MEETING_CANCELLED (qua require_can_edit_meeting)
2. POST /huy lại lần 2 → 409 (idempotent guard)
3. Upload tài liệu cho cuộc họp HUY → 409
4. Bấm tay điểm danh cho cuộc họp HUY → 409
5. Tạo kết luận cho cuộc họp HUY → 409
"""

import io

import pytest
from httpx import AsyncClient
from sqlalchemy import text as sa_text
from sqlalchemy.ext.asyncio import AsyncSession


BASE = "/api/v1/hop-khong-giay/cuoc-hop"


def _payload(don_vi_id, chu_toa_id):
    return {
        "tieu_de": "Test G4-fix-5 — meeting will be cancelled",
        "khoi": "CHUYEN_MON",
        "hinh_thuc": "TRUC_TIEP",
        "ngay_hop": "2026-06-01",
        "gio_bat_dau": "08:30",
        "don_vi_to_chuc_id": str(don_vi_id),
        "chu_toa_id": str(chu_toa_id),
        "thanh_phan": [
            {"cong_chuc_id": "aaaaaaaa-0002-0000-0000-000000000002", "loai_tham_du": "BAT_BUOC"},
        ],
    }


async def _create_and_cancel(
    client: AsyncClient, chu_toa_user, seed_test_users, db_session: AsyncSession,
) -> str:
    """Helper: tạo cuộc họp + hủy → trả về ch_id."""
    create = await client.post(BASE + "/", json=_payload(
        seed_test_users["don_vi_a"], chu_toa_user.sub,
    ))
    ch_id = create.json()["data"]["id"]
    huy = await client.post(f"{BASE}/{ch_id}/huy", json={"ly_do": "Test"})
    assert huy.status_code == 200
    return ch_id


@pytest.mark.asyncio
async def test_patch_cancelled_meeting_returns_409(
    client: AsyncClient, chu_toa_user, seed_test_users, db_session: AsyncSession,
):
    ch_id = await _create_and_cancel(client, chu_toa_user, seed_test_users, db_session)

    resp = await client.patch(f"{BASE}/{ch_id}", json={"dia_diem": "New place"})
    assert resp.status_code == 409
    assert resp.json()["detail"]["error"]["code"] == "MEETING_CANCELLED"


@pytest.mark.asyncio
async def test_huy_lai_lan_2_returns_409(
    client: AsyncClient, chu_toa_user, seed_test_users, db_session: AsyncSession,
):
    """Hủy lần 2 → 409 (require_can_edit_meeting block trước khi vào service)."""
    ch_id = await _create_and_cancel(client, chu_toa_user, seed_test_users, db_session)

    resp = await client.post(f"{BASE}/{ch_id}/huy", json={"ly_do": "Lần 2"})
    assert resp.status_code == 409
    assert resp.json()["detail"]["error"]["code"] == "MEETING_CANCELLED"


@pytest.mark.asyncio
async def test_upload_tai_lieu_cancelled_409(
    client: AsyncClient, chu_toa_user, seed_test_users, db_session: AsyncSession,
):
    ch_id = await _create_and_cancel(client, chu_toa_user, seed_test_users, db_session)

    files = {"file": ("after_cancel.pdf", io.BytesIO(b"%PDF-1"), "application/pdf")}
    resp = await client.post(
        "/api/v1/hop-khong-giay/tai-lieu/upload",
        data={"cuoc_hop_id": ch_id},
        files=files,
    )
    assert resp.status_code == 409
    assert resp.json()["detail"]["error"]["code"] == "MEETING_CANCELLED"


@pytest.mark.asyncio
async def test_bam_tay_cancelled_409(
    client: AsyncClient, chu_toa_user, seed_test_users, db_session: AsyncSession,
):
    ch_id = await _create_and_cancel(client, chu_toa_user, seed_test_users, db_session)

    resp = await client.post("/api/v1/hop-khong-giay/diem-danh/bam-tay", json={
        "cuoc_hop_id": ch_id,
        "diem_danh": [{
            "cong_chuc_id": "aaaaaaaa-0002-0000-0000-000000000002",
            "trang_thai": "CO_MAT",
        }],
    })
    assert resp.status_code == 409
    assert resp.json()["detail"]["error"]["code"] == "MEETING_CANCELLED"


@pytest.mark.asyncio
async def test_tao_ket_luan_cancelled_409(
    client: AsyncClient, chu_toa_user, seed_test_users, db_session: AsyncSession,
):
    ch_id = await _create_and_cancel(client, chu_toa_user, seed_test_users, db_session)

    resp = await client.post(f"{BASE}/{ch_id}/ket-luan", json={
        "noi_dung": "Sau khi hủy",
        "nguoi_phu_trach_id": chu_toa_user.sub,
    })
    assert resp.status_code == 409
    assert resp.json()["detail"]["error"]["code"] == "MEETING_CANCELLED"
