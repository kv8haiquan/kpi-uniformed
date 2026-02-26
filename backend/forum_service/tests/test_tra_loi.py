"""
forum_service/tests/test_tra_loi.py
====================================
Test CRUD tra loi (reply) trong forum.

Endpoint coverage:
  POST   /chu-de/{chu_de_id}/tra-loi  — tao tra loi moi
  PUT    /tra-loi/{tra_loi_id}        — sua tra loi (author only)
  DELETE /tra-loi/{tra_loi_id}        — xoa tra loi (author only)
  PATCH  /tra-loi/{tra_loi_id}/an     — an tra loi (DIEU_PHOI only)
"""

import pytest
from httpx import AsyncClient

from forum_service.tests.conftest import API


# =========================================================================
# TAO TRA LOI (POST /chu-de/{chu_de_id}/tra-loi)
# =========================================================================


@pytest.mark.asyncio
async def test_tao_tra_loi_thanh_cong(client: AsyncClient, user_khac, sample_chu_de):
    """User_khac tao tra loi moi trong sample_chu_de."""
    payload = {"noi_dung": "Tra loi moi test content day du"}
    resp = await client.post(
        f"{API}/chu-de/{sample_chu_de['id']}/tra-loi",
        json=payload,
    )
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert "id" in data
    assert data["chu_de_id"] == sample_chu_de["id"]
    assert data["noi_dung"] == payload["noi_dung"]


@pytest.mark.asyncio
async def test_tra_loi_chu_de_khoa_403(client: AsyncClient, user_khac, khoa_chu_de):
    """User_khac thu tra loi vao chu de bi khoa -> 403 FORUM_ERR_003."""
    payload = {"noi_dung": "Tra loi thu vao chu de da khoa"}
    resp = await client.post(
        f"{API}/chu-de/{khoa_chu_de['id']}/tra-loi",
        json=payload,
    )
    assert resp.status_code == 403
    # FastAPI wraps HTTPException.detail in "detail" key
    detail = resp.json()["detail"]
    assert detail["success"] is False
    assert detail["error"]["code"] == "FORUM_ERR_003"


@pytest.mark.asyncio
async def test_tra_loi_nested_cap_2(
    client: AsyncClient, cbcc_user, sample_tra_loi, sample_chu_de
):
    """Cbcc_user tra loi sample_tra_loi (level 1) -> tao level 2."""
    payload = {
        "noi_dung": "Tra loi nested cap 2 cho tra loi cap 1",
        "parent_id": sample_tra_loi["id"],
    }
    resp = await client.post(
        f"{API}/chu-de/{sample_chu_de['id']}/tra-loi",
        json=payload,
    )
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert data["parent_id"] == sample_tra_loi["id"]


@pytest.mark.asyncio
async def test_tra_loi_nested_flatten_cap_3(
    client: AsyncClient, cbcc_user, nested_tra_loi, sample_tra_loi, sample_chu_de
):
    """Cbcc_user tra loi nested_tra_loi (level 2) -> service flatten ve level 1 parent."""
    payload = {
        "noi_dung": "Tra loi thu cap 3 se bi flatten ve cap 1",
        "parent_id": nested_tra_loi["id"],
    }
    resp = await client.post(
        f"{API}/chu-de/{sample_chu_de['id']}/tra-loi",
        json=payload,
    )
    assert resp.status_code == 201
    data = resp.json()["data"]
    # Service phai flatten parent_id ve level 1 parent (sample_tra_loi)
    assert data["parent_id"] == sample_tra_loi["id"]


# =========================================================================
# SUA TRA LOI (PUT /tra-loi/{tra_loi_id})
# =========================================================================


@pytest.mark.asyncio
async def test_sua_tra_loi_author(client: AsyncClient, user_khac, sample_tra_loi):
    """User_khac (author cua sample_tra_loi) cap nhat tra loi thanh cong."""
    payload = {"noi_dung": "Noi dung da cap nhat day du cho test"}
    resp = await client.put(
        f"{API}/tra-loi/{sample_tra_loi['id']}",
        json=payload,
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["noi_dung"] == payload["noi_dung"]


@pytest.mark.asyncio
async def test_sua_tra_loi_nguoi_khac_403(
    client: AsyncClient, cbcc_user, sample_tra_loi
):
    """Cbcc_user (khong phai author) thu sua sample_tra_loi -> 403."""
    payload = {"noi_dung": "Sua tra loi khong phai cua minh"}
    resp = await client.put(
        f"{API}/tra-loi/{sample_tra_loi['id']}",
        json=payload,
    )
    assert resp.status_code == 403


# =========================================================================
# XOA TRA LOI (DELETE /tra-loi/{tra_loi_id})
# =========================================================================


@pytest.mark.asyncio
async def test_xoa_tra_loi_author(client: AsyncClient, user_khac, sample_tra_loi):
    """User_khac (author) xoa sample_tra_loi thanh cong."""
    resp = await client.delete(f"{API}/tra-loi/{sample_tra_loi['id']}")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_xoa_tra_loi_nguoi_khac_403(
    client: AsyncClient, cbcc_user, sample_tra_loi
):
    """Cbcc_user (khong phai author) thu xoa sample_tra_loi -> 403."""
    resp = await client.delete(f"{API}/tra-loi/{sample_tra_loi['id']}")
    assert resp.status_code == 403


# =========================================================================
# AN TRA LOI (PATCH /tra-loi/{tra_loi_id}/an)
# =========================================================================


@pytest.mark.asyncio
async def test_an_tra_loi_dieu_phoi(
    client: AsyncClient, dieu_phoi_user, sample_tra_loi
):
    """Dieu_phoi_user an sample_tra_loi thanh cong."""
    resp = await client.patch(f"{API}/tra-loi/{sample_tra_loi['id']}/an")
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["message"] == "An tra loi thanh cong"
