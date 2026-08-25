"""
Tests cho bao cao + dashboard — 5 test cases.
"""

import uuid

import pytest

from lms_service.main import app
from lms_service.dependencies import get_current_user
from lms_service.tests.conftest import _make_user, _set_user, dang_ky_va_duyet


pytestmark = pytest.mark.asyncio


async def _setup_completed_for_report(client) -> dict:
    """Helper: khoa hoan thanh + chung chi."""
    kh = await client.post("/api/v1/lms/khoa-hoc", json={
        "ma_khoa_hoc": f"KH-BC-{uuid.uuid4().hex[:6]}",
        "ten_khoa_hoc": "Report test", "loai": "TU_HOC",
    })
    kh_id = kh.json()["data"]["id"]
    bh = await client.post(f"/api/v1/lms/khoa-hoc/{kh_id}/bai-hoc", json={
        "tieu_de": "Bai 1", "loai_noi_dung": "HTML",
    })
    bh_id = bh.json()["data"]["id"]
    await client.patch(f"/api/v1/lms/khoa-hoc/{kh_id}/trang-thai", json={"trang_thai": "CHO_DUYET"})
    await client.patch(f"/api/v1/lms/khoa-hoc/{kh_id}/trang-thai", json={"trang_thai": "DA_XUAT_BAN"})

    cbcc = _make_user("CHUYEN_VIEN", [], idx=4)
    await dang_ky_va_duyet(client, kh_id, cbcc)
    await client.patch(f"/api/v1/lms/bai-hoc/{bh_id}/tien-do", json={
        "thoi_gian_xem_giay": 3600, "hoan_thanh": True,
    })
    return {"kh_id": kh_id, "cbcc": cbcc}


class TestBaoCaoCaNhan:

    async def test_bao_cao_ca_nhan(self, client, admin_user):
        """Bao cao sau khi hoan thanh 1 khoa."""
        setup = await _setup_completed_for_report(client)
        # Van la cbcc sau _setup
        resp = await client.get("/api/v1/lms/bao-cao/ca-nhan")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["khoa_hoan_thanh"] >= 1
        assert data["tong_chung_chi"] >= 1
        assert data["tong_gio_hoc"] >= 1


class TestBaoCaoDonVi:

    async def test_admin_xem_don_vi(self, client, admin_user):
        """Admin xem bao cao don vi."""
        resp = await client.get("/api/v1/lms/bao-cao/don-vi/a0000000-0000-0000-0000-000000000001")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "tong_cbcc" in data
        assert "ti_le_hoan_thanh" in data

    async def test_cbcc_khong_xem_don_vi(self, client, cbcc_user):
        """CBCC thuong → 403."""
        resp = await client.get("/api/v1/lms/bao-cao/don-vi/a0000000-0000-0000-0000-000000000001")
        assert resp.status_code == 403


class TestBaoCaoKhoaHoc:

    async def test_bao_cao_khoa_hoc(self, client, admin_user):
        """QT xem bao cao khoa hoc."""
        setup = await _setup_completed_for_report(client)
        admin = _make_user("SUPER_ADMIN", ["QT_DAO_TAO"], idx=0)
        _set_user(admin)
        resp = await client.get(f"/api/v1/lms/bao-cao/khoa-hoc/{setup['kh_id']}")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["tong_dang_ky"] >= 1
        assert "phan_bo_trang_thai" in data


class TestDashboard:

    async def test_dashboard_summary(self, client, cbcc_user):
        """Dashboard tra dung cau truc."""
        resp = await client.get("/api/v1/lms/dashboard/summary")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "khoa_dang_hoc" in data
        assert "khoa_sap_het_han" in data
        assert "chung_chi_moi" in data
