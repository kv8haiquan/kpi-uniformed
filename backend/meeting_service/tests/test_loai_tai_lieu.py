"""Loại tài liệu — lưu MÃ, không lưu nhãn (meeting_025).

Trước đây loại tài liệu được lưu bằng chính chuỗi NHÃN vào `tai_lieu.mo_ta`.
Hậu quả dựng lại được trên bản sao dữ liệu thật:

    Trước khi đổi tên: 'Giấy mời'     đang dùng = 1
    Sau khi đổi tên  : 'Giấy mời họp' đang dùng = 0

Tức chỉ cần bấm "Sửa tên" một lần trên màn hình Quản trị danh mục là mọi tài
liệu mang loại đó thành mồ côi, VÀ số "đang dùng" tụt về 0 nên chính màn hình
đó cho phép xoá một mục vẫn còn tài liệu — không cảnh báo gì.

Bộ test dưới đây khoá lại hành vi đúng: đổi tên bao nhiêu lần thì liên kết
vẫn nguyên.

    DB_NAME=kpi_haiquan_test ALLOW_PROD_TEST=true \
    pytest meeting_service/tests/test_loai_tai_lieu.py -v
"""

from __future__ import annotations

import io
import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import text as sa_text
from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = pytest.mark.asyncio

BASE = "/api/v1/hop-khong-giay/tai-lieu"
BASE_HOP = "/api/v1/hop-khong-giay/cuoc-hop"
BASE_DM = "/api/v1/hop-khong-giay/danh-muc"


def _payload_hop(don_vi_id, chu_toa_id) -> dict:
    return {
        "tieu_de": "Test loại tài liệu",
        "khoi": "CHUYEN_MON",
        "hinh_thuc": "TRUC_TIEP",
        "ngay_hop": "2026-09-15",
        "gio_bat_dau": "08:30",
        "don_vi_to_chuc_id": str(don_vi_id),
        "chu_toa_id": str(chu_toa_id),
        "thanh_phan": [],
    }


@pytest.fixture
async def cuoc_hop(client: AsyncClient, seed_test_users, chu_toa_user) -> str:
    r = await client.post(BASE_HOP + "/",
                          json=_payload_hop(seed_test_users["don_vi_a"],
                                            chu_toa_user.sub))
    assert r.status_code in (200, 201), r.text
    return r.json()["data"]["id"]


async def _tai_len(client: AsyncClient, ch: str, loai: str | None,
                   ten="tai-lieu.pdf"):
    data = {"cuoc_hop_id": ch}
    if loai is not None:
        data["loai_tai_lieu"] = loai
    return await client.post(
        BASE + "/upload", data=data,
        files={"file": (ten, io.BytesIO(b"%PDF-1.4 x"), "application/pdf")})


# ── ghi và đọc ────────────────────────────────────────────────────────

async def test_luu_ma_chu_khong_luu_nhan(
    client: AsyncClient, db_session: AsyncSession, cuoc_hop, chu_toa_user,
):
    r = await _tai_len(client, cuoc_hop, "GIAY_MOI")
    assert r.status_code == 201, r.text
    assert r.json()["data"]["loai_tai_lieu"] == "GIAY_MOI"

    trong_csdl = (await db_session.execute(sa_text(
        "SELECT loai_tai_lieu, mo_ta FROM meeting.tai_lieu WHERE id = :i"
    ), {"i": r.json()["data"]["id"]})).first()
    assert trong_csdl.loai_tai_lieu == "GIAY_MOI"
    # `mo_ta` phải trở lại đúng nghĩa mô tả tự do, không gánh thêm loại.
    assert trong_csdl.mo_ta is None


async def test_danh_sach_kem_nhan_de_khoi_goi_them_danh_muc(
    client: AsyncClient, cuoc_hop, chu_toa_user,
):
    await _tai_len(client, cuoc_hop, "BAO_CAO")
    ds = (await client.get(f"{BASE_HOP}/{cuoc_hop}/tai-lieu")).json()["data"]
    assert len(ds) == 1
    assert ds[0]["loai_tai_lieu"] == "BAO_CAO"
    assert ds[0]["loai_nhan"] == "Báo cáo"


async def test_khong_bat_buoc_co_loai(client: AsyncClient, cuoc_hop,
                                      chu_toa_user):
    """854 tài liệu đã di trú đều chưa có loại — bắt buộc là chặn cả kho cũ."""
    r = await _tai_len(client, cuoc_hop, None)
    assert r.status_code == 201, r.text
    assert r.json()["data"]["loai_tai_lieu"] is None


async def test_ma_khong_co_trong_danh_muc_bi_chan(
    client: AsyncClient, cuoc_hop, chu_toa_user,
):
    r = await _tai_len(client, cuoc_hop, "KHONG_CO_MA_NAY")
    assert r.status_code == 422
    assert r.json()["detail"]["error"]["code"] == "LOAI_TAI_LIEU_KHONG_HOP_LE"


async def test_muc_da_tat_khong_dat_moi_duoc(
    client: AsyncClient, db_session: AsyncSession, cuoc_hop, chu_toa_user,
):
    """Tắt một loại là để ngừng dùng cho tài liệu MỚI — nếu vẫn đặt được thì
    nút Tắt không có tác dụng gì."""
    await db_session.execute(sa_text("""
        UPDATE meeting.danh_muc SET is_active = false
         WHERE nhom = 'LOAI_TAI_LIEU' AND ma = 'KET_LUAN'"""))
    await db_session.flush()

    r = await _tai_len(client, cuoc_hop, "KET_LUAN")
    assert r.status_code == 422


# ── điểm gãy cũ: đổi tên nhãn ─────────────────────────────────────────

async def test_doi_ten_nhan_khong_lam_mo_coi_tai_lieu(
    client: AsyncClient, db_session: AsyncSession, cuoc_hop, admin_user,
    chu_toa_user,
):
    """Đây chính là lỗi đã dựng lại được trên dữ liệu thật.

    Trước meeting_025: đổi tên xong thì `dem_su_dung` trả 0 và màn hình quản
    trị cho xoá mất mục vẫn còn tài liệu.
    """
    r = await _tai_len(client, cuoc_hop, "GIAY_MOI")
    assert r.status_code == 201, r.text
    tl_id = r.json()["data"]["id"]

    from meeting_service.tests.conftest import _make_user, _set_user
    _set_user(_make_user("TEST-G3-001", None, vai_tro="ADMIN", is_admin=True))

    dm = next(x for x in (await client.get(
        BASE_DM + "/", params={"nhom": "LOAI_TAI_LIEU", "dem-su-dung": True}
    )).json()["data"] if x["ma"] == "GIAY_MOI")
    assert dm["dang_su_dung"] == 1

    r = await client.patch(f"{BASE_DM}/{dm['id']}",
                           json={"nhan": "Giấy mời họp"})
    assert r.status_code == 200, r.text

    sau = next(x for x in (await client.get(
        BASE_DM + "/", params={"nhom": "LOAI_TAI_LIEU", "dem-su-dung": True}
    )).json()["data"] if x["ma"] == "GIAY_MOI")
    assert sau["nhan"] == "Giấy mời họp"
    assert sau["dang_su_dung"] == 1, \
        "đổi tên xong mà đếm về 0 — tài liệu lại thành mồ côi như trước"

    # Tài liệu vẫn giữ nguyên mã, và nhãn trả về đã đổi theo.
    con = (await db_session.execute(sa_text(
        "SELECT loai_tai_lieu FROM meeting.tai_lieu WHERE id = :i"
    ), {"i": tl_id})).scalar_one()
    assert con == "GIAY_MOI"


async def test_khong_xoa_duoc_muc_dang_co_tai_lieu(
    client: AsyncClient, cuoc_hop, admin_user, chu_toa_user,
):
    r = await _tai_len(client, cuoc_hop, "BIEN_BAN")
    assert r.status_code == 201, r.text

    from meeting_service.tests.conftest import _make_user, _set_user
    _set_user(_make_user("TEST-G3-001", None, vai_tro="ADMIN", is_admin=True))

    dm = next(x for x in (await client.get(
        BASE_DM + "/", params={"nhom": "LOAI_TAI_LIEU"}
    )).json()["data"] if x["ma"] == "BIEN_BAN")

    r = await client.delete(f"{BASE_DM}/{dm['id']}")
    assert r.status_code == 409, r.text
    assert r.json()["detail"]["error"]["code"] == "DM_DANG_SU_DUNG"


# ── sửa loại sau khi đã tải lên ───────────────────────────────────────

async def test_sua_loai_sau_khi_tai_len(client: AsyncClient, cuoc_hop,
                                        chu_toa_user):
    r = await _tai_len(client, cuoc_hop, "GIAY_MOI")
    tl_id = r.json()["data"]["id"]

    r = await client.patch(f"{BASE}/{tl_id}",
                           json={"loai_tai_lieu": "TAI_LIEU_HOP"})
    assert r.status_code == 200, r.text
    assert r.json()["data"]["loai_tai_lieu"] == "TAI_LIEU_HOP"


async def test_sua_sang_ma_khong_hop_le_bi_chan(client: AsyncClient, cuoc_hop,
                                                chu_toa_user):
    r = await _tai_len(client, cuoc_hop, "GIAY_MOI")
    tl_id = r.json()["data"]["id"]

    r = await client.patch(f"{BASE}/{tl_id}", json={"loai_tai_lieu": "BAY"})
    assert r.status_code == 422
    assert r.json()["detail"]["error"]["code"] == "LOAI_TAI_LIEU_KHONG_HOP_LE"
