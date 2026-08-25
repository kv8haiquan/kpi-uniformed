"""
Tests cho chung chi + khao sat — 6 test cases.
"""

import uuid

import pytest

from lms_service.main import app
from lms_service.dependencies import get_current_user
from lms_service.tests.conftest import _make_user, _set_user, dang_ky_va_duyet


pytestmark = pytest.mark.asyncio


async def _setup_completed(client) -> dict:
    """Helper: khoa DA_XUAT_BAN + cbcc dang ky + hoan thanh."""
    # Admin tao khoa
    kh = await client.post("/api/v1/lms/khoa-hoc", json={
        "ma_khoa_hoc": f"KH-CC-{uuid.uuid4().hex[:6]}",
        "ten_khoa_hoc": "Chứng chỉ test", "loai": "TU_HOC",
    })
    kh_id = kh.json()["data"]["id"]
    bh = await client.post(f"/api/v1/lms/khoa-hoc/{kh_id}/bai-hoc", json={
        "tieu_de": "Bai 1", "loai_noi_dung": "HTML",
    })
    bh_id = bh.json()["data"]["id"]
    await client.patch(f"/api/v1/lms/khoa-hoc/{kh_id}/trang-thai", json={"trang_thai": "CHO_DUYET"})
    await client.patch(f"/api/v1/lms/khoa-hoc/{kh_id}/trang-thai", json={"trang_thai": "DA_XUAT_BAN"})

    # Switch sang cbcc, dang ky + hoan thanh
    cbcc = _make_user("CHUYEN_VIEN", [], idx=4)
    await dang_ky_va_duyet(client, kh_id, cbcc)
    await client.patch(f"/api/v1/lms/bai-hoc/{bh_id}/tien-do", json={
        "thoi_gian_xem_giay": 600, "hoan_thanh": True,
    })
    return {"kh_id": kh_id, "bh_id": bh_id, "cbcc": cbcc}


class TestAutoChungChi:

    async def test_tu_dong_cap_khi_hoan_thanh(self, client, admin_user):
        """Full: dang ky → hoan thanh → chung chi tu tao."""
        setup = await _setup_completed(client)
        # Verify chung chi cua toi (van la cbcc user)
        resp = await client.get("/api/v1/lms/chung-chi/cua-toi")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data) >= 1
        assert data[0]["ma_chung_chi"].startswith("CC-")

    async def test_xac_minh_public(self, client, admin_user):
        """Xac minh KHONG can auth."""
        setup = await _setup_completed(client)
        # Lay ma chung chi
        resp = await client.get("/api/v1/lms/chung-chi/cua-toi")
        ma = resp.json()["data"][0]["ma_chung_chi"]
        # Clear user override — xac minh la public
        app.dependency_overrides.pop(get_current_user, None)
        resp2 = await client.get(f"/api/v1/lms/chung-chi/xac-minh/{ma}")
        assert resp2.status_code == 200
        assert resp2.json()["data"]["ma_chung_chi"] == ma

    async def test_xac_minh_ma_sai(self, client):
        """Ma khong ton tai → 404."""
        resp = await client.get("/api/v1/lms/chung-chi/xac-minh/CC-INVALID-000000")
        assert resp.status_code == 404


class TestKhaoSat:

    async def test_gui_khao_sat_sau_hoan_thanh(self, client, admin_user):
        """Hoan thanh → gui khao sat OK."""
        setup = await _setup_completed(client)
        resp = await client.post("/api/v1/lms/khao-sat", json={
            "khoa_hoc_id": setup["kh_id"],
            "noi_dung": {"chat_luong": 5, "nhan_xet": "Tot"},
        })
        assert resp.status_code == 201

    async def test_gui_khao_sat_chua_hoan_thanh(self, client, admin_user):
        """Chua hoan thanh → 400."""
        kh = await client.post("/api/v1/lms/khoa-hoc", json={
            "ma_khoa_hoc": f"KH-KS-{uuid.uuid4().hex[:6]}",
            "ten_khoa_hoc": "KS test", "loai": "TU_HOC",
        })
        kh_id = kh.json()["data"]["id"]
        cbcc = _make_user("CHUYEN_VIEN", [], idx=4)
        _set_user(cbcc)
        resp = await client.post("/api/v1/lms/khao-sat", json={
            "khoa_hoc_id": kh_id, "noi_dung": {"rating": 5},
        })
        assert resp.status_code == 400

    async def test_thong_ke_khao_sat(self, client, admin_user):
        """Thong ke khao sat."""
        setup = await _setup_completed(client)
        # Gui khao sat (van la cbcc)
        await client.post("/api/v1/lms/khao-sat", json={
            "khoa_hoc_id": setup["kh_id"], "noi_dung": {"rating": 4},
        })
        # Switch ve admin xem thong ke
        admin = _make_user("SUPER_ADMIN", ["QT_DAO_TAO"], idx=0)
        _set_user(admin)
        resp = await client.get(f"/api/v1/lms/khoa-hoc/{setup['kh_id']}/khao-sat/thong-ke")
        assert resp.status_code == 200
        assert resp.json()["data"]["tong_khao_sat"] >= 1
