"""
Tests cho CRUD chuyen de — 9 test cases.
"""

import uuid

import pytest

pytestmark = pytest.mark.asyncio


class TestChuyenDeCRUD:
    """CRUD operations cho chuyen de."""

    async def test_tao_thanh_cong(self, client, admin_user):
        """Tao chuyen de moi — 201."""
        ma = f"CD-{uuid.uuid4().hex[:6]}"
        resp = await client.post("/api/v1/lms/chuyen-de", json={
            "ma_chuyen_de": ma,
            "ten_chuyen_de": "Test tạo chuyên đề",
            "mo_ta": "Mô tả",
            "thu_tu": 1,
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["ma_chuyen_de"] == ma
        assert data["data"]["ten_chuyen_de"] == "Test tạo chuyên đề"

    async def test_tao_trung_ma(self, client, admin_user, created_chuyen_de):
        """Tao voi ma da ton tai — 409."""
        resp = await client.post("/api/v1/lms/chuyen-de", json={
            "ma_chuyen_de": created_chuyen_de["ma_chuyen_de"],
            "ten_chuyen_de": "Trùng mã",
        })
        assert resp.status_code == 409

    async def test_danh_sach(self, client, cbcc_user, created_chuyen_de):
        """Lay danh sach — 200, co it nhat 1 item."""
        resp = await client.get("/api/v1/lms/chuyen-de")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert len(data["data"]) >= 1

    async def test_danh_sach_filter_active(self, client, cbcc_user, created_chuyen_de):
        """Filter is_active=true."""
        resp = await client.get("/api/v1/lms/chuyen-de?is_active=true")
        assert resp.status_code == 200
        for item in resp.json()["data"]:
            assert item["is_active"] is True

    async def test_chi_tiet(self, client, cbcc_user, created_chuyen_de):
        """Chi tiet — 200."""
        resp = await client.get(f"/api/v1/lms/chuyen-de/{created_chuyen_de['id']}")
        assert resp.status_code == 200
        assert resp.json()["data"]["id"] == created_chuyen_de["id"]

    async def test_chi_tiet_404(self, client, cbcc_user):
        """Chi tiet khong ton tai — 404."""
        resp = await client.get(f"/api/v1/lms/chuyen-de/{uuid.uuid4()}")
        assert resp.status_code == 404

    async def test_cap_nhat(self, client, admin_user, created_chuyen_de):
        """Cap nhat ten — 200."""
        resp = await client.put(
            f"/api/v1/lms/chuyen-de/{created_chuyen_de['id']}",
            json={"ten_chuyen_de": "Tên đã cập nhật"},
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["ten_chuyen_de"] == "Tên đã cập nhật"

    async def test_xoa_soft_delete(self, client, admin_user, created_chuyen_de):
        """Xoa (soft delete) — 200."""
        resp = await client.delete(f"/api/v1/lms/chuyen-de/{created_chuyen_de['id']}")
        assert resp.status_code == 200
        assert resp.json()["data"] is None


class TestChuyenDePhanQuyen:
    """Permission tests cho chuyen de."""

    async def test_cbcc_khong_tao_duoc(self, client, cbcc_user):
        """CBCC thuong khong co quyen tao — 403."""
        resp = await client.post("/api/v1/lms/chuyen-de", json={
            "ma_chuyen_de": "CD-FAIL",
            "ten_chuyen_de": "Sẽ thất bại",
        })
        assert resp.status_code == 403

    async def test_giang_vien_khong_tao_duoc(self, client, giang_vien_user):
        """GIANG_VIEN khong co quyen tao chuyen de (chi QT_DAO_TAO) — 403."""
        resp = await client.post("/api/v1/lms/chuyen-de", json={
            "ma_chuyen_de": "CD-FAIL2",
            "ten_chuyen_de": "Sẽ thất bại",
        })
        assert resp.status_code == 403

    async def test_cbcc_xem_duoc(self, client, cbcc_user, created_chuyen_de):
        """CBCC thuong co quyen xem danh sach — 200."""
        resp = await client.get("/api/v1/lms/chuyen-de")
        assert resp.status_code == 200
