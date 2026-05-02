"""Test SQLAlchemy model TrangThaiTrinhChieu (Phase 4.1 DB_P2).

Threat model:
- Model phải reflect exact schema DB (defaults, CHECK constraints, FK).
- KHÔNG có cột is_deleted — verify bằng UPSERT pattern + UNIQUE.
- CASCADE từ cuoc_hop verify để tránh orphan state row.

Methodology: dùng db_session fixture (tx-rollback), savepoint cho các test
constraint violation để session vẫn usable cho các SELECT verify.
"""

from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from sqlalchemy import select, text as sa_text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from meeting_service.models import CuocHop, TrangThaiTrinhChieu


async def _seed_cuoc_hop(db_session: AsyncSession, seed_test_users) -> UUID:
    """Tạo 1 cuoc_hop test (chưa commit) và return id để test bám vào."""
    chu_toa_id = UUID("aaaaaaaa-0001-0000-0000-000000000001")  # TEST-G3-001
    don_vi_id = seed_test_users["don_vi_a"]
    ch = CuocHop(
        tieu_de="Test TTC model",
        ngay_hop=date(2026, 5, 15),
        gio_bat_dau=time(8, 30),
        gio_ket_thuc=time(10, 0),
        don_vi_to_chuc_id=don_vi_id,
        chu_toa_id=chu_toa_id,
        created_by=chu_toa_id,
    )
    db_session.add(ch)
    await db_session.flush()
    return ch.id


@pytest.mark.asyncio
async def test_create_with_default_values(db_session: AsyncSession, seed_test_users):
    """1/8: defaults đúng (page=1, zoom=1.0, is_active=False, cap_nhat_luc=NOW)."""
    cuoc_hop_id = await _seed_cuoc_hop(db_session, seed_test_users)

    ttc = TrangThaiTrinhChieu(cuoc_hop_id=cuoc_hop_id)
    db_session.add(ttc)
    await db_session.flush()
    await db_session.refresh(ttc)

    assert ttc.id is not None
    assert ttc.trang_hien_tai == 1
    assert ttc.zoom_level == Decimal("1.00")
    assert ttc.is_active is False
    assert ttc.tai_lieu_hien_tai_id is None
    assert ttc.bat_dau_luc is None
    assert ttc.ket_thuc_luc is None
    assert ttc.cap_nhat_luc is not None


@pytest.mark.asyncio
async def test_unique_cuoc_hop_constraint(db_session: AsyncSession, seed_test_users):
    """2/8: tạo 2 row cùng cuoc_hop_id → IntegrityError."""
    cuoc_hop_id = await _seed_cuoc_hop(db_session, seed_test_users)

    db_session.add(TrangThaiTrinhChieu(cuoc_hop_id=cuoc_hop_id))
    await db_session.flush()

    with pytest.raises(IntegrityError):
        async with db_session.begin_nested():
            db_session.add(TrangThaiTrinhChieu(cuoc_hop_id=cuoc_hop_id))
            await db_session.flush()


@pytest.mark.asyncio
async def test_upsert_via_on_conflict(db_session: AsyncSession, seed_test_users):
    """3/8: UPSERT bằng INSERT ... ON CONFLICT (cuoc_hop_id) DO UPDATE — không tạo row mới."""
    cuoc_hop_id = await _seed_cuoc_hop(db_session, seed_test_users)

    upsert_sql = sa_text("""
        INSERT INTO meeting.trang_thai_trinh_chieu (cuoc_hop_id, trang_hien_tai)
        VALUES (:ch, :page)
        ON CONFLICT (cuoc_hop_id) DO UPDATE
            SET trang_hien_tai = EXCLUDED.trang_hien_tai,
                cap_nhat_luc = NOW()
        RETURNING id, trang_hien_tai
    """)

    r1 = await db_session.execute(upsert_sql, {"ch": str(cuoc_hop_id), "page": 1})
    row1 = r1.one()

    r2 = await db_session.execute(upsert_sql, {"ch": str(cuoc_hop_id), "page": 7})
    row2 = r2.one()

    assert row1.id == row2.id, "UPSERT phải UPDATE row cũ, không tạo row mới"
    assert row2.trang_hien_tai == 7

    count = await db_session.execute(sa_text(
        "SELECT COUNT(*) FROM meeting.trang_thai_trinh_chieu WHERE cuoc_hop_id = :ch"
    ), {"ch": str(cuoc_hop_id)})
    assert count.scalar_one() == 1


@pytest.mark.asyncio
async def test_check_active_has_doc(db_session: AsyncSession, seed_test_users):
    """4/8: is_active=TRUE + tai_lieu_hien_tai_id=NULL → CheckViolation."""
    cuoc_hop_id = await _seed_cuoc_hop(db_session, seed_test_users)

    with pytest.raises(IntegrityError) as exc_info:
        async with db_session.begin_nested():
            db_session.add(TrangThaiTrinhChieu(
                cuoc_hop_id=cuoc_hop_id,
                is_active=True,
                tai_lieu_hien_tai_id=None,
            ))
            await db_session.flush()
    assert "chk_ttc_active_has_doc" in str(exc_info.value)


@pytest.mark.asyncio
async def test_check_zoom_range(db_session: AsyncSession, seed_test_users):
    """5/8: zoom ngoài [0.5, 4.0] → CheckViolation."""
    cuoc_hop_id = await _seed_cuoc_hop(db_session, seed_test_users)

    # zoom = 5.0 (vượt max)
    with pytest.raises(IntegrityError) as exc_info:
        async with db_session.begin_nested():
            db_session.add(TrangThaiTrinhChieu(
                cuoc_hop_id=cuoc_hop_id,
                zoom_level=Decimal("5.00"),
            ))
            await db_session.flush()
    assert "chk_ttc_zoom_range" in str(exc_info.value)


@pytest.mark.asyncio
async def test_check_page_positive(db_session: AsyncSession, seed_test_users):
    """6/8: trang_hien_tai <= 0 → CheckViolation."""
    cuoc_hop_id = await _seed_cuoc_hop(db_session, seed_test_users)

    with pytest.raises(IntegrityError) as exc_info:
        async with db_session.begin_nested():
            db_session.add(TrangThaiTrinhChieu(
                cuoc_hop_id=cuoc_hop_id,
                trang_hien_tai=0,
            ))
            await db_session.flush()
    assert "chk_ttc_trang_positive" in str(exc_info.value)


@pytest.mark.asyncio
async def test_check_thoi_gian_hop_le(db_session: AsyncSession, seed_test_users):
    """7/8: bat_dau_luc > ket_thuc_luc → CheckViolation."""
    cuoc_hop_id = await _seed_cuoc_hop(db_session, seed_test_users)

    now = datetime.now(timezone.utc)
    with pytest.raises(IntegrityError) as exc_info:
        async with db_session.begin_nested():
            db_session.add(TrangThaiTrinhChieu(
                cuoc_hop_id=cuoc_hop_id,
                bat_dau_luc=now,
                ket_thuc_luc=now - timedelta(hours=1),  # ngược logic
            ))
            await db_session.flush()
    assert "chk_ttc_thoi_gian_hop_le" in str(exc_info.value)


@pytest.mark.asyncio
async def test_cascade_delete_cuoc_hop(db_session: AsyncSession, seed_test_users):
    """8/8: xóa cuoc_hop → trang_thai_trinh_chieu cũng bị xóa (ON DELETE CASCADE)."""
    cuoc_hop_id = await _seed_cuoc_hop(db_session, seed_test_users)

    db_session.add(TrangThaiTrinhChieu(cuoc_hop_id=cuoc_hop_id))
    await db_session.flush()

    # Verify row tồn tại
    count_before = await db_session.execute(sa_text(
        "SELECT COUNT(*) FROM meeting.trang_thai_trinh_chieu WHERE cuoc_hop_id = :ch"
    ), {"ch": str(cuoc_hop_id)})
    assert count_before.scalar_one() == 1

    # Hard-delete cuoc_hop bằng SQL (bypass soft-delete) để trigger CASCADE
    await db_session.execute(sa_text(
        "DELETE FROM meeting.cuoc_hop WHERE id = :id"
    ), {"id": str(cuoc_hop_id)})
    await db_session.flush()

    count_after = await db_session.execute(sa_text(
        "SELECT COUNT(*) FROM meeting.trang_thai_trinh_chieu WHERE cuoc_hop_id = :ch"
    ), {"ch": str(cuoc_hop_id)})
    assert count_after.scalar_one() == 0
