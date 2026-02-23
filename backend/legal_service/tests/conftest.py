"""
legal_service/tests/conftest.py
================================
Test fixtures cho module Phap luat.

Pattern:
  - db_session: real DB test session, flush (không commit) để rollback sau test
  - client: AsyncClient với override get_db
  - 5 user fixtures: cbcc, bien_tap, qt_noi_dung, lanh_dao, admin
  - Data fixtures: dùng direct DB insert (không qua API) tránh xung đột user fixture

QUAN TRỌNG: Data fixtures dùng db_session.flush() (không commit),
data sẽ visible trong cùng session nhưng rollback sau test nếu không có commit.
Tuy nhiên, khi API handler gọi db.commit(), data sẽ được persist.
"""

import os
import sys
import uuid
from datetime import date, datetime, timedelta, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from legal_service.config import settings
from legal_service.dependencies import get_current_user, get_db
from legal_service.main import app
from shared.auth import TokenPayload


# =========================================================================
# REAL CONG_CHUC IDs từ production DB — cần cho FK constraint nguoi_nhap_id
# =========================================================================
_REAL_CC_IDS = [
    "00327c43-c9a3-44d7-8306-7084e75cb2b5",  # idx=0 → cbcc_user
    "01014af6-1505-495b-95ab-8c1503cfa061",  # idx=1 → bien_tap_user
    "01abd5c1-5c34-475b-8ea8-803ad461f66d",  # idx=2 → qt_noi_dung_user
    "02a492ad-fb32-430d-8c4e-e9ded9b8d964",  # idx=3 → lanh_dao_user
    "02fed37c-1c82-4250-a6ea-7bf9db7b6955",  # idx=4 → admin_user
]

# Don vi IDs cho test phân quyền lãnh đạo
_LANH_DAO_DON_VI_ID = "a0000000-0000-0000-0000-000000000001"
_OTHER_DON_VI_ID = "b0000000-0000-0000-0000-000000000002"


def _now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


# =========================================================================
# DATABASE FIXTURES
# =========================================================================


@pytest_asyncio.fixture
async def db_session():
    """Tạo DB session cho mỗi test với transaction isolation đúng chuẩn.

    Dùng connection-level transaction + join_transaction_mode="create_savepoint":
    - session.commit() bên trong API handler chỉ commit đến SAVEPOINT (không tới DB thật)
    - conn.rollback() cuối test xóa sạch toàn bộ thay đổi của test đó
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
    """CBCC thường — chỉ xem văn bản đã xuất bản."""
    user = _make_user("CC", [], idx=0)
    _set_user(user)
    yield user
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def bien_tap_user():
    """Biên tập viên — tạo/sửa VB, gửi duyệt."""
    user = _make_user("CC", ["BIEN_TAP"], idx=1)
    _set_user(user)
    yield user
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def qt_noi_dung_user():
    """Quản trị nội dung — toàn quyền Legal."""
    user = _make_user("CC", ["QT_NOI_DUNG"], idx=2)
    _set_user(user)
    yield user
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def lanh_dao_user():
    """Lãnh đạo đơn vị — xem báo cáo đơn vị mình."""
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
async def sample_loai_van_ban(db_session: AsyncSession):
    """Tạo loại văn bản test trực tiếp vào DB."""
    from legal_service.models.loai_van_ban import LoaiVanBan

    lvb = LoaiVanBan(
        ma=f"TEST-{uuid.uuid4().hex[:6].upper()}",
        ten="Loại VB Test",
        thu_tu=99,
    )
    db_session.add(lvb)
    await db_session.flush()
    await db_session.refresh(lvb)
    return {"id": str(lvb.id), "ma": lvb.ma, "ten": lvb.ten, "thu_tu": 99}


@pytest_asyncio.fixture
async def sample_van_ban(db_session: AsyncSession, sample_loai_van_ban):
    """Tạo văn bản trạng thái NHAP trực tiếp vào DB."""
    from uuid import UUID

    from legal_service.models.van_ban import VanBan

    vb = VanBan(
        so_hieu=f"VB-TEST-{uuid.uuid4().hex[:8].upper()}",
        trich_yeu="Văn bản test hải quan khu vực 8",
        loai_van_ban_id=UUID(sample_loai_van_ban["id"]),
        co_quan_ban_hanh="Chi cục HQKV8",
        ngay_ban_hanh=date(2026, 1, 15),
        trang_thai_hieu_luc="CON_HIEU_LUC",
        muc_do="BINH_THUONG",
        bat_buoc_doc=False,
        trang_thai_duyet="NHAP",
        noi_dung_html="<p>Nội dung văn bản test</p>",
        nguoi_nhap_id=UUID(_REAL_CC_IDS[1]),  # bien_tap_user
        phien_ban=1,
        is_deleted=False,
        created_at=_now(),
        updated_at=_now(),
    )
    db_session.add(vb)
    await db_session.flush()
    await db_session.refresh(vb)
    return {
        "id": str(vb.id),
        "so_hieu": vb.so_hieu,
        "trang_thai_duyet": "NHAP",
        "nguoi_nhap_id": _REAL_CC_IDS[1],
        "loai_van_ban_id": sample_loai_van_ban["id"],
    }


@pytest_asyncio.fixture
async def published_van_ban(db_session: AsyncSession, sample_loai_van_ban):
    """Tạo văn bản đã xuất bản (DA_XUAT_BAN) trực tiếp vào DB."""
    from uuid import UUID

    from legal_service.models.van_ban import VanBan

    now = _now()
    vb = VanBan(
        so_hieu=f"VB-PUB-{uuid.uuid4().hex[:8].upper()}",
        trich_yeu="Văn bản xuất bản test hải quan",
        loai_van_ban_id=UUID(sample_loai_van_ban["id"]),
        co_quan_ban_hanh="Chi cục HQKV8",
        ngay_ban_hanh=date(2026, 1, 15),
        noi_dung_html="<p>Nội dung văn bản xuất bản</p>",
        trang_thai_hieu_luc="CON_HIEU_LUC",
        muc_do="BINH_THUONG",
        bat_buoc_doc=False,
        trang_thai_duyet="DA_XUAT_BAN",
        nguoi_nhap_id=UUID(_REAL_CC_IDS[2]),  # qt_noi_dung_user
        nguoi_duyet_id=UUID(_REAL_CC_IDS[2]),
        ngay_xuat_ban=now,
        phien_ban=1,
        is_deleted=False,
        created_at=now,
        updated_at=now,
    )
    db_session.add(vb)
    await db_session.flush()
    await db_session.refresh(vb)
    return {
        "id": str(vb.id),
        "so_hieu": vb.so_hieu,
        "trang_thai_duyet": "DA_XUAT_BAN",
        "loai_van_ban_id": sample_loai_van_ban["id"],
    }


@pytest_asyncio.fixture
async def sample_quiz(db_session: AsyncSession, published_van_ban):
    """Tạo quiz 5 câu cho văn bản đã xuất bản."""
    from uuid import UUID

    from legal_service.models.quiz_van_ban import QuizVanBan

    # 5 câu hỏi, đáp án đúng index=0
    cau_hoi = [
        {
            "noi_dung": f"Câu hỏi {i + 1}: Quy định nào áp dụng cho hải quan?",
            "dap_an": ["Đáp án A (đúng)", "Đáp án B", "Đáp án C", "Đáp án D"],
            "correct": 0,
            "giai_thich": f"Giải thích câu {i + 1}: Đáp án A là đúng.",
        }
        for i in range(5)
    ]

    quiz = QuizVanBan(
        van_ban_id=UUID(published_van_ban["id"]),
        tieu_de="Quiz test phap luat",
        so_cau_hoi=5,
        thoi_gian_phut=30,
        diem_dat=70.0,
        cau_hoi=cau_hoi,
        nguoi_tao_id=UUID(_REAL_CC_IDS[2]),
        is_active=True,
        created_at=_now(),
    )
    db_session.add(quiz)
    await db_session.flush()
    await db_session.refresh(quiz)
    return {
        "id": str(quiz.id),
        "van_ban_id": published_van_ban["id"],
        "so_cau_hoi": 5,
        "diem_dat": 70.0,
        "cau_hoi": cau_hoi,
    }
