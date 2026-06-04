"""
lms_service/tests/test_cbcc.py
==============================
Test endpoints helper CBCC & Đơn vị, đặc biệt endpoint MỚI
    GET /don-vi/{id}/cong-chuc
dùng cho form giao bài kiểu accordion (bỏ chọn từng người).

LƯU Ý: Tất cả test ở đây CHỈ ĐỌC (GET) — an toàn với DB production
(không dùng fixture tạo dữ liệu, không INSERT/UPDATE/DELETE).
"""

import pytest
from httpx import AsyncClient

FAKE_DON_VI_ID = "a0000000-0000-0000-0000-000000000001"  # = don_vi_id của user test


@pytest.mark.asyncio
async def test_list_don_vi(client: AsyncClient, admin_user):
    """GET /don-vi trả danh sách đơn vị."""
    resp = await client.get("/api/v1/lms/don-vi")
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert isinstance(body["data"], list)
    assert len(body["data"]) > 0


@pytest.mark.asyncio
async def test_cong_chuc_theo_don_vi_tra_du_field(client: AsyncClient, admin_user):
    """GET /don-vi/{id}/cong-chuc trả full CBCC active với đủ field."""
    dv_resp = await client.get("/api/v1/lms/don-vi")
    don_vis = dv_resp.json()["data"]

    found = None
    for dv in don_vis:
        r = await client.get(f"/api/v1/lms/don-vi/{dv['id']}/cong-chuc")
        assert r.status_code == 200
        data = r.json()["data"]
        assert isinstance(data, list)
        if data:
            found = data
            break

    assert found is not None, "Không tìm thấy đơn vị nào có CBCC active"
    first = found[0]
    assert {"id", "ma_cc", "ho_ten", "chuc_vu", "is_lanh_dao"}.issubset(first.keys())


@pytest.mark.asyncio
async def test_cong_chuc_theo_don_vi_khong_cap_100(client: AsyncClient, admin_user):
    """Endpoint mới KHÔNG bị giới hạn 100 như /cbcc/search — đơn vị lớn trả đủ."""
    dv_resp = await client.get("/api/v1/lms/don-vi")
    don_vis = dv_resp.json()["data"]

    max_count = 0
    for dv in don_vis:
        r = await client.get(f"/api/v1/lms/don-vi/{dv['id']}/cong-chuc")
        max_count = max(max_count, len(r.json()["data"]))

    # Có đơn vị > 100 người (Móng Cái ~135) → chứng minh không bị cap 100
    assert max_count > 100, f"Đơn vị lớn nhất chỉ {max_count} người — kiểm tra lại cap"


@pytest.mark.asyncio
async def test_cong_chuc_theo_don_vi_cbcc_thuong_bi_chan(client: AsyncClient, cbcc_user):
    """CBCC thường (không GIANG_VIEN/QT_DAO_TAO/lãnh đạo) → 403."""
    resp = await client.get(f"/api/v1/lms/don-vi/{FAKE_DON_VI_ID}/cong-chuc")
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_lanh_dao_chi_xem_don_vi_minh(client: AsyncClient, lanh_dao_user):
    """Lãnh đạo xin đơn vị KHÁC đơn vị mình → 403."""
    dv_resp = await client.get("/api/v1/lms/don-vi")
    don_vis = dv_resp.json()["data"]
    other = next((dv for dv in don_vis if dv["id"] != FAKE_DON_VI_ID), None)
    assert other is not None
    resp = await client.get(f"/api/v1/lms/don-vi/{other['id']}/cong-chuc")
    assert resp.status_code == 403
