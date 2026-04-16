"""
Tests cho dang ky khoa hoc — 8 test cases.
"""

import uuid
from unittest.mock import AsyncMock, patch

import pytest
from lms_service.main import app
from lms_service.dependencies import get_current_user
from lms_service.tests.conftest import _make_user, _set_user, _REAL_CC_IDS


pytestmark = pytest.mark.asyncio


async def _setup_published(client):
    """Helper: tao khoa DA_XUAT_BAN (admin da set truoc)."""
    kh = await client.post("/api/v1/lms/khoa-hoc", json={
        "ma_khoa_hoc": f"KH-DK-{uuid.uuid4().hex[:6]}",
        "ten_khoa_hoc": "Khóa đăng ký test",
        "loai": "TU_HOC",
    })
    kh_id = kh.json()["data"]["id"]
    await client.post(f"/api/v1/lms/khoa-hoc/{kh_id}/bai-hoc", json={
        "tieu_de": "Bài 1", "loai_noi_dung": "HTML",
    })
    await client.patch(f"/api/v1/lms/khoa-hoc/{kh_id}/trang-thai", json={"trang_thai": "CHO_DUYET"})
    await client.patch(f"/api/v1/lms/khoa-hoc/{kh_id}/trang-thai", json={"trang_thai": "DA_XUAT_BAN"})
    return kh_id


class TestDangKyTuNguyen:

    async def test_dang_ky_thanh_cong(self, client, admin_user):
        """Dang ky tu nguyen — 201."""
        kh_id = await _setup_published(client)
        # Switch sang cbcc
        cbcc = _make_user("CHUYEN_VIEN", [], idx=4)
        _set_user(cbcc)

        resp = await client.post(f"/api/v1/lms/khoa-hoc/{kh_id}/dang-ky")
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["loai_dang_ky"] == "TU_NGUYEN"
        assert data["trang_thai"] == "CHUA_BAT_DAU"

    async def test_dang_ky_trung(self, client, admin_user):
        """Dang ky lan 2 — 409."""
        kh_id = await _setup_published(client)
        cbcc = _make_user("CHUYEN_VIEN", [], idx=4)
        _set_user(cbcc)
        await client.post(f"/api/v1/lms/khoa-hoc/{kh_id}/dang-ky")
        resp = await client.post(f"/api/v1/lms/khoa-hoc/{kh_id}/dang-ky")
        assert resp.status_code == 409

    async def test_dang_ky_khoa_chua_xuat_ban(self, client, admin_user, created_khoa_hoc):
        """Dang ky khoa NHAP — 400."""
        cbcc = _make_user("CHUYEN_VIEN", [], idx=4)
        _set_user(cbcc)
        resp = await client.post(f"/api/v1/lms/khoa-hoc/{created_khoa_hoc['id']}/dang-ky")
        assert resp.status_code == 400


class TestGiaoBai:

    @patch("lms_service.services.dang_ky_service.gui_thong_bao_bulk", new_callable=AsyncMock)
    async def test_giao_bai_batch(self, mock_notify, client, admin_user):
        """Giao cho list cong_chuc_ids."""
        kh_id = await _setup_published(client)
        resp = await client.post(f"/api/v1/lms/khoa-hoc/{kh_id}/giao-bai", json={
            "cong_chuc_ids": _REAL_CC_IDS[1:4],
            "loai_dang_ky": "BAT_BUOC",
        })
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["da_giao"] == 3
        assert data["da_co"] == 0
        # Verify notification was called
        assert mock_notify.called

    @patch("lms_service.services.dang_ky_service.gui_thong_bao_bulk", new_callable=AsyncMock)
    async def test_giao_bai_skip_duplicate(self, mock_notify, client, admin_user):
        """Giao lai — skip da co."""
        kh_id = await _setup_published(client)
        await client.post(f"/api/v1/lms/khoa-hoc/{kh_id}/giao-bai", json={
            "cong_chuc_ids": [_REAL_CC_IDS[1]],
            "loai_dang_ky": "BAT_BUOC",
        })
        mock_notify.reset_mock()  # Reset mock for second call
        resp = await client.post(f"/api/v1/lms/khoa-hoc/{kh_id}/giao-bai", json={
            "cong_chuc_ids": [_REAL_CC_IDS[1]],
            "loai_dang_ky": "BAT_BUOC",
        })
        assert resp.json()["data"]["da_giao"] == 0
        assert resp.json()["data"]["da_co"] == 1
        # Verify notification was NOT called (no newly assigned)
        assert not mock_notify.called


class TestHuyDangKy:

    async def test_huy_tu_nguyen_chua_bat_dau(self, client, admin_user):
        """TU_NGUYEN + CHUA_BAT_DAU → huy OK."""
        kh_id = await _setup_published(client)
        cbcc = _make_user("CHUYEN_VIEN", [], idx=4)
        _set_user(cbcc)
        await client.post(f"/api/v1/lms/khoa-hoc/{kh_id}/dang-ky")
        resp = await client.delete(f"/api/v1/lms/khoa-hoc/{kh_id}/dang-ky")
        assert resp.status_code == 200


class TestCuaToi:

    async def test_khoa_hoc_cua_toi(self, client, admin_user):
        """Dang ky → GET cua-toi thay khoa."""
        kh_id = await _setup_published(client)
        cbcc = _make_user("CHUYEN_VIEN", [], idx=4)
        _set_user(cbcc)
        await client.post(f"/api/v1/lms/khoa-hoc/{kh_id}/dang-ky")
        resp = await client.get("/api/v1/lms/dang-ky/cua-toi")
        assert resp.status_code == 200
        assert len(resp.json()["data"]) >= 1
