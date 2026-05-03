"""
Test endpoint /cong-chuc/search.

G4-fix-2 (4 tests):
1. Happy path: SUPER_ADMIN search "Test" → list match
2. CBCC thường — search OK (G4-fix-7 mở quyền cho mọi user authenticated)
3. Permission granted: THU_KY_HOP → search OK
4. SQL injection safe

G4-fix-3 (3 tests):
5. List by don_vi_id only (không q) → trả CBCC trong đơn vị
6. Combine q + don_vi_id → AND filter
7. Neither q nor don_vi_id → 400 MISSING_FILTER
"""

from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy import text as sa_text
from sqlalchemy.ext.asyncio import AsyncSession

from shared.auth import TokenPayload


URL = "/api/v1/hop-khong-giay/cong-chuc/search"


def _make_token(
    sub: str,
    *,
    vai_tro: str = "CC",
    is_admin: bool = False,
    is_lanh_dao: bool = False,
    platform_roles: list[str] | None = None,
) -> TokenPayload:
    return TokenPayload(
        sub=sub,
        ma_cc="TEST-G3-001",
        ho_ten="Test",
        vai_tro=vai_tro,
        don_vi_id="aaaaaaaa-0000-0000-0000-000000000000",
        is_admin=is_admin,
        is_lanh_dao=is_lanh_dao,
        platform_roles=platform_roles or [],
        exp=int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()),
        type="access",
    )


def _override_user(user: TokenPayload):
    from meeting_service.dependencies import get_current_user
    from meeting_service.main import app
    async def _o():
        return user
    app.dependency_overrides[get_current_user] = _o


@pytest.mark.asyncio
async def test_happy_super_admin_search(client: AsyncClient, seed_test_users):
    """SUPER_ADMIN search 'Test' → trả về TEST-G3-* CBCC đã seed."""
    _override_user(_make_token("aaaaaaaa-0001-0000-0000-000000000001",
                                vai_tro="ADMIN", is_admin=True))
    resp = await client.get(URL, params={"q": "Test"})
    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]
    assert isinstance(data, list)
    # Phải có ít nhất 1 TEST-G3-* user (đã seed ở conftest)
    test_users = [u for u in data if u["ma_cc"].startswith("TEST-G3-")]
    assert len(test_users) >= 1
    # Verify shape
    item = test_users[0]
    for field in ("id", "ho_ten", "ma_cc", "ten_don_vi"):
        assert field in item


@pytest.mark.asyncio
async def test_cbcc_thuong_search_ok(client: AsyncClient, seed_test_users):
    """G4-fix-7: CBCC thuần CC, không lãnh đạo → vẫn được search.

    Lý do mở quyền: cho công chức tự tạo cuộc họp + chọn thành phần.
    Trước đây chặn 403, nay cho phép mọi user đã đăng nhập.
    """
    _override_user(_make_token(
        "aaaaaaaa-0004-0000-0000-000000000004",
        vai_tro="CC",
        is_admin=False,
        is_lanh_dao=False,
        platform_roles=[],
    ))
    resp = await client.get(URL, params={"q": "Test"})
    assert resp.status_code == 200, resp.text
    assert isinstance(resp.json()["data"], list)


@pytest.mark.asyncio
async def test_perm_granted_thu_ky_hop(client: AsyncClient, seed_test_users):
    """TEST-G3-* user vai_tro=CC + platform_role=THU_KY_HOP → search OK."""
    _override_user(_make_token(
        "aaaaaaaa-0002-0000-0000-000000000002",
        vai_tro="CC",
        is_admin=False,
        is_lanh_dao=False,
        platform_roles=["THU_KY_HOP"],
    ))
    resp = await client.get(URL, params={"q": "TEST"})
    assert resp.status_code == 200, resp.text
    assert isinstance(resp.json()["data"], list)


@pytest.mark.asyncio
async def test_sql_injection_safe(
    client: AsyncClient, seed_test_users, db_session: AsyncSession,
):
    """q chứa SQL injection payload → không crash, không thực thi DROP."""
    _override_user(_make_token("aaaaaaaa-0001-0000-0000-000000000001",
                                vai_tro="ADMIN", is_admin=True))

    payload = "'; DROP TABLE meeting.cuoc_hop; --"
    resp = await client.get(URL, params={"q": payload})
    assert resp.status_code == 200, resp.text
    # Trả về list rỗng (không CBCC nào khớp pattern này)
    assert resp.json()["data"] == []

    # Verify bảng meeting.cuoc_hop vẫn tồn tại
    res = await db_session.execute(sa_text(
        "SELECT to_regclass('meeting.cuoc_hop')"
    ))
    table_oid = res.scalar()
    assert table_oid is not None, "Bảng meeting.cuoc_hop bị drop — SQL injection thành công!"


# ════════════════════════════════════════════════════════════════════
# G4-fix-3 — Filter theo don_vi_id
# ════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_list_by_don_vi_only_no_query(client, seed_test_users):
    """Truyền chỉ don_vi_id (không q) → list CBCC trong đơn vị đó."""
    _override_user(_make_token("aaaaaaaa-0001-0000-0000-000000000001",
                                vai_tro="ADMIN", is_admin=True))

    don_vi_a = seed_test_users["don_vi_a"]
    resp = await client.get(URL, params={"don_vi_id": str(don_vi_a), "limit": 100})
    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]
    assert isinstance(data, list)
    # TEST-G3-001 và TEST-G3-002 thuộc don_vi_a (xem conftest)
    test_ids_in_a = [u["ma_cc"] for u in data
                      if u["ma_cc"] in ("TEST-G3-001", "TEST-G3-002")]
    assert "TEST-G3-001" in test_ids_in_a
    assert "TEST-G3-002" in test_ids_in_a
    # TEST-G3-003 / TEST-G3-004 thuộc don_vi_b → không xuất hiện
    test_ids_in_b = [u["ma_cc"] for u in data
                      if u["ma_cc"] in ("TEST-G3-003", "TEST-G3-004")]
    assert test_ids_in_b == []


@pytest.mark.asyncio
async def test_combine_q_and_don_vi_id(client, seed_test_users):
    """q + don_vi_id → AND filter."""
    _override_user(_make_token("aaaaaaaa-0001-0000-0000-000000000001",
                                vai_tro="ADMIN", is_admin=True))

    don_vi_a = seed_test_users["don_vi_a"]
    # q="TEST-G3-002" + don_vi_a → match đúng 1 user
    resp = await client.get(URL, params={
        "q": "TEST-G3-002",
        "don_vi_id": str(don_vi_a),
    })
    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]
    assert len(data) == 1
    assert data[0]["ma_cc"] == "TEST-G3-002"

    # q="TEST-G3-003" (don_vi_b) + don_vi_a → 0 match (không cùng đơn vị)
    resp2 = await client.get(URL, params={
        "q": "TEST-G3-003",
        "don_vi_id": str(don_vi_a),
    })
    assert resp2.status_code == 200
    assert resp2.json()["data"] == []


@pytest.mark.asyncio
async def test_missing_filter_400(client, seed_test_users):
    """Không truyền q, không truyền don_vi_id → 400 MISSING_FILTER."""
    _override_user(_make_token("aaaaaaaa-0001-0000-0000-000000000001",
                                vai_tro="ADMIN", is_admin=True))

    resp = await client.get(URL)
    assert resp.status_code == 400
    assert resp.json()["detail"]["error"]["code"] == "MISSING_FILTER"
