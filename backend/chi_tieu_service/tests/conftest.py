"""
chi_tieu_service/tests/conftest.py
==================================
Fixtures cho INTEGRATION test.

⚠️ AN TOAN PRODUCTION: integration test CHI chay khi co bien moi truong
   CHI_TIEU_TEST_DATABASE_URL tro toi 1 DB TEST RIENG (da migrate schema
   chi_tieu + co vai public.cong_chuc/don_vi de thoa FK).
   KHONG co bien nay -> toan bo test integration bi SKIP.
   TUYET DOI khong tro vao localhost:5432 (= production).
"""

import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from chi_tieu_service.main import app
from chi_tieu_service.dependencies import get_db, get_current_user
from shared.auth import TokenPayload

TEST_DB_URL = os.getenv("CHI_TIEU_TEST_DATABASE_URL")

# Skip toan bo integration test neu khong co DB test rieng
requires_test_db = pytest.mark.skipif(
    not TEST_DB_URL,
    reason="Dat CHI_TIEU_TEST_DATABASE_URL (DB test rieng) de chay integration test. "
           "KHONG dung production (localhost:5432).",
)


@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine(TEST_DB_URL, echo=False)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        yield session
    await engine.dispose()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession):
    async def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


def _set_user(user: TokenPayload):
    async def _override():
        return user
    app.dependency_overrides[get_current_user] = _override


@pytest.fixture
def qt_user():
    """Quan tri chi tieu (full quyen danh muc/giao nam)."""
    user = TokenPayload(
        sub=os.getenv("CHI_TIEU_TEST_CC_ID", "00000000-0000-0000-0000-000000000000"),
        exp=int((datetime.utcnow() + timedelta(hours=8)).timestamp()),
        type="access", ma_cc="TEST-QTCT", vai_tro="SUPER_ADMIN", is_admin=True,
        platform_roles=["QT_CHI_TIEU"],
    )
    _set_user(user)
    yield user
    app.dependency_overrides.pop(get_current_user, None)
