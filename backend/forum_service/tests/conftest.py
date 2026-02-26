"""
forum_service/tests/conftest.py
================================
Test fixtures cho module Dien dan.

Pattern (copy tu legal_service):
  - db_session: real DB session voi savepoint rollback
  - client: AsyncClient voi override get_db
  - 5 user fixtures: cbcc, chuyen_gia, dieu_phoi, lanh_dao, admin
  - Data fixtures: direct DB insert (khong qua API)
"""

import os
import sys
import uuid
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from forum_service.config import settings
from forum_service.dependencies import get_current_user, get_db
from forum_service.main import app
from shared.auth import TokenPayload


# =========================================================================
# REAL CONG_CHUC IDs tu production DB — can cho FK constraint tac_gia_id
# =========================================================================
_REAL_CC_IDS = [
    "00327c43-c9a3-44d7-8306-7084e75cb2b5",  # idx=0 -> cbcc_user
    "01014af6-1505-495b-95ab-8c1503cfa061",  # idx=1 -> chuyen_gia_user
    "01abd5c1-5c34-475b-8ea8-803ad461f66d",  # idx=2 -> dieu_phoi_user
    "02a492ad-fb32-430d-8c4e-e9ded9b8d964",  # idx=3 -> lanh_dao_user
    "02fed37c-1c82-4250-a6ea-7bf9db7b6955",  # idx=4 -> admin_user
    "03aeff5a-09b8-46ea-b88d-51323dd32c0e",  # idx=5 -> user_khac (for vote tests)
]

_DON_VI_ID = "a0000000-0000-0000-0000-000000000001"

API = "/api/forum/v1"


def _now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


# =========================================================================
# DATABASE FIXTURES
# =========================================================================


@pytest_asyncio.fixture
async def db_session():
    """Tao DB session voi savepoint isolation.

    session.commit() trong API handler chi commit den SAVEPOINT.
    conn.rollback() cuoi test xoa sach thay doi.
    """
    engine = create_async_engine(settings.database_url, echo=False)
    async with engine.connect() as conn:
        await conn.begin()
        factory = async_sessionmaker(
            bind=conn,
            class_=AsyncSession,
            expire_on_commit=False,
            join_transaction_mode="create_savepoint",
        )
        async with factory() as session:
            yield session
        await conn.rollback()
    await engine.dispose()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession):
    """HTTP client voi override get_db -> test session."""

    async def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


# =========================================================================
# USER HELPERS
# =========================================================================


def _make_user(
    vai_tro: str,
    platform_roles: list,
    is_lanh_dao: bool = False,
    is_admin: bool = False,
    idx: int = 0,
    don_vi_id: str = _DON_VI_ID,
) -> TokenPayload:
    """Tao TokenPayload mock cho test."""
    return TokenPayload(
        sub=_REAL_CC_IDS[idx % len(_REAL_CC_IDS)],
        exp=int((datetime.now(timezone.utc) + timedelta(hours=8)).timestamp()),
        type="access",
        ma_cc=f"TEST-{idx:02d}",
        vai_tro=vai_tro,
        don_vi_id=don_vi_id,
        is_lanh_dao=is_lanh_dao,
        is_admin=is_admin,
        platform_roles=platform_roles,
    )


def _set_user(user: TokenPayload):
    """Override get_current_user dependency voi user mock."""

    async def _override():
        return user

    app.dependency_overrides[get_current_user] = _override


# =========================================================================
# USER FIXTURES (5 vai tro)
# =========================================================================


@pytest.fixture
def cbcc_user():
    """CBCC thuong — tao/xem chu de, tra loi, vote."""
    user = _make_user("CC", [], idx=0)
    _set_user(user)
    yield user
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def chuyen_gia_user():
    """Chuyen gia — chon dap an chuan, dang bai chuyen muc chi_doc."""
    user = _make_user("CC", ["CHUYEN_GIA"], idx=1)
    _set_user(user)
    yield user
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def dieu_phoi_user():
    """Dieu phoi forum — ghim/khoa/duyet/an, quan ly chuyen muc."""
    user = _make_user("CC", ["DIEU_PHOI_FORUM"], idx=2)
    _set_user(user)
    yield user
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def lanh_dao_user():
    """Lanh dao don vi — xem bao cao don vi."""
    user = _make_user("TDV", [], is_lanh_dao=True, idx=3, don_vi_id=_DON_VI_ID)
    _set_user(user)
    yield user
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def admin_user():
    """SUPER_ADMIN — bypass tat ca quyen."""
    user = _make_user("SUPER_ADMIN", [], is_admin=True, idx=4)
    _set_user(user)
    yield user
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def user_khac():
    """User khac — dung cho test vote (khong phai tac gia)."""
    user = _make_user("CC", [], idx=5)
    _set_user(user)
    yield user
    app.dependency_overrides.pop(get_current_user, None)


# =========================================================================
# DATA FIXTURES — Direct DB insert
# =========================================================================


@pytest_asyncio.fixture
async def sample_chuyen_muc(db_session: AsyncSession):
    """Chuyen muc binh thuong (chi_doc=False, yeu_cau_duyet=False)."""
    from forum_service.models.chuyen_muc import ChuyenMuc

    cm = ChuyenMuc(
        ten_chuyen_muc=f"Chuyen muc test {uuid.uuid4().hex[:6]}",
        mo_ta="Mo ta chuyen muc test",
        thu_tu=1,
        chi_doc=False,
        yeu_cau_duyet=False,
        is_active=True,
        created_at=_now(),
    )
    db_session.add(cm)
    await db_session.flush()
    await db_session.refresh(cm)
    return {
        "id": str(cm.id),
        "ten_chuyen_muc": cm.ten_chuyen_muc,
    }


@pytest_asyncio.fixture
async def chi_doc_chuyen_muc(db_session: AsyncSession):
    """Chuyen muc chi doc — chi CHUYEN_GIA/DIEU_PHOI duoc dang bai."""
    from forum_service.models.chuyen_muc import ChuyenMuc

    cm = ChuyenMuc(
        ten_chuyen_muc=f"CM chi doc {uuid.uuid4().hex[:6]}",
        mo_ta="Chuyen muc chi doc test",
        thu_tu=2,
        chi_doc=True,
        yeu_cau_duyet=False,
        is_active=True,
        created_at=_now(),
    )
    db_session.add(cm)
    await db_session.flush()
    await db_session.refresh(cm)
    return {"id": str(cm.id), "ten_chuyen_muc": cm.ten_chuyen_muc}


@pytest_asyncio.fixture
async def yeu_cau_duyet_chuyen_muc(db_session: AsyncSession):
    """Chuyen muc yeu cau duyet — bai moi se o trang thai CHO_DUYET."""
    from forum_service.models.chuyen_muc import ChuyenMuc

    cm = ChuyenMuc(
        ten_chuyen_muc=f"CM yeu cau duyet {uuid.uuid4().hex[:6]}",
        mo_ta="Chuyen muc can duyet test",
        thu_tu=3,
        chi_doc=False,
        yeu_cau_duyet=True,
        is_active=True,
        created_at=_now(),
    )
    db_session.add(cm)
    await db_session.flush()
    await db_session.refresh(cm)
    return {"id": str(cm.id), "ten_chuyen_muc": cm.ten_chuyen_muc}


@pytest_asyncio.fixture
async def sample_chu_de(db_session: AsyncSession, sample_chuyen_muc):
    """Chu de MO, tac gia la cbcc_user (idx=0)."""
    from forum_service.models.chu_de import ChuDe

    cd = ChuDe(
        chuyen_muc_id=uuid.UUID(sample_chuyen_muc["id"]),
        tieu_de="Chu de test hai quan khu vuc 8",
        noi_dung="<p>Noi dung chu de test ve thu tuc hai quan chi tiet</p>",
        tags=["test", "haiquan"],
        tac_gia_id=uuid.UUID(_REAL_CC_IDS[0]),
        trang_thai="MO",
        is_ghim=False,
        is_khoa=False,
        so_luot_xem=0,
        so_tra_loi=0,
        so_upvote=0,
        is_deleted=False,
        created_at=_now(),
        updated_at=_now(),
    )
    db_session.add(cd)
    await db_session.flush()
    await db_session.refresh(cd)
    return {
        "id": str(cd.id),
        "tieu_de": cd.tieu_de,
        "trang_thai": "MO",
        "tac_gia_id": _REAL_CC_IDS[0],
        "chuyen_muc_id": sample_chuyen_muc["id"],
    }


@pytest_asyncio.fixture
async def khoa_chu_de(db_session: AsyncSession, sample_chuyen_muc):
    """Chu de bi khoa (is_khoa=True)."""
    from forum_service.models.chu_de import ChuDe

    cd = ChuDe(
        chuyen_muc_id=uuid.UUID(sample_chuyen_muc["id"]),
        tieu_de="Chu de da bi khoa de test thu nghiem",
        noi_dung="<p>Noi dung chu de test bi khoa khong tra loi duoc</p>",
        tags=["khoa"],
        tac_gia_id=uuid.UUID(_REAL_CC_IDS[0]),
        trang_thai="MO",
        is_ghim=False,
        is_khoa=True,
        so_luot_xem=0,
        so_tra_loi=0,
        so_upvote=0,
        is_deleted=False,
        created_at=_now(),
        updated_at=_now(),
    )
    db_session.add(cd)
    await db_session.flush()
    await db_session.refresh(cd)
    return {"id": str(cd.id), "tac_gia_id": _REAL_CC_IDS[0]}


@pytest_asyncio.fixture
async def old_chu_de(db_session: AsyncSession, sample_chuyen_muc):
    """Chu de tao 48h truoc — de test qua han sua."""
    from forum_service.models.chu_de import ChuDe

    cd = ChuDe(
        chuyen_muc_id=uuid.UUID(sample_chuyen_muc["id"]),
        tieu_de="Chu de cu da qua 24h de kiem tra gioi han",
        noi_dung="<p>Noi dung chu de cu da qua han sua de kiem tra quy tac</p>",
        tags=["cu"],
        tac_gia_id=uuid.UUID(_REAL_CC_IDS[0]),
        trang_thai="MO",
        is_ghim=False,
        is_khoa=False,
        so_luot_xem=5,
        so_tra_loi=0,
        so_upvote=0,
        is_deleted=False,
        created_at=_now() - timedelta(hours=48),
        updated_at=_now() - timedelta(hours=48),
    )
    db_session.add(cd)
    await db_session.flush()
    await db_session.refresh(cd)
    return {
        "id": str(cd.id),
        "tac_gia_id": _REAL_CC_IDS[0],
        "chuyen_muc_id": sample_chuyen_muc["id"],
    }


@pytest_asyncio.fixture
async def sample_tra_loi(db_session: AsyncSession, sample_chu_de):
    """Tra loi cap 1, tac gia la user_khac (idx=5)."""
    from forum_service.models.tra_loi import TraLoi

    tl = TraLoi(
        chu_de_id=uuid.UUID(sample_chu_de["id"]),
        parent_id=None,
        noi_dung="<p>Tra loi cap 1 cho chu de test</p>",
        tac_gia_id=uuid.UUID(_REAL_CC_IDS[5]),
        is_dap_an_chuan=False,
        is_an=False,
        so_upvote=0,
        is_deleted=False,
        created_at=_now(),
        updated_at=_now(),
    )
    db_session.add(tl)
    # Tang so_tra_loi cua chu de
    from sqlalchemy import update
    from forum_service.models.chu_de import ChuDe
    await db_session.execute(
        update(ChuDe)
        .where(ChuDe.id == uuid.UUID(sample_chu_de["id"]))
        .values(so_tra_loi=ChuDe.so_tra_loi + 1)
    )
    await db_session.flush()
    await db_session.refresh(tl)
    return {
        "id": str(tl.id),
        "chu_de_id": sample_chu_de["id"],
        "tac_gia_id": _REAL_CC_IDS[5],
    }


@pytest_asyncio.fixture
async def nested_tra_loi(db_session: AsyncSession, sample_tra_loi, sample_chu_de):
    """Tra loi cap 2 (con cua sample_tra_loi)."""
    from forum_service.models.tra_loi import TraLoi

    tl = TraLoi(
        chu_de_id=uuid.UUID(sample_chu_de["id"]),
        parent_id=uuid.UUID(sample_tra_loi["id"]),
        noi_dung="<p>Tra loi cap 2 nested reply cho test</p>",
        tac_gia_id=uuid.UUID(_REAL_CC_IDS[0]),
        is_dap_an_chuan=False,
        is_an=False,
        so_upvote=0,
        is_deleted=False,
        created_at=_now(),
        updated_at=_now(),
    )
    db_session.add(tl)
    await db_session.flush()
    await db_session.refresh(tl)
    return {
        "id": str(tl.id),
        "parent_id": sample_tra_loi["id"],
        "chu_de_id": sample_chu_de["id"],
    }
