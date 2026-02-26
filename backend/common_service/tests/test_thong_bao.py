"""
common_service/tests/test_thong_bao.py
========================================
Tests cho Notification Center API — 15 tests.

Business rules:
  - CBCC chi thay thong bao cua minh
  - Sap xep: KHAN dau, roi QUAN_TRONG, roi BINH_THUONG, theo created_at DESC
  - Danh dau da doc: chi nguoi nhan, 404 neu khong ton tai, 403 nguoi khac
  - Internal API: X-Internal-Key, validate loai/muc_do
"""

import uuid

import pytest
from httpx import AsyncClient

from common_service.tests.conftest import _REAL_CC_IDS, INTERNAL_KEY

API = "/api/common/v1/thong-bao"
INTERNAL = "/internal/v1/thong-bao"


# ===========================================================================
# Test Danh sach
# ===========================================================================


class TestThongBaoDanhSach:
    """Test danh sach thong bao."""

    async def test_danh_sach_chi_cua_minh(
        self, client: AsyncClient, cbcc_user, sample_thong_bao
    ):
        """CBCC chi thay thong bao cua minh (5 records)."""
        resp = await client.get(API)
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert len(data["data"]) == 5
        assert data["pagination"]["total_items"] == 5

    async def test_danh_sach_loc_chua_doc(
        self, client: AsyncClient, cbcc_user, sample_thong_bao
    ):
        """Filter da_doc=false chi tra thong bao chua doc."""
        resp = await client.get(API, params={"da_doc": False})
        assert resp.status_code == 200
        items = resp.json()["data"]
        assert len(items) == 3  # 3 chua doc
        for item in items:
            assert item["da_doc"] is False

    async def test_danh_sach_loc_theo_loai(
        self, client: AsyncClient, cbcc_user, sample_thong_bao
    ):
        """Filter loai=LMS."""
        resp = await client.get(API, params={"loai": "LMS"})
        assert resp.status_code == 200
        items = resp.json()["data"]
        assert len(items) == 1
        assert items[0]["loai"] == "LMS"

    async def test_danh_sach_loc_theo_muc_do(
        self, client: AsyncClient, cbcc_user, sample_thong_bao
    ):
        """Filter muc_do=KHAN."""
        resp = await client.get(API, params={"muc_do": "KHAN"})
        assert resp.status_code == 200
        items = resp.json()["data"]
        assert len(items) == 1
        assert items[0]["muc_do"] == "KHAN"

    async def test_danh_sach_sap_xep(
        self, client: AsyncClient, cbcc_user, sample_thong_bao
    ):
        """KHAN xep dau tien, roi theo thoi gian."""
        resp = await client.get(API)
        items = resp.json()["data"]
        assert items[0]["muc_do"] == "KHAN"
        # Hai KHAN khong co → check thong bao dau tien la KHAN
        khan_items = [i for i in items if i["muc_do"] == "KHAN"]
        assert len(khan_items) >= 1
        # KHAN truoc BINH_THUONG
        first_bt_idx = next(
            (i for i, item in enumerate(items) if item["muc_do"] == "BINH_THUONG"),
            len(items),
        )
        first_khan_idx = next(
            (i for i, item in enumerate(items) if item["muc_do"] == "KHAN"),
            len(items),
        )
        assert first_khan_idx < first_bt_idx

    async def test_phan_trang(
        self, client: AsyncClient, cbcc_user, sample_thong_bao
    ):
        """Phan trang page=1 (3 items), page=2 (2 items) voi page_size=3."""
        resp1 = await client.get(API, params={"page": 1, "page_size": 3})
        assert resp1.status_code == 200
        data1 = resp1.json()
        assert len(data1["data"]) == 3
        assert data1["pagination"]["total_items"] == 5
        assert data1["pagination"]["total_pages"] == 2

        resp2 = await client.get(API, params={"page": 2, "page_size": 3})
        assert resp2.status_code == 200
        data2 = resp2.json()
        assert len(data2["data"]) == 2


# ===========================================================================
# Test Dem chua doc
# ===========================================================================


class TestThongBaoCount:
    """Test dem thong bao chua doc."""

    async def test_dem_chua_doc(
        self, client: AsyncClient, cbcc_user, sample_thong_bao
    ):
        """Dem dung tong + phan loai muc do."""
        resp = await client.get(f"{API}/count")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["count"] == 3  # 3 chua doc
        assert data["khan"] == 1
        assert data["quan_trong"] == 1
        assert data["binh_thuong"] == 1


# ===========================================================================
# Test Danh dau da doc
# ===========================================================================


class TestThongBaoDanhDauDaDoc:
    """Test danh dau da doc."""

    async def test_danh_dau_da_doc(
        self, client: AsyncClient, cbcc_user, sample_thong_bao
    ):
        """Danh dau da doc thanh cong → da_doc=True, ngay_doc filled."""
        tb_id = sample_thong_bao[0]["id"]  # chua doc
        resp = await client.patch(f"{API}/{tb_id}/doc")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["da_doc"] is True
        assert data["ngay_doc"] is not None

    async def test_danh_dau_da_doc_nguoi_khac(
        self, client: AsyncClient, cbcc_user, sample_thong_bao_nguoi_khac
    ):
        """CBCC khong the danh dau thong bao cua nguoi khac → 403."""
        tb_id = sample_thong_bao_nguoi_khac["id"]
        resp = await client.patch(f"{API}/{tb_id}/doc")
        assert resp.status_code == 403

    async def test_danh_dau_da_doc_khong_ton_tai(
        self, client: AsyncClient, cbcc_user
    ):
        """Thong bao khong ton tai → 404."""
        fake_id = str(uuid.uuid4())
        resp = await client.patch(f"{API}/{fake_id}/doc")
        assert resp.status_code == 404

    async def test_danh_dau_tat_ca(
        self, client: AsyncClient, cbcc_user, sample_thong_bao
    ):
        """Danh dau tat ca chua doc → da doc."""
        resp = await client.patch(f"{API}/doc-tat-ca")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["updated_count"] == 3  # 3 chua doc → da doc

        # Verify: count = 0
        count_resp = await client.get(f"{API}/count")
        assert count_resp.json()["data"]["count"] == 0


# ===========================================================================
# Test Internal API
# ===========================================================================


class TestThongBaoInternal:
    """Test Internal API — tao thong bao."""

    async def test_internal_tao_thong_bao(
        self, client: AsyncClient, db_session
    ):
        """Tao 1 thong bao voi X-Internal-Key hop le."""
        resp = await client.post(
            INTERNAL,
            json={
                "nguoi_nhan_id": _REAL_CC_IDS[0],
                "tieu_de": "Thong bao test internal",
                "loai": "LMS",
                "muc_do": "BINH_THUONG",
            },
            headers={"X-Internal-Key": INTERNAL_KEY},
        )
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["tieu_de"] == "Thong bao test internal"
        assert data["loai"] == "LMS"

    async def test_internal_tao_thong_bao_sai_key(
        self, client: AsyncClient, db_session
    ):
        """X-Internal-Key sai → 401."""
        resp = await client.post(
            INTERNAL,
            json={
                "nguoi_nhan_id": _REAL_CC_IDS[0],
                "tieu_de": "Test sai key",
                "loai": "KPI",
            },
            headers={"X-Internal-Key": "wrong-key"},
        )
        assert resp.status_code == 401

    async def test_internal_tao_bulk(
        self, client: AsyncClient, db_session
    ):
        """Tao hang loat cho nhieu nguoi nhan."""
        resp = await client.post(
            f"{INTERNAL}/bulk",
            json={
                "nguoi_nhan_ids": [_REAL_CC_IDS[0], _REAL_CC_IDS[1], _REAL_CC_IDS[2]],
                "tieu_de": "Thong bao chung bulk",
                "loai": "HE_THONG",
                "muc_do": "QUAN_TRONG",
            },
            headers={"X-Internal-Key": INTERNAL_KEY},
        )
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["created_count"] == 3

    async def test_internal_loai_khong_hop_le(
        self, client: AsyncClient, db_session
    ):
        """Loai khong hop le → 400."""
        resp = await client.post(
            INTERNAL,
            json={
                "nguoi_nhan_id": _REAL_CC_IDS[0],
                "tieu_de": "Loai sai",
                "loai": "INVALID_MODULE",
            },
            headers={"X-Internal-Key": INTERNAL_KEY},
        )
        assert resp.status_code == 400
