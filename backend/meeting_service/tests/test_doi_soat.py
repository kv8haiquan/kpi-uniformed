"""Kiểm thử màn hình đối soát di trú — G4.9.

Màn hình này quyết định 412 file thật thuộc về cuộc họp nào, và bản Excel xuất
ra là biên bản nộp khi nghiệm thu. Sai ở đây là sai vào hồ sơ.

Ba điều phải đúng:

  1. Chỉ Chánh Văn phòng và Quản trị viên vào được.
  2. Gợi ý ứng viên là DANH SÁCH để chọn, và phải nói thật khi không có ứng
     viên nào nổi trội — ngày nào cũng có 2–8 cuộc họp nên máy không tự quyết
     được.
  3. Bỏ quyết định KHÔNG được xoá cuộc họp lịch sử đã tạo.

    ./scripts/dev.sh test meeting_service/tests/test_doi_soat.py -v
"""

from __future__ import annotations

import pytest
from sqlalchemy import text as sa_text
from sqlalchemy.ext.asyncio import AsyncSession

from meeting_service.services.doi_soat_service import tach_tu

pytestmark = pytest.mark.asyncio

BASE = "/api/v1/hop-khong-giay/doi-soat"


async def _co_du_lieu(db: AsyncSession) -> bool:
    return bool((await db.execute(sa_text(
        "SELECT count(*) FROM meeting.di_tru_doi_soat"))).scalar())


@pytest.fixture
async def hoan_tac(db_session: AsyncSession):
    """Trả mọi quyết định về trạng thái ban đầu sau mỗi test.

    Dữ liệu đối soát là dữ liệu di trú THẬT, không tạo lại được, nên test chỉ
    được mượn rồi trả nguyên trạng.
    """
    yield
    await db_session.execute(sa_text("""
        UPDATE meeting.di_tru_doi_soat
           SET quyet_dinh = NULL, cuoc_hop_id = NULL,
               nguoi_quyet_dinh_id = NULL, thoi_diem_quyet_dinh = NULL,
               ghi_chu = NULL
    """))
    await db_session.execute(sa_text(
        "DELETE FROM common.audit_log "
        " WHERE module = 'MEETING' AND doi_tuong_loai = 'DI_TRU_DOI_SOAT'"))
    # Cuộc họp lịch sử do test dựng ra — nhận diện bằng mô tả cố định.
    await db_session.execute(sa_text(
        "DELETE FROM meeting.cuoc_hop "
        " WHERE mo_ta LIKE 'Cuộc họp dựng lại từ thư mục tài liệu%'"))
    await db_session.commit()


async def _mot_thu_muc(client) -> dict:
    d = (await client.get(f"{BASE}/")).json()["data"]
    return d["dong"][0]


# ── phân quyền ────────────────────────────────────────────────────────

async def test_nguoi_thuong_khong_vao_duoc(client, cbcc_user):
    assert (await client.get(f"{BASE}/")).status_code == 403
    assert (await client.get(f"{BASE}/quyen")).json()["data"]["duoc_xem"] is False


async def test_quan_tri_vao_duoc(client, admin_user):
    assert (await client.get(f"{BASE}/quyen")).json()["data"]["duoc_xem"] is True
    assert (await client.get(f"{BASE}/")).status_code == 200


# ── danh sách ─────────────────────────────────────────────────────────

async def test_danh_sach_du_tong_hop(client, db_session, admin_user):
    if not await _co_du_lieu(db_session):
        pytest.skip("chưa có dữ liệu đối soát")
    d = (await client.get(f"{BASE}/")).json()["data"]
    th = d["tong_hop"]
    assert th["tong_thu_muc"] == len(d["dong"])
    assert th["da_quyet_dinh"] + th["con_lai"] == th["tong_thu_muc"]
    assert th["tong_file"] == sum(x["so_file"] for x in d["dong"])


async def test_danh_sach_co_ten_file(client, db_session, admin_user):
    """Tên thư mục nhiều khi viết tắt quá — phải nhìn tên file mới đoán ra."""
    if not await _co_du_lieu(db_session):
        pytest.skip("chưa có dữ liệu đối soát")
    d = (await client.get(f"{BASE}/")).json()["data"]
    co_ten = [x for x in d["dong"] if x["danh_sach_file"]]
    assert co_ten, "không thư mục nào có danh sách tên file"
    # Số tên file phải khớp số file đã đếm, kể cả khi có thư mục con.
    for x in co_ten:
        assert len(x["danh_sach_file"]) == x["so_file"], x["duong_dan_thu_muc"]


async def test_loc_theo_nhom(client, db_session, admin_user):
    if not await _co_du_lieu(db_session):
        pytest.skip("chưa có dữ liệu đối soát")
    d = (await client.get(f"{BASE}/?nhom=E")).json()["data"]
    assert all(x["nhom"] == "E" for x in d["dong"])


# ── gợi ý ứng viên ────────────────────────────────────────────────────

async def test_ung_vien_tra_danh_sach_khong_tra_dap_an(client, db_session,
                                                       admin_user):
    if not await _co_du_lieu(db_session):
        pytest.skip("chưa có dữ liệu đối soát")
    tm = await _mot_thu_muc(client)
    d = (await client.get(f"{BASE}/{tm['id']}/ung-vien")).json()["data"]
    assert "ung_vien" in d and "co_ung_vien_noi_troi" in d
    # Xếp giảm dần theo điểm để người xem đọc từ trên xuống.
    diem = [x["diem"] for x in d["ung_vien"]]
    assert diem == sorted(diem, reverse=True)


async def test_ung_vien_noi_rai_tu_nao_trung(client, db_session, admin_user):
    if not await _co_du_lieu(db_session):
        pytest.skip("chưa có dữ liệu đối soát")
    for tm in (await client.get(f"{BASE}/")).json()["data"]["dong"]:
        d = (await client.get(f"{BASE}/{tm['id']}/ung-vien")).json()["data"]
        if d["ung_vien"]:
            assert d["ung_vien"][0]["tu_trung"], "phải nói rõ trùng từ nào"
            return
    pytest.skip("không thư mục nào có ứng viên")


# ── quyết định ────────────────────────────────────────────────────────

async def test_gan_cuoc_hop_phai_chi_ra_cuoc_hop(client, db_session,
                                                 admin_user, hoan_tac):
    if not await _co_du_lieu(db_session):
        pytest.skip("chưa có dữ liệu đối soát")
    tm = await _mot_thu_muc(client)
    resp = await client.post(f"{BASE}/{tm['id']}/quyet-dinh",
                             json={"quyet_dinh": "GAN_CUOC_HOP"})
    assert resp.status_code == 400
    assert resp.json()["detail"]["error"]["code"] == "THIEU_CUOC_HOP"


async def test_quyet_dinh_sai_bi_tu_choi(client, db_session, admin_user,
                                         hoan_tac):
    if not await _co_du_lieu(db_session):
        pytest.skip("chưa có dữ liệu đối soát")
    tm = await _mot_thu_muc(client)
    resp = await client.post(f"{BASE}/{tm['id']}/quyet-dinh",
                             json={"quyet_dinh": "KHONG_CO_LOAI_NAY"})
    assert resp.status_code == 400


async def test_ghi_quyet_dinh_kem_nguoi_va_thoi_diem(client, db_session,
                                                     admin_user, hoan_tac):
    """Biên bản nghiệm thu phải trả lời được: ai quyết, lúc nào."""
    if not await _co_du_lieu(db_session):
        pytest.skip("chưa có dữ liệu đối soát")
    tm = await _mot_thu_muc(client)
    resp = await client.post(f"{BASE}/{tm['id']}/quyet-dinh",
                             json={"quyet_dinh": "KHO_LUU_TRU",
                                   "ghi_chu": "không xác định được cuộc họp"})
    assert resp.status_code == 200, resp.text

    d = (await client.get(f"{BASE}/")).json()["data"]
    dong = next(x for x in d["dong"] if x["id"] == tm["id"])
    assert dong["quyet_dinh"] == "KHO_LUU_TRU"
    assert dong["nguoi_quyet_dinh"]
    assert dong["thoi_diem_quyet_dinh"]


async def test_tao_cuoc_hop_lich_su(client, db_session, admin_user, hoan_tac):
    """Tài liệu có trước khi hệ thống chạy thì không có cuộc họp để gắn."""
    if not await _co_du_lieu(db_session):
        pytest.skip("chưa có dữ liệu đối soát")
    tm = next((x for x in (await client.get(f"{BASE}/")).json()["data"]["dong"]
               if x["ngay_suy_ra"]), None)
    if not tm:
        pytest.skip("không thư mục nào suy ra được ngày")

    resp = await client.post(f"{BASE}/{tm['id']}/quyet-dinh",
                             json={"quyet_dinh": "TAO_CUOC_HOP_LICH_SU"})
    assert resp.status_code == 200, resp.text
    ch_id = resp.json()["data"]["cuoc_hop_id"]
    assert ch_id

    ch = (await db_session.execute(sa_text(
        "SELECT nguon, ngay_hien_thi, ma_lich FROM meeting.cuoc_hop "
        "WHERE id = :id"), {"id": ch_id})).one()
    assert ch.nguon == "LICH_CONG_TAC"
    assert ch.ngay_hien_thi.isoformat() == tm["ngay_suy_ra"]
    assert ch.ma_lich.startswith("LH")


async def test_khong_suy_ra_ngay_thi_khong_tao_duoc(client, db_session,
                                                    admin_user, hoan_tac):
    if not await _co_du_lieu(db_session):
        pytest.skip("chưa có dữ liệu đối soát")
    tm = next((x for x in (await client.get(f"{BASE}/")).json()["data"]["dong"]
               if not x["ngay_suy_ra"]), None)
    if not tm:
        pytest.skip("thư mục nào cũng suy ra được ngày")

    resp = await client.post(f"{BASE}/{tm['id']}/quyet-dinh",
                             json={"quyet_dinh": "TAO_CUOC_HOP_LICH_SU"})
    assert resp.status_code == 400
    assert resp.json()["detail"]["error"]["code"] == "KHONG_SUY_RA_NGAY"


async def test_huy_quyet_dinh_khong_xoa_cuoc_hop_da_tao(client, db_session,
                                                        admin_user, hoan_tac):
    """Cuộc họp đã dựng có thể đã được gắn tài liệu khác — không xoá kèm."""
    if not await _co_du_lieu(db_session):
        pytest.skip("chưa có dữ liệu đối soát")
    tm = next((x for x in (await client.get(f"{BASE}/")).json()["data"]["dong"]
               if x["ngay_suy_ra"]), None)
    if not tm:
        pytest.skip("không thư mục nào suy ra được ngày")

    ch_id = (await client.post(
        f"{BASE}/{tm['id']}/quyet-dinh",
        json={"quyet_dinh": "TAO_CUOC_HOP_LICH_SU"})).json()["data"]["cuoc_hop_id"]

    resp = await client.delete(f"{BASE}/{tm['id']}/quyet-dinh")
    assert resp.status_code == 200
    assert resp.json()["data"]["quyet_dinh"] is None

    con = (await db_session.execute(sa_text(
        "SELECT is_deleted FROM meeting.cuoc_hop WHERE id = :id"),
        {"id": ch_id})).scalar()
    assert con is False, "huỷ quyết định không được xoá cuộc họp đã tạo"


async def test_huy_khi_chua_quyet_dinh_bi_tu_choi(client, db_session,
                                                  admin_user, hoan_tac):
    if not await _co_du_lieu(db_session):
        pytest.skip("chưa có dữ liệu đối soát")
    tm = await _mot_thu_muc(client)
    resp = await client.delete(f"{BASE}/{tm['id']}/quyet-dinh")
    assert resp.status_code == 400
    assert resp.json()["detail"]["error"]["code"] == "CHUA_QUYET_DINH"


# ── biên bản ──────────────────────────────────────────────────────────

async def test_xuat_bien_ban(client, admin_user):
    resp = await client.get(f"{BASE}/xuat-excel")
    assert resp.status_code == 200
    assert resp.content[:2] == b"PK"
    assert "attachment" in resp.headers["content-disposition"]


async def test_nguoi_thuong_khong_xuat_duoc_bien_ban(client, cbcc_user):
    assert (await client.get(f"{BASE}/xuat-excel")).status_code == 403
