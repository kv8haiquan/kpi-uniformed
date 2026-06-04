"""
chi_tieu_service/tests/test_api_integration.py
==============================================
Integration test API (CRUD danh muc) — CHI chay khi co CHI_TIEU_TEST_DATABASE_URL.
Mac dinh SKIP (xem conftest) de khong bao gio cham production DB.

Chay (vd):
    CHI_TIEU_TEST_DATABASE_URL=postgresql+asyncpg://user:pw@localhost:5544/kpi_test \
        pytest chi_tieu_service/tests/test_api_integration.py -v
"""

import uuid

import pytest

from chi_tieu_service.tests.conftest import requires_test_db

pytestmark = [pytest.mark.asyncio, requires_test_db]


class TestLinhVucCRUD:
    async def test_tao_va_lay_danh_sach(self, client, qt_user):
        ma = f"LV-{uuid.uuid4().hex[:6]}"
        resp = await client.post("/api/v1/chi-tieu/linh-vuc", json={
            "ma_linh_vuc": ma, "ten_linh_vuc": "Linh vuc test", "thu_tu": 1,
        })
        assert resp.status_code == 201
        assert resp.json()["data"]["ma_linh_vuc"] == ma

        ds = await client.get("/api/v1/chi-tieu/linh-vuc")
        assert ds.status_code == 200
        assert any(x["ma_linh_vuc"] == ma for x in ds.json()["data"])

    async def test_tao_trung_ma(self, client, qt_user):
        ma = f"LV-{uuid.uuid4().hex[:6]}"
        body = {"ma_linh_vuc": ma, "ten_linh_vuc": "Trung ma test"}
        assert (await client.post("/api/v1/chi-tieu/linh-vuc", json=body)).status_code == 201
        dup = await client.post("/api/v1/chi-tieu/linh-vuc", json=body)
        assert dup.status_code == 400
        assert dup.json()["error"]["code"] == "CT_ERR_DUP"


class TestDanhMucCRUD:
    async def test_tao_chi_tieu(self, client, qt_user):
        lv = await client.post("/api/v1/chi-tieu/linh-vuc", json={
            "ma_linh_vuc": f"LV-{uuid.uuid4().hex[:6]}", "ten_linh_vuc": "LV cho chi tieu",
        })
        lv_id = lv.json()["data"]["id"]
        resp = await client.post("/api/v1/chi-tieu/danh-muc", json={
            "linh_vuc_id": lv_id, "ma_chi_tieu": f"CT-{uuid.uuid4().hex[:6]}",
            "ten_chi_tieu": "Kim ngach XNK", "don_vi_tinh": "trieu USD",
            "kieu_du_lieu": "THAP_PHAN", "co_phan_dau": True,
        })
        assert resp.status_code == 201
        assert resp.json()["data"]["co_phan_dau"] is True
