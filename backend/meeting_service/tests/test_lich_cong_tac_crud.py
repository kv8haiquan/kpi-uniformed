"""Kiểm thử quản lý lịch công tác — G4.3.

Ba điểm dễ hỏng nhất, mỗi điểm một nhóm test:

  1. `ma_lich` phải liên tục và không trùng, kể cả khi hai người lưu cùng lúc.
  2. Dòng nguồn HKG KHÔNG được sửa qua màn hình lịch — cuộc họp có quy trình
     riêng (thành phần, điểm danh, biên bản, thông báo Zalo).
  3. Huỷ là đổi trạng thái, không phải xoá.

    ./scripts/dev.sh test meeting_service/tests/test_lich_cong_tac_crud.py -v
"""

from __future__ import annotations

import asyncio
from datetime import date, time
from uuid import UUID

import pytest
from sqlalchemy import text as sa_text
from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = pytest.mark.asyncio

BASE = "/api/v1/hop-khong-giay/lich-cong-tac"


def _lich_moi(**ghi_de) -> dict:
    d = {
        "tieu_de": "TEST G4.3 — họp giao ban thử nghiệm",
        "loai_lich": "HOP",
        "ngay_hop": "2026-09-15",
        "gio_bat_dau": "08:00:00",
        "dia_diem": "Phòng họp thử nghiệm",
    }
    d.update(ghi_de)
    return d


async def _xoa_sach(db: AsyncSession) -> None:
    """Dọn mọi lịch do test tạo. Nhận diện bằng tiền tố tiêu đề."""
    await db.execute(sa_text(
        "DELETE FROM meeting.lanh_dao_lien_quan WHERE cuoc_hop_id IN "
        "(SELECT id FROM meeting.cuoc_hop WHERE tieu_de LIKE 'TEST G4.3%')"))
    await db.execute(sa_text(
        "DELETE FROM common.audit_log WHERE doi_tuong_id IN "
        "(SELECT id FROM meeting.cuoc_hop WHERE tieu_de LIKE 'TEST G4.3%')"))
    await db.execute(sa_text(
        "DELETE FROM meeting.cuoc_hop WHERE tieu_de LIKE 'TEST G4.3%'"))
    await db.commit()


@pytest.fixture
async def don_dep(db_session: AsyncSession):
    await _xoa_sach(db_session)
    yield
    await _xoa_sach(db_session)


# ── tạo ───────────────────────────────────────────────────────────────

async def test_tao_lich_sinh_ma_va_ngay_hien_thi(client, admin_user, don_dep):
    resp = await client.post(f"{BASE}/", json=_lich_moi())
    assert resp.status_code == 201, resp.text
    d = resp.json()["data"]

    assert d["ma_lich"].startswith("LH")
    assert len(d["ma_lich"]) >= 6
    assert d["nguon"] == "LICH_CONG_TAC"
    # Không truyền ngay_hien_thi thì phải tự lấy ngày bắt đầu, nếu không sự
    # kiện sẽ không hiện trên lịch (lịch xếp theo ngay_hien_thi).
    assert d["ngay_hien_thi"] == d["ngay_hop"] == "2026-09-15"
    assert d["trang_thai"] == "LEN_KE_HOACH"


async def test_ma_lich_khong_trung_khi_tao_dong_thoi(engine, admin_user,
                                                     db_session, don_dep):
    """Hai người bấm Lưu cùng lúc vẫn phải ra hai mã khác nhau.

    Không có khoá thì cả hai cùng đọc ra một `max(ma_lich)` rồi cùng +1 và sinh
    ra mã trùng.

    Phải đi thẳng vào service với **hai session riêng**: fixture `client` dùng
    chung một AsyncSession cho mọi request, mà SQLAlchemy không cho hai coroutine
    flush cùng lúc trên một session — gọi qua HTTP sẽ vỡ vì lý do đó chứ không
    phải vì thiếu khoá, nên không kiểm được điều đang cần kiểm.
    """
    from sqlalchemy.ext.asyncio import async_sessionmaker

    from meeting_service.services.lich_cong_tac_service import LichCongTacService

    nguoi_id = UUID(admin_user.sub)
    tao_session = async_sessionmaker(engine, expire_on_commit=False)

    async def tao_mot(i: int) -> str:
        async with tao_session() as s:
            kq = await LichCongTacService(s).tao(
                {"tieu_de": f"TEST G4.3 đồng thời {i}",
                 "loai_lich": "HOP",
                 "ngay_hop": date(2026, 9, 15),
                 "gio_bat_dau": time(8, 0)},
                nguoi_id=nguoi_id)
            return kq["ma_lich"]

    ma = await asyncio.gather(*[tao_mot(i) for i in range(5)])
    assert len(set(ma)) == 5, f"có mã trùng: {ma}"


async def test_loai_lich_sai_bi_tu_choi(client, admin_user, don_dep):
    resp = await client.post(f"{BASE}/", json=_lich_moi(loai_lich="KHONG_CO"))
    assert resp.status_code == 422


async def test_ngay_ket_thuc_truoc_ngay_bat_dau_bi_tu_choi(client, admin_user,
                                                           don_dep):
    resp = await client.post(
        f"{BASE}/", json=_lich_moi(ngay_ket_thuc="2026-09-01"))
    assert resp.status_code == 422


# ── sửa ───────────────────────────────────────────────────────────────

async def test_sua_ghi_nhat_ky_tung_truong(client, admin_user, don_dep):
    tao = (await client.post(f"{BASE}/", json=_lich_moi())).json()["data"]

    resp = await client.patch(f"{BASE}/{tao['id']}",
                              json={"tieu_de": "TEST G4.3 — đã đổi nội dung",
                                    "dia_diem": "Phòng họp số 2"})
    assert resp.status_code == 200, resp.text
    assert resp.json()["data"]["tieu_de"] == "TEST G4.3 — đã đổi nội dung"

    nk = (await client.get(f"{BASE}/{tao['id']}/nhat-ky")).json()["data"]
    sua = [x for x in nk if x["hanh_dong"] == "SUA_LICH"]
    assert sua, "không ghi nhật ký khi sửa"
    truong = {t["truong"] for t in sua[0]["chi_tiet"]["thay_doi"]}
    assert truong == {"tieu_de", "dia_diem"}


async def test_doi_ngay_bat_dau_keo_theo_ngay_hien_thi(client, admin_user,
                                                       don_dep):
    """Quên đồng bộ hai cột là sự kiện nằm sai ngày trên lịch."""
    tao = (await client.post(f"{BASE}/", json=_lich_moi())).json()["data"]
    resp = await client.patch(f"{BASE}/{tao['id']}",
                              json={"ngay_hop": "2026-09-20"})
    d = resp.json()["data"]
    assert d["ngay_hop"] == d["ngay_hien_thi"] == "2026-09-20"


async def test_sua_khong_doi_gi_thi_khong_ghi_nhat_ky(client, admin_user,
                                                      don_dep):
    tao = (await client.post(f"{BASE}/", json=_lich_moi())).json()["data"]
    await client.patch(f"{BASE}/{tao['id']}", json={"tieu_de": tao["tieu_de"]})

    nk = (await client.get(f"{BASE}/{tao['id']}/nhat-ky")).json()["data"]
    assert not [x for x in nk if x["hanh_dong"] == "SUA_LICH"]


async def test_trang_thai_sai_bi_tu_choi(client, admin_user, don_dep):
    tao = (await client.post(f"{BASE}/", json=_lich_moi())).json()["data"]
    resp = await client.patch(f"{BASE}/{tao['id']}",
                              json={"trang_thai": "KHONG_CO_TRANG_THAI_NAY"})
    assert resp.status_code == 400
    assert resp.json()["detail"]["error"]["code"] == "TRANG_THAI_KHONG_HOP_LE"


# ── ranh giới với Họp Không Giấy ──────────────────────────────────────

async def test_khong_sua_duoc_cuoc_hop_hkg(client, db_session, admin_user):
    """Cuộc họp HKG phải đi qua nghiệp vụ của nó, không sửa tắt ở lịch."""
    hkg_id = (await db_session.execute(sa_text(
        "SELECT id FROM meeting.cuoc_hop "
        "WHERE nguon = 'HKG' AND is_deleted = false LIMIT 1"))).scalar()
    if not hkg_id:
        pytest.skip("chưa có cuộc họp HKG nào")

    resp = await client.patch(f"{BASE}/{hkg_id}", json={"tieu_de": "đổi trộm"})
    assert resp.status_code == 409
    assert resp.json()["detail"]["error"]["code"] == "THUOC_HOP_KHONG_GIAY"

    resp = await client.delete(f"{BASE}/{hkg_id}")
    assert resp.status_code == 409


# ── huỷ và xoá ────────────────────────────────────────────────────────

async def test_huy_giu_lai_ban_ghi_va_ly_do(client, db_session, admin_user,
                                            don_dep):
    tao = (await client.post(f"{BASE}/", json=_lich_moi())).json()["data"]

    resp = await client.post(f"{BASE}/{tao['id']}/huy",
                             json={"ly_do_huy": "Lãnh đạo bận đột xuất"})
    assert resp.status_code == 200, resp.text
    assert resp.json()["data"]["trang_thai"] == "HUY"

    # Vẫn còn trong CSDL, chỉ đổi trạng thái.
    con = (await db_session.execute(sa_text(
        "SELECT trang_thai, ly_do_huy, is_deleted FROM meeting.cuoc_hop "
        "WHERE id = :id"), {"id": tao["id"]})).one()
    assert con.trang_thai == "HUY"
    assert con.ly_do_huy == "Lãnh đạo bận đột xuất"
    assert con.is_deleted is False


async def test_huy_hai_lan_bi_tu_choi(client, admin_user, don_dep):
    tao = (await client.post(f"{BASE}/", json=_lich_moi())).json()["data"]
    await client.post(f"{BASE}/{tao['id']}/huy", json={"ly_do_huy": "lý do"})
    resp = await client.post(f"{BASE}/{tao['id']}/huy",
                             json={"ly_do_huy": "lại huỷ"})
    assert resp.status_code == 400
    assert resp.json()["detail"]["error"]["code"] == "DA_HUY"


async def test_xoa_la_xoa_mem(client, db_session, admin_user, don_dep):
    tao = (await client.post(f"{BASE}/", json=_lich_moi())).json()["data"]
    assert (await client.delete(f"{BASE}/{tao['id']}")).status_code == 200

    row = (await db_session.execute(sa_text(
        "SELECT is_deleted FROM meeting.cuoc_hop WHERE id = :id"),
        {"id": tao["id"]})).scalar()
    assert row is True, "phải còn dòng, chỉ đánh dấu đã xoá"

    assert (await client.get(f"{BASE}/{tao['id']}")).status_code == 404


# ── phân quyền ────────────────────────────────────────────────────────

async def test_nguoi_thuong_khong_sua_duoc_lich_nguoi_khac(
        client, db_session, admin_user, cbcc_user, don_dep):
    """admin_user tạo, cbcc_user sửa → phải bị chặn.

    Hai fixture cùng ghi đè `get_current_user`; fixture nào chạy sau thì thắng,
    nên cbcc_user (khai báo sau) là người gọi API trong test này. Bản ghi được
    tạo thẳng bằng SQL để tránh phụ thuộc thứ tự đó.
    """
    ch_id = (await db_session.execute(sa_text("""
        INSERT INTO meeting.cuoc_hop
            (tieu_de, ngay_hop, gio_bat_dau, trang_thai, nguon, loai_lich,
             ma_lich, created_by)
        VALUES ('TEST G4.3 — của người khác', '2026-09-15', '08:00',
                'LEN_KE_HOACH', 'LICH_CONG_TAC', 'HOP', 'LH9999',
                (SELECT id FROM public.cong_chuc WHERE ma_cc = 'TEST-G3-001'))
        RETURNING id
    """))).scalar()
    await db_session.commit()

    resp = await client.patch(f"{BASE}/{ch_id}", json={"tieu_de": "sửa trộm"})
    assert resp.status_code == 403
    assert resp.json()["detail"]["error"]["code"] == "KHONG_DU_QUYEN"


async def test_quyen_cua_toi(client, admin_user):
    d = (await client.get(f"{BASE}/quyen/cua-toi")).json()["data"]
    assert d["la_quan_tri_lich"] is True


# ── xuất Excel ────────────────────────────────────────────────────────

async def test_xuat_excel(client, admin_user):
    resp = await client.get(f"{BASE}/xuat-excel?gioi-han=50")
    assert resp.status_code == 200
    assert "spreadsheetml" in resp.headers["content-type"]
    assert resp.content[:2] == b"PK"  # .xlsx là tệp zip
    assert len(resp.content) > 3000
