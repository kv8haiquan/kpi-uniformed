"""
forum_service/tests/test_theo_doi.py
=====================================
Tests cho theo doi chu de (follow/unfollow).

Endpoints:
  - POST /chu-de/{chu_de_id}/theo-doi
  - DELETE /chu-de/{chu_de_id}/theo-doi
  - GET /theo-doi/cua-toi

Test cases:
  1. theo_doi_thanh_cong — user_khac follows sample_chu_de
  2. auto_theo_doi_khi_tao_chu_de — author auto-follows when creating chu_de
  3. bo_theo_doi — user_khac unfollows after following
  4. danh_sach_theo_doi — user_khac checks list after following
  5. theo_doi_idempotent — calling theo_doi twice returns success both times
  6. bo_theo_doi_chua_theo_doi_404 — unfollow without following returns 404
"""

import pytest

# API constant from conftest
API = "/api/forum/v1"


@pytest.mark.asyncio
async def test_theo_doi_thanh_cong(client, cbcc_user, user_khac, sample_chu_de):
    """user_khac theo doi sample_chu_de thanh cong."""
    # user_khac follows sample_chu_de
    resp = await client.post(f"{API}/chu-de/{sample_chu_de['id']}/theo-doi")
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert "thanh cong" in data["message"].lower() or "theo doi" in data["message"].lower()


@pytest.mark.asyncio
async def test_auto_theo_doi_khi_tao_chu_de(
    client, cbcc_user, sample_chuyen_muc, db_session
):
    """Tac gia tu dong theo doi chu de khi tao moi."""
    # cbcc_user creates a new chu de
    payload = {
        "chuyen_muc_id": sample_chuyen_muc["id"],
        "tieu_de": "Chu de de test auto theo doi",
        "noi_dung": "<p>Noi dung chu de de kiem tra auto theo doi</p>",
        "tags": ["test", "auto-follow"],
    }
    resp = await client.post(f"{API}/chu-de", json=payload)
    assert resp.status_code == 201
    created_id = resp.json()["data"]["id"]

    # Check cbcc_user's theo_doi list contains the created chu_de
    resp = await client.get(f"{API}/theo-doi/cua-toi")
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True

    # Find the created chu_de in the list
    chu_de_ids = [item["id"] for item in data["data"]]
    assert created_id in chu_de_ids, "Tac gia should auto-follow chu de they created"


@pytest.mark.asyncio
async def test_bo_theo_doi(client, cbcc_user, user_khac, sample_chu_de):
    """user_khac theo doi roi bo theo doi sample_chu_de."""
    # First: user_khac follows
    resp = await client.post(f"{API}/chu-de/{sample_chu_de['id']}/theo-doi")
    assert resp.status_code == 200

    # Then: user_khac unfollows
    resp = await client.delete(f"{API}/chu-de/{sample_chu_de['id']}/theo-doi")
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert "bo theo doi" in data["message"].lower() or "huy" in data["message"].lower()


@pytest.mark.asyncio
async def test_danh_sach_theo_doi(client, cbcc_user, user_khac, sample_chu_de):
    """user_khac xem danh sach chu de dang theo doi."""
    # First: user_khac follows sample_chu_de
    resp = await client.post(f"{API}/chu-de/{sample_chu_de['id']}/theo-doi")
    assert resp.status_code == 200

    # Then: user_khac checks list
    resp = await client.get(f"{API}/theo-doi/cua-toi")
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert isinstance(data["data"], list)
    assert len(data["data"]) >= 1, "Should have at least 1 followed chu_de"

    # Verify sample_chu_de is in the list
    chu_de_ids = [item["id"] for item in data["data"]]
    assert sample_chu_de["id"] in chu_de_ids


@pytest.mark.asyncio
async def test_theo_doi_idempotent(client, cbcc_user, user_khac, sample_chu_de):
    """Theo doi 2 lan lien tiep khong gay loi (idempotent)."""
    # First call: theo doi
    resp1 = await client.post(f"{API}/chu-de/{sample_chu_de['id']}/theo-doi")
    assert resp1.status_code == 200
    assert resp1.json()["success"] is True

    # Second call: theo doi again (should still return success)
    resp2 = await client.post(f"{API}/chu-de/{sample_chu_de['id']}/theo-doi")
    assert resp2.status_code == 200
    assert resp2.json()["success"] is True


@pytest.mark.asyncio
async def test_bo_theo_doi_chua_theo_doi_404(client, cbcc_user, user_khac, sample_chu_de):
    """user_khac chua theo doi ma bo theo doi thi tra ve 404."""
    # user_khac hasn't followed sample_chu_de yet, tries to unfollow
    resp = await client.delete(f"{API}/chu-de/{sample_chu_de['id']}/theo-doi")
    assert resp.status_code == 404
    # Service raises HTTPException with nested detail dict
    data = resp.json()
    assert "detail" in data
    # Detail is a dict with success=False and error object
    if isinstance(data["detail"], dict):
        assert data["detail"]["success"] is False
        assert "error" in data["detail"]
        assert "chua theo doi" in data["detail"]["error"]["message"].lower()
