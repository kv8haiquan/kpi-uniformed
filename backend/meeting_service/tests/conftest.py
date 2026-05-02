"""
meeting_service/tests/conftest.py
==================================
Test methodology bắt buộc theo §5 G2 prompt — DB là production đào tạo.

Guards:
1. production_test_guard: phải có ALLOW_PROD_TEST=true mới chạy
2. seed_test_users (session-scope): tạo 4 TEST-G3-* CBCC dedicated
3. db_session (function-scope): tx-rollback per test
4. cleanup_test_users (session-scope, autouse): teardown an toàn
"""

import os
import shutil
import sys
import tempfile
import uuid
from datetime import datetime, timedelta, timezone
from typing import AsyncGenerator

# pytest đặt CWD ở root nên cần insert backend/ vào sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text as sa_text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

# G4-fix-8 (02/05/2026): sandbox upload_dir vào tmpdir TRƯỚC khi import service.
# Trước đây cleanup fixture rmtree("uploads/meeting") đã xóa nhầm file production
# của user. Sandbox tmpdir đảm bảo tests không bao giờ chạm vào production data.
_TEST_UPLOAD_DIR = tempfile.mkdtemp(prefix="hkg_test_uploads_")
os.environ["HKG_UPLOAD_DIR"] = _TEST_UPLOAD_DIR

# Disable APScheduler trong test (background coroutine không cần thiết)
os.environ.setdefault("HKG_DISABLE_SCHEDULER", "true")

# Phase 4.1: disable rate limit trong test (tránh 429 false positive khi
# nhiều test gọi upload trong cùng IP).
os.environ.setdefault("HKG_DISABLE_RATE_LIMIT", "true")

from meeting_service.main import app


@pytest.fixture(scope="session", autouse=True)
def _cleanup_test_upload_dir():
    """Xóa toàn bộ tmpdir test khi pytest session kết thúc."""
    yield
    shutil.rmtree(_TEST_UPLOAD_DIR, ignore_errors=True)
from meeting_service.config import settings
from meeting_service.dependencies import get_db, get_current_user
from shared.auth import TokenPayload


# ════════════════════════════════════════════════════════════════════
# 1. PRODUCTION GUARD — refuse to run without explicit opt-in
# ════════════════════════════════════════════════════════════════════
@pytest.fixture(scope="session", autouse=True)
def production_test_guard():
    if os.getenv("ALLOW_PROD_TEST") != "true":
        pytest.exit(
            "Refuse to run on prod-like DB without ALLOW_PROD_TEST=true. "
            "Run: ALLOW_PROD_TEST=true pytest meeting_service/tests/",
            1,
        )


# ════════════════════════════════════════════════════════════════════
# 2. ENGINE / SEED DATA
# ════════════════════════════════════════════════════════════════════

# UUID hardcoded cho 4 test users — chỉ dùng để identify trong test scope
TEST_USERS = {
    "TEST-G3-001": uuid.UUID("aaaaaaaa-0001-0000-0000-000000000001"),
    "TEST-G3-002": uuid.UUID("aaaaaaaa-0002-0000-0000-000000000002"),
    "TEST-G3-003": uuid.UUID("aaaaaaaa-0003-0000-0000-000000000003"),
    "TEST-G3-004": uuid.UUID("aaaaaaaa-0004-0000-0000-000000000004"),
}


# Engine + seed function-scoped vì pytest-asyncio default loop scope=function.
# Async connections bị bind vào loop, không thể share giữa các test.
@pytest_asyncio.fixture
async def engine():
    eng = create_async_engine(settings.database_url, echo=False)
    yield eng
    await eng.dispose()


@pytest_asyncio.fixture
async def seed_test_users(engine):
    """Seed 4 TEST-G3-* CBCC vào public.cong_chuc + 1 don_vi test."""
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # Lấy 1 vai_tro_id và 1 don_vi_id thật để FK hợp lệ
    async with factory() as s:
        # DB dùng tên ngắn 'CC' thay vì 'CONG_CHUC'
        vai_tro_row = await s.execute(sa_text(
            "SELECT id FROM public.vai_tro WHERE ma_vai_tro = 'CC' LIMIT 1"
        ))
        vai_tro_id = vai_tro_row.scalar_one()

        # 2 don_vi cho test phân quyền cross-unit
        dv_rows = await s.execute(sa_text(
            "SELECT id FROM public.don_vi ORDER BY ma_don_vi LIMIT 2"
        ))
        dv_ids = [row[0] for row in dv_rows.fetchall()]
        assert len(dv_ids) >= 2, "Cần ít nhất 2 đơn vị thật để test cross-unit"
        don_vi_a, don_vi_b = dv_ids[0], dv_ids[1]

        # Seed 4 user. ON CONFLICT DO NOTHING để re-run an toàn.
        for ma_cc, uid in TEST_USERS.items():
            don_vi = don_vi_a if ma_cc in ("TEST-G3-001", "TEST-G3-002") else don_vi_b
            await s.execute(sa_text("""
                INSERT INTO public.cong_chuc
                    (id, ma_cc, ho_ten, vai_tro_id, don_vi_id,
                     password_hash, is_active, is_lanh_dao)
                VALUES (:id, :ma_cc, :ho_ten, :vai_tro_id, :don_vi_id,
                        'TEST_NOT_LOGIN', TRUE, FALSE)
                ON CONFLICT (id) DO NOTHING
            """), {
                "id": str(uid),
                "ma_cc": ma_cc,
                "ho_ten": f"Test User {ma_cc}",
                "vai_tro_id": str(vai_tro_id),
                "don_vi_id": str(don_vi),
            })
        await s.commit()

    yield {"don_vi_a": don_vi_a, "don_vi_b": don_vi_b}

    # Teardown — xóa tất cả TEST-G3-*
    async with factory() as s:
        await s.execute(sa_text("""
            DELETE FROM public.cong_chuc_platform_role
             WHERE cong_chuc_id IN (
                SELECT id FROM public.cong_chuc WHERE ma_cc LIKE 'TEST-G3-%'
             )
        """))
        await s.execute(sa_text(
            "DELETE FROM public.cong_chuc WHERE ma_cc LIKE 'TEST-G3-%'"
        ))
        await s.commit()


# ════════════════════════════════════════════════════════════════════
# 3. DB SESSION — tx rollback per test
# ════════════════════════════════════════════════════════════════════
@pytest_asyncio.fixture
async def db_session(engine, seed_test_users):
    """Session với rollback ở cuối test → DB không persist."""
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession):
    """ASGI httpx client. Override get_db để tránh commit."""
    async def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


# ════════════════════════════════════════════════════════════════════
# 4. USER FIXTURES — TEST-G3-* dedicated, KHÔNG pick user thật
# ════════════════════════════════════════════════════════════════════

def _make_user(
    ma_cc: str,
    don_vi_id,
    *,
    vai_tro: str = "CC",
    is_lanh_dao: bool = False,
    is_admin: bool = False,
    platform_roles: list[str] | None = None,
) -> TokenPayload:
    return TokenPayload(
        sub=str(TEST_USERS[ma_cc]),
        ma_cc=ma_cc,
        ho_ten=f"Test User {ma_cc}",
        vai_tro=vai_tro,
        don_vi_id=str(don_vi_id),
        is_lanh_dao=is_lanh_dao,
        is_admin=is_admin,
        platform_roles=platform_roles or [],
        exp=int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()),
        type="access",
    )


def _set_user(user: TokenPayload):
    async def _override():
        return user
    app.dependency_overrides[get_current_user] = _override


@pytest.fixture
def admin_user(seed_test_users):
    u = _make_user(
        "TEST-G3-001", seed_test_users["don_vi_a"],
        vai_tro="ADMIN", is_admin=True,
    )
    _set_user(u)
    yield u
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def chu_toa_user(seed_test_users):
    """TEST-G3-001 đóng vai chu_toa của cuộc họp Phòng A."""
    u = _make_user(
        "TEST-G3-001", seed_test_users["don_vi_a"],
        vai_tro="TDV", is_lanh_dao=True,
    )
    _set_user(u)
    yield u
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def thu_ky_phong_a(seed_test_users):
    """TEST-G3-002 là THU_KY_HOP của Phòng A."""
    dv_a = seed_test_users["don_vi_a"]
    u = _make_user(
        "TEST-G3-002", dv_a,
        platform_roles=["THU_KY_HOP"],
    )
    # Mock pham_vi cho THU_KY_HOP — gán role thật vào DB scope
    _set_user(u)
    yield u
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def thu_ky_phong_b(seed_test_users):
    """TEST-G3-003 là THU_KY_HOP của Phòng B (KHÁC phòng A)."""
    u = _make_user(
        "TEST-G3-003", seed_test_users["don_vi_b"],
        platform_roles=["THU_KY_HOP"],
    )
    _set_user(u)
    yield u
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def cbcc_user(seed_test_users):
    """TEST-G3-004 — CBCC thường, không platform role."""
    u = _make_user("TEST-G3-004", seed_test_users["don_vi_b"])
    _set_user(u)
    yield u
    app.dependency_overrides.pop(get_current_user, None)
