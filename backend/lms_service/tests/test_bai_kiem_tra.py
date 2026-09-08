"""
Tests cho cau hoi + bai kiem tra + luong thi — 10 test cases.
"""

import io
import uuid

import pytest
import pytest_asyncio
from httpx import AsyncClient

import lms_service.config as lms_config

from lms_service.main import app
from lms_service.dependencies import get_current_user
from lms_service.tests.conftest import (
    _make_user, _set_user, _REAL_CC_IDS, dang_ky_va_duyet,
)


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

    # BKT + 3 cau hoi tao inline.
    # Cau hoi BAT BUOC gan vao bai kiem tra (CauHoiCreate.bai_kiem_tra_id) nen
    # khong the tao cau hoi truoc roi moi tao BKT — phai dung `cau_hoi_moi`.
    bkt = await client.post(f"/api/v1/lms/khoa-hoc/{kh_id}/bai-kiem-tra", json={
        "tieu_de": "BKT test",
        "diem_dat": 30, "tron_de": False, "tron_dap_an": False,
        "cau_hoi_moi": [
            {"noi_dung": "Cau TN1?", "loai": "TRAC_NGHIEM_1", "diem": 2,
             "dap_an": {"lua_chon": [{"key": "A", "noi_dung": "Sai"},
                                     {"key": "B", "noi_dung": "Dung"}],
                        "dap_an_dung": "B"}},
            {"noi_dung": "Dung hay sai?", "loai": "DUNG_SAI", "diem": 1,
             "dap_an": {"dap_an_dung": True}},
            {"noi_dung": "Tu luan?", "loai": "TU_LUAN", "diem": 5,
             "dap_an": {"huong_dan_cham": "3 y"}},
        ],
    })
    assert bkt.status_code == 201, f"tao BKT that bai: {bkt.json()}"
    bkt_id = bkt.json()["data"]["id"]

    # Lay lai id cau hoi. Tra ve theo `loai` chu khong dua vao thu tu danh sach
    # — moi loai chi xuat hien 1 lan nen xac dinh duy nhat.
    ch_resp = await client.get("/api/v1/lms/cau-hoi",
                               params={"bai_kiem_tra_id": bkt_id, "page_size": 100})
    theo_loai = {c["loai"]: c["id"] for c in ch_resp.json()["data"]}
    ch_ids = [theo_loai["TRAC_NGHIEM_1"], theo_loai["DUNG_SAI"], theo_loai["TU_LUAN"]]

    return {"kh_id": kh_id, "bh_id": bh_id, "bkt_id": bkt_id, "ch_ids": ch_ids}


class TestCauHoiCRUD:

    async def test_tao_cau_hoi_trac_nghiem(self, client, admin_user):
        """Them cau hoi vao ngan hang — phai kem bai_kiem_tra_id."""
        kh = await client.post("/api/v1/lms/khoa-hoc", json={
            "ma_khoa_hoc": f"KH-CH-{uuid.uuid4().hex[:6]}", "ten_khoa_hoc": "CH test",
        })
        kh_id = kh.json()["data"]["id"]
        # BKT trac nghiem phai co san it nhat 1 cau moi tao duoc
        bkt = await client.post(f"/api/v1/lms/khoa-hoc/{kh_id}/bai-kiem-tra", json={
            "tieu_de": "BKT cho cau hoi",
            "cau_hoi_moi": [
                {"noi_dung": "Cau mo dau?", "loai": "TRAC_NGHIEM_1",
                 "dap_an": {"lua_chon": [{"key": "A", "noi_dung": "A"}], "dap_an_dung": "A"}},
            ],
        })
        assert bkt.status_code == 201, bkt.json()
        bkt_id = bkt.json()["data"]["id"]

        resp = await client.post("/api/v1/lms/cau-hoi", json={
            "khoa_hoc_id": kh_id, "bai_kiem_tra_id": bkt_id,
            "noi_dung": "Test?", "loai": "TRAC_NGHIEM_1",
            "dap_an": {"lua_chon": [{"key": "A", "noi_dung": "A"}], "dap_an_dung": "A"},
        })
        assert resp.status_code == 201, resp.json()

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
        await dang_ky_va_duyet(client, setup["kh_id"], cbcc)

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
        await dang_ky_va_duyet(client, setup["kh_id"], cbcc)
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
        await dang_ky_va_duyet(client, setup["kh_id"], cbcc)
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
        await dang_ky_va_duyet(client, setup["kh_id"], cbcc)
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

    async def test_ket_qua_tat_ca_giang_vien(self, client, admin_user):
        """GET /bai-kiem-tra/{id}/ket-qua-tat-ca → admin/giang vien co the xem tat ca ket qua."""
        setup = await _setup_exam(client)

        # CBCC 1 thi
        cbcc1 = _make_user("CHUYEN_VIEN", [], idx=4)
        await dang_ky_va_duyet(client, setup["kh_id"], cbcc1)
        start1 = await client.post(f"/api/v1/lms/bai-kiem-tra/{setup['bkt_id']}/bat-dau")
        kq_id1 = start1.json()["data"]["ket_qua_id"]
        await client.post(f"/api/v1/lms/bai-kiem-tra/{setup['bkt_id']}/nop-bai", json={
            "ket_qua_id": kq_id1,
            "tra_loi": [
                {"cau_hoi_id": setup["ch_ids"][0], "dap_an": "B"},
                {"cau_hoi_id": setup["ch_ids"][1], "dap_an": True},
                {"cau_hoi_id": setup["ch_ids"][2], "dap_an": "Bai 1"},
            ],
        })

        # CBCC 2 thi
        cbcc2 = _make_user("CHUYEN_VIEN", [], idx=5)
        await dang_ky_va_duyet(client, setup["kh_id"], cbcc2)
        start2 = await client.post(f"/api/v1/lms/bai-kiem-tra/{setup['bkt_id']}/bat-dau")
        kq_id2 = start2.json()["data"]["ket_qua_id"]
        await client.post(f"/api/v1/lms/bai-kiem-tra/{setup['bkt_id']}/nop-bai", json={
            "ket_qua_id": kq_id2,
            "tra_loi": [
                {"cau_hoi_id": setup["ch_ids"][0], "dap_an": "A"},
                {"cau_hoi_id": setup["ch_ids"][1], "dap_an": False},
                {"cau_hoi_id": setup["ch_ids"][2], "dap_an": "Bai 2"},
            ],
        })

        # Admin xem tat ca ket qua
        _set_user(admin_user)
        resp = await client.get(f"/api/v1/lms/bai-kiem-tra/{setup['bkt_id']}/ket-qua-tat-ca")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data) == 2

        # Verify fields exist
        for item in data:
            assert "id" in item
            assert "cong_chuc_id" in item
            assert "ho_ten" in item
            assert "ma_cc" in item
            assert "don_vi_ten" in item
            assert "lan_thu" in item
            assert "diem" in item
            assert "so_cau_dung" in item
            assert "so_cau_sai" in item
            assert "thoi_gian_lam_giay" in item
            assert "dat_yeu_cau" in item
            assert "so_lan_vi_pham" in item
            assert "ngay_lam" in item

        # Verify different users
        cc_ids = {item["cong_chuc_id"] for item in data}
        assert len(cc_ids) == 2

    async def test_ket_qua_tat_ca_cbcc_no_access(self, client, admin_user):
        """CBCC thuong khong co quyen xem tat ca ket qua → 403."""
        setup = await _setup_exam(client)
        cbcc = _make_user("CHUYEN_VIEN", [], idx=4)
        _set_user(cbcc)
        resp = await client.get(f"/api/v1/lms/bai-kiem-tra/{setup['bkt_id']}/ket-qua-tat-ca")
        assert resp.status_code == 403


# =========================================================================
# BKT THUC HANH — NOP FILE PDF
# =========================================================================

async def _setup_bkt_thuc_hanh(client, dinh_dang: str = "pdf") -> dict:
    """Tao khoa hoc da xuat ban + 1 BKT thuc hanh nhan dinh dang truyen vao."""
    kh = await client.post("/api/v1/lms/khoa-hoc", json={
        "ma_khoa_hoc": f"KH-TH-{uuid.uuid4().hex[:6]}",
        "ten_khoa_hoc": "Thuc hanh test", "loai": "BAT_BUOC",
    })
    kh_id = kh.json()["data"]["id"]
    await client.post(f"/api/v1/lms/khoa-hoc/{kh_id}/bai-hoc", json={
        "tieu_de": "Bai 1", "loai_noi_dung": "HTML",
    })
    await client.patch(f"/api/v1/lms/khoa-hoc/{kh_id}/trang-thai", json={"trang_thai": "CHO_DUYET"})
    await client.patch(f"/api/v1/lms/khoa-hoc/{kh_id}/trang-thai", json={"trang_thai": "DA_XUAT_BAN"})

    bkt = await client.post(f"/api/v1/lms/khoa-hoc/{kh_id}/bai-kiem-tra", json={
        "tieu_de": "Bai tap thuc hanh PDF",
        "loai_bai_kiem_tra": "THUC_HANH",
        "yeu_cau_bai_lam": "Viet bao cao va nop file PDF",
        "dinh_dang_cho_phep": dinh_dang,
        "dung_luong_toi_da_mb": 20,
    })
    assert bkt.status_code == 201, f"tao BKT thuc hanh that bai: {bkt.json()}"
    return {"kh_id": kh_id, "bkt_id": bkt.json()["data"]["id"], "bkt": bkt.json()["data"]}


class TestNopPdfThucHanh:
    """Bai tap thuc hanh nhan file PDF (khong chi video)."""

    async def test_tao_bkt_dinh_dang_pdf(self, client, admin_user):
        """dinh_dang_cho_phep = 'pdf' duoc chap nhan va chuan hoa."""
        s = await _setup_bkt_thuc_hanh(client, dinh_dang=".PDF, pdf ,docx")
        # bo dau cham, ha chu thuong, khu trung lap, giu thu tu
        assert s["bkt"]["dinh_dang_cho_phep"] == "pdf,docx"

    async def test_tao_bkt_dinh_dang_khong_ho_tro(self, client, admin_user):
        """Dinh dang ngoai danh muc (exe) bi tu choi ngay o tang schema."""
        kh = await client.post("/api/v1/lms/khoa-hoc", json={
            "ma_khoa_hoc": f"KH-TH-{uuid.uuid4().hex[:6]}",
            "ten_khoa_hoc": "Thuc hanh exe", "loai": "BAT_BUOC",
        })
        kh_id = kh.json()["data"]["id"]
        resp = await client.post(f"/api/v1/lms/khoa-hoc/{kh_id}/bai-kiem-tra", json={
            "tieu_de": "BKT xau",
            "loai_bai_kiem_tra": "THUC_HANH",
            "yeu_cau_bai_lam": "Nop file",
            "dinh_dang_cho_phep": "exe",
        })
        assert resp.status_code == 422, resp.text

    async def test_nop_pdf_thanh_cong(self, client, admin_user, tmp_path, monkeypatch):
        """Hoc vien nop file PDF cho BKT thuc hanh — 201 + trang thai CHO_CHAM."""
        monkeypatch.setattr(lms_config.settings, "upload_dir", str(tmp_path))
        s = await _setup_bkt_thuc_hanh(client, dinh_dang="pdf")
        await dang_ky_va_duyet(client, s["kh_id"], admin_user)

        resp = await client.post(
            f"/api/v1/lms/bai-kiem-tra/{s['bkt_id']}/nop-bai-thuc-hanh",
            files={"file": ("bao-cao.pdf", io.BytesIO(b"%PDF-1.4 bao cao"), "application/pdf")},
        )
        assert resp.status_code == 201, resp.text
        data = resp.json()["data"]
        assert data["bai_nop_ten_file"] == "bao-cao.pdf"
        assert data["bai_nop_url"].endswith(".pdf")
        assert data["trang_thai_cham"] == "CHO_CHAM"
        assert data["lan_thu"] == 1

    async def test_nop_video_khi_chi_cho_pdf(self, client, admin_user, tmp_path, monkeypatch):
        """BKT chi nhan PDF thi file .mp4 bi tu choi."""
        monkeypatch.setattr(lms_config.settings, "upload_dir", str(tmp_path))
        s = await _setup_bkt_thuc_hanh(client, dinh_dang="pdf")
        await dang_ky_va_duyet(client, s["kh_id"], admin_user)

        resp = await client.post(
            f"/api/v1/lms/bai-kiem-tra/{s['bkt_id']}/nop-bai-thuc-hanh",
            files={"file": ("clip.mp4", io.BytesIO(b"\x00\x00\x00\x18ftypmp42"), "video/mp4")},
        )
        assert resp.status_code == 400, resp.text
        assert resp.json()["detail"]["error"]["code"] == "LMS_ERR_006"

    async def test_nop_pdf_gia_bi_tu_choi(self, client, admin_user, tmp_path, monkeypatch):
        """File doi duoi thanh .pdf nhung khong co chu ky %PDF- bi chan."""
        monkeypatch.setattr(lms_config.settings, "upload_dir", str(tmp_path))
        s = await _setup_bkt_thuc_hanh(client, dinh_dang="pdf")
        await dang_ky_va_duyet(client, s["kh_id"], admin_user)

        resp = await client.post(
            f"/api/v1/lms/bai-kiem-tra/{s['bkt_id']}/nop-bai-thuc-hanh",
            files={"file": ("gia-mao.pdf", io.BytesIO(b"MZ\x90\x00 khong phai pdf"), "application/pdf")},
        )
        assert resp.status_code == 400, resp.text
        assert resp.json()["detail"]["error"]["code"] == "LMS_ERR_008"

    async def test_duong_dan_cu_nop_video_van_chay(self, client, admin_user, tmp_path, monkeypatch):
        """Client cu goi /nop-video van nop duoc (giu tuong thich nguoc)."""
        monkeypatch.setattr(lms_config.settings, "upload_dir", str(tmp_path))
        s = await _setup_bkt_thuc_hanh(client, dinh_dang="pdf,mp4")
        await dang_ky_va_duyet(client, s["kh_id"], admin_user)

        resp = await client.post(
            f"/api/v1/lms/bai-kiem-tra/{s['bkt_id']}/nop-video",
            files={"file": ("bai.pdf", io.BytesIO(b"%PDF-1.7 x"), "application/pdf")},
        )
        assert resp.status_code == 201, resp.text
