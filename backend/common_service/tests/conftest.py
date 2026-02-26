"""
common_service/tests/conftest.py
=================================
Test fixtures cho module Common (Thong bao, File Storage, Knowledge Base, KPI Integration).

Pattern:
  - db_session: real DB session, savepoint/rollback sau moi test
  - client: AsyncClient voi override get_db + get_current_user
  - 6 user fixtures: cbcc, chuyen_gia, qt_noi_dung, qt_attt, lanh_dao, admin
  - Data fixtures: direct DB insert (khong qua API)

QUAN TRONG: Data fixtures dung db_session.flush() (khong commit),
data visible trong cung session nhung rollback sau test khi khong co commit that.
Khi API handler goi db.commit(), data persist den savepoint.
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

from common_service.config import settings
from common_service.dependencies import get_current_user, get_db
from common_service.main import app
from shared.auth import TokenPayload


# =========================================================================
# REAL CONG_CHUC IDs tu production DB — can cho FK constraint
# =========================================================================
_REAL_CC_IDS = [
    "00327c43-c9a3-44d7-8306-7084e75cb2b5",  # idx=0 → cbcc_user
    "01014af6-1505-495b-95ab-8c1503cfa061",  # idx=1 → chuyen_gia_user
    "01abd5c1-5c34-475b-8ea8-803ad461f66d",  # idx=2 → qt_noi_dung_user
    "02a492ad-fb32-430d-8c4e-e9ded9b8d964",  # idx=3 → lanh_dao_user
    "02fed37c-1c82-4250-a6ea-7bf9db7b6955",  # idx=4 → admin_user
]

_LANH_DAO_DON_VI_ID = "a0000000-0000-0000-0000-000000000001"

# Internal API key (mac dinh tu dependencies.py)
INTERNAL_KEY = os.getenv("INTERNAL_API_KEY", "kv08-internal-secret-key")


def _now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


# =========================================================================
# DATABASE FIXTURES
# =========================================================================


@pytest_asyncio.fixture
async def db_session():
    """Tao DB session voi savepoint/rollback — dam bao test isolation."""
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
    """HTTP client voi override get_db → dung test session."""

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
    """Tao TokenPayload mock cho test."""
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
    """Override get_current_user dependency voi user mock."""

    async def _override():
        return user

    app.dependency_overrides[get_current_user] = _override


# =========================================================================
# USER FIXTURES (6 vai tro)
# =========================================================================


@pytest.fixture
def cbcc_user():
    """CBCC thuong — nguoi dung co ban."""
    user = _make_user("CC", [], idx=0)
    _set_user(user)
    yield user
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def chuyen_gia_user():
    """Chuyen gia — tao KB, tra loi forum."""
    user = _make_user("CC", ["CHUYEN_GIA"], idx=1)
    _set_user(user)
    yield user
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def qt_noi_dung_user():
    """Quan tri noi dung — duyet KB, quan ly Portal."""
    user = _make_user("CC", ["QT_NOI_DUNG"], idx=2)
    _set_user(user)
    yield user
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def qt_attt_user():
    """Quan tri ATTT."""
    user = _make_user("CC", ["QT_ATTT"], idx=2)
    _set_user(user)
    yield user
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def lanh_dao_user():
    """Lanh dao — vai tro quan ly."""
    user = _make_user(
        "TDV", [], is_lanh_dao=True, idx=3, don_vi_id=_LANH_DAO_DON_VI_ID
    )
    _set_user(user)
    yield user
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def admin_user():
    """Admin SUPER_ADMIN — bypass tat ca quyen."""
    user = _make_user("SUPER_ADMIN", [], idx=4)
    _set_user(user)
    yield user
    app.dependency_overrides.pop(get_current_user, None)


# =========================================================================
# DATA FIXTURES — Direct DB insert
# =========================================================================


@pytest_asyncio.fixture
async def sample_thong_bao(db_session: AsyncSession):
    """Tao 5 thong bao mau cho cbcc_user (idx=0) — mix muc do + loai."""
    from common_service.models.thong_bao import ThongBao

    now = _now()
    nguoi_nhan_id = uuid.UUID(_REAL_CC_IDS[0])  # cbcc_user

    records = [
        ThongBao(
            nguoi_nhan_id=nguoi_nhan_id,
            tieu_de="Thong bao KHAN cap",
            noi_dung="Noi dung khan",
            loai="KPI",
            muc_do="KHAN",
            da_doc=False,
            created_at=now - timedelta(hours=1),
        ),
        ThongBao(
            nguoi_nhan_id=nguoi_nhan_id,
            tieu_de="Thong bao QUAN TRONG tu LMS",
            noi_dung="Khoa hoc sap het han",
            loai="LMS",
            muc_do="QUAN_TRONG",
            link_url="/dao-tao/khoa-hoc/abc",
            da_doc=False,
            created_at=now - timedelta(hours=2),
        ),
        ThongBao(
            nguoi_nhan_id=nguoi_nhan_id,
            tieu_de="Thong bao binh thuong tu FORUM",
            noi_dung="Chu de moi duoc tao",
            loai="FORUM",
            muc_do="BINH_THUONG",
            da_doc=False,
            created_at=now - timedelta(hours=3),
        ),
        ThongBao(
            nguoi_nhan_id=nguoi_nhan_id,
            tieu_de="Thong bao da doc tu LEGAL",
            noi_dung="Van ban moi ban hanh",
            loai="LEGAL",
            muc_do="QUAN_TRONG",
            da_doc=True,
            ngay_doc=now - timedelta(hours=1),
            created_at=now - timedelta(hours=4),
        ),
        ThongBao(
            nguoi_nhan_id=nguoi_nhan_id,
            tieu_de="Thong bao he thong binh thuong",
            noi_dung="Bao tri he thong",
            loai="HE_THONG",
            muc_do="BINH_THUONG",
            da_doc=True,
            ngay_doc=now,
            created_at=now - timedelta(hours=5),
        ),
    ]
    db_session.add_all(records)
    await db_session.flush()
    for r in records:
        await db_session.refresh(r)

    return [
        {"id": str(r.id), "tieu_de": r.tieu_de, "muc_do": r.muc_do,
         "loai": r.loai, "da_doc": r.da_doc, "nguoi_nhan_id": str(r.nguoi_nhan_id)}
        for r in records
    ]


@pytest_asyncio.fixture
async def sample_thong_bao_nguoi_khac(db_session: AsyncSession):
    """Tao 1 thong bao cho chuyen_gia_user (idx=1) — dung de test phan quyen."""
    from common_service.models.thong_bao import ThongBao

    tb = ThongBao(
        nguoi_nhan_id=uuid.UUID(_REAL_CC_IDS[1]),
        tieu_de="Thong bao rieng chuyen gia",
        loai="HE_THONG",
        muc_do="BINH_THUONG",
        da_doc=False,
        created_at=_now(),
    )
    db_session.add(tb)
    await db_session.flush()
    await db_session.refresh(tb)
    return {"id": str(tb.id), "nguoi_nhan_id": _REAL_CC_IDS[1]}


@pytest_asyncio.fixture
async def sample_file_storage(db_session: AsyncSession):
    """Tao 3 file metadata mau — upload boi cbcc_user (idx=0)."""
    from common_service.models.file_storage import FileStorage

    files = [
        FileStorage(
            file_name="report.pdf",
            file_path="lms/documents/test-uuid-1.pdf",
            file_size_bytes=1024 * 100,  # 100KB
            mime_type="application/pdf",
            module="LMS",
            doi_tuong_type="BAI_HOC",
            nguoi_tai_len_id=uuid.UUID(_REAL_CC_IDS[0]),
            created_at=_now(),
        ),
        FileStorage(
            file_name="image.png",
            file_path="portal/images/test-uuid-2.png",
            file_size_bytes=1024 * 50,  # 50KB
            mime_type="image/png",
            module="PORTAL",
            nguoi_tai_len_id=uuid.UUID(_REAL_CC_IDS[0]),
            created_at=_now(),
        ),
        FileStorage(
            file_name="deleted.docx",
            file_path="legal/documents/test-uuid-3.docx",
            file_size_bytes=1024 * 200,
            mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            module="LEGAL",
            nguoi_tai_len_id=uuid.UUID(_REAL_CC_IDS[0]),
            is_deleted=True,
            created_at=_now(),
        ),
    ]
    db_session.add_all(files)
    await db_session.flush()
    for f in files:
        await db_session.refresh(f)

    return [
        {"id": str(f.id), "file_name": f.file_name, "module": f.module,
         "is_deleted": f.is_deleted, "nguoi_tai_len_id": str(f.nguoi_tai_len_id)}
        for f in files
    ]


@pytest_asyncio.fixture
async def sample_knowledge_base(db_session: AsyncSession):
    """Tao 4 KB mau — 2 SOP + 2 FAQ, cac trang thai khac nhau.

    Chu so huu:
      - idx=0,1: chuyen_gia_user (idx=1)
      - idx=2: qt_noi_dung_user (idx=2) → DA_XUAT_BAN
      - idx=3: chuyen_gia_user (idx=1) → DA_XUAT_BAN voi van_ban_lien_quan
    """
    from common_service.models.knowledge_base import KnowledgeBase

    now = _now()
    kbs = [
        KnowledgeBase(
            loai="SOP",
            tieu_de="SOP Quy trinh xuat nhap khau",
            noi_dung="<p>Buoc 1: Khai bao to khai. Buoc 2: Kiem tra thue.</p>",
            chuyen_de=["XNK", "Thue"],
            tags=["XNK", "quy_trinh", "thue"],
            chu_so_huu_id=uuid.UUID(_REAL_CC_IDS[1]),
            trang_thai="NHAP",
            phien_ban=1,
            created_at=now,
            updated_at=now,
        ),
        KnowledgeBase(
            loai="FAQ",
            tieu_de="FAQ Ve thu tuc hai quan",
            noi_dung="<p>Hoi: Thoi gian xu ly to khai? Dap: 4 gio lam viec.</p>",
            chuyen_de=["Hai_quan"],
            tags=["FAQ", "thu_tuc"],
            chu_so_huu_id=uuid.UUID(_REAL_CC_IDS[1]),
            trang_thai="CHO_DUYET",
            phien_ban=1,
            created_at=now,
            updated_at=now,
        ),
        KnowledgeBase(
            loai="SOP",
            tieu_de="SOP Kiem tra thue xuat khau",
            noi_dung="<p>Quy trinh kiem tra thue xuat khau chi tiet.</p>",
            chuyen_de=["Thue"],
            tags=["thue", "xuat_khau"],
            chu_so_huu_id=uuid.UUID(_REAL_CC_IDS[2]),
            trang_thai="DA_XUAT_BAN",
            phien_ban=2,
            created_at=now - timedelta(days=10),
            updated_at=now,
        ),
        KnowledgeBase(
            loai="FAQ",
            tieu_de="FAQ Ve quy dinh phap luat moi",
            noi_dung="<p>Hoi: Luat hai quan 2025 co gi moi? Dap: Nhieu thay doi.</p>",
            chuyen_de=["Phap_luat"],
            tags=["phap_luat", "luat_hai_quan"],
            van_ban_lien_quan=["aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"],
            chu_so_huu_id=uuid.UUID(_REAL_CC_IDS[1]),
            trang_thai="DA_XUAT_BAN",
            phien_ban=1,
            created_at=now - timedelta(days=5),
            updated_at=now,
        ),
    ]
    db_session.add_all(kbs)
    await db_session.flush()
    for kb in kbs:
        await db_session.refresh(kb)

    return [
        {"id": str(kb.id), "loai": kb.loai, "tieu_de": kb.tieu_de,
         "trang_thai": kb.trang_thai, "chu_so_huu_id": str(kb.chu_so_huu_id),
         "phien_ban": kb.phien_ban}
        for kb in kbs
    ]


@pytest_asyncio.fixture
async def sample_kpi_log(db_session: AsyncSession):
    """Tao 3 KPI log mau cho cbcc_user (idx=0) — thang 2, nam 2026."""
    from common_service.models.kpi_integration_log import KpiIntegrationLog

    logs = [
        KpiIntegrationLog(
            cong_chuc_id=uuid.UUID(_REAL_CC_IDS[0]),
            thang=2,
            nam=2026,
            module="LMS",
            metrics={"khoa_hoan_thanh": 3, "gio_hoc": 15, "diem_tb": 85.5},
            diem_quy_doi=85.5,
        ),
        KpiIntegrationLog(
            cong_chuc_id=uuid.UUID(_REAL_CC_IDS[0]),
            thang=2,
            nam=2026,
            module="FORUM",
            metrics={"bai_dang": 5, "tra_loi": 12, "luot_vote": 20},
            diem_quy_doi=72.0,
        ),
        KpiIntegrationLog(
            cong_chuc_id=uuid.UUID(_REAL_CC_IDS[0]),
            thang=2,
            nam=2026,
            module="LEGAL",
            metrics={"vb_da_doc": 10, "quiz_pass": 8, "diem_tb": 90.0},
            diem_quy_doi=90.0,
        ),
    ]
    db_session.add_all(logs)
    await db_session.flush()
    for log in logs:
        await db_session.refresh(log)

    return [
        {"id": str(log.id), "module": log.module, "thang": log.thang,
         "nam": log.nam, "cong_chuc_id": str(log.cong_chuc_id)}
        for log in logs
    ]
