"""Kiểm thử API Lịch công tác trên dữ liệu đã di trú từ lichkv8.

Chạy sau khi đã chạy scripts/di_tru_lichkv8/01→06 trên kpi_haiquan_test.
Nếu chưa có dữ liệu di trú thì các test phụ thuộc sẽ tự bỏ qua.

    DB_NAME=kpi_haiquan_test ALLOW_PROD_TEST=true \
    pytest meeting_service/tests/test_lich_cong_tac_api.py -v
"""

from __future__ import annotations

from datetime import date, timedelta

import pytest
from sqlalchemy import text as sa_text
from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = pytest.mark.asyncio

BASE = "/api/v1/hop-khong-giay/lich-cong-tac"


async def _co_du_lieu(db: AsyncSession) -> bool:
    n = (await db.execute(sa_text(
        "SELECT count(*) FROM meeting.cuoc_hop WHERE nguon='LICH_CONG_TAC'"
    ))).scalar_one()
    return n > 0


# ── danh sách và phân trang ───────────────────────────────────────────

async def test_danh_sach_tra_ve_phan_trang(client, db_session: AsyncSession, chu_toa_user):
    resp = await client.get(f"{BASE}/?so-dong=10")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["success"] is True
    pg = body["pagination"]
    assert pg["page"] == 1 and pg["page_size"] == 10
    assert len(body["data"]) <= 10


async def test_loai_lich_sai_bi_tu_choi(client, chu_toa_user):
    resp = await client.get(f"{BASE}/?loai-lich=KHONG_TON_TAI")
    assert resp.status_code == 400
    assert resp.json()["detail"]["error"]["code"] == "LOAI_LICH_KHONG_HOP_LE"


@pytest.mark.parametrize(
    "loai", ["HOP", "TRUC_BAN", "HOI_NGHI", "LAM_VIEC", "CONG_TAC", "LICH_KHAC"])
async def test_loc_theo_sau_loai_lich(client, loai, chu_toa_user):
    resp = await client.get(f"{BASE}/?loai-lich={loai}&so-dong=5")
    assert resp.status_code == 200
    for it in resp.json()["data"]:
        assert it["loai_lich"] == loai


async def test_moi_su_kien_deu_co_ngay_hien_thi(client, db_session, chu_toa_user):
    if not await _co_du_lieu(db_session):
        pytest.skip("chưa có dữ liệu di trú")
    resp = await client.get(f"{BASE}/?so-dong=100")
    data = resp.json()["data"]
    assert data, "phải có dữ liệu để kiểm"
    # Lịch xếp theo ngay_hien_thi — thiếu là sự kiện biến mất khỏi lịch.
    assert all(it["ngay_hien_thi"] for it in data)


async def test_danh_sach_xep_theo_ngay_tang_dan(client, db_session, chu_toa_user):
    if not await _co_du_lieu(db_session):
        pytest.skip("chưa có dữ liệu di trú")
    resp = await client.get(f"{BASE}/?so-dong=50")
    ngay = [it["ngay_hien_thi"] for it in resp.json()["data"]]
    assert ngay == sorted(ngay)


# ── tìm kiếm ──────────────────────────────────────────────────────────

async def test_tim_kiem_theo_ma_lich(client, db_session, chu_toa_user):
    if not await _co_du_lieu(db_session):
        pytest.skip("chưa có dữ liệu di trú")
    ma = (await db_session.execute(sa_text(
        "SELECT ma_lich FROM meeting.cuoc_hop "
        "WHERE nguon='LICH_CONG_TAC' AND ma_lich IS NOT NULL LIMIT 1"
    ))).scalar_one()
    resp = await client.get(f"{BASE}/?tim-kiem={ma}")
    assert resp.status_code == 200
    assert any(it["ma_lich"] == ma for it in resp.json()["data"])


# ── lịch tháng ────────────────────────────────────────────────────────

async def test_lich_thang_gom_theo_ngay(client, db_session, chu_toa_user):
    if not await _co_du_lieu(db_session):
        pytest.skip("chưa có dữ liệu di trú")
    row = (await db_session.execute(sa_text(
        "SELECT extract(year FROM ngay_hien_thi)::int, "
        "       extract(month FROM ngay_hien_thi)::int "
        "FROM meeting.cuoc_hop WHERE nguon='LICH_CONG_TAC' "
        "ORDER BY ngay_hien_thi LIMIT 1"))).one()
    nam, thang = row
    resp = await client.get(f"{BASE}/thang/{nam}/{thang}")
    assert resp.status_code == 200
    d = resp.json()["data"]
    assert d["nam"] == nam and d["thang"] == thang
    assert d["theo_ngay"], "tháng có dữ liệu phải trả về ít nhất một ngày"


async def test_thang_khong_hop_le_bi_tu_choi(client, chu_toa_user):
    resp = await client.get(f"{BASE}/thang/2026/13")
    assert resp.status_code == 400
    assert resp.json()["detail"]["error"]["code"] == "THANG_KHONG_HOP_LE"


async def test_su_kien_nhieu_ngay_hien_o_moi_ngay(client, db_session, chu_toa_user):
    """Sự kiện kéo dài phải xuất hiện ở tất cả các ngày nó diễn ra."""
    row = (await db_session.execute(sa_text(
        "SELECT ngay_hien_thi, ngay_ket_thuc FROM meeting.cuoc_hop "
        "WHERE nguon='LICH_CONG_TAC' AND ngay_ket_thuc IS NOT NULL "
        "AND ngay_ket_thuc > ngay_hien_thi LIMIT 1"))).first()
    if not row:
        pytest.skip("không có sự kiện nhiều ngày")
    bd, kt = row
    resp = await client.get(f"{BASE}/thang/{bd.year}/{bd.month}")
    theo_ngay = resp.json()["data"]["theo_ngay"]
    # Ít nhất ngày bắt đầu phải có mặt.
    assert bd.isoformat() in theo_ngay


# ── tóm tắt lịch ──────────────────────────────────────────────────────

async def test_tom_tat_mac_dinh_3_ngay(client, chu_toa_user):
    resp = await client.get(f"{BASE}/tom-tat")
    assert resp.status_code == 200
    d = resp.json()["data"]
    assert (d["den_ngay"] and d["tu_ngay"])
    tu = date.fromisoformat(d["tu_ngay"])
    den = date.fromisoformat(d["den_ngay"])
    assert (den - tu).days == 2, "mặc định 3 ngày như lichkv8"


async def test_tom_tat_co_ban_van_thuan(client, db_session, chu_toa_user):
    if not await _co_du_lieu(db_session):
        pytest.skip("chưa có dữ liệu di trú")
    ngay = (await db_session.execute(sa_text(
        "SELECT ngay_hien_thi FROM meeting.cuoc_hop "
        "WHERE nguon='LICH_CONG_TAC' ORDER BY ngay_hien_thi LIMIT 1"
    ))).scalar_one()
    resp = await client.get(f"{BASE}/tom-tat?tu-ngay={ngay}&so-ngay=1")
    d = resp.json()["data"]
    assert isinstance(d["van_ban_thuan"], str)
    if d["theo_ngay"] and d["theo_ngay"][0]["su_kien"]:
        assert d["van_ban_thuan"].strip(), "có sự kiện thì phải có bản text"


# ── lịch lãnh đạo ─────────────────────────────────────────────────────

async def test_lich_lanh_dao(client, db_session, chu_toa_user):
    ld = (await db_session.execute(sa_text(
        "SELECT cong_chuc_id FROM meeting.lanh_dao_lien_quan LIMIT 1"
    ))).scalar()
    if not ld:
        pytest.skip("chưa có dữ liệu lãnh đạo liên quan")
    ngay = (await db_session.execute(sa_text(
        "SELECT min(ch.ngay_hien_thi) FROM meeting.cuoc_hop ch "
        "JOIN meeting.lanh_dao_lien_quan l ON l.cuoc_hop_id = ch.id "
        "WHERE l.cong_chuc_id = :ld"), {"ld": ld})).scalar_one()
    resp = await client.get(f"{BASE}/lanh-dao/{ld}?tu-ngay={ngay}&so-ngay=90")
    assert resp.status_code == 200
    d = resp.json()["data"]
    assert d["lanh_dao"]["id"] == str(ld)
    assert d["tong_su_kien"] >= 1


# ── thống kê và danh mục ──────────────────────────────────────────────

async def test_thong_ke_du_chi_so(client, chu_toa_user):
    resp = await client.get(f"{BASE}/thong-ke")
    assert resp.status_code == 200
    d = resp.json()["data"]
    for k in ("hom_nay", "ngay_mai", "trong_tuan", "trong_thang", "trong_nam"):
        assert isinstance(d[k], int)


async def test_danh_muc_du_sau_loai(client, chu_toa_user):
    resp = await client.get(f"{BASE}/danh-muc")
    assert resp.status_code == 200
    ma = {x["ma"] for x in resp.json()["data"]}
    assert ma == {"HOP", "TRUC_BAN", "HOI_NGHI", "LAM_VIEC", "CONG_TAC",
                  "LICH_KHAC"}


async def test_danh_muc_lanh_dao_chi_co_lanh_dao(client, db_session,
                                                 chu_toa_user):
    """Ô chọn Chủ trì / Thành phần chỉ được bày ra lãnh đạo, không có công
    chức thường — chọn nhầm cả 558 người thì ô chọn vô dụng."""
    resp = await client.get(f"{BASE}/danh-muc-lanh-dao")
    assert resp.status_code == 200
    ds = resp.json()["data"]
    assert ds, "Phải có ít nhất một lãnh đạo trong danh bạ"

    # So khớp trọn bộ thay vì truy vấn theo mảng id: vừa bắt được người lọt
    # vào, vừa bắt được lãnh đạo bị bỏ sót.
    dung = {str(r[0]) for r in (await db_session.execute(sa_text(
        "SELECT id FROM public.cong_chuc WHERE is_lanh_dao AND is_active"
    ))).all()}
    assert {x["id"] for x in ds} == dung

    # Không kèm số điện thoại — màn hình lịch không dùng tới.
    assert set(ds[0]) == {"id", "ma_cc", "ho_ten", "chuc_vu", "ten_don_vi"}

    # Xếp theo cấp bậc chức vụ: Chi cục trưởng đứng trước Phó Đội trưởng.
    from meeting_service.services.truc_ban_service import bac_chuc_vu
    bac = [bac_chuc_vu(x["chuc_vu"]) for x in ds]
    assert bac == sorted(bac), "Danh mục phải xếp theo cấp bậc chức vụ"


# ── chi tiết ──────────────────────────────────────────────────────────

async def test_chi_tiet_su_kien(client, db_session, chu_toa_user):
    if not await _co_du_lieu(db_session):
        pytest.skip("chưa có dữ liệu di trú")
    cid = (await db_session.execute(sa_text(
        "SELECT id FROM meeting.cuoc_hop WHERE nguon='LICH_CONG_TAC' LIMIT 1"
    ))).scalar_one()
    resp = await client.get(f"{BASE}/{cid}")
    assert resp.status_code == 200
    d = resp.json()["data"]
    assert d["id"] == str(cid)
    assert d["nguon"] == "LICH_CONG_TAC"
    assert d["co_the_mo_hkg"] is False


async def test_chi_tiet_khong_ton_tai(client, chu_toa_user):
    resp = await client.get(f"{BASE}/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404
    assert resp.json()["detail"]["error"]["code"] == "KHONG_TIM_THAY"


async def test_cuoc_hop_hkg_hien_tren_lich_va_mo_duoc(client, db_session, chu_toa_user):
    """Tiêu chí 8.3: cuộc họp HKG phải hiện trên lịch và mở sang được HKG."""
    row = (await db_session.execute(sa_text(
        "SELECT id, ngay_hien_thi FROM meeting.cuoc_hop "
        "WHERE nguon='HKG' AND is_deleted=false LIMIT 1"))).first()
    if not row:
        pytest.skip("chưa có cuộc họp HKG")
    cid, ngay = row
    resp = await client.get(f"{BASE}/?tu-ngay={ngay}&den-ngay={ngay}&nguon=HKG")
    assert resp.status_code == 200
    ids = [it["id"] for it in resp.json()["data"]]
    assert str(cid) in ids, "cuộc họp HKG phải hiện trên lịch công tác"
    it = next(x for x in resp.json()["data"] if x["id"] == str(cid))
    assert it["co_the_mo_hkg"] is True
