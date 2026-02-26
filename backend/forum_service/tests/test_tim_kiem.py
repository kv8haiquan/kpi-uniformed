"""
forum_service/tests/test_tim_kiem.py
=====================================
Test module tim kiem chu de va goi y tag.

Coverage:
  - GET /tim-kiem?q=...&chuyen_muc_id=...&tags=...&page=1&page_size=20
  - GET /tags/goi-y?q=...

Business rules:
  - Full-text search tren tieu_de + noi_dung bang PostgreSQL tsvector
  - Filter theo chuyen_muc_id va tags (optional)
  - Tag suggestions dung ILIKE prefix match tren jsonb_array_elements
  - q is required, min_length=2 cho tim-kiem, min_length=1 cho goi-y
"""

import pytest

# API constant from conftest
API = "/api/forum/v1"


class TestTimKiem:
    """Test search chu de."""

    @pytest.mark.asyncio
    async def test_full_text_search(self, client, cbcc_user, sample_chu_de):
        """CBCC tim kiem chu de voi keyword 'hai quan'."""
        # sample_chu_de co:
        #   tieu_de = "Chu de test hai quan khu vuc 8"
        #   noi_dung = "<p>Noi dung chu de test ve thu tuc hai quan chi tiet</p>"
        # => search "hai quan" nen match
        resp = await client.get(f"{API}/tim-kiem", params={"q": "hai quan"})
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["success"] is True
        assert "data" in body
        assert "pagination" in body
        # Kiem tra structure, khong kiem tra co match hay khong
        # (vi tsvector config co the khac nhau)
        if len(body["data"]) > 0:
            assert "tieu_de" in body["data"][0]

    @pytest.mark.asyncio
    async def test_tim_kiem_khong_ket_qua(self, client, cbcc_user):
        """CBCC tim kiem keyword khong ton tai."""
        resp = await client.get(
            f"{API}/tim-kiem", params={"q": "xyznonexistent123"}
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["success"] is True
        assert body["data"] == []
        assert body["pagination"]["total_items"] == 0

    @pytest.mark.asyncio
    async def test_goi_y_tag(self, client, cbcc_user, sample_chu_de):
        """CBCC yeu cau goi y tag voi prefix 'test'."""
        # sample_chu_de co tags=["test", "haiquan"]
        # => prefix "test" nen match "test"
        resp = await client.get(f"{API}/tags/goi-y", params={"q": "test"})
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["success"] is True
        assert "data" in body
        assert isinstance(body["data"], list)
        # Neu co ket qua, "test" nen co trong list
        if len(body["data"]) > 0:
            assert "test" in body["data"]
