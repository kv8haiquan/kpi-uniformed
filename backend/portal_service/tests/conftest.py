"""
portal_service/tests/conftest.py
=================================
Test fixtures cho module Portal (CMS tin tức + Tài liệu).

Pattern:
  - db_session: real DB session, savepoint/rollback sau mỗi test
  - client: AsyncClient với override get_db + get_current_user
  - 5 user fixtures: cbcc, bien_tap, qt_noi_dung, lanh_dao, admin
  - Data fixtures: direct DB insert (không qua API)

QUAN TRỌNG: Data fixtures dùng db_session.flush() (không commit),
data visible trong cùng session nhưng rollback sau test khi không có commit thật.
Khi API handler gọi db.commit(), data persist đến savepoint.
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

from portal_service.config import settings
from portal_service.dependencies import get_current_user, get_db
from portal_service.main import app
from shared.auth import TokenPayload


# =========================================================================
# REAL CONG_CHUC IDs từ production DB — cần cho FK constraint nguoi_soan_id
# =========================================================================
_REAL_CC_IDS = [
    "00327c43-c9a3-44d7-8306-7084e75cb2b5",  # idx=0 → cbcc_user
    "01014af6-1505-495b-95ab-8c1503cfa061",  # idx=1 → bien_tap_user
    "01abd5c1-5c34-475b-8ea8-803ad461f66d",  # idx=2 → qt_noi_dung_user
    "02a492ad-fb32-430d-8c4e-e9ded9b8d964",  # idx=3 → lanh_dao_user
    "02fed37c-1c82-4250-a6ea-7bf9db7b6955",  # idx=4 → admin_user
]

_LANH_DAO_DON_VI_ID = "a0000000-0000-0000-0000-000000000001"


def _now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


# =========================================================================
# DATABASE FIXTURES
# =========================================================================


@pytest_asyncio.fixture
async def db_session():
    """Tạo DB session với savepoint/rollback — đảm bảo test isolation.

    Dùng connection-level transaction + join_transaction_mode="create_savepoint":
    - session.commit() bên trong API handler chỉ commit đến SAVEPOINT (không tới DB thật)
    - conn.rollback() cuối test xóa sạch toàn bộ thay đổi
    - DB không bị ô nhiễm test data giữa các test
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
    """HTTP client với override get_db → dùng test session."""

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
    idx: int = 0,
    don_vi_id: str = _LANH_DAO_DON_VI_ID,
) -> TokenPayload:
    """Tạo TokenPayload mock cho test."""
    return TokenPayload(
        sub=_REAL_CC_IDS[idx % len(_REAL_CC_IDS)],
        exp=int((datetime.utcnow() + timedelta(hours=8)).timestamp()),
        type="access",
        ma_cc=f"TEST-{idx:02d}",
        vai_tro=vai_tro,
        don_vi_id=don_vi_id,
        is_lanh_dao=is_lanh_dao,
        platform_roles=platform_roles,
    )


def _set_user(user: TokenPayload):
    """Override get_current_user dependency với user mock."""

    async def _override():
        return user

    app.dependency_overrides[get_current_user] = _override


# =========================================================================
# USER FIXTURES (5 vai trò)
# =========================================================================


@pytest.fixture
def cbcc_user():
    """CBCC thường — chỉ xem bài đã xuất bản."""
    user = _make_user("CC", [], idx=0)
    _set_user(user)
    yield user
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def bien_tap_user():
    """Biên tập viên — tạo/sửa bài, gửi duyệt."""
    user = _make_user("CC", ["BIEN_TAP"], idx=1)
    _set_user(user)
    yield user
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def qt_noi_dung_user():
    """Quản trị nội dung — toàn quyền Portal."""
    user = _make_user("CC", ["QT_NOI_DUNG"], idx=2)
    _set_user(user)
    yield user
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def lanh_dao_user():
    """Lãnh đạo — duyệt và xuất bản bài viết."""
    user = _make_user(
        "TDV", [], is_lanh_dao=True, idx=3, don_vi_id=_LANH_DAO_DON_VI_ID
    )
    _set_user(user)
    yield user
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def admin_user():
    """Admin SUPER_ADMIN — bypass tất cả quyền."""
    user = _make_user("SUPER_ADMIN", [], idx=4)
    _set_user(user)
    yield user
    app.dependency_overrides.pop(get_current_user, None)


# =========================================================================
# DATA FIXTURES — Direct DB insert (tránh xung đột user fixture ordering)
# =========================================================================


@pytest_asyncio.fixture
async def sample_chuyen_muc(db_session: AsyncSession):
    """Tạo chuyên mục test trực tiếp vào DB."""
    from portal_service.models.chuyen_muc import ChuyenMuc

    slug = f"test-cm-{uuid.uuid4().hex[:8]}"
    cm = ChuyenMuc(
        ten="Chuyên mục Test",
        slug=slug,
        mo_ta="Chuyên mục dùng cho test",
        loai="TIN_TUC",
        thu_tu=99,
        is_active=True,
        created_at=_now(),
    )
    db_session.add(cm)
    await db_session.flush()
    await db_session.refresh(cm)
    return {"id": str(cm.id), "ten": cm.ten, "slug": cm.slug, "loai": cm.loai}


@pytest_asyncio.fixture
async def sample_thu_muc(db_session: AsyncSession):
    """Tạo thư mục test trực tiếp vào DB."""
    from portal_service.models.thu_muc import ThuMuc
    from uuid import UUID

    tm = ThuMuc(
        ten="Thu muc Test",
        parent_id=None,
        thu_tu=99,
        quyen_truy_cap="TAT_CA",
        created_by=UUID(_REAL_CC_IDS[2]),  # qt_noi_dung_user
        created_at=_now(),
    )
    db_session.add(tm)
    await db_session.flush()
    await db_session.refresh(tm)
    return {"id": str(tm.id), "ten": tm.ten, "quyen_truy_cap": tm.quyen_truy_cap}


@pytest_asyncio.fixture
async def sample_bai_viet_nhap(db_session: AsyncSession, sample_chuyen_muc):
    """Tạo bài viết NHAP của bien_tap_user (idx=1)."""
    from portal_service.models.bai_viet import BaiViet
    from uuid import UUID

    bv = BaiViet(
        chuyen_muc_id=UUID(sample_chuyen_muc["id"]),
        tieu_de="Bai viet test nhap",
        tom_tat="Tom tat test",
        noi_dung="<p>Noi dung test</p>",
        trang_thai="NHAP",
        nguoi_soan_id=UUID(_REAL_CC_IDS[1]),  # bien_tap_user
        is_ghim=False,
        so_luot_xem=0,
        is_deleted=False,
        created_at=_now(),
        updated_at=_now(),
    )
    db_session.add(bv)
    await db_session.flush()
    await db_session.refresh(bv)
    return {
        "id": str(bv.id),
        "tieu_de": bv.tieu_de,
        "trang_thai": "NHAP",
        "nguoi_soan_id": _REAL_CC_IDS[1],
        "chuyen_muc_id": sample_chuyen_muc["id"],
    }


@pytest_asyncio.fixture
async def sample_bai_viet_xuat_ban(db_session: AsyncSession, sample_chuyen_muc):
    """Tạo bài viết đã XUAT_BAN (nguoi_soan = bien_tap_user idx=1)."""
    from portal_service.models.bai_viet import BaiViet
    from uuid import UUID

    now = _now()
    bv = BaiViet(
        chuyen_muc_id=UUID(sample_chuyen_muc["id"]),
        tieu_de="Bai viet xuat ban test",
        tom_tat="Tom tat bai xuat ban",
        noi_dung="<p>Noi dung xuat ban</p>",
        trang_thai="XUAT_BAN",
        nguoi_soan_id=UUID(_REAL_CC_IDS[1]),
        nguoi_kiem_tra_id=UUID(_REAL_CC_IDS[2]),
        nguoi_duyet_id=UUID(_REAL_CC_IDS[3]),
        ngay_xuat_ban=now,
        is_ghim=False,
        so_luot_xem=5,
        is_deleted=False,
        created_at=now,
        updated_at=now,
    )
    db_session.add(bv)
    await db_session.flush()
    await db_session.refresh(bv)
    return {
        "id": str(bv.id),
        "tieu_de": bv.tieu_de,
        "trang_thai": "XUAT_BAN",
        "nguoi_soan_id": _REAL_CC_IDS[1],
        "chuyen_muc_id": sample_chuyen_muc["id"],
    }


@pytest_asyncio.fixture
async def sample_tai_lieu(db_session: AsyncSession, sample_thu_muc):
    """Tạo tài liệu test trực tiếp vào DB."""
    from portal_service.models.tai_lieu import TaiLieu
    from uuid import UUID

    tl = TaiLieu(
        ten_tai_lieu="Tai lieu test",
        mo_ta="Mo ta tai lieu test",
        thu_muc_id=UUID(sample_thu_muc["id"]),
        file_url="https://example.com/test.pdf",
        file_name="test.pdf",
        file_size_bytes=1024,
        file_type="application/pdf",
        phien_ban=1,
        phien_ban_truoc_id=None,
        tags=["test", "2026"],
        quyen_truy_cap="TAT_CA",
        nguoi_tai_len_id=UUID(_REAL_CC_IDS[2]),
        is_deleted=False,
        created_at=_now(),
    )
    db_session.add(tl)
    await db_session.flush()
    await db_session.refresh(tl)
    return {
        "id": str(tl.id),
        "ten_tai_lieu": tl.ten_tai_lieu,
        "file_url": tl.file_url,
        "file_type": tl.file_type,
        "thu_muc_id": sample_thu_muc["id"],
        "phien_ban": 1,
    }
