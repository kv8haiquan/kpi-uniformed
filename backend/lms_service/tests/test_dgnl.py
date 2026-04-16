"""
lms_service/tests/test_dgnl.py
==============================
Tests cho module Danh gia Nang luc (DGNL):
  - Linh vuc CRUD (4 tests)
  - Vi tri viec lam CRUD (4 tests)
  - Ky thi CRUD + trang thai (8 tests)
  - Cau truc de (4 tests)
  - Validate ngan hang (2 tests)
  - Thi sinh + lam thi + cham diem (8 tests)
  - Phan quyen (4 tests)
  Total: 34 tests
"""

import uuid
from datetime import datetime, timedelta

import pytest
import pytest_asyncio
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

BASE = "/api/v1/lms"


# =========================================================================
# HELPERS
# =========================================================================

async def _create_linh_vuc(client: AsyncClient, ma: str = None, ten: str = None) -> dict:
    ma = ma or f"LV-{uuid.uuid4().hex[:6]}"
    ten = ten or f"Lĩnh vực {ma}"
    resp = await client.post(f"{BASE}/linh-vuc", json={
        "ma_linh_vuc": ma,
        "ten_linh_vuc": ten,
    })
    assert resp.status_code == 201
    return resp.json()["data"]


async def _create_vi_tri(client: AsyncClient, ma: str = None, ten: str = None) -> dict:
    ma = ma or f"VT-{uuid.uuid4().hex[:6]}"
    ten = ten or f"Vị trí {ma}"
    resp = await client.post(f"{BASE}/vi-tri-viec-lam", json={
        "ma_vi_tri": ma,
        "ten_vi_tri": ten,
    })
    assert resp.status_code == 201
    return resp.json()["data"]


async def _create_ky_thi(client: AsyncClient, ma: str = None) -> dict:
    ma = ma or f"KT-{uuid.uuid4().hex[:6]}"
    now = datetime.utcnow()
    resp = await client.post(f"{BASE}/ky-thi", json={
        "ma_ky_thi": ma,
        "ten_ky_thi": f"Kỳ thi {ma}",
        "ngay_bat_dau": (now - timedelta(hours=1)).isoformat(),
        "ngay_ket_thuc": (now + timedelta(days=7)).isoformat(),
        "thoi_gian_lam_bai_phut": 30,
        "diem_dat": 50,
        "so_lan_thi_toi_da": 2,
    })
    assert resp.status_code == 201
    return resp.json()["data"]


async def _setup_full_exam(client: AsyncClient, admin_user) -> dict:
    """Setup hoan chinh: linh_vuc + vi_tri + ky_thi + cau_truc_de + cau_hoi + thi_sinh."""
    # Linh vuc
    uid = uuid.uuid4().hex[:6]
    lv = await _create_linh_vuc(client, f"LV-FULL-{uid}", "Lĩnh vực test")

    # Vi tri
    vt = await _create_vi_tri(client, f"VT-FULL-{uid}", "Vị trí test")

    # Ky thi
    kt = await _create_ky_thi(client, f"KT-FULL-{uid}")

    # Tao cau hoi co linh_vuc_id
    # Can 1 khoa hoc + BKT de gan cau hoi (bai_kiem_tra_id required)
    kh_resp = await client.post(f"{BASE}/khoa-hoc", json={
        "ma_khoa_hoc": f"KH-DGNL-{uid}",
        "ten_khoa_hoc": "Khóa test ĐGNL",
        "loai": "TU_HOC",
    })
    kh_id = kh_resp.json()["data"]["id"]

    # Tao cau hoi truoc (se tu dong tao junction + cap nhat so_cau_hoi)
    def _ch(noi_dung, do_kho, da_dung):
        return {
            "noi_dung": noi_dung, "loai": "TRAC_NGHIEM_1", "do_kho": do_kho,
            "dap_an": {"lua_chon": [{"key": "A", "noi_dung": "Đáp A"}, {"key": "B", "noi_dung": "Đáp B"}], "dap_an_dung": da_dung},
        }

    # Tao BKT voi cau_hoi_ids (bat buoc co it nhat 1 cau)
    ch_bodies = []
    for i in range(5):
        ch_bodies.append(_ch(f"Câu DỄ {i+1}", "DE", "A"))
    for i in range(3):
        ch_bodies.append(_ch(f"Câu TB {i+1}", "TRUNG_BINH", "B"))
    for i in range(2):
        ch_bodies.append(_ch(f"Câu KHÓ {i+1}", "KHO", "A"))

    # Tao BKT voi cau_hoi_moi (inline)
    bkt_resp = await client.post(f"{BASE}/khoa-hoc/{kh_id}/bai-kiem-tra", json={
        "tieu_de": f"BKT-DGNL-{uid}",
        "diem_dat": 30,
        "cau_hoi_moi": ch_bodies,
    })
    assert bkt_resp.status_code == 201, f"BKT create failed: {bkt_resp.json()}"
    bkt_id = bkt_resp.json()["data"]["id"]

    # Cap nhat linh_vuc_id cho cac cau hoi vua tao
    ch_resp = await client.get(f"{BASE}/cau-hoi", params={"bai_kiem_tra_id": bkt_id, "page_size": 100})
    cau_hoi_ids = []
    for ch in ch_resp.json()["data"]:
        await client.put(f"{BASE}/cau-hoi/{ch['id']}", json={"linh_vuc_id": lv["id"]})
        cau_hoi_ids.append(ch["id"])

    # Cau truc de: 2 DE + 1 TB + 1 KHO = 4 cau
    resp = await client.post(f"{BASE}/ky-thi/{kt['id']}/cau-truc-de", json={
        "vi_tri_id": vt["id"],
        "cau_truc": [
            {"linh_vuc_id": lv["id"], "so_cau_de": 2, "so_cau_trung_binh": 1, "so_cau_kho": 1},
        ],
    })
    assert resp.status_code == 201

    return {
        "linh_vuc": lv,
        "vi_tri": vt,
        "ky_thi": kt,
        "cau_hoi_ids": cau_hoi_ids,
    }


# =========================================================================
# LINH VUC CRUD
# =========================================================================

class TestLinhVucCRUD:
    async def test_tao_linh_vuc(self, client, admin_user):
        lv = await _create_linh_vuc(client)
        assert lv["ma_linh_vuc"]
        assert lv["is_active"] is True

    async def test_danh_sach_linh_vuc(self, client, admin_user):
        await _create_linh_vuc(client, f"LV-LIST-{uuid.uuid4().hex[:6]}")
        resp = await client.get(f"{BASE}/linh-vuc")
        assert resp.status_code == 200
        assert resp.json()["success"] is True
        # Co it nhat seed data (4) + 1 vua tao
        assert len(resp.json()["data"]) >= 1

    async def test_cap_nhat_linh_vuc(self, client, admin_user):
        lv = await _create_linh_vuc(client)
        resp = await client.put(f"{BASE}/linh-vuc/{lv['id']}", json={
            "ten_linh_vuc": "Tên mới",
        })
        assert resp.status_code == 200
        assert resp.json()["data"]["ten_linh_vuc"] == "Tên mới"

    async def test_xoa_linh_vuc(self, client, admin_user):
        lv = await _create_linh_vuc(client)
        resp = await client.delete(f"{BASE}/linh-vuc/{lv['id']}")
        assert resp.status_code == 200

    async def test_tao_linh_vuc_trung_ma(self, client, admin_user):
        ma = f"LV-DUP-{uuid.uuid4().hex[:4]}"
        await _create_linh_vuc(client, ma)
        resp = await client.post(f"{BASE}/linh-vuc", json={
            "ma_linh_vuc": ma,
            "ten_linh_vuc": "Trùng mã",
        })
        assert resp.status_code == 400


# =========================================================================
# VI TRI VIEC LAM CRUD
# =========================================================================

class TestViTriViecLamCRUD:
    async def test_tao_vi_tri(self, client, admin_user):
        vt = await _create_vi_tri(client)
        assert vt["ma_vi_tri"]

    async def test_danh_sach_vi_tri(self, client, admin_user):
        await _create_vi_tri(client, f"VT-LIST-{uuid.uuid4().hex[:6]}")
        resp = await client.get(f"{BASE}/vi-tri-viec-lam")
        assert resp.status_code == 200
        assert len(resp.json()["data"]) >= 1

    async def test_cap_nhat_vi_tri(self, client, admin_user):
        vt = await _create_vi_tri(client)
        resp = await client.put(f"{BASE}/vi-tri-viec-lam/{vt['id']}", json={
            "ten_vi_tri": "Vị trí mới",
        })
        assert resp.status_code == 200
        assert resp.json()["data"]["ten_vi_tri"] == "Vị trí mới"

    async def test_xoa_vi_tri(self, client, admin_user):
        vt = await _create_vi_tri(client)
        resp = await client.delete(f"{BASE}/vi-tri-viec-lam/{vt['id']}")
        assert resp.status_code == 200


# =========================================================================
# KY THI CRUD + TRANG THAI
# =========================================================================

class TestKyThiCRUD:
    async def test_tao_ky_thi(self, client, admin_user):
        kt = await _create_ky_thi(client)
        assert kt["trang_thai"] == "NHAP"
        assert kt["ma_ky_thi"]

    async def test_danh_sach_ky_thi(self, client, admin_user):
        await _create_ky_thi(client)
        resp = await client.get(f"{BASE}/ky-thi")
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    async def test_chi_tiet_ky_thi(self, client, admin_user):
        kt = await _create_ky_thi(client)
        resp = await client.get(f"{BASE}/ky-thi/{kt['id']}")
        assert resp.status_code == 200
        assert resp.json()["data"]["id"] == kt["id"]

    async def test_cap_nhat_ky_thi(self, client, admin_user):
        kt = await _create_ky_thi(client)
        resp = await client.put(f"{BASE}/ky-thi/{kt['id']}", json={
            "ten_ky_thi": "Tên kỳ thi mới",
        })
        assert resp.status_code == 200
        assert resp.json()["data"]["ten_ky_thi"] == "Tên kỳ thi mới"

    async def test_xoa_ky_thi_nhap(self, client, admin_user):
        kt = await _create_ky_thi(client)
        resp = await client.delete(f"{BASE}/ky-thi/{kt['id']}")
        assert resp.status_code == 200

    async def test_tao_ky_thi_trung_ma(self, client, admin_user):
        ma = f"KT-DUP-{uuid.uuid4().hex[:4]}"
        await _create_ky_thi(client, ma)
        now = datetime.utcnow()
        resp = await client.post(f"{BASE}/ky-thi", json={
            "ma_ky_thi": ma,
            "ten_ky_thi": "Trùng mã",
            "ngay_bat_dau": now.isoformat(),
            "ngay_ket_thuc": (now + timedelta(days=1)).isoformat(),
        })
        assert resp.status_code == 400

    async def test_cap_nhat_ky_thi_khong_phai_nhap(self, client, admin_user):
        """Khong duoc sua ky thi khi khong o trang thai NHAP."""
        data = await _setup_full_exam(client, admin_user)
        kt = data["ky_thi"]
        # Chuyen sang CHO_DUYET
        await client.patch(f"{BASE}/ky-thi/{kt['id']}/trang-thai", json={"trang_thai": "CHO_DUYET"})
        # Thu cap nhat
        resp = await client.put(f"{BASE}/ky-thi/{kt['id']}", json={"ten_ky_thi": "Moi"})
        assert resp.status_code == 400


class TestKyThiTrangThai:
    async def test_nhap_to_cho_duyet(self, client, admin_user):
        data = await _setup_full_exam(client, admin_user)
        kt = data["ky_thi"]
        resp = await client.patch(f"{BASE}/ky-thi/{kt['id']}/trang-thai", json={"trang_thai": "CHO_DUYET"})
        assert resp.status_code == 200
        assert resp.json()["data"]["trang_thai"] == "CHO_DUYET"

    async def test_cho_duyet_to_nhap(self, client, admin_user):
        """Tra lai tu CHO_DUYET ve NHAP."""
        data = await _setup_full_exam(client, admin_user)
        kt = data["ky_thi"]
        await client.patch(f"{BASE}/ky-thi/{kt['id']}/trang-thai", json={"trang_thai": "CHO_DUYET"})
        resp = await client.patch(f"{BASE}/ky-thi/{kt['id']}/trang-thai", json={"trang_thai": "NHAP"})
        assert resp.status_code == 200
        assert resp.json()["data"]["trang_thai"] == "NHAP"

    async def test_cho_duyet_to_dang_mo(self, client, admin_user):
        data = await _setup_full_exam(client, admin_user)
        kt = data["ky_thi"]
        await client.patch(f"{BASE}/ky-thi/{kt['id']}/trang-thai", json={"trang_thai": "CHO_DUYET"})
        resp = await client.patch(f"{BASE}/ky-thi/{kt['id']}/trang-thai", json={"trang_thai": "DANG_MO"})
        assert resp.status_code == 200
        assert resp.json()["data"]["trang_thai"] == "DANG_MO"

    async def test_nhap_to_dang_mo_invalid(self, client, admin_user):
        """Khong the nhay tu NHAP sang DANG_MO."""
        data = await _setup_full_exam(client, admin_user)
        kt = data["ky_thi"]
        resp = await client.patch(f"{BASE}/ky-thi/{kt['id']}/trang-thai", json={"trang_thai": "DANG_MO"})
        assert resp.status_code == 400

    async def test_nhap_to_cho_duyet_no_cau_truc(self, client, admin_user):
        """Khong the gui duyet khi chua co cau truc de."""
        kt = await _create_ky_thi(client)
        resp = await client.patch(f"{BASE}/ky-thi/{kt['id']}/trang-thai", json={"trang_thai": "CHO_DUYET"})
        assert resp.status_code == 400


# =========================================================================
# CAU TRUC DE
# =========================================================================

class TestCauTrucDe:
    async def test_upsert_cau_truc_de(self, client, admin_user):
        lv = await _create_linh_vuc(client, f"LV-CTD-{uuid.uuid4().hex[:4]}")
        vt = await _create_vi_tri(client, f"VT-CTD-{uuid.uuid4().hex[:4]}")
        kt = await _create_ky_thi(client)

        resp = await client.post(f"{BASE}/ky-thi/{kt['id']}/cau-truc-de", json={
            "vi_tri_id": vt["id"],
            "cau_truc": [
                {"linh_vuc_id": lv["id"], "so_cau_de": 5, "so_cau_trung_binh": 3, "so_cau_kho": 2},
            ],
        })
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert len(data) >= 1
        assert data[0]["tong_cau"] == 10

    async def test_lay_cau_truc_de(self, client, admin_user):
        data = await _setup_full_exam(client, admin_user)
        kt = data["ky_thi"]
        resp = await client.get(f"{BASE}/ky-thi/{kt['id']}/cau-truc-de")
        assert resp.status_code == 200
        assert len(resp.json()["data"]) >= 1

    async def test_xoa_cau_truc_de_vi_tri(self, client, admin_user):
        data = await _setup_full_exam(client, admin_user)
        kt = data["ky_thi"]
        vt = data["vi_tri"]
        resp = await client.delete(f"{BASE}/ky-thi/{kt['id']}/cau-truc-de/{vt['id']}")
        assert resp.status_code == 200

    async def test_upsert_overwrite(self, client, admin_user):
        """Upsert ghi de cau truc cu."""
        lv = await _create_linh_vuc(client, f"LV-OVW-{uuid.uuid4().hex[:4]}")
        vt = await _create_vi_tri(client, f"VT-OVW-{uuid.uuid4().hex[:4]}")
        kt = await _create_ky_thi(client)

        await client.post(f"{BASE}/ky-thi/{kt['id']}/cau-truc-de", json={
            "vi_tri_id": vt["id"],
            "cau_truc": [{"linh_vuc_id": lv["id"], "so_cau_de": 5, "so_cau_trung_binh": 0, "so_cau_kho": 0}],
        })

        # Overwrite
        resp = await client.post(f"{BASE}/ky-thi/{kt['id']}/cau-truc-de", json={
            "vi_tri_id": vt["id"],
            "cau_truc": [{"linh_vuc_id": lv["id"], "so_cau_de": 10, "so_cau_trung_binh": 5, "so_cau_kho": 0}],
        })
        assert resp.status_code == 201
        # Tim vi tri trong response
        vt_data = [d for d in resp.json()["data"] if d["vi_tri_id"] == vt["id"]]
        assert len(vt_data) == 1
        assert vt_data[0]["tong_cau"] == 15


# =========================================================================
# VALIDATE NGAN HANG
# =========================================================================

class TestValidate:
    async def test_validate_du_cau_hoi(self, client, admin_user):
        data = await _setup_full_exam(client, admin_user)
        kt = data["ky_thi"]
        resp = await client.post(f"{BASE}/ky-thi/{kt['id']}/validate")
        assert resp.status_code == 200
        assert resp.json()["data"]["tat_ca_du"] is True

    async def test_validate_thieu_cau_hoi(self, client, admin_user):
        """Cau truc de yeu cau nhieu hon cau hoi co san."""
        lv = await _create_linh_vuc(client, f"LV-VALI-{uuid.uuid4().hex[:4]}")
        vt = await _create_vi_tri(client, f"VT-VALI-{uuid.uuid4().hex[:4]}")
        kt = await _create_ky_thi(client)

        # Cau truc de: 100 cau DE — khong co san
        await client.post(f"{BASE}/ky-thi/{kt['id']}/cau-truc-de", json={
            "vi_tri_id": vt["id"],
            "cau_truc": [{"linh_vuc_id": lv["id"], "so_cau_de": 100, "so_cau_trung_binh": 0, "so_cau_kho": 0}],
        })

        resp = await client.post(f"{BASE}/ky-thi/{kt['id']}/validate")
        assert resp.status_code == 200
        assert resp.json()["data"]["tat_ca_du"] is False


# =========================================================================
# THI SINH + LAM THI + CHAM DIEM
# =========================================================================

class TestThiSinh:
    async def test_giao_thi_sinh(self, client, admin_user):
        data = await _setup_full_exam(client, admin_user)
        kt = data["ky_thi"]
        vt = data["vi_tri"]

        resp = await client.post(f"{BASE}/ky-thi/{kt['id']}/thi-sinh", json={
            "danh_sach": [
                {"cong_chuc_id": "00327c43-c9a3-44d7-8306-7084e75cb2b5", "vi_tri_id": vt["id"]},
                {"cong_chuc_id": "01014af6-1505-495b-95ab-8c1503cfa061", "vi_tri_id": vt["id"]},
            ],
        })
        assert resp.status_code == 201
        assert resp.json()["data"]["thanh_cong"] == 2

    async def test_danh_sach_thi_sinh(self, client, admin_user):
        data = await _setup_full_exam(client, admin_user)
        kt = data["ky_thi"]
        vt = data["vi_tri"]

        await client.post(f"{BASE}/ky-thi/{kt['id']}/thi-sinh", json={
            "danh_sach": [{"cong_chuc_id": "00327c43-c9a3-44d7-8306-7084e75cb2b5", "vi_tri_id": vt["id"]}],
        })

        resp = await client.get(f"{BASE}/ky-thi/{kt['id']}/thi-sinh")
        assert resp.status_code == 200
        assert len(resp.json()["data"]) == 1

    async def test_xoa_thi_sinh_chua_thi(self, client, admin_user):
        data = await _setup_full_exam(client, admin_user)
        kt = data["ky_thi"]
        vt = data["vi_tri"]
        cc_id = "01014af6-1505-495b-95ab-8c1503cfa061"

        await client.post(f"{BASE}/ky-thi/{kt['id']}/thi-sinh", json={
            "danh_sach": [{"cong_chuc_id": cc_id, "vi_tri_id": vt["id"]}],
        })

        resp = await client.delete(f"{BASE}/ky-thi/{kt['id']}/thi-sinh/{cc_id}")
        assert resp.status_code == 200

    async def test_giao_trung_bo_qua(self, client, admin_user):
        """Giao thi sinh trung lap — bo qua khong loi."""
        data = await _setup_full_exam(client, admin_user)
        kt = data["ky_thi"]
        vt = data["vi_tri"]
        cc_id = "00327c43-c9a3-44d7-8306-7084e75cb2b5"

        await client.post(f"{BASE}/ky-thi/{kt['id']}/thi-sinh", json={
            "danh_sach": [{"cong_chuc_id": cc_id, "vi_tri_id": vt["id"]}],
        })
        resp = await client.post(f"{BASE}/ky-thi/{kt['id']}/thi-sinh", json={
            "danh_sach": [{"cong_chuc_id": cc_id, "vi_tri_id": vt["id"]}],
        })
        assert resp.status_code == 201
        assert resp.json()["data"]["bo_qua"] == 1


class TestLamThi:
    async def _setup_and_open(self, client, admin_user) -> dict:
        """Setup + mo ky thi + giao thi sinh cho admin_user."""
        data = await _setup_full_exam(client, admin_user)
        kt = data["ky_thi"]
        vt = data["vi_tri"]
        cc_id = "00327c43-c9a3-44d7-8306-7084e75cb2b5"  # admin_user idx=0

        # Giao thi sinh
        await client.post(f"{BASE}/ky-thi/{kt['id']}/thi-sinh", json={
            "danh_sach": [{"cong_chuc_id": cc_id, "vi_tri_id": vt["id"]}],
        })

        # Mo ky thi: NHAP -> CHO_DUYET -> DANG_MO
        await client.patch(f"{BASE}/ky-thi/{kt['id']}/trang-thai", json={"trang_thai": "CHO_DUYET"})
        await client.patch(f"{BASE}/ky-thi/{kt['id']}/trang-thai", json={"trang_thai": "DANG_MO"})

        data["cc_id"] = cc_id
        return data

    async def test_bat_dau_thi(self, client, admin_user):
        data = await self._setup_and_open(client, admin_user)
        kt = data["ky_thi"]

        resp = await client.post(f"{BASE}/ky-thi/{kt['id']}/bat-dau")
        assert resp.status_code == 200
        result = resp.json()["data"]
        assert result["tong_so_cau"] == 4  # 2 DE + 1 TB + 1 KHO
        assert len(result["cau_hoi"]) == 4
        # Khong co dap an dung
        for ch in result["cau_hoi"]:
            assert "dap_an_dung" not in str(ch)

    async def test_nop_bai_va_cham_diem(self, client, admin_user):
        data = await self._setup_and_open(client, admin_user)
        kt = data["ky_thi"]

        # Bat dau
        start_resp = await client.post(f"{BASE}/ky-thi/{kt['id']}/bat-dau")
        cau_hoi = start_resp.json()["data"]["cau_hoi"]

        # Tra loi tat ca cau A
        cau_tra_loi = [{"cau_hoi_id": ch["id"], "tra_loi": {"dap_an": "A"}} for ch in cau_hoi]

        resp = await client.post(f"{BASE}/ky-thi/{kt['id']}/nop-bai", json={
            "cau_tra_loi": cau_tra_loi,
        })
        assert resp.status_code == 200
        result = resp.json()["data"]
        assert result["ket_qua"]["tong_so_cau"] == 4
        assert result["ket_qua"]["xep_loai"] in ("DAT", "KHONG_DAT")
        assert result["ket_qua"]["diem_tong"] >= 0

    async def test_ket_qua_ca_nhan(self, client, admin_user):
        data = await self._setup_and_open(client, admin_user)
        kt = data["ky_thi"]

        # Bat dau + nop bai
        start_resp = await client.post(f"{BASE}/ky-thi/{kt['id']}/bat-dau")
        cau_hoi = start_resp.json()["data"]["cau_hoi"]
        cau_tra_loi = [{"cau_hoi_id": ch["id"], "tra_loi": {"dap_an": "A"}} for ch in cau_hoi]
        await client.post(f"{BASE}/ky-thi/{kt['id']}/nop-bai", json={"cau_tra_loi": cau_tra_loi})

        # Xem ket qua
        resp = await client.get(f"{BASE}/ky-thi/{kt['id']}/ket-qua")
        assert resp.status_code == 200
        assert resp.json()["data"]["thi_sinh"]["ho_ten"] is not None

    async def test_thong_ke_ky_thi(self, client, admin_user):
        data = await self._setup_and_open(client, admin_user)
        kt = data["ky_thi"]

        # Bat dau + nop
        start_resp = await client.post(f"{BASE}/ky-thi/{kt['id']}/bat-dau")
        cau_hoi = start_resp.json()["data"]["cau_hoi"]
        cau_tra_loi = [{"cau_hoi_id": ch["id"], "tra_loi": {"dap_an": "A"}} for ch in cau_hoi]
        await client.post(f"{BASE}/ky-thi/{kt['id']}/nop-bai", json={"cau_tra_loi": cau_tra_loi})

        resp = await client.get(f"{BASE}/ky-thi/{kt['id']}/thong-ke")
        assert resp.status_code == 200
        tq = resp.json()["data"]["tong_quan"]
        assert tq["tong_thi_sinh"] == 1
        assert tq["da_thi"] == 1


# =========================================================================
# PHAN QUYEN
# =========================================================================

class TestPhanQuyen:
    async def test_cbcc_khong_tao_ky_thi(self, client, cbcc_user):
        now = datetime.utcnow()
        resp = await client.post(f"{BASE}/ky-thi", json={
            "ma_ky_thi": "KT-NOAUTH",
            "ten_ky_thi": "Test no auth",
            "ngay_bat_dau": now.isoformat(),
            "ngay_ket_thuc": (now + timedelta(days=1)).isoformat(),
        })
        assert resp.status_code == 403

    async def test_cbcc_khong_tao_linh_vuc(self, client, cbcc_user):
        resp = await client.post(f"{BASE}/linh-vuc", json={
            "ma_linh_vuc": "LV-NOAUTH",
            "ten_linh_vuc": "Test no auth",
        })
        assert resp.status_code == 403

    async def test_cbcc_xem_linh_vuc_ok(self, client, cbcc_user):
        """CBCC duoc xem danh sach linh vuc."""
        resp = await client.get(f"{BASE}/linh-vuc")
        assert resp.status_code == 200

    async def test_cbcc_xem_ky_thi_ok(self, client, cbcc_user):
        """CBCC duoc xem danh sach ky thi (chi thay duoc giao)."""
        resp = await client.get(f"{BASE}/ky-thi")
        assert resp.status_code == 200
