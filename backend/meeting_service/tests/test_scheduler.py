"""
Test 4 scheduler jobs với freezegun mock thời gian.

Critical tests (theo yêu cầu user):
- nhac_hop_3_tang: 3 windows + idempotent (không duplicate)
- nhac_han_ket_luan: cron logic (han = today+3)
- mark_tre_han: UPDATE rows past han
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from uuid import UUID

import pytest
from freezegun import freeze_time
from httpx import AsyncClient
from sqlalchemy import text as sa_text
from sqlalchemy.ext.asyncio import AsyncSession

from meeting_service.services.scheduler_helpers import (
    mark_tre_han_logic,
    nhac_han_ket_luan_logic,
    nhac_hop_3_tang_logic,
    reset_cache,
)


BASE_CH = "/api/v1/hop-khong-giay/cuoc-hop"


def _meeting_payload(don_vi_id, chu_toa_id, ngay_hop, gio_bat_dau, thanh_phan):
    return {
        "tieu_de": "Test scheduler — họp mai",
        "khoi": "CHUYEN_MON",
        "hinh_thuc": "TRUC_TIEP",
        "ngay_hop": ngay_hop,
        "gio_bat_dau": gio_bat_dau,
        "don_vi_to_chuc_id": str(don_vi_id),
        "chu_toa_id": str(chu_toa_id),
        "thanh_phan": thanh_phan,
    }


# ════════════════════════════════════════════════════════════════════
# NHAC_HOP_3_TANG — yêu cầu critical từ user
# ════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_nhac_hop_3_tang_full_lifecycle(
    client: AsyncClient, chu_toa_user, seed_test_users, db_session: AsyncSession,
):
    """
    Test 4 transitions như user yêu cầu:
    - now = họp_time - 24h - 3p → trigger NHAC_HOP_24H 1 lần
    - now = họp_time - 24h - 1p → KHÔNG trigger lại
    - now = họp_time - 1h  - 3p → trigger NHAC_HOP_1H
    - now = họp_time - 30p - 3p → trigger NHAC_HOP_30P

    Verify common.thong_bao chỉ có 3 row, không duplicate.
    """
    reset_cache()

    # Tạo cuộc họp tương lai cố định: 2026-06-15 09:00 UTC
    hop_time = datetime(2026, 6, 15, 9, 0, tzinfo=timezone.utc)

    create = await client.post(BASE_CH + "/", json=_meeting_payload(
        seed_test_users["don_vi_a"], chu_toa_user.sub,
        ngay_hop="2026-06-15", gio_bat_dau="09:00",
        thanh_phan=[
            {"cong_chuc_id": "aaaaaaaa-0002-0000-0000-000000000002", "loai_tham_du": "BAT_BUOC"},
            {"cong_chuc_id": "aaaaaaaa-0003-0000-0000-000000000003", "loai_tham_du": "BAT_BUOC"},
        ],
    ))
    ch_id = create.json()["data"]["id"]

    # Set trang_thai = DA_THONG_BAO (scheduler chỉ trigger khi đã thông báo)
    await db_session.execute(sa_text(
        "UPDATE meeting.cuoc_hop SET trang_thai='DA_THONG_BAO' WHERE id=:id"
    ), {"id": ch_id})
    await db_session.flush()

    # ─── Window 24h ─── (now = hop_time - 24h - 3p = 24h-window OK)
    reset_cache()
    n1 = await nhac_hop_3_tang_logic(db_session, now=hop_time - timedelta(hours=24, minutes=3))
    assert n1 == 2, f"Mong 2 (=2 thành phần × 1 window 24h), got {n1}"

    # ─── 1 phút sau, vẫn trong window 24h → KHÔNG trigger lại (idempotent) ───
    reset_cache()
    n2 = await nhac_hop_3_tang_logic(db_session, now=hop_time - timedelta(hours=24, minutes=1))
    assert n2 == 0, f"Đã có row trong thong_bao → không gửi lại, got {n2}"

    # ─── Window 1h ───
    reset_cache()
    n3 = await nhac_hop_3_tang_logic(db_session, now=hop_time - timedelta(hours=1, minutes=3))
    assert n3 == 2

    # ─── Window 30p ───
    reset_cache()
    n4 = await nhac_hop_3_tang_logic(db_session, now=hop_time - timedelta(minutes=33))
    assert n4 == 2

    # Verify thong_bao có đúng 6 rows (3 windows × 2 thành phần), không duplicate
    res = await db_session.execute(sa_text("""
        SELECT doi_tuong_type, COUNT(*) AS n
          FROM common.thong_bao
         WHERE loai='MEETING'
           AND doi_tuong_id=:ch_id
           AND doi_tuong_type IN ('NHAC_HOP_24H','NHAC_HOP_1H','NHAC_HOP_30P')
         GROUP BY doi_tuong_type
         ORDER BY doi_tuong_type
    """), {"ch_id": ch_id})
    rows = {r[0]: r[1] for r in res.fetchall()}
    assert rows == {"NHAC_HOP_1H": 2, "NHAC_HOP_24H": 2, "NHAC_HOP_30P": 2}


@pytest.mark.asyncio
async def test_nhac_hop_skip_outside_window(
    client: AsyncClient, chu_toa_user, seed_test_users, db_session: AsyncSession,
):
    """now ngoài window (vd 12h trước họp) → KHÔNG gửi gì."""
    reset_cache()

    create = await client.post(BASE_CH + "/", json=_meeting_payload(
        seed_test_users["don_vi_a"], chu_toa_user.sub,
        ngay_hop="2026-06-15", gio_bat_dau="09:00",
        thanh_phan=[
            {"cong_chuc_id": "aaaaaaaa-0002-0000-0000-000000000002", "loai_tham_du": "BAT_BUOC"},
        ],
    ))
    ch_id = create.json()["data"]["id"]
    await db_session.execute(sa_text(
        "UPDATE meeting.cuoc_hop SET trang_thai='DA_THONG_BAO' WHERE id=:id"
    ), {"id": ch_id})
    await db_session.flush()

    hop_time = datetime(2026, 6, 15, 9, 0, tzinfo=timezone.utc)
    # 12h trước → không trong bất kỳ window nào
    n = await nhac_hop_3_tang_logic(db_session, now=hop_time - timedelta(hours=12))
    assert n == 0


# ════════════════════════════════════════════════════════════════════
# NHẮC HẠN KẾT LUẬN
# ════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_nhac_han_ket_luan_3_days(
    client: AsyncClient, chu_toa_user, seed_test_users, db_session: AsyncSession,
):
    """Tạo ket_luan han = today+3 → job phải gửi 1 notif."""
    create = await client.post(BASE_CH + "/", json={
        "tieu_de": "Test", "khoi": "CHUYEN_MON", "hinh_thuc": "TRUC_TIEP",
        "ngay_hop": "2026-06-01", "gio_bat_dau": "08:00",
        "don_vi_to_chuc_id": str(seed_test_users["don_vi_a"]),
        "chu_toa_id": chu_toa_user.sub,
        "thanh_phan": [],
    })
    ch_id = create.json()["data"]["id"]

    today = date.today()
    target = today + timedelta(days=3)

    kl_resp = await client.post(f"{BASE_CH}/{ch_id}/ket-luan", json={
        "noi_dung": "Báo cáo X", "nguoi_phu_trach_id": chu_toa_user.sub,
        "han_hoan_thanh": target.isoformat(),
    })
    kl_id = kl_resp.json()["data"]["id"]

    # Run job
    n = await nhac_han_ket_luan_logic(db_session)
    assert n >= 1

    # Verify thong_bao
    res = await db_session.execute(sa_text("""
        SELECT COUNT(*) FROM common.thong_bao
         WHERE loai='MEETING' AND doi_tuong_type='NHAC_HAN_3_NGAY'
           AND doi_tuong_id=:kl_id
    """), {"kl_id": kl_id})
    assert res.scalar() == 1

    # Re-run → idempotent
    n2 = await nhac_han_ket_luan_logic(db_session)
    res2 = await db_session.execute(sa_text("""
        SELECT COUNT(*) FROM common.thong_bao
         WHERE doi_tuong_id=:kl_id AND doi_tuong_type='NHAC_HAN_3_NGAY'
    """), {"kl_id": kl_id})
    assert res2.scalar() == 1, "Không duplicate khi run lại"


# ════════════════════════════════════════════════════════════════════
# MARK TRỄ HẠN
# ════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_mark_tre_han_yesterday(
    client: AsyncClient, chu_toa_user, seed_test_users, db_session: AsyncSession,
):
    """Ket_luan han < today, chưa hoàn thành → trang_thai TRE_HAN."""
    create = await client.post(BASE_CH + "/", json={
        "tieu_de": "Test", "khoi": "CHUYEN_MON", "hinh_thuc": "TRUC_TIEP",
        "ngay_hop": "2026-04-01", "gio_bat_dau": "08:00",
        "don_vi_to_chuc_id": str(seed_test_users["don_vi_a"]),
        "chu_toa_id": chu_toa_user.sub,
        "thanh_phan": [],
    })
    ch_id = create.json()["data"]["id"]

    yesterday = date.today() - timedelta(days=1)
    kl_resp = await client.post(f"{BASE_CH}/{ch_id}/ket-luan", json={
        "noi_dung": "Quá hạn", "nguoi_phu_trach_id": chu_toa_user.sub,
        "han_hoan_thanh": yesterday.isoformat(),
    })
    kl_id = kl_resp.json()["data"]["id"]

    # Run job
    affected = await mark_tre_han_logic(db_session)
    assert affected >= 1

    # Verify
    res = await db_session.execute(sa_text(
        "SELECT trang_thai FROM meeting.ket_luan WHERE id=:id"
    ), {"id": kl_id})
    assert res.scalar() == "TRE_HAN"


@pytest.mark.asyncio
async def test_mark_tre_han_does_not_touch_completed(
    client: AsyncClient, chu_toa_user, seed_test_users, db_session: AsyncSession,
):
    """Ket_luan đã HOAN_THANH dù quá hạn → KHÔNG đổi."""
    create = await client.post(BASE_CH + "/", json={
        "tieu_de": "T", "khoi": "CHUYEN_MON", "hinh_thuc": "TRUC_TIEP",
        "ngay_hop": "2026-04-01", "gio_bat_dau": "08:00",
        "don_vi_to_chuc_id": str(seed_test_users["don_vi_a"]),
        "chu_toa_id": chu_toa_user.sub,
        "thanh_phan": [],
    })
    ch_id = create.json()["data"]["id"]

    yesterday = date.today() - timedelta(days=1)
    kl_resp = await client.post(f"{BASE_CH}/{ch_id}/ket-luan", json={
        "noi_dung": "Done", "nguoi_phu_trach_id": chu_toa_user.sub,
        "han_hoan_thanh": yesterday.isoformat(),
    })
    kl_id = kl_resp.json()["data"]["id"]

    # Force HOAN_THANH
    await db_session.execute(sa_text(
        "UPDATE meeting.ket_luan SET trang_thai='HOAN_THANH', tien_do_phan_tram=100 WHERE id=:id"
    ), {"id": kl_id})
    await db_session.flush()

    affected = await mark_tre_han_logic(db_session)
    res = await db_session.execute(sa_text(
        "SELECT trang_thai FROM meeting.ket_luan WHERE id=:id"
    ), {"id": kl_id})
    assert res.scalar() == "HOAN_THANH"  # Không bị đổi
