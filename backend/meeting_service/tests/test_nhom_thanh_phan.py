"""
Tests cho nhóm thành phần (meeting.nhom_thanh_phan).

Coverage:
- CRUD nhóm: create / list / detail / update / delete (cascade chi_tiet)
- CRUD thành viên: add / update / remove + duplicate 409
- Validate: vai_tro/loai_tham_du sai → 422; cong_chuc trùng trong request → 400
- Merge: happy path, skip duplicate, auto-fill thu_ky_id, multi-nhóm,
  nhom_id không tồn tại → 404
"""

from datetime import date as _date, datetime as _dt, timedelta as _td

import pytest
from httpx import AsyncClient
from sqlalchemy import text as sa_text
from sqlalchemy.ext.asyncio import AsyncSession


BASE_NHOM = "/api/v1/hop-khong-giay/nhom-thanh-phan"
BASE_CH = "/api/v1/hop-khong-giay/cuoc-hop"


def _ch_payload(don_vi_id, chu_toa_id, thu_ky_id=None, thanh_phan=None):
    today = _date.today().isoformat()
    gio = (_dt.now() - _td(minutes=1)).time().strftime("%H:%M")
    return {
        "tieu_de": "Test nhóm thành phần",
        "khoi": "CHUYEN_MON",
        "hinh_thuc": "TRUC_TIEP",
        "ngay_hop": today,
        "gio_bat_dau": gio,
        "don_vi_to_chuc_id": str(don_vi_id),
        "chu_toa_id": str(chu_toa_id),
        "thu_ky_id": str(thu_ky_id) if thu_ky_id else None,
        "thanh_phan": thanh_phan or [],
    }


# ════════════════════════════════════════════════════════════════════
# CRUD nhóm
# ════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_tao_nhom_happy(
    client: AsyncClient, chu_toa_user, seed_test_users,
):
    """Tạo nhóm với 3 thành viên (CHU_TRI/THU_KY/THANH_VIEN)."""
    payload = {
        "ten_nhom": "Nhóm test",
        "mo_ta": "Mô tả test",
        "loai_nhom": "Giao ban",
        "chi_tiet": [
            {"cong_chuc_id": "aaaaaaaa-0001-0000-0000-000000000001",
             "vai_tro": "CHU_TRI"},
            {"cong_chuc_id": "aaaaaaaa-0002-0000-0000-000000000002",
             "vai_tro": "THU_KY"},
            {"cong_chuc_id": "aaaaaaaa-0003-0000-0000-000000000003",
             "vai_tro": "THANH_VIEN", "loai_tham_du": "THAM_KHAO"},
        ],
    }
    resp = await client.post(BASE_NHOM + "/", json=payload)
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["success"] is True
    data = body["data"]
    assert data["ten_nhom"] == "Nhóm test"
    assert data["loai_nhom"] == "Giao ban"
    assert len(data["chi_tiet"]) == 3
    # Sorted: CHU_TRI > THU_KY > THANH_VIEN
    vts = [x["vai_tro"] for x in data["chi_tiet"]]
    assert vts == ["CHU_TRI", "THU_KY", "THANH_VIEN"]


@pytest.mark.asyncio
async def test_tao_nhom_trung_thanh_vien_400(
    client: AsyncClient, chu_toa_user, seed_test_users,
):
    """cong_chuc_id trùng trong cùng 1 request → 400."""
    payload = {
        "ten_nhom": "X",
        "chi_tiet": [
            {"cong_chuc_id": "aaaaaaaa-0001-0000-0000-000000000001"},
            {"cong_chuc_id": "aaaaaaaa-0001-0000-0000-000000000001"},
        ],
    }
    resp = await client.post(BASE_NHOM + "/", json=payload)
    assert resp.status_code == 400
    assert resp.json()["detail"]["error"]["code"] == "DUPLICATE_MEMBER"


@pytest.mark.asyncio
async def test_tao_nhom_vai_tro_invalid_422(
    client: AsyncClient, chu_toa_user, seed_test_users,
):
    """vai_tro không trong enum → 422."""
    payload = {
        "ten_nhom": "X",
        "chi_tiet": [
            {"cong_chuc_id": "aaaaaaaa-0001-0000-0000-000000000001",
             "vai_tro": "BOGUS"},
        ],
    }
    resp = await client.post(BASE_NHOM + "/", json=payload)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_list_nhom_search_filter(
    client: AsyncClient, chu_toa_user, seed_test_users,
):
    """List có q + loai_nhom filter."""
    # Tạo 2 nhóm
    await client.post(BASE_NHOM + "/", json={"ten_nhom": "Giao ban A", "loai_nhom": "Loai1"})
    await client.post(BASE_NHOM + "/", json={"ten_nhom": "Họp khác", "loai_nhom": "Loai2"})

    # Search
    r1 = await client.get(BASE_NHOM + "/?q=Giao")
    assert r1.status_code == 200
    items1 = r1.json()["data"]
    assert any("Giao ban A" in x["ten_nhom"] for x in items1)
    assert all("Họp khác" not in x["ten_nhom"] for x in items1)

    # Filter loai_nhom
    r2 = await client.get(BASE_NHOM + "/?loai_nhom=Loai2")
    assert r2.status_code == 200
    items2 = r2.json()["data"]
    assert all(x["loai_nhom"] == "Loai2" for x in items2)


@pytest.mark.asyncio
async def test_update_nhom_metadata(
    client: AsyncClient, chu_toa_user, seed_test_users,
):
    create = await client.post(BASE_NHOM + "/", json={"ten_nhom": "Old"})
    nhom_id = create.json()["data"]["id"]

    resp = await client.patch(f"{BASE_NHOM}/{nhom_id}", json={
        "ten_nhom": "New",
        "mo_ta": "New mô tả",
        "loai_nhom": "Loai mới",
    })
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["ten_nhom"] == "New"
    assert data["mo_ta"] == "New mô tả"
    assert data["loai_nhom"] == "Loai mới"


@pytest.mark.asyncio
async def test_delete_nhom_cascade_chi_tiet(
    client: AsyncClient, chu_toa_user, seed_test_users, db_session: AsyncSession,
):
    """Xoá nhóm → chi tiết bị cascade xoá theo."""
    create = await client.post(BASE_NHOM + "/", json={
        "ten_nhom": "Sẽ xoá",
        "chi_tiet": [
            {"cong_chuc_id": "aaaaaaaa-0001-0000-0000-000000000001"},
            {"cong_chuc_id": "aaaaaaaa-0002-0000-0000-000000000002"},
        ],
    })
    nhom_id = create.json()["data"]["id"]

    # Verify chi_tiet count = 2
    r = await db_session.execute(sa_text(
        "SELECT COUNT(*) FROM meeting.nhom_thanh_phan_chi_tiet WHERE nhom_id = :id"
    ), {"id": nhom_id})
    assert r.scalar() == 2

    # Delete
    resp = await client.delete(f"{BASE_NHOM}/{nhom_id}")
    assert resp.status_code == 200

    # Verify cascade
    r2 = await db_session.execute(sa_text(
        "SELECT COUNT(*) FROM meeting.nhom_thanh_phan_chi_tiet WHERE nhom_id = :id"
    ), {"id": nhom_id})
    assert r2.scalar() == 0

    # Get → 404
    r3 = await client.get(f"{BASE_NHOM}/{nhom_id}")
    assert r3.status_code == 404


# ════════════════════════════════════════════════════════════════════
# CRUD thành viên
# ════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_them_thanh_vien_batch(
    client: AsyncClient, chu_toa_user, seed_test_users,
):
    """Batch add — happy path + skip trùng (đã có hoặc duplicate trong request)."""
    create = await client.post(BASE_NHOM + "/", json={
        "ten_nhom": "Batch test",
        "chi_tiet": [
            {"cong_chuc_id": "aaaaaaaa-0001-0000-0000-000000000001"},
        ],
    })
    nhom_id = create.json()["data"]["id"]

    # Batch: 3 items — CC1 đã có (skip), CC2 mới, CC2 lặp lại (skip)
    r = await client.post(f"{BASE_NHOM}/{nhom_id}/thanh-vien/batch", json={
        "chi_tiet": [
            {"cong_chuc_id": "aaaaaaaa-0001-0000-0000-000000000001",
             "vai_tro": "THANH_VIEN"},
            {"cong_chuc_id": "aaaaaaaa-0002-0000-0000-000000000002",
             "vai_tro": "THU_KY", "loai_tham_du": "THAM_KHAO"},
            {"cong_chuc_id": "aaaaaaaa-0002-0000-0000-000000000002",
             "vai_tro": "CHU_TRI"},
        ],
    })
    assert r.status_code == 200, r.text
    data = r.json()["data"]
    assert data["so_them"] == 1
    assert data["so_bo_qua_trung"] == 2
    assert data["tong_thanh_vien"] == 2

    # Verify vai_tro của CC2 = THU_KY (lần đầu gặp được apply, lần lặp bị skip)
    detail = await client.get(f"{BASE_NHOM}/{nhom_id}")
    cc2 = next(
        x for x in detail.json()["data"]["chi_tiet"]
        if x["cong_chuc_id"] == "aaaaaaaa-0002-0000-0000-000000000002"
    )
    assert cc2["vai_tro"] == "THU_KY"
    assert cc2["loai_tham_du"] == "THAM_KHAO"


@pytest.mark.asyncio
async def test_batch_nhom_not_found_404(
    client: AsyncClient, chu_toa_user, seed_test_users,
):
    fake = "00000000-0000-0000-0000-000000000000"
    r = await client.post(f"{BASE_NHOM}/{fake}/thanh-vien/batch", json={
        "chi_tiet": [
            {"cong_chuc_id": "aaaaaaaa-0001-0000-0000-000000000001"},
        ],
    })
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_batch_empty_list_422(
    client: AsyncClient, chu_toa_user, seed_test_users,
):
    create = await client.post(BASE_NHOM + "/", json={"ten_nhom": "X"})
    nhom_id = create.json()["data"]["id"]

    r = await client.post(f"{BASE_NHOM}/{nhom_id}/thanh-vien/batch", json={"chi_tiet": []})
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_them_thanh_vien_duplicate_409(
    client: AsyncClient, chu_toa_user, seed_test_users,
):
    create = await client.post(BASE_NHOM + "/", json={
        "ten_nhom": "X",
        "chi_tiet": [{"cong_chuc_id": "aaaaaaaa-0001-0000-0000-000000000001"}],
    })
    nhom_id = create.json()["data"]["id"]

    # Add lại CC1 → 409
    r = await client.post(f"{BASE_NHOM}/{nhom_id}/thanh-vien", json={
        "cong_chuc_id": "aaaaaaaa-0001-0000-0000-000000000001",
    })
    assert r.status_code == 409
    assert r.json()["detail"]["error"]["code"] == "MEMBER_EXISTS"


@pytest.mark.asyncio
async def test_update_xoa_thanh_vien(
    client: AsyncClient, chu_toa_user, seed_test_users,
):
    create = await client.post(BASE_NHOM + "/", json={
        "ten_nhom": "X",
        "chi_tiet": [
            {"cong_chuc_id": "aaaaaaaa-0001-0000-0000-000000000001",
             "vai_tro": "THANH_VIEN"},
        ],
    })
    nhom_id = create.json()["data"]["id"]
    cc_id = "aaaaaaaa-0001-0000-0000-000000000001"

    # Update vai_tro → CHU_TRI
    r1 = await client.put(f"{BASE_NHOM}/{nhom_id}/thanh-vien/{cc_id}", json={
        "vai_tro": "CHU_TRI",
    })
    assert r1.status_code == 200
    assert r1.json()["data"]["vai_tro"] == "CHU_TRI"

    # Delete
    r2 = await client.delete(f"{BASE_NHOM}/{nhom_id}/thanh-vien/{cc_id}")
    assert r2.status_code == 200

    # Detail → chi_tiet rỗng
    r3 = await client.get(f"{BASE_NHOM}/{nhom_id}")
    assert r3.json()["data"]["chi_tiet"] == []


# ════════════════════════════════════════════════════════════════════
# MERGE — them-tu-nhom
# ════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_merge_happy_path(
    client: AsyncClient, chu_toa_user, seed_test_users,
):
    """Merge 1 nhóm có 2 thành viên (khác chu_toa) → so_them=2, tong=3."""
    # Tạo nhóm với 2 member khác chu_toa
    nhom = await client.post(BASE_NHOM + "/", json={
        "ten_nhom": "Để merge",
        "chi_tiet": [
            {"cong_chuc_id": "aaaaaaaa-0002-0000-0000-000000000002"},
            {"cong_chuc_id": "aaaaaaaa-0003-0000-0000-000000000003"},
        ],
    })
    nhom_id = nhom.json()["data"]["id"]

    # Tạo cuộc họp với chu_toa_user (CC1) + 0 thành phần ban đầu
    ch = await client.post(BASE_CH + "/", json=_ch_payload(
        seed_test_users["don_vi_a"], chu_toa_user.sub,
    ))
    assert ch.status_code == 201
    ch_id = ch.json()["data"]["id"]

    # Lưu ý: chu_toa cũng auto-thành thanh_phan từ tạo cuộc họp? Kiểm tra trước
    list_tp_before = await client.get(f"{BASE_CH}/{ch_id}/thanh-phan")
    so_truoc = len(list_tp_before.json()["data"])

    # Merge
    r = await client.post(f"{BASE_CH}/{ch_id}/thanh-phan/them-tu-nhom", json={
        "nhom_ids": [nhom_id],
    })
    assert r.status_code == 200, r.text
    data = r.json()["data"]
    assert data["so_them"] == 2
    assert data["so_bo_qua_trung"] == 0
    assert data["tong_thanh_phan"] == so_truoc + 2


@pytest.mark.asyncio
async def test_merge_skip_duplicate(
    client: AsyncClient, chu_toa_user, seed_test_users,
):
    """Merge lần 2 → so_them=0, so_bo_qua tăng."""
    nhom = await client.post(BASE_NHOM + "/", json={
        "ten_nhom": "Dup",
        "chi_tiet": [{"cong_chuc_id": "aaaaaaaa-0002-0000-0000-000000000002"}],
    })
    nhom_id = nhom.json()["data"]["id"]

    ch = await client.post(BASE_CH + "/", json=_ch_payload(
        seed_test_users["don_vi_a"], chu_toa_user.sub,
    ))
    ch_id = ch.json()["data"]["id"]

    # Merge lần 1
    r1 = await client.post(f"{BASE_CH}/{ch_id}/thanh-phan/them-tu-nhom", json={
        "nhom_ids": [nhom_id],
    })
    assert r1.json()["data"]["so_them"] == 1

    # Merge lần 2 — skip
    r2 = await client.post(f"{BASE_CH}/{ch_id}/thanh-phan/them-tu-nhom", json={
        "nhom_ids": [nhom_id],
    })
    assert r2.status_code == 200
    d2 = r2.json()["data"]
    assert d2["so_them"] == 0
    assert d2["so_bo_qua_trung"] == 1


@pytest.mark.asyncio
async def test_merge_auto_fill_thu_ky(
    client: AsyncClient, chu_toa_user, seed_test_users,
):
    """Cuộc họp có thu_ky_id=NULL + nhóm có vai_tro=THU_KY → auto-fill."""
    # Nhóm có 1 THU_KY
    nhom = await client.post(BASE_NHOM + "/", json={
        "ten_nhom": "Có thư ký",
        "chi_tiet": [
            {"cong_chuc_id": "aaaaaaaa-0002-0000-0000-000000000002",
             "vai_tro": "THU_KY"},
        ],
    })
    nhom_id = nhom.json()["data"]["id"]

    # Cuộc họp KHÔNG truyền thu_ky_id (NULL)
    ch = await client.post(BASE_CH + "/", json=_ch_payload(
        seed_test_users["don_vi_a"], chu_toa_user.sub, thu_ky_id=None,
    ))
    ch_id = ch.json()["data"]["id"]
    assert ch.json()["data"]["thu_ky_id"] is None

    # Merge
    r = await client.post(f"{BASE_CH}/{ch_id}/thanh-phan/them-tu-nhom", json={
        "nhom_ids": [nhom_id],
    })
    assert r.status_code == 200
    assert r.json()["data"]["thu_ky_auto_filled"] is True

    # Verify thu_ky_id đã được điền
    detail = await client.get(f"{BASE_CH}/{ch_id}")
    assert detail.json()["data"]["thu_ky_id"] == "aaaaaaaa-0002-0000-0000-000000000002"


@pytest.mark.asyncio
async def test_merge_giu_nguyen_thu_ky_neu_da_co(
    client: AsyncClient, chu_toa_user, seed_test_users,
):
    """Cuộc họp đã có thu_ky_id → KHÔNG ghi đè dù nhóm có THU_KY khác."""
    nhom = await client.post(BASE_NHOM + "/", json={
        "ten_nhom": "Có thư ký khác",
        "chi_tiet": [
            {"cong_chuc_id": "aaaaaaaa-0003-0000-0000-000000000003",
             "vai_tro": "THU_KY"},
        ],
    })
    nhom_id = nhom.json()["data"]["id"]

    ch = await client.post(BASE_CH + "/", json=_ch_payload(
        seed_test_users["don_vi_a"], chu_toa_user.sub,
        thu_ky_id="aaaaaaaa-0002-0000-0000-000000000002",
    ))
    ch_id = ch.json()["data"]["id"]

    r = await client.post(f"{BASE_CH}/{ch_id}/thanh-phan/them-tu-nhom", json={
        "nhom_ids": [nhom_id],
    })
    assert r.json()["data"]["thu_ky_auto_filled"] is False

    detail = await client.get(f"{BASE_CH}/{ch_id}")
    # thu_ky_id giữ nguyên CC2, không bị ghi đè bởi CC3
    assert detail.json()["data"]["thu_ky_id"] == "aaaaaaaa-0002-0000-0000-000000000002"


@pytest.mark.asyncio
async def test_merge_nhom_not_found_404(
    client: AsyncClient, chu_toa_user, seed_test_users,
):
    """nhom_id không tồn tại → 404."""
    ch = await client.post(BASE_CH + "/", json=_ch_payload(
        seed_test_users["don_vi_a"], chu_toa_user.sub,
    ))
    ch_id = ch.json()["data"]["id"]

    fake = "00000000-0000-0000-0000-000000000000"
    r = await client.post(f"{BASE_CH}/{ch_id}/thanh-phan/them-tu-nhom", json={
        "nhom_ids": [fake],
    })
    assert r.status_code == 404
    assert r.json()["detail"]["error"]["code"] == "NHOM_NOT_FOUND"


@pytest.mark.asyncio
async def test_merge_multi_nhom_uu_tien_nhom_dau_cho_thu_ky(
    client: AsyncClient, chu_toa_user, seed_test_users,
):
    """Truyền 2 nhóm đều có THU_KY → ưu tiên người trong nhóm đầu."""
    nhom_a = await client.post(BASE_NHOM + "/", json={
        "ten_nhom": "Nhóm A",
        "chi_tiet": [
            {"cong_chuc_id": "aaaaaaaa-0002-0000-0000-000000000002",
             "vai_tro": "THU_KY"},
        ],
    })
    nhom_b = await client.post(BASE_NHOM + "/", json={
        "ten_nhom": "Nhóm B",
        "chi_tiet": [
            {"cong_chuc_id": "aaaaaaaa-0003-0000-0000-000000000003",
             "vai_tro": "THU_KY"},
        ],
    })
    nhom_a_id = nhom_a.json()["data"]["id"]
    nhom_b_id = nhom_b.json()["data"]["id"]

    ch = await client.post(BASE_CH + "/", json=_ch_payload(
        seed_test_users["don_vi_a"], chu_toa_user.sub,
    ))
    ch_id = ch.json()["data"]["id"]

    r = await client.post(f"{BASE_CH}/{ch_id}/thanh-phan/them-tu-nhom", json={
        "nhom_ids": [nhom_a_id, nhom_b_id],
    })
    assert r.json()["data"]["thu_ky_auto_filled"] is True

    detail = await client.get(f"{BASE_CH}/{ch_id}")
    # Ưu tiên nhóm A → CC2
    assert detail.json()["data"]["thu_ky_id"] == "aaaaaaaa-0002-0000-0000-000000000002"
