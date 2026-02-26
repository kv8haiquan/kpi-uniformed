"""
forum_service/tests/test_phan_quyen.py
======================================
Tests phan quyen (permissions/authorization) cho module Forum.

11 test cases:
  1. test_cbcc_khong_tao_chuyen_muc — CBCC khong duoc tao chuyen muc
  2. test_dieu_phoi_tao_chuyen_muc — DIEU_PHOI_FORUM tao duoc chuyen muc
  3. test_admin_tao_chuyen_muc — SUPER_ADMIN bypass role check
  4. test_cbcc_khong_ghim_chu_de — CBCC khong ghim duoc chu de
  5. test_dieu_phoi_ghim_chu_de — DIEU_PHOI_FORUM ghim duoc chu de
  6. test_cbcc_khong_dang_chi_doc — CBCC khong dang duoc bai trong chuyen muc chi doc
  7. test_chuyen_gia_dang_chi_doc — CHUYEN_GIA dang duoc bai trong chuyen muc chi doc
  8. test_cbcc_khong_an_tra_loi — CBCC khong an duoc tra loi
  9. test_dieu_phoi_an_tra_loi — DIEU_PHOI_FORUM an duoc tra loi
 10. test_admin_bypass_quyen_ghim — SUPER_ADMIN bypass phan quyen ghim
 11. test_lanh_dao_khong_co_quyen_dieu_phoi — is_lanh_dao khong tu dong co quyen DIEU_PHOI

Pattern:
  - User fixtures tu dong override get_current_user
  - Chi declare fixture can thiet (user + data fixtures neu can)
  - Kiem tra status_code + response body
"""

import pytest
from httpx import AsyncClient

# API constant
API = "/api/forum/v1"


# =========================================================================
# TEST 1-3: QUAN LY CHUYEN MUC (chi DIEU_PHOI/ADMIN)
# =========================================================================


@pytest.mark.asyncio
async def test_cbcc_khong_tao_chuyen_muc(client: AsyncClient, cbcc_user):
    """CBCC thuong khong duoc tao chuyen muc."""
    response = await client.post(
        f"{API}/chuyen-muc",
        json={"ten_chuyen_muc": "Test chuyen muc moi de kiem tra"},
    )
    assert response.status_code == 403
    data = response.json()
    # 403 responses have error nested under "detail"
    assert "detail" in data
    error_data = data["detail"]
    assert error_data["success"] is False
    assert "error" in error_data
    # Expect PERM_001 (role check failed)
    assert error_data["error"]["code"] in ["PERM_001", "PERMISSION_DENIED", "UNAUTHORIZED"]


@pytest.mark.asyncio
async def test_dieu_phoi_tao_chuyen_muc(client: AsyncClient, dieu_phoi_user):
    """DIEU_PHOI_FORUM tao duoc chuyen muc."""
    response = await client.post(
        f"{API}/chuyen-muc",
        json={"ten_chuyen_muc": "Test chuyen muc moi de kiem tra"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert "data" in data
    assert data["data"]["ten_chuyen_muc"] == "Test chuyen muc moi de kiem tra"


@pytest.mark.asyncio
async def test_admin_tao_chuyen_muc(client: AsyncClient, admin_user):
    """SUPER_ADMIN bypass role check, tao duoc chuyen muc."""
    response = await client.post(
        f"{API}/chuyen-muc",
        json={"ten_chuyen_muc": "Test chuyen muc admin de kiem tra"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert "data" in data
    assert data["data"]["ten_chuyen_muc"] == "Test chuyen muc admin de kiem tra"


# =========================================================================
# TEST 4-5: HANH DONG GHIM CHU DE (chi DIEU_PHOI/ADMIN)
# =========================================================================


@pytest.mark.asyncio
async def test_cbcc_khong_ghim_chu_de(
    client: AsyncClient, cbcc_user, sample_chu_de
):
    """CBCC thuong khong duoc ghim chu de."""
    response = await client.patch(
        f"{API}/chu-de/{sample_chu_de['id']}/hanh-dong",
        json={"hanh_dong": "GHIM"},
    )
    assert response.status_code == 403
    data = response.json()
    # 403 responses have error nested under "detail"
    assert "detail" in data
    error_data = data["detail"]
    assert error_data["success"] is False
    assert "error" in error_data
    assert error_data["error"]["code"] in ["PERM_001", "PERMISSION_DENIED", "UNAUTHORIZED"]


@pytest.mark.asyncio
async def test_dieu_phoi_ghim_chu_de(
    client: AsyncClient, dieu_phoi_user, sample_chu_de
):
    """DIEU_PHOI_FORUM ghim duoc chu de."""
    response = await client.patch(
        f"{API}/chu-de/{sample_chu_de['id']}/hanh-dong",
        json={"hanh_dong": "GHIM"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "data" in data
    # Kiem tra is_ghim=True neu endpoint tra ve
    if "is_ghim" in data["data"]:
        assert data["data"]["is_ghim"] is True


# =========================================================================
# TEST 6-7: DANG BAI TRONG CHUYEN MUC CHI DOC (chi CHUYEN_GIA/DIEU_PHOI/ADMIN)
# =========================================================================


@pytest.mark.asyncio
async def test_cbcc_khong_dang_chi_doc(
    client: AsyncClient, cbcc_user, chi_doc_chuyen_muc
):
    """CBCC thuong khong duoc dang bai trong chuyen muc chi doc."""
    response = await client.post(
        f"{API}/chu-de",
        json={
            "chuyen_muc_id": chi_doc_chuyen_muc["id"],
            "tieu_de": "Bai viet test trong chuyen muc chi doc",
            "noi_dung": "Noi dung bai viet test dai it nhat 30 ky tu de pass validation",
            "tags": ["test"],
        },
    )
    assert response.status_code == 403
    data = response.json()
    # 403 responses have error nested under "detail"
    assert "detail" in data
    error_data = data["detail"]
    assert error_data["success"] is False
    assert "error" in error_data
    # FORUM_ERR_004 = chi doc chuyen muc check
    assert error_data["error"]["code"] in ["PERM_001", "FORUM_ERR_004", "PERMISSION_DENIED", "UNAUTHORIZED"]


@pytest.mark.asyncio
async def test_chuyen_gia_dang_chi_doc(
    client: AsyncClient, chuyen_gia_user, chi_doc_chuyen_muc
):
    """CHUYEN_GIA dang duoc bai trong chuyen muc chi doc."""
    response = await client.post(
        f"{API}/chu-de",
        json={
            "chuyen_muc_id": chi_doc_chuyen_muc["id"],
            "tieu_de": "Bai viet chuyen gia trong chuyen muc chi doc",
            "noi_dung": "Noi dung bai viet chuyen gia test dai it nhat 30 ky tu de pass",
            "tags": ["chuyengia"],
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert "data" in data
    assert data["data"]["tieu_de"] == "Bai viet chuyen gia trong chuyen muc chi doc"


# =========================================================================
# TEST 8-9: AN TRA LOI (chi DIEU_PHOI/ADMIN)
# =========================================================================


@pytest.mark.asyncio
async def test_cbcc_khong_an_tra_loi(
    client: AsyncClient, cbcc_user, sample_tra_loi
):
    """CBCC thuong khong duoc an tra loi."""
    response = await client.patch(
        f"{API}/tra-loi/{sample_tra_loi['id']}/an",
    )
    assert response.status_code == 403
    data = response.json()
    # 403 responses have error nested under "detail"
    assert "detail" in data
    error_data = data["detail"]
    assert error_data["success"] is False
    assert "error" in error_data
    assert error_data["error"]["code"] in ["PERM_001", "PERMISSION_DENIED", "UNAUTHORIZED"]


@pytest.mark.asyncio
async def test_dieu_phoi_an_tra_loi(
    client: AsyncClient, dieu_phoi_user, sample_tra_loi
):
    """DIEU_PHOI_FORUM an duoc tra loi."""
    response = await client.patch(
        f"{API}/tra-loi/{sample_tra_loi['id']}/an",
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    # Endpoint tra ve data: None
    assert "message" in data


# =========================================================================
# TEST 10-11: EDGE CASES VE PHAN QUYEN
# =========================================================================


@pytest.mark.asyncio
async def test_admin_bypass_quyen_ghim(
    client: AsyncClient, admin_user, sample_chu_de
):
    """SUPER_ADMIN bypass kiem tra platform_roles, ghim duoc chu de."""
    response = await client.patch(
        f"{API}/chu-de/{sample_chu_de['id']}/hanh-dong",
        json={"hanh_dong": "GHIM"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "data" in data


@pytest.mark.asyncio
async def test_lanh_dao_khong_co_quyen_dieu_phoi(
    client: AsyncClient, lanh_dao_user, sample_chu_de
):
    """is_lanh_dao=True khong tu dong co quyen DIEU_PHOI_FORUM."""
    response = await client.patch(
        f"{API}/chu-de/{sample_chu_de['id']}/hanh-dong",
        json={"hanh_dong": "GHIM"},
    )
    assert response.status_code == 403
    data = response.json()
    # 403 responses have error nested under "detail"
    assert "detail" in data
    error_data = data["detail"]
    assert error_data["success"] is False
    assert "error" in error_data
    assert error_data["error"]["code"] in ["PERM_001", "PERMISSION_DENIED", "UNAUTHORIZED"]
