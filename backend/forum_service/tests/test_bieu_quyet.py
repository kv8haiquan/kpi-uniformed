"""
forum_service/tests/test_bieu_quyet.py
=======================================
Test vote/unvote chu de va tra loi.

ENDPOINTS:
  POST /bieu-quyet       — vote with toggle logic
  DELETE /bieu-quyet     — xoa vote

VOTE LOGIC:
  1. No existing vote → INSERT, CREATED, so_upvote +1 (UP) or -1 (DOWN)
  2. Same type → DELETE (toggle off), TOGGLED_OFF, reverse so_upvote
  3. Different type → UPDATE loai, CHANGED, so_upvote ±2

CONSTRAINT: User cannot vote on their own content (FORUM_ERR_011)
"""

import pytest

API = "/api/forum/v1"


class TestBieuQuyet:
    """Test vote functionality voi toggle logic."""

    @pytest.mark.asyncio
    async def test_upvote_chu_de(
        self, client, db_session, user_khac, sample_chu_de, sample_chuyen_muc
    ):
        """user_khac (NOT author) upvotes sample_chu_de.

        Expected: CREATED, loai=UP, so_upvote_moi=1
        """
        payload = {
            "doi_tuong_type": "CHU_DE",
            "doi_tuong_id": sample_chu_de["id"],
            "loai": "UP",
        }
        resp = await client.post(f"{API}/bieu-quyet", json=payload)
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["hanh_dong"] == "CREATED"
        assert data["data"]["loai"] == "UP"
        assert data["data"]["so_upvote_moi"] == 1

    @pytest.mark.asyncio
    async def test_toggle_upvote(
        self, client, db_session, user_khac, sample_chu_de, sample_chuyen_muc
    ):
        """user_khac upvotes sample_chu_de TWICE (same loai=UP → toggle off).

        First POST → CREATED, so_upvote_moi=1
        Second POST with same data → TOGGLED_OFF, loai=null, so_upvote_moi=0
        """
        payload = {
            "doi_tuong_type": "CHU_DE",
            "doi_tuong_id": sample_chu_de["id"],
            "loai": "UP",
        }

        # First vote
        resp1 = await client.post(f"{API}/bieu-quyet", json=payload)
        assert resp1.status_code == 200
        data1 = resp1.json()
        assert data1["data"]["hanh_dong"] == "CREATED"
        assert data1["data"]["loai"] == "UP"
        assert data1["data"]["so_upvote_moi"] == 1

        # Second vote (toggle off)
        resp2 = await client.post(f"{API}/bieu-quyet", json=payload)
        assert resp2.status_code == 200
        data2 = resp2.json()
        assert data2["data"]["hanh_dong"] == "TOGGLED_OFF"
        assert data2["data"]["loai"] is None
        assert data2["data"]["so_upvote_moi"] == 0

    @pytest.mark.asyncio
    async def test_doi_vote_up_sang_down(
        self, client, db_session, user_khac, sample_chu_de, sample_chuyen_muc
    ):
        """user_khac upvotes then changes to downvote.

        First POST loai="UP" → CREATED, so_upvote_moi=1
        Second POST loai="DOWN" → CHANGED, loai="DOWN", so_upvote_moi=-1 (delta=-2)
        """
        # First: upvote
        payload_up = {
            "doi_tuong_type": "CHU_DE",
            "doi_tuong_id": sample_chu_de["id"],
            "loai": "UP",
        }
        resp1 = await client.post(f"{API}/bieu-quyet", json=payload_up)
        assert resp1.status_code == 200
        data1 = resp1.json()
        assert data1["data"]["hanh_dong"] == "CREATED"
        assert data1["data"]["loai"] == "UP"
        assert data1["data"]["so_upvote_moi"] == 1

        # Second: change to downvote
        payload_down = {
            "doi_tuong_type": "CHU_DE",
            "doi_tuong_id": sample_chu_de["id"],
            "loai": "DOWN",
        }
        resp2 = await client.post(f"{API}/bieu-quyet", json=payload_down)
        assert resp2.status_code == 200
        data2 = resp2.json()
        assert data2["data"]["hanh_dong"] == "CHANGED"
        assert data2["data"]["loai"] == "DOWN"
        assert data2["data"]["so_upvote_moi"] == -1

    @pytest.mark.asyncio
    async def test_downvote_tra_loi(
        self, client, db_session, cbcc_user, sample_tra_loi, sample_chu_de
    ):
        """cbcc_user (idx=0, NOT author of sample_tra_loi by idx=5) downvotes sample_tra_loi.

        Expected: CREATED, loai=DOWN, so_upvote_moi=-1
        """
        payload = {
            "doi_tuong_type": "TRA_LOI",
            "doi_tuong_id": sample_tra_loi["id"],
            "loai": "DOWN",
        }
        resp = await client.post(f"{API}/bieu-quyet", json=payload)
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["hanh_dong"] == "CREATED"
        assert data["data"]["loai"] == "DOWN"
        assert data["data"]["so_upvote_moi"] == -1

    @pytest.mark.asyncio
    async def test_khong_vote_chinh_minh(
        self, client, db_session, cbcc_user, sample_chu_de, sample_chuyen_muc
    ):
        """cbcc_user (idx=0, author of sample_chu_de) tries to vote on sample_chu_de → 400 FORUM_ERR_011.

        Constraint: User cannot vote on their own content.
        """
        payload = {
            "doi_tuong_type": "CHU_DE",
            "doi_tuong_id": sample_chu_de["id"],
            "loai": "UP",
        }
        resp = await client.post(f"{API}/bieu-quyet", json=payload)
        assert resp.status_code == 400, resp.text
        data = resp.json()
        # HTTPException wraps detail dict in "detail" key
        assert "detail" in data
        detail = data["detail"]
        assert detail["success"] is False
        assert detail["error"]["code"] == "FORUM_ERR_011"

    @pytest.mark.asyncio
    async def test_xoa_vote(
        self, client, db_session, user_khac, sample_chu_de, sample_chuyen_muc
    ):
        """user_khac upvotes sample_chu_de, then xoa vote via DELETE.

        First POST loai="UP" → CREATED
        Then DELETE /bieu-quyet → 200, success message
        """
        # First: create vote
        payload_create = {
            "doi_tuong_type": "CHU_DE",
            "doi_tuong_id": sample_chu_de["id"],
            "loai": "UP",
        }
        resp1 = await client.post(f"{API}/bieu-quyet", json=payload_create)
        assert resp1.status_code == 200
        data1 = resp1.json()
        assert data1["data"]["hanh_dong"] == "CREATED"
        assert data1["data"]["so_upvote_moi"] == 1

        # Second: delete vote
        payload_delete = {
            "doi_tuong_type": "CHU_DE",
            "doi_tuong_id": sample_chu_de["id"],
        }
        resp2 = await client.request("DELETE", f"{API}/bieu-quyet", json=payload_delete)
        assert resp2.status_code == 200, resp2.text
        data2 = resp2.json()
        assert data2["success"] is True
        assert "xoa vote" in data2["message"].lower()
