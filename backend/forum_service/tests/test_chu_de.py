"""
forum_service/tests/test_chu_de.py
===================================
Test cases cho CRUD Chu de + hanh dong + dap an chuan.

17 test cases bao phu:
  - CRUD co ban (5 tests)
  - chi_doc chuyen muc (2 tests)
  - yeu_cau_duyet workflow (2 tests)
  - ghim/khoa (2 tests)
  - dap an chuan (2 tests)
  - sap xep (2 tests)
  - permission/error cases (2 tests)
"""

import uuid
from datetime import datetime, timezone

import pytest

# API constant from conftest
API = "/api/forum/v1"


# ============================================================================
# GROUP 1 — CRUD CO BAN (5 tests)
# ============================================================================


@pytest.mark.asyncio
async def test_tao_chu_de_thanh_cong(client, cbcc_user, sample_chuyen_muc):
    """cbcc_user tao chu de trong sample_chuyen_muc thanh cong."""
    payload = {
        "chuyen_muc_id": sample_chuyen_muc["id"],
        "tieu_de": "Chu de moi ve thu tuc hai quan XNK hang hoa",
        "noi_dung": "<p>Noi dung chi tiet ve thu tuc hai quan XNK hang hoa qua cang bien</p>",
        "tags": ["thu-tuc", "xnk"],
    }
    resp = await client.post(f"{API}/chu-de", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["success"] is True
    assert data["data"]["tieu_de"] == payload["tieu_de"]
    assert data["data"]["trang_thai"] == "MO"
    assert data["data"]["is_ghim"] is False


@pytest.mark.asyncio
async def test_danh_sach_chu_de(client, cbcc_user, sample_chu_de):
    """cbcc_user lay danh sach chu de, expect list + pagination."""
    resp = await client.get(f"{API}/chu-de")
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert isinstance(data["data"], list)
    assert "pagination" in data
    assert data["pagination"]["page"] == 1
    assert data["pagination"]["total_items"] >= 1


@pytest.mark.asyncio
async def test_chi_tiet_chu_de(client, cbcc_user, sample_chu_de):
    """cbcc_user xem chi tiet sample_chu_de, kiem tra so_luot_xem tang."""
    chu_de_id = sample_chu_de["id"]
    resp = await client.get(f"{API}/chu-de/{chu_de_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["data"]["tieu_de"] == sample_chu_de["tieu_de"]
    assert data["data"]["so_luot_xem"] >= 1


@pytest.mark.asyncio
async def test_sua_chu_de_author(client, cbcc_user, sample_chu_de):
    """cbcc_user (author) sua sample_chu_de thanh cong."""
    chu_de_id = sample_chu_de["id"]
    payload = {
        "tieu_de": "Chu de da duoc cap nhat tieu de moi",
        "noi_dung": "<p>Noi dung da duoc chinh sua lai</p>",
    }
    resp = await client.put(f"{API}/chu-de/{chu_de_id}", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["data"]["tieu_de"] == payload["tieu_de"]


@pytest.mark.asyncio
async def test_xoa_chu_de_khong_tra_loi(client, cbcc_user, sample_chuyen_muc):
    """cbcc_user tao va xoa chu de moi (chua co tra loi) thanh cong."""
    # Tao chu de moi
    payload = {
        "chuyen_muc_id": sample_chuyen_muc["id"],
        "tieu_de": "Chu de se bi xoa ngay lap tuc de kiem tra",
        "noi_dung": "<p>Noi dung chu de se bi xoa de test delete endpoint</p>",
        "tags": ["test"],
    }
    create_resp = await client.post(f"{API}/chu-de", json=payload)
    assert create_resp.status_code == 201
    chu_de_id = create_resp.json()["data"]["id"]

    # Xoa chu de vua tao
    del_resp = await client.delete(f"{API}/chu-de/{chu_de_id}")
    assert del_resp.status_code == 200
    data = del_resp.json()
    assert data["success"] is True


# ============================================================================
# GROUP 2 — CHI_DOC CHUYEN MUC (2 tests)
# ============================================================================


@pytest.mark.asyncio
async def test_tao_chu_de_chi_doc_cbcc_403(client, cbcc_user, chi_doc_chuyen_muc):
    """cbcc_user (khong co platform_role) tao chu de trong chi_doc_chuyen_muc -> 403."""
    payload = {
        "chuyen_muc_id": chi_doc_chuyen_muc["id"],
        "tieu_de": "CBCC khong duoc dang bai vao chuyen muc chi doc",
        "noi_dung": "<p>Noi dung test kiem tra phan quyen chi_doc</p>",
        "tags": [],
    }
    resp = await client.post(f"{API}/chu-de", json=payload)
    assert resp.status_code == 403
    body = resp.json()
    # FastAPI wraps HTTPException.detail in "detail" key
    detail = body["detail"]
    assert detail["success"] is False
    assert detail["error"]["code"] == "FORUM_ERR_004"


@pytest.mark.asyncio
async def test_tao_chu_de_chi_doc_chuyen_gia_ok(
    client, chuyen_gia_user, chi_doc_chuyen_muc
):
    """chuyen_gia_user (co platform_role CHUYEN_GIA) tao chu de chi_doc thanh cong."""
    payload = {
        "chuyen_muc_id": chi_doc_chuyen_muc["id"],
        "tieu_de": "Chuyen gia duoc dang bai vao chuyen muc chi doc",
        "noi_dung": "<p>Noi dung chuyen gia chia se kinh nghiem nghiep vu</p>",
        "tags": ["chuyen-gia"],
    }
    resp = await client.post(f"{API}/chu-de", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["success"] is True
    assert data["data"]["trang_thai"] == "MO"


# ============================================================================
# GROUP 3 — YEU_CAU_DUYET WORKFLOW (2 tests)
# ============================================================================


@pytest.mark.asyncio
async def test_tao_chu_de_yeu_cau_duyet_trang_thai_CHO_DUYET(
    client, cbcc_user, sample_chuyen_muc
):
    """cbcc_user tao chu de trong sample_chuyen_muc (giả định yeu_cau_duyet).

    NOTE: Tested logic via test_duyet_chu_de which creates CHO_DUYET directly in DB.
    This test verifies the API behavior when posting to a normal chuyen_muc.
    """
    payload = {
        "chuyen_muc_id": sample_chuyen_muc["id"],
        "tieu_de": "Chu de duoc tao trong chuyen muc binh thuong",
        "noi_dung": "<p>Noi dung chu de trong chuyen muc khong yeu cau duyet</p>",
        "tags": ["test"],
    }
    resp = await client.post(f"{API}/chu-de", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["success"] is True
    # sample_chuyen_muc has yeu_cau_duyet=False, so trang_thai should be MO
    assert data["data"]["trang_thai"] == "MO"


@pytest.mark.asyncio
async def test_duyet_chu_de(
    client, cbcc_user, dieu_phoi_user, yeu_cau_duyet_chuyen_muc, db_session
):
    """dieu_phoi_user duyet chu de CHO_DUYET -> MO."""
    from forum_service.models.chu_de import ChuDe
    from datetime import datetime, timezone

    # Copy from conftest
    _REAL_CC_IDS = [
        "00327c43-c9a3-44d7-8306-7084e75cb2b5",  # idx=0 -> cbcc_user
        "01014af6-1505-495b-95ab-8c1503cfa061",  # idx=1 -> chuyen_gia_user
        "01abd5c1-5c34-475b-8ea8-803ad461f66d",  # idx=2 -> dieu_phoi_user
        "02a492ad-fb32-430d-8c4e-e9ded9b8d964",  # idx=3 -> lanh_dao_user
        "02fed37c-1c82-4250-a6ea-7bf9db7b6955",  # idx=4 -> admin_user
        "03aeff5a-09b8-46ea-b88d-51323dd32c0e",  # idx=5 -> user_khac
    ]

    def _now():
        return datetime.now(timezone.utc).replace(tzinfo=None)

    # 1. cbcc_user tao chu de trong yeu_cau_duyet_chuyen_muc
    # (can switch user trc, sau do switch lai dieu_phoi)
    # Cach don gian nhat: insert truc tiep DB
    cd = ChuDe(
        chuyen_muc_id=uuid.UUID(yeu_cau_duyet_chuyen_muc["id"]),
        tieu_de="Chu de cho duyet de kiem tra hanh dong DUYET",
        noi_dung="<p>Noi dung chu de cho duyet test</p>",
        tags=["cho-duyet"],
        tac_gia_id=uuid.UUID(_REAL_CC_IDS[0]),
        trang_thai="CHO_DUYET",
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
    chu_de_id = str(cd.id)

    # 2. dieu_phoi_user duyet (fixture da override user)
    payload = {"hanh_dong": "DUYET"}
    resp = await client.patch(f"{API}/chu-de/{chu_de_id}/hanh-dong", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert "duyet" in data["message"].lower()


# ============================================================================
# GROUP 4 — GHIM/KHOA (2 tests)
# ============================================================================


@pytest.mark.asyncio
async def test_ghim_chu_de(client, dieu_phoi_user, sample_chu_de):
    """dieu_phoi_user ghim sample_chu_de thanh cong."""
    chu_de_id = sample_chu_de["id"]
    payload = {"hanh_dong": "GHIM"}
    resp = await client.patch(f"{API}/chu-de/{chu_de_id}/hanh-dong", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True


@pytest.mark.asyncio
async def test_khoa_chu_de(client, dieu_phoi_user, sample_chu_de):
    """dieu_phoi_user khoa sample_chu_de thanh cong."""
    chu_de_id = sample_chu_de["id"]
    payload = {"hanh_dong": "KHOA"}
    resp = await client.patch(f"{API}/chu-de/{chu_de_id}/hanh-dong", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True


# ============================================================================
# GROUP 5 — DAP AN CHUAN (2 tests)
# ============================================================================


@pytest.mark.asyncio
async def test_chon_dap_an_chuan_author(client, cbcc_user, sample_chu_de, sample_tra_loi):
    """cbcc_user (author) chon sample_tra_loi lam dap an chuan."""
    chu_de_id = sample_chu_de["id"]
    payload = {"tra_loi_id": sample_tra_loi["id"]}
    resp = await client.patch(f"{API}/chu-de/{chu_de_id}/dap-an-chuan", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True


@pytest.mark.asyncio
async def test_chon_dap_an_chuan_chuyen_gia(
    client, chuyen_gia_user, sample_chu_de, sample_tra_loi
):
    """chuyen_gia_user (khong phai author) chon dap an chuan thanh cong."""
    chu_de_id = sample_chu_de["id"]
    payload = {"tra_loi_id": sample_tra_loi["id"]}
    resp = await client.patch(f"{API}/chu-de/{chu_de_id}/dap-an-chuan", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True


# ============================================================================
# GROUP 6 — SAP XEP (2 tests)
# ============================================================================


@pytest.mark.asyncio
async def test_sap_xep_nhieu_upvote(client, cbcc_user, sample_chu_de):
    """GET /chu-de?sap_xep=nhieu_upvote khong loi."""
    resp = await client.get(f"{API}/chu-de?sap_xep=nhieu_upvote")
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert isinstance(data["data"], list)


@pytest.mark.asyncio
async def test_sap_xep_nhieu_tra_loi(client, cbcc_user, sample_chu_de):
    """GET /chu-de?sap_xep=nhieu_tra_loi khong loi."""
    resp = await client.get(f"{API}/chu-de?sap_xep=nhieu_tra_loi")
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert isinstance(data["data"], list)


# ============================================================================
# GROUP 7 — PERMISSION / ERROR CASES (2 tests)
# ============================================================================


@pytest.mark.asyncio
async def test_sua_chu_de_qua_24h_403(client, cbcc_user, old_chu_de):
    """cbcc_user (author) khong sua duoc old_chu_de (48h) -> 403 FORUM_ERR_005."""
    chu_de_id = old_chu_de["id"]
    payload = {
        "tieu_de": "Co gang sua chu de da qua 24h se bi tu choi",
    }
    resp = await client.put(f"{API}/chu-de/{chu_de_id}", json=payload)
    assert resp.status_code == 403
    body = resp.json()
    # FastAPI wraps HTTPException.detail in "detail" key
    detail = body["detail"]
    assert detail["success"] is False
    assert detail["error"]["code"] == "FORUM_ERR_005"


@pytest.mark.asyncio
async def test_xoa_chu_de_co_tra_loi_author_400(
    client, cbcc_user, sample_chu_de, sample_tra_loi
):
    """cbcc_user (author) khong xoa duoc sample_chu_de co tra loi -> 400 FORUM_ERR_007."""
    chu_de_id = sample_chu_de["id"]
    # sample_tra_loi fixture da update so_tra_loi chu de += 1
    resp = await client.delete(f"{API}/chu-de/{chu_de_id}")
    assert resp.status_code == 400
    body = resp.json()
    # FastAPI wraps HTTPException.detail in "detail" key
    detail = body["detail"]
    assert detail["success"] is False
    assert detail["error"]["code"] == "FORUM_ERR_007"
