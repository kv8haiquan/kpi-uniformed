"""
Tests cho cau hoi + bai kiem tra + luong thi — 10 test cases.
"""

import uuid

import pytest
import pytest_asyncio
from httpx import AsyncClient

from lms_service.main import app
from lms_service.dependencies import get_current_user
from lms_service.tests.conftest import _make_user, _set_user, _REAL_CC_IDS


pytestmark = pytest.mark.asyncio


async def _setup_exam(client) -> dict:
    """Helper: tao full setup cho thi (admin da set truoc).
    Returns dict voi khoa_hoc_id, bkt_id, cau_hoi_ids, bai_hoc_id.
    """
    # Khoa hoc
    kh = await client.post("/api/v1/lms/khoa-hoc", json={
        "ma_khoa_hoc": f"KH-EX-{uuid.uuid4().hex[:6]}",
        "ten_khoa_hoc": "Exam test", "loai": "BAT_BUOC",
    })
    kh_id = kh.json()["data"]["id"]

    # Bai hoc
    bh = await client.post(f"/api/v1/lms/khoa-hoc/{kh_id}/bai-hoc", json={
        "tieu_de": "Bai 1", "loai_noi_dung": "HTML",
    })
    bh_id = bh.json()["data"]["id"]

    # Xuat ban
    await client.patch(f"/api/v1/lms/khoa-hoc/{kh_id}/trang-thai", json={"trang_thai": "CHO_DUYET"})
    await client.patch(f"/api/v1/lms/khoa-hoc/{kh_id}/trang-thai", json={"trang_thai": "DA_XUAT_BAN"})

    # 3 cau hoi
    ch1 = await client.post("/api/v1/lms/cau-hoi", json={
        "khoa_hoc_id": kh_id, "noi_dung": "Cau TN1?", "loai": "TRAC_NGHIEM_1",
        "dap_an": {"lua_chon": [{"key": "A", "noi_dung": "Sai"}, {"key": "B", "noi_dung": "Dung"}], "dap_an_dung": "B"},
        "diem": 2,
    })
    ch2 = await client.post("/api/v1/lms/cau-hoi", json={
        "khoa_hoc_id": kh_id, "noi_dung": "Dung hay sai?", "loai": "DUNG_SAI",
        "dap_an": {"dap_an_dung": True}, "diem": 1,
    })
    ch3 = await client.post("/api/v1/lms/cau-hoi", json={
        "khoa_hoc_id": kh_id, "noi_dung": "Tu luan?", "loai": "TU_LUAN",
        "dap_an": {"huong_dan_cham": "3 y"}, "diem": 5,
    })
    ch_ids = [ch1.json()["data"]["id"], ch2.json()["data"]["id"], ch3.json()["data"]["id"]]

    # BKT
    bkt = await client.post(f"/api/v1/lms/khoa-hoc/{kh_id}/bai-kiem-tra", json={
        "khoa_hoc_id": kh_id, "tieu_de": "BKT test",
        "diem_dat": 30, "tron_de": False, "tron_dap_an": False,
        "cau_hoi_ids": ch_ids,
    })
    bkt_id = bkt.json()["data"]["id"]

    return {"kh_id": kh_id, "bh_id": bh_id, "bkt_id": bkt_id, "ch_ids": ch_ids}


class TestCauHoiCRUD:

    async def test_tao_cau_hoi_trac_nghiem(self, client, admin_user):
        kh = await client.post("/api/v1/lms/khoa-hoc", json={
            "ma_khoa_hoc": f"KH-CH-{uuid.uuid4().hex[:6]}", "ten_khoa_hoc": "CH test",
        })
        kh_id = kh.json()["data"]["id"]
        resp = await client.post("/api/v1/lms/cau-hoi", json={
            "khoa_hoc_id": kh_id, "noi_dung": "Test?", "loai": "TRAC_NGHIEM_1",
            "dap_an": {"lua_chon": [{"key": "A", "noi_dung": "A"}], "dap_an_dung": "A"},
        })
        assert resp.status_code == 201

    async def test_cbcc_khong_xem_ngan_hang(self, client, cbcc_user):
        """CBCC khong co quyen GET /cau-hoi — 403."""
        resp = await client.get("/api/v1/lms/cau-hoi")
        assert resp.status_code == 403


class TestBaiKiemTraCRUD:

    async def test_tao_bkt_gan_cau_hoi(self, client, admin_user):
        """Tao BKT + gan cau hoi."""
        setup = await _setup_exam(client)
        resp = await client.get(f"/api/v1/lms/bai-kiem-tra/{setup['bkt_id']}")
        assert resp.status_code == 200
        assert resp.json()["data"]["so_cau_hoi"] == 3


class TestLuongThi:

    async def test_bat_dau_thi(self, client, admin_user):
        """Dang ky → bat dau thi → cau hoi KHONG co dap an."""
        setup = await _setup_exam(client)
        # Switch sang cbcc va dang ky
        cbcc = _make_user("CHUYEN_VIEN", [], idx=4)
        _set_user(cbcc)
        await client.post(f"/api/v1/lms/khoa-hoc/{setup['kh_id']}/dang-ky")

        resp = await client.post(f"/api/v1/lms/bai-kiem-tra/{setup['bkt_id']}/bat-dau")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["so_cau"] == 3
        assert "ket_qua_id" in data
        # Verify khong co dap_an_dung
        for ch in data["cau_hoi"]:
            assert "dap_an_dung" not in str(ch.get("lua_chon", ""))

    async def test_bat_dau_chua_dang_ky(self, client, admin_user):
        """Chua dang ky → 400."""
        setup = await _setup_exam(client)
        cbcc = _make_user("CHUYEN_VIEN", [], idx=4)
        _set_user(cbcc)
        resp = await client.post(f"/api/v1/lms/bai-kiem-tra/{setup['bkt_id']}/bat-dau")
        assert resp.status_code == 400

    async def test_nop_bai_cham_diem(self, client, admin_user):
        """Nop bai → auto-grade: TN dung, DS dung, TL=None."""
        setup = await _setup_exam(client)
        cbcc = _make_user("CHUYEN_VIEN", [], idx=4)
        _set_user(cbcc)
        await client.post(f"/api/v1/lms/khoa-hoc/{setup['kh_id']}/dang-ky")
        start = await client.post(f"/api/v1/lms/bai-kiem-tra/{setup['bkt_id']}/bat-dau")
        kq_id = start.json()["data"]["ket_qua_id"]

        resp = await client.post(f"/api/v1/lms/bai-kiem-tra/{setup['bkt_id']}/nop-bai", json={
            "ket_qua_id": kq_id,
            "tra_loi": [
                {"cau_hoi_id": setup["ch_ids"][0], "dap_an": "B"},
                {"cau_hoi_id": setup["ch_ids"][1], "dap_an": True},
                {"cau_hoi_id": setup["ch_ids"][2], "dap_an": "Bai tu luan"},
            ],
        })
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["so_cau_dung"] == 2
        assert len(data["chi_tiet"]) == 3

    async def test_nop_bai_truot(self, client, admin_user):
        """Tra loi sai het → dat=False."""
        setup = await _setup_exam(client)
        cbcc = _make_user("CHUYEN_VIEN", [], idx=4)
        _set_user(cbcc)
        await client.post(f"/api/v1/lms/khoa-hoc/{setup['kh_id']}/dang-ky")
        start = await client.post(f"/api/v1/lms/bai-kiem-tra/{setup['bkt_id']}/bat-dau")
        kq_id = start.json()["data"]["ket_qua_id"]

        resp = await client.post(f"/api/v1/lms/bai-kiem-tra/{setup['bkt_id']}/nop-bai", json={
            "ket_qua_id": kq_id,
            "tra_loi": [
                {"cau_hoi_id": setup["ch_ids"][0], "dap_an": "A"},  # sai
                {"cau_hoi_id": setup["ch_ids"][1], "dap_an": False},  # sai
                {"cau_hoi_id": setup["ch_ids"][2], "dap_an": "text"},
            ],
        })
        data = resp.json()["data"]
        assert data["dat_yeu_cau"] is False
        assert data["so_cau_dung"] == 0

    async def test_xem_ket_qua(self, client, admin_user):
        """GET /ket-qua/{id} → thay chi tiet."""
        setup = await _setup_exam(client)
        cbcc = _make_user("CHUYEN_VIEN", [], idx=4)
        _set_user(cbcc)
        await client.post(f"/api/v1/lms/khoa-hoc/{setup['kh_id']}/dang-ky")
        start = await client.post(f"/api/v1/lms/bai-kiem-tra/{setup['bkt_id']}/bat-dau")
        kq_id = start.json()["data"]["ket_qua_id"]
        await client.post(f"/api/v1/lms/bai-kiem-tra/{setup['bkt_id']}/nop-bai", json={
            "ket_qua_id": kq_id,
            "tra_loi": [
                {"cau_hoi_id": setup["ch_ids"][0], "dap_an": "B"},
                {"cau_hoi_id": setup["ch_ids"][1], "dap_an": True},
                {"cau_hoi_id": setup["ch_ids"][2], "dap_an": "text"},
            ],
        })
        resp = await client.get(f"/api/v1/lms/ket-qua/{kq_id}")
        assert resp.status_code == 200
        assert resp.json()["data"]["chi_tiet"] is not None
