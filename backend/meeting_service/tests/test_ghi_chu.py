"""
Ghi chú cá nhân và chia sẻ — G5.2.

Điều phải giữ bằng mọi giá: ghi chú là dữ liệu riêng. Nửa số test dưới đây
chỉ để chứng minh người ngoài không đọc được, kể cả quản trị, và người được
chia sẻ thì không sửa/xoá được.
"""

import io

import pytest
from httpx import AsyncClient
from sqlalchemy import text as sa_text
from sqlalchemy.ext.asyncio import AsyncSession

from meeting_service.tests.conftest import _make_user, _set_user

BASE = "/api/v1/hop-khong-giay/ghi-chu"


def _doi_user(ma_cc: str, don_vi_id, **kw):
    """Đổi người đăng nhập giữa chừng một test."""
    u = _make_user(ma_cc, don_vi_id, **kw)
    _set_user(u)
    return u


async def _tao(client: AsyncClient, tieu_de="Ghi chú thử", **kw) -> dict:
    r = await client.post(BASE, json={"tieu_de": tieu_de, **kw})
    assert r.status_code == 201, r.text
    return r.json()["data"]


# ── CRUD ──────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_tao_va_doc_lai(client: AsyncClient, cbcc_user, seed_test_users):
    gc = await _tao(client, "Chuẩn bị họp giao ban",
                    noi_dung="Nhớ in 3 bản báo cáo")
    assert gc["la_cua_toi"] is True
    assert gc["nguoi_tao_id"] == str(cbcc_user.sub)

    r = await client.get(f"{BASE}/{gc['id']}")
    assert r.status_code == 200
    assert r.json()["data"]["noi_dung"] == "Nhớ in 3 bản báo cáo"


@pytest.mark.asyncio
async def test_sua_va_ghim(client: AsyncClient, cbcc_user, seed_test_users):
    gc = await _tao(client)
    r = await client.patch(f"{BASE}/{gc['id']}",
                           json={"tieu_de": "Đã sửa", "is_ghim": True})
    assert r.status_code == 200, r.text
    assert r.json()["data"]["tieu_de"] == "Đã sửa"
    assert r.json()["data"]["is_ghim"] is True


@pytest.mark.asyncio
async def test_xoa_mem_thi_khong_con_doc_duoc(
    client: AsyncClient, cbcc_user, seed_test_users,
):
    gc = await _tao(client)
    assert (await client.delete(f"{BASE}/{gc['id']}")).status_code == 200
    assert (await client.get(f"{BASE}/{gc['id']}")).status_code == 404


@pytest.mark.asyncio
async def test_gan_cuoc_hop_khong_ton_tai_thi_404(
    client: AsyncClient, cbcc_user, seed_test_users,
):
    r = await client.post(BASE, json={
        "tieu_de": "Gắn họp ma",
        "cuoc_hop_id": "00000000-0000-0000-0000-000000000000"})
    assert r.status_code == 404
    assert r.json()["detail"]["error"]["code"] == "MEETING_NOT_FOUND"


@pytest.mark.asyncio
async def test_tieu_de_rong_thi_422(client: AsyncClient, cbcc_user,
                                    seed_test_users):
    r = await client.post(BASE, json={"tieu_de": "   "})
    assert r.status_code == 422


# ── riêng tư ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_nguoi_khac_khong_doc_duoc(
    client: AsyncClient, cbcc_user, seed_test_users,
):
    gc = await _tao(client, "Bí mật của tôi")
    try:
        _doi_user("TEST-G3-002", seed_test_users["don_vi_a"])
        r = await client.get(f"{BASE}/{gc['id']}")
        # 404 chứ không 403 — không xác nhận ghi chú có tồn tại.
        assert r.status_code == 404
        assert (await client.get(BASE)).json()["data"] == []
    finally:
        _set_user(cbcc_user)   # trả lại quyền cho chủ ghi chú


@pytest.mark.asyncio
async def test_quan_tri_cung_khong_doc_duoc(
    client: AsyncClient, cbcc_user, seed_test_users,
):
    """Khác mọi nghiệp vụ khác trong module: đây là sổ tay cá nhân."""
    gc = await _tao(client, "Không dành cho quản trị")
    try:
        _doi_user("TEST-G3-001", seed_test_users["don_vi_a"],
                  vai_tro="ADMIN", is_admin=True)
        assert (await client.get(f"{BASE}/{gc['id']}")).status_code == 404
    finally:
        _set_user(cbcc_user)   # trả lại quyền cho chủ ghi chú


# ── chia sẻ ───────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_chia_se_thi_nguoi_nhan_doc_duoc_nhung_khong_sua_duoc(
    client: AsyncClient, cbcc_user, seed_test_users,
):
    from meeting_service.tests.conftest import TEST_USERS

    gc = await _tao(client, "Gửi anh Hai xem giúp")
    nhan_id = str(TEST_USERS["TEST-G3-002"])
    r = await client.post(f"{BASE}/{gc['id']}/chia-se",
                          json={"nguoi_nhan_ids": [nhan_id],
                                "loi_nhan": "Anh xem giúp em"})
    assert r.status_code == 200, r.text
    assert r.json()["data"][0]["moi"] is True

    try:
        _doi_user("TEST-G3-002", seed_test_users["don_vi_a"])
        chi_tiet = (await client.get(f"{BASE}/{gc['id']}")).json()["data"]
        assert chi_tiet["la_cua_toi"] is False
        assert chi_tiet["da_doc"] is False
        assert chi_tiet["loi_nhan"] == "Anh xem giúp em"
        # Người nhận KHÔNG thấy ghi chú còn được gửi cho ai khác.
        assert chi_tiet["chia_se"] == []

        assert (await client.patch(f"{BASE}/{gc['id']}",
                                   json={"tieu_de": "Sửa trộm"})).status_code == 403
        assert (await client.delete(f"{BASE}/{gc['id']}")).status_code == 403
    finally:
        _set_user(cbcc_user)   # trả lại quyền cho chủ ghi chú


@pytest.mark.asyncio
async def test_chia_se_hai_lan_khong_nhan_doi(
    client: AsyncClient, cbcc_user, seed_test_users, db_session: AsyncSession,
):
    from meeting_service.tests.conftest import TEST_USERS

    gc = await _tao(client)
    nhan_id = str(TEST_USERS["TEST-G3-002"])
    body = {"nguoi_nhan_ids": [nhan_id, nhan_id]}
    assert (await client.post(f"{BASE}/{gc['id']}/chia-se",
                              json=body)).status_code == 200
    lan_hai = await client.post(f"{BASE}/{gc['id']}/chia-se", json=body)
    assert lan_hai.json()["data"][0]["moi"] is False

    dem = await db_session.scalar(sa_text(
        "SELECT count(*) FROM meeting.ghi_chu_chia_se WHERE ghi_chu_id = :i"),
        {"i": gc["id"]})
    assert dem == 1


@pytest.mark.asyncio
async def test_khong_chia_se_cho_chinh_minh(
    client: AsyncClient, cbcc_user, seed_test_users,
):
    gc = await _tao(client)
    r = await client.post(f"{BASE}/{gc['id']}/chia-se",
                          json={"nguoi_nhan_ids": [str(cbcc_user.sub)]})
    assert r.status_code == 400
    assert r.json()["detail"]["error"]["code"] == "NOTE_NO_RECIPIENT"


@pytest.mark.asyncio
async def test_dem_chua_doc_va_danh_dau_da_doc(
    client: AsyncClient, cbcc_user, seed_test_users,
):
    from meeting_service.tests.conftest import TEST_USERS

    gc = await _tao(client)
    await client.post(f"{BASE}/{gc['id']}/chia-se",
                      json={"nguoi_nhan_ids": [str(TEST_USERS["TEST-G3-002"])]})
    try:
        _doi_user("TEST-G3-002", seed_test_users["don_vi_a"])
        assert (await client.get(f"{BASE}/chua-doc")
                ).json()["data"]["so_chua_doc"] == 1

        r = await client.post(f"{BASE}/{gc['id']}/da-doc")
        assert r.status_code == 200 and r.json()["data"]["vua_doi"] is True
        assert (await client.get(f"{BASE}/chua-doc")
                ).json()["data"]["so_chua_doc"] == 0
        # Gọi lại không đổi gì thêm.
        assert (await client.post(f"{BASE}/{gc['id']}/da-doc")
                ).json()["data"]["vua_doi"] is False
    finally:
        _set_user(cbcc_user)   # trả lại quyền cho chủ ghi chú


@pytest.mark.asyncio
async def test_thu_hoi_chia_se_thi_mat_quyen_doc(
    client: AsyncClient, cbcc_user, seed_test_users,
):
    from meeting_service.tests.conftest import TEST_USERS

    gc = await _tao(client)
    await client.post(f"{BASE}/{gc['id']}/chia-se",
                      json={"nguoi_nhan_ids": [str(TEST_USERS["TEST-G3-002"])]})
    chia_se_id = (await client.get(f"{BASE}/{gc['id']}")
                  ).json()["data"]["chia_se"][0]["id"]
    assert (await client.delete(f"{BASE}/{gc['id']}/chia-se/{chia_se_id}")
            ).status_code == 200

    try:
        _doi_user("TEST-G3-002", seed_test_users["don_vi_a"])
        assert (await client.get(f"{BASE}/{gc['id']}")).status_code == 404
    finally:
        _set_user(cbcc_user)   # trả lại quyền cho chủ ghi chú


@pytest.mark.asyncio
async def test_nguoi_nhan_khong_thu_hoi_duoc_chia_se(
    client: AsyncClient, cbcc_user, seed_test_users,
):
    from meeting_service.tests.conftest import TEST_USERS

    gc = await _tao(client)
    await client.post(f"{BASE}/{gc['id']}/chia-se",
                      json={"nguoi_nhan_ids": [str(TEST_USERS["TEST-G3-002"])]})
    chia_se_id = (await client.get(f"{BASE}/{gc['id']}")
                  ).json()["data"]["chia_se"][0]["id"]
    try:
        _doi_user("TEST-G3-002", seed_test_users["don_vi_a"])
        assert (await client.delete(f"{BASE}/{gc['id']}/chia-se/{chia_se_id}")
                ).status_code == 403
    finally:
        _set_user(cbcc_user)   # trả lại quyền cho chủ ghi chú


# ── danh sách ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_pham_vi_loc_dung(client: AsyncClient, cbcc_user,
                                seed_test_users):
    from meeting_service.tests.conftest import TEST_USERS

    cua_toi = await _tao(client, "Của tôi")
    await client.post(f"{BASE}/{cua_toi['id']}/chia-se",
                      json={"nguoi_nhan_ids": [str(TEST_USERS["TEST-G3-002"])]})
    try:
        _doi_user("TEST-G3-002", seed_test_users["don_vi_a"])
        rieng = await _tao(client, "Của người nhận")

        ids = lambda ds: {x["id"] for x in ds}  # noqa: E731
        tat_ca = (await client.get(BASE)).json()["data"]
        assert ids(tat_ca) == {cua_toi["id"], rieng["id"]}

        chi_toi = (await client.get(BASE, params={"pham-vi": "CUA_TOI"})
                   ).json()["data"]
        assert ids(chi_toi) == {rieng["id"]}

        duoc_chia = (await client.get(BASE, params={"pham-vi": "DUOC_CHIA_SE"})
                     ).json()["data"]
        assert ids(duoc_chia) == {cua_toi["id"]}
    finally:
        _set_user(cbcc_user)   # trả lại quyền cho chủ ghi chú


@pytest.mark.asyncio
async def test_ghim_len_dau_va_tim_kiem(client: AsyncClient, cbcc_user,
                                        seed_test_users):
    await _tao(client, "Ghi chú thường")
    ghim = await _tao(client, "Ghi chú quan trọng", is_ghim=True,
                      noi_dung="nội dung có chữ khoá dac_biet")

    ds = (await client.get(BASE)).json()["data"]
    assert ds[0]["id"] == ghim["id"]

    tim = (await client.get(BASE, params={"tu-khoa": "dac_biet"})).json()["data"]
    assert [x["id"] for x in tim] == [ghim["id"]]


@pytest.mark.asyncio
async def test_pham_vi_sai_thi_422(client: AsyncClient, cbcc_user,
                                   seed_test_users):
    assert (await client.get(BASE, params={"pham-vi": "LUNG_TUNG"})
            ).status_code == 422


# ── đính kèm ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_dinh_kem_va_quyen_doc_theo_ghi_chu(
    client: AsyncClient, cbcc_user, seed_test_users, db_session: AsyncSession,
):
    from meeting_service.tests.conftest import TEST_USERS

    gc = await _tao(client)
    r = await client.post(
        f"{BASE}/{gc['id']}/tai-lieu",
        files={"file": ("bien-ban.txt", io.BytesIO(b"noi dung"), "text/plain")})
    assert r.status_code == 201, r.text
    tl_id = r.json()["data"]["id"]

    # Ghi đúng chủ thể: ghi_chu_id có, cuoc_hop_id rỗng (CHECK ck_tai_lieu_chu_the)
    dong = (await db_session.execute(sa_text(
        "SELECT cuoc_hop_id, ghi_chu_id FROM meeting.tai_lieu WHERE id = :i"),
        {"i": tl_id})).first()
    assert dong[0] is None and str(dong[1]) == gc["id"]

    assert (await client.get(f"{BASE}/{gc['id']}")
            ).json()["data"]["tai_lieu"][0]["id"] == tl_id
    assert (await client.get(f"{BASE}/tai-lieu/{tl_id}/xem")).status_code == 200

    # Người ngoài không xin được URL xem
    try:
        _doi_user("TEST-G3-002", seed_test_users["don_vi_a"])
        assert (await client.get(f"{BASE}/tai-lieu/{tl_id}/xem")
                ).status_code == 404
        assert (await client.delete(f"{BASE}/tai-lieu/{tl_id}")
                ).status_code == 404
    finally:
        _set_user(cbcc_user)   # trả lại quyền cho chủ ghi chú

    # Chia sẻ xong thì người nhận xem được nhưng vẫn không xoá được
    await client.post(f"{BASE}/{gc['id']}/chia-se",
                      json={"nguoi_nhan_ids": [str(TEST_USERS["TEST-G3-002"])]})
    try:
        _doi_user("TEST-G3-002", seed_test_users["don_vi_a"])
        assert (await client.get(f"{BASE}/tai-lieu/{tl_id}/tai")
                ).status_code == 200
        assert (await client.delete(f"{BASE}/tai-lieu/{tl_id}")
                ).status_code == 403
    finally:
        _set_user(cbcc_user)   # trả lại quyền cho chủ ghi chú

    assert (await client.delete(f"{BASE}/tai-lieu/{tl_id}")).status_code == 200
    assert (await client.get(f"{BASE}/{gc['id']}")
            ).json()["data"]["tai_lieu"] == []


@pytest.mark.asyncio
async def test_xoa_ghi_chu_thi_dinh_kem_khuat_theo(
    client: AsyncClient, cbcc_user, seed_test_users,
):
    gc = await _tao(client)
    r = await client.post(
        f"{BASE}/{gc['id']}/tai-lieu",
        files={"file": ("a.txt", io.BytesIO(b"x"), "text/plain")})
    tl_id = r.json()["data"]["id"]

    await client.delete(f"{BASE}/{gc['id']}")
    assert (await client.get(f"{BASE}/tai-lieu/{tl_id}/xem")).status_code == 404


@pytest.mark.asyncio
async def test_dinh_kem_vao_ghi_chu_nguoi_khac_bi_chan(
    client: AsyncClient, cbcc_user, seed_test_users,
):
    gc = await _tao(client)
    try:
        _doi_user("TEST-G3-002", seed_test_users["don_vi_a"])
        r = await client.post(
            f"{BASE}/{gc['id']}/tai-lieu",
            files={"file": ("a.txt", io.BytesIO(b"x"), "text/plain")})
        # 404 chứ không 403 — người ngoài không được biết ghi chú có tồn tại.
        assert r.status_code == 404
    finally:
        _set_user(cbcc_user)   # trả lại quyền cho chủ ghi chú


# ── gợi ý người nhận ──────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_goi_y_nguoi_nhan_bo_chinh_minh(
    client: AsyncClient, cbcc_user, seed_test_users,
):
    ds = (await client.get(f"{BASE}/nguoi-nhan",
                           params={"tu-khoa": "TEST-G3"})).json()["data"]
    assert ds, "Phải gợi ý được các user test"
    assert str(cbcc_user.sub) not in {x["id"] for x in ds}
