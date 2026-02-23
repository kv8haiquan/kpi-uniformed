"""
Tests cho khoa hoc CRUD + Workflow — 12 test cases.
"""

import uuid

import pytest

pytestmark = pytest.mark.asyncio


class TestKhoaHocCRUD:
    """CRUD operations cho khoa hoc."""

    async def test_tao_khoa_hoc(self, client, admin_user):
        """Tao khoa hoc moi — 201 NHAP."""
        resp = await client.post("/api/v1/lms/khoa-hoc", json={
            "ma_khoa_hoc": f"KH-{uuid.uuid4().hex[:6]}",
            "ten_khoa_hoc": "Khóa test",
            "loai": "BAT_BUOC",
        })
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["trang_thai"] == "NHAP"
        assert data["giang_vien_id"] is not None

    async def test_tao_trung_ma(self, client, admin_user, created_khoa_hoc):
        """Tao voi ma da ton tai — 409."""
        resp = await client.post("/api/v1/lms/khoa-hoc", json={
            "ma_khoa_hoc": created_khoa_hoc["ma_khoa_hoc"],
            "ten_khoa_hoc": "Trùng",
        })
        assert resp.status_code == 409

    async def test_danh_sach_cbcc_chi_thay_da_xuat_ban(self, client, cbcc_user, published_khoa_hoc):
        """CBCC thuong chi thay khoa DA_XUAT_BAN."""
        resp = await client.get("/api/v1/lms/khoa-hoc")
        assert resp.status_code == 200
        for item in resp.json()["data"]:
            assert item["trang_thai"] == "DA_XUAT_BAN"

    async def test_danh_sach_quan_ly(self, client, qt_dao_tao_user, created_khoa_hoc):
        """QT_DAO_TAO thay tat ca trang thai qua /quan-ly."""
        resp = await client.get("/api/v1/lms/khoa-hoc/quan-ly")
        assert resp.status_code == 200
        assert resp.json()["pagination"]["total_items"] >= 1

    async def test_chi_tiet(self, client, admin_user, created_khoa_hoc):
        """Chi tiet khoa hoc — 200."""
        resp = await client.get(f"/api/v1/lms/khoa-hoc/{created_khoa_hoc['id']}")
        assert resp.status_code == 200
        assert resp.json()["data"]["id"] == created_khoa_hoc["id"]

    async def test_cap_nhat(self, client, admin_user, created_khoa_hoc):
        """Cap nhat khoa hoc — 200."""
        resp = await client.put(
            f"/api/v1/lms/khoa-hoc/{created_khoa_hoc['id']}",
            json={"ten_khoa_hoc": "Tên cập nhật"},
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["ten_khoa_hoc"] == "Tên cập nhật"

    async def test_xoa_nhap_khong_hoc_vien(self, client, admin_user, created_khoa_hoc):
        """Xoa khoa NHAP, chua co hoc vien — 200."""
        resp = await client.delete(f"/api/v1/lms/khoa-hoc/{created_khoa_hoc['id']}")
        assert resp.status_code == 200


class TestKhoaHocWorkflow:
    """Workflow trang thai khoa hoc."""

    async def test_nhap_cho_duyet_khong_co_bai(self, client, admin_user, created_khoa_hoc):
        """NHAP → CHO_DUYET that bai neu chua co bai hoc."""
        resp = await client.patch(
            f"/api/v1/lms/khoa-hoc/{created_khoa_hoc['id']}/trang-thai",
            json={"trang_thai": "CHO_DUYET"},
        )
        assert resp.status_code == 400
        assert "bài học" in resp.json()["detail"]["error"]["message"]

    async def test_transition_khong_hop_le(self, client, admin_user, created_khoa_hoc):
        """NHAP → DA_XUAT_BAN (skip CHO_DUYET) — 400."""
        resp = await client.patch(
            f"/api/v1/lms/khoa-hoc/{created_khoa_hoc['id']}/trang-thai",
            json={"trang_thai": "DA_XUAT_BAN"},
        )
        assert resp.status_code == 400
        assert "LMS_ERR_010" in resp.json()["detail"]["error"]["code"]

    async def test_workflow_full(self, client, admin_user, created_khoa_hoc):
        """Full: NHAP → (add bai) → CHO_DUYET → DA_XUAT_BAN."""
        kh_id = created_khoa_hoc["id"]

        # Add bai hoc
        bh_resp = await client.post(f"/api/v1/lms/khoa-hoc/{kh_id}/bai-hoc", json={
            "tieu_de": "Bài test workflow",
            "loai_noi_dung": "HTML",
        })
        assert bh_resp.status_code == 201

        # CHO_DUYET
        resp1 = await client.patch(f"/api/v1/lms/khoa-hoc/{kh_id}/trang-thai",
                                   json={"trang_thai": "CHO_DUYET"})
        assert resp1.status_code == 200
        assert resp1.json()["data"]["trang_thai"] == "CHO_DUYET"

        # DA_XUAT_BAN
        resp2 = await client.patch(f"/api/v1/lms/khoa-hoc/{kh_id}/trang-thai",
                                   json={"trang_thai": "DA_XUAT_BAN"})
        assert resp2.status_code == 200
        assert resp2.json()["data"]["trang_thai"] == "DA_XUAT_BAN"
        assert resp2.json()["data"]["nguoi_duyet_id"] is not None

    async def test_tu_choi_can_ghi_chu(self, client, admin_user, created_khoa_hoc):
        """CHO_DUYET → NHAP (tu choi) bat buoc ghi_chu."""
        kh_id = created_khoa_hoc["id"]

        # Setup: add bai + gui duyet
        await client.post(f"/api/v1/lms/khoa-hoc/{kh_id}/bai-hoc", json={
            "tieu_de": "Bài test",
            "loai_noi_dung": "HTML",
        })
        await client.patch(f"/api/v1/lms/khoa-hoc/{kh_id}/trang-thai",
                          json={"trang_thai": "CHO_DUYET"})

        # Tu choi khong co ghi_chu → 400
        resp = await client.patch(f"/api/v1/lms/khoa-hoc/{kh_id}/trang-thai",
                                  json={"trang_thai": "NHAP"})
        assert resp.status_code == 400
        assert "lý do" in resp.json()["detail"]["error"]["message"]

        # Tu choi co ghi_chu → 200
        resp2 = await client.patch(f"/api/v1/lms/khoa-hoc/{kh_id}/trang-thai",
                                   json={"trang_thai": "NHAP", "ghi_chu": "Nội dung chưa đủ"})
        assert resp2.status_code == 200


class TestKhoaHocPhanQuyen:
    """Permission tests cho khoa hoc."""

    async def test_cbcc_khong_tao_duoc(self, client, cbcc_user):
        """CBCC thuong khong co quyen tao khoa hoc — 403."""
        resp = await client.post("/api/v1/lms/khoa-hoc", json={
            "ma_khoa_hoc": "KH-FAIL",
            "ten_khoa_hoc": "Sẽ thất bại",
        })
        assert resp.status_code == 403
