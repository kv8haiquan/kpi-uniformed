"""Kiểm thử báo cáo Thống kê tài liệu họp trên dữ liệu đã di trú.

Báo cáo này quyết định Văn phòng có nhắc đơn vị nộp tài liệu hay không, nên
sai là nhắc oan. Test chạy trên 489 cuộc họp và 813 tài liệu thật.

    ./scripts/dev.sh test meeting_service/tests/test_thong_ke_tai_lieu.py -v
"""

from __future__ import annotations

import pytest
from sqlalchemy import text as sa_text
from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = pytest.mark.asyncio

BASE = "/api/v1/hop-khong-giay/thong-ke-tai-lieu"


async def _co_du_lieu(db: AsyncSession) -> bool:
    n = (await db.execute(sa_text(
        "SELECT count(*) FROM meeting.cuoc_hop WHERE nguon='LICH_CONG_TAC'"
    ))).scalar_one()
    return n > 0


# ── cấu trúc kết quả ──────────────────────────────────────────────────

async def test_bao_cao_tra_du_tong_hop(client, chu_toa_user):
    resp = await client.get(f"{BASE}/")
    assert resp.status_code == 200, resp.text
    d = resp.json()["data"]
    for k in ("tong", "DA_GAN_TAI_LIEU", "THIEU_TAI_LIEU",
              "CHUA_GIAO_CHUAN_BI", "CO_GIAO_CHUAN_BI"):
        assert k in d["tong_hop"]


async def test_tinh_trang_sai_bi_tu_choi(client, chu_toa_user):
    resp = await client.get(f"{BASE}/?tinh-trang=KHONG_TON_TAI")
    assert resp.status_code == 400
    assert resp.json()["detail"]["error"]["code"] == "TINH_TRANG_KHONG_HOP_LE"


async def test_danh_muc_du_5_tinh_trang(client, chu_toa_user):
    resp = await client.get(f"{BASE}/tinh-trang")
    ma = {x["ma"] for x in resp.json()["data"]}
    assert ma == {"TAT_CA", "CO_GIAO_CHUAN_BI", "DA_GAN_TAI_LIEU",
                  "THIEU_TAI_LIEU", "CHUA_GIAO_CHUAN_BI"}


# ── quy tắc nghiệp vụ ─────────────────────────────────────────────────

async def test_loai_tru_lich_truc_ban(client, db_session, chu_toa_user):
    """Trực ban không có nghĩa vụ chuẩn bị tài liệu — phải loại khỏi báo cáo."""
    if not await _co_du_lieu(db_session):
        pytest.skip("chưa có dữ liệu di trú")
    resp = await client.get(f"{BASE}/?gioi-han=2000")
    assert all(d["loai_lich"] != "TRUC_BAN" for d in resp.json()["data"]["dong"])


async def test_mac_dinh_khong_tinh_lich_huy(client, db_session, chu_toa_user):
    if not await _co_du_lieu(db_session):
        pytest.skip("chưa có dữ liệu di trú")
    resp = await client.get(f"{BASE}/?gioi-han=2000")
    assert all(d["trang_thai"] != "HUY" for d in resp.json()["data"]["dong"])


async def test_bat_tinh_lich_huy_thi_co(client, db_session, chu_toa_user):
    n = (await db_session.execute(sa_text(
        "SELECT count(*) FROM meeting.cuoc_hop "
        "WHERE trang_thai='HUY' AND is_deleted=false"))).scalar_one()
    if not n:
        pytest.skip("không có lịch đã hủy")
    resp = await client.get(f"{BASE}/?tinh-lich-huy=true&gioi-han=2000")
    assert any(d["trang_thai"] == "HUY" for d in resp.json()["data"]["dong"])


async def test_chua_giao_chuan_bi_khi_khong_co_don_vi(
        client, db_session, chu_toa_user):
    if not await _co_du_lieu(db_session):
        pytest.skip("chưa có dữ liệu di trú")
    resp = await client.get(
        f"{BASE}/?tinh-trang=CHUA_GIAO_CHUAN_BI&gioi-han=2000")
    for d in resp.json()["data"]["dong"]:
        assert not (d["don_vi_chuan_bi"] or "").strip()


async def test_da_gan_tai_lieu_phai_co_tai_lieu_chuan_bi(
        client, db_session, chu_toa_user):
    """Điểm mấu chốt: 'đã gắn' tính theo tài liệu CHUẨN BỊ, không tính giấy mời."""
    if not await _co_du_lieu(db_session):
        pytest.skip("chưa có dữ liệu di trú")
    resp = await client.get(f"{BASE}/?tinh-trang=DA_GAN_TAI_LIEU&gioi-han=2000")
    for d in resp.json()["data"]["dong"]:
        assert d["so_tai_lieu_chuan_bi"] > 0
        assert (d["don_vi_chuan_bi"] or "").strip()


async def test_thieu_tai_lieu_co_giao_nhung_khong_co_tai_lieu(
        client, db_session, chu_toa_user):
    if not await _co_du_lieu(db_session):
        pytest.skip("chưa có dữ liệu di trú")
    resp = await client.get(f"{BASE}/?tinh-trang=THIEU_TAI_LIEU&gioi-han=2000")
    for d in resp.json()["data"]["dong"]:
        assert (d["don_vi_chuan_bi"] or "").strip(), "phải có đơn vị được giao"
        assert d["so_tai_lieu_chuan_bi"] == 0


async def test_cuoc_hop_chi_co_giay_moi_bi_tinh_la_thieu(
        client, db_session, chu_toa_user):
    """Nộp mỗi giấy mời thì vẫn là chưa hoàn thành nghĩa vụ chuẩn bị.

    Đây là lý do tồn tại của quy tắc giấy mời — nếu đếm mọi file thì cuộc họp
    chỉ có giấy mời sẽ bị báo nhầm thành đã nộp đủ.
    """
    if not await _co_du_lieu(db_session):
        pytest.skip("chưa có dữ liệu di trú")
    resp = await client.get(f"{BASE}/?tinh-trang=THIEU_TAI_LIEU&gioi-han=2000")
    dong = resp.json()["data"]["dong"]
    chi_giay_moi = [d for d in dong if d["so_giay_moi"] > 0]
    for d in chi_giay_moi:
        assert d["so_tai_lieu"] > 0, "có file nhưng vẫn thiếu tài liệu chuẩn bị"
        assert d["so_tai_lieu_chuan_bi"] == 0


async def test_tong_hop_cong_dung_bang_tong(client, db_session, chu_toa_user):
    if not await _co_du_lieu(db_session):
        pytest.skip("chưa có dữ liệu di trú")
    th = (await client.get(f"{BASE}/?gioi-han=2000")).json()["data"]["tong_hop"]
    assert (th["DA_GAN_TAI_LIEU"] + th["THIEU_TAI_LIEU"]
            + th["CHUA_GIAO_CHUAN_BI"]) == th["tong"]
    assert th["CO_GIAO_CHUAN_BI"] == th["DA_GAN_TAI_LIEU"] + th["THIEU_TAI_LIEU"]


# ── bộ lọc ────────────────────────────────────────────────────────────

async def test_loc_theo_khoang_ngay(client, db_session, chu_toa_user):
    if not await _co_du_lieu(db_session):
        pytest.skip("chưa có dữ liệu di trú")
    ngay = (await db_session.execute(sa_text(
        "SELECT min(ngay_hien_thi) FROM meeting.cuoc_hop "
        "WHERE nguon='LICH_CONG_TAC'"))).scalar_one()
    resp = await client.get(f"{BASE}/?tu-ngay={ngay}&den-ngay={ngay}")
    for d in resp.json()["data"]["dong"]:
        assert d["ngay"] == ngay.isoformat()


async def test_tim_theo_tu_khoa(client, db_session, chu_toa_user):
    if not await _co_du_lieu(db_session):
        pytest.skip("chưa có dữ liệu di trú")
    dv = (await db_session.execute(sa_text(
        "SELECT don_vi_chuan_bi FROM meeting.cuoc_hop "
        "WHERE don_vi_chuan_bi IS NOT NULL LIMIT 1"))).scalar()
    if not dv:
        pytest.skip("không có đơn vị chuẩn bị")
    resp = await client.get(f"{BASE}/?tu-khoa={dv}&gioi-han=2000")
    assert resp.status_code == 200
    assert resp.json()["data"]["dong"]


# ── xuất Excel ────────────────────────────────────────────────────────

async def test_xuat_excel(client, chu_toa_user):
    resp = await client.get(f"{BASE}/xuat-excel?gioi-han=50")
    assert resp.status_code == 200
    assert "spreadsheetml" in resp.headers["content-type"]
    assert "attachment" in resp.headers["content-disposition"]
    # PK.. là chữ ký của tệp zip, mà .xlsx là zip.
    assert resp.content[:2] == b"PK"
    assert len(resp.content) > 3000
