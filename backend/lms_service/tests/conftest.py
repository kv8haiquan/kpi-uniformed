"""
lms_service/tests/conftest.py
=============================
Test fixtures: DB session, HTTP client, mock users (5 vai tro).
"""

import sys
import os
import uuid
from datetime import datetime, timedelta
from typing import AsyncGenerator

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from lms_service.main import app
from lms_service.config import settings
from lms_service.dependencies import get_db, get_current_user
from shared.auth import TokenPayload


# =========================================================================
# PYTEST CONFIG
# =========================================================================
# Dung scope="function" cho loop, moi test co event loop rieng
pytest_plugins = []


# =========================================================================
# DATABASE
# =========================================================================
@pytest_asyncio.fixture
async def db_session():
    """Tao engine + session moi cho moi test, rollback sau khi xong."""
    engine = create_async_engine(settings.database_url, echo=False)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        yield session
        await session.rollback()
    await engine.dispose()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession):
    """HTTP client — override get_db de dung test session."""
    async def _override_get_db():
        # Khong commit/rollback — test session se rollback
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


# =========================================================================
# USER FIXTURES
# =========================================================================
# Real cong_chuc IDs tu database — can thiet vi FK constraint
_REAL_CC_IDS = [
    "00327c43-c9a3-44d7-8306-7084e75cb2b5",
    "01014af6-1505-495b-95ab-8c1503cfa061",
    "01abd5c1-5c34-475b-8ea8-803ad461f66d",
    "02a492ad-fb32-430d-8c4e-e9ded9b8d964",
    "02fed37c-1c82-4250-a6ea-7bf9db7b6955",
]


def _make_user(vai_tro: str, platform_roles: list[str], is_lanh_dao: bool = False, idx: int = 0) -> TokenPayload:
    return TokenPayload(
        sub=_REAL_CC_IDS[idx % len(_REAL_CC_IDS)],
        exp=int((datetime.utcnow() + timedelta(hours=8)).timestamp()),
        type="access",
        ma_cc=f"TEST-{vai_tro[:5]}",
        vai_tro=vai_tro,
        don_vi_id="a0000000-0000-0000-0000-000000000001",
        is_lanh_dao=is_lanh_dao,
        platform_roles=platform_roles,
    )


def _set_user(user: TokenPayload):
    async def _override():
        return user
    app.dependency_overrides[get_current_user] = _override


@pytest.fixture
def admin_user():
    user = _make_user("SUPER_ADMIN", ["QT_DAO_TAO"], idx=0)
    _set_user(user)
    yield user
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def qt_dao_tao_user():
    user = _make_user("CHUYEN_VIEN", ["QT_DAO_TAO"], idx=1)
    _set_user(user)
    yield user
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def giang_vien_user():
    user = _make_user("CHUYEN_VIEN", ["GIANG_VIEN"], idx=2)
    _set_user(user)
    yield user
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def lanh_dao_user():
    user = _make_user("TRUONG_PHONG", [], is_lanh_dao=True, idx=3)
    _set_user(user)
    yield user
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def cbcc_user():
    user = _make_user("CHUYEN_VIEN", [], idx=4)
    _set_user(user)
    yield user
    app.dependency_overrides.pop(get_current_user, None)


# =========================================================================
# DATA HELPERS
# =========================================================================
@pytest_asyncio.fixture
async def created_chuyen_de(client: AsyncClient, admin_user):
    resp = await client.post("/api/v1/lms/chuyen-de", json={
        "ma_chuyen_de": f"CD-{uuid.uuid4().hex[:6]}",
        "ten_chuyen_de": "Chuyên đề test",
        "mo_ta": "Mô tả test",
    })
    assert resp.status_code == 201
    return resp.json()["data"]


@pytest_asyncio.fixture
async def created_khoa_hoc(client: AsyncClient, admin_user):
    resp = await client.post("/api/v1/lms/khoa-hoc", json={
        "ma_khoa_hoc": f"KH-{uuid.uuid4().hex[:6]}",
        "ten_khoa_hoc": "Khóa học test",
        "mo_ta": "Mô tả test",
        "loai": "TU_HOC",
    })
    assert resp.status_code == 201
    return resp.json()["data"]


@pytest_asyncio.fixture
async def published_khoa_hoc(client: AsyncClient, admin_user):
    kh_resp = await client.post("/api/v1/lms/khoa-hoc", json={
        "ma_khoa_hoc": f"KH-PUB-{uuid.uuid4().hex[:6]}",
        "ten_khoa_hoc": "Khóa published test",
        "loai": "TU_HOC",
    })
    kh = kh_resp.json()["data"]
    kh_id = kh["id"]
    await client.post(f"/api/v1/lms/khoa-hoc/{kh_id}/bai-hoc", json={
        "tieu_de": "Bài test",
        "loai_noi_dung": "HTML",
    })
    await client.patch(f"/api/v1/lms/khoa-hoc/{kh_id}/trang-thai",
                       json={"trang_thai": "CHO_DUYET"})
    await client.patch(f"/api/v1/lms/khoa-hoc/{kh_id}/trang-thai",
                       json={"trang_thai": "DA_XUAT_BAN"})
    return kh
