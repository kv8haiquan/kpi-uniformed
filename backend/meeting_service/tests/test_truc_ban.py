"""Kiểm thử lịch trực ban — G4.7 và nhập Excel G4.8.

Bốn điều dễ sai nhất:

  1. Thứ tự chức vụ — "Phó Chi cục trưởng" không được xếp ngang "Chi cục
     trưởng", và "Chánh Văn **phòng**" không được nhận nhầm là cấp phó.
  2. Ma trận phải trả CẢ ngày trống — ô trống là chỗ Văn phòng phải đi hỏi.
  3. Nộp rồi thì khoá; mở khoá chỉ quản trị lịch làm được.
  4. Nhập Excel không được ghi khi mới xem trước, và một dòng hỏng không làm
     hỏng cả file.

    ./scripts/dev.sh test meeting_service/tests/test_truc_ban.py -v
"""

from __future__ import annotations

from datetime import date, timedelta
from io import BytesIO

import pytest
from sqlalchemy import text as sa_text
from sqlalchemy.ext.asyncio import AsyncSession

from meeting_service.services.truc_ban_service import bac_chuc_vu, tuan_chua

pytestmark = pytest.mark.asyncio

BASE = "/api/v1/hop-khong-giay/truc-ban"

# Ngày nằm ngoài dải dữ liệu di trú (06/06–16/08/2026) để test không đụng số
# liệu thật khi kiểm tra ma trận.
NGAY_TEST = date(2026, 12, 5)      # Thứ Bảy
TEN_TEST = "TEST TRUCBAN"


async def _xoa_sach(db: AsyncSession) -> None:
    # Xoá theo LOẠI đối tượng chứ không theo id: hành động NOP_ trỏ vào
    # truc_ban_tru_so, còn NHAP_EXCEL_ không có đối tượng nào cả. Sót lại thì
    # khoá ngoại giữ chân bản ghi công chức test và cả bộ test vỡ ở bước dọn.
    await db.execute(sa_text(
        "DELETE FROM common.audit_log "
        " WHERE module = 'MEETING' "
        "   AND doi_tuong_loai IN ('TRUC_BAN', 'TRUC_BAN_TRU_SO')"))
    await db.execute(sa_text(
        "DELETE FROM meeting.truc_ban WHERE ho_ten LIKE :t"),
        {"t": f"{TEN_TEST}%"})
    await db.execute(sa_text(
        "DELETE FROM meeting.truc_ban_tru_so WHERE ngay_truc >= :n"),
        {"n": date(2026, 12, 1)})
    await db.commit()


@pytest.fixture
async def don_dep(db_session: AsyncSession):
    await _xoa_sach(db_session)
    yield
    await _xoa_sach(db_session)


@pytest.fixture
async def tru_so_chi_cuc(db_session: AsyncSession) -> str:
    return str((await db_session.execute(sa_text(
        "SELECT id FROM meeting.tru_so WHERE ma_tru_so = 'CHICUC'"
    ))).scalar())


def _nguoi(tru_so_id: str, **ghi_de) -> dict:
    d = {
        "ngay_truc": NGAY_TEST.isoformat(),
        "tru_so_id": tru_so_id,
        "ho_ten": f"{TEN_TEST} Nguyễn Văn A",
        "chuc_vu": "Công chức",
        "so_dien_thoai": "0900000000",
    }
    d.update(ghi_de)
    return d


# ── ma trận ───────────────────────────────────────────────────────────

async def test_ma_tran_tra_ca_ngay_trong(client, admin_user):
    """Ngày không ai trực vẫn phải có hàng — ô trống là thông tin."""
    resp = await client.get(
        f"{BASE}/ma-tran?tu-ngay=2026-12-01&den-ngay=2026-12-07")
    assert resp.status_code == 200, resp.text
    d = resp.json()["data"]
    assert len(d["hang"]) == 7
    assert all(len(h["o"]) == len(d["tru_so"]) for h in d["hang"])


async def test_ma_tran_danh_dau_cuoi_tuan(client, admin_user):
    d = (await client.get(
        f"{BASE}/ma-tran?tu-ngay=2026-12-01&den-ngay=2026-12-07")
         ).json()["data"]
    cuoi_tuan = [h["ngay"] for h in d["hang"] if h["cuoi_tuan"]]
    assert cuoi_tuan == ["2026-12-05", "2026-12-06"]


async def test_ma_tran_khoang_qua_dai_bi_tu_choi(client, admin_user):
    resp = await client.get(
        f"{BASE}/ma-tran?tu-ngay=2026-01-01&den-ngay=2026-12-31")
    assert resp.status_code == 400
    assert resp.json()["detail"]["error"]["code"] == "KHOANG_NGAY_QUA_DAI"


async def test_ma_tran_sap_xep_theo_chuc_vu(client, admin_user,
                                            tru_so_chi_cuc, don_dep):
    await client.post(f"{BASE}/", json=_nguoi(
        tru_so_chi_cuc, ho_ten=f"{TEN_TEST} Công chức", chuc_vu="Công chức"))
    await client.post(f"{BASE}/", json=_nguoi(
        tru_so_chi_cuc, ho_ten=f"{TEN_TEST} Lãnh đạo",
        chuc_vu="Phó Chi cục trưởng"))

    d = (await client.get(
        f"{BASE}/ma-tran?tu-ngay={NGAY_TEST}&den-ngay={NGAY_TEST}")
         ).json()["data"]
    o = next(x for h in d["hang"] for x in h["o"]
             if x["tru_so_id"] == tru_so_chi_cuc)
    assert [n["chuc_vu"] for n in o["nguoi"]] == ["Phó Chi cục trưởng",
                                                  "Công chức"]


# ── nhập tay ──────────────────────────────────────────────────────────

async def test_them_va_xoa(client, admin_user, tru_so_chi_cuc, don_dep):
    resp = await client.post(f"{BASE}/", json=_nguoi(tru_so_chi_cuc))
    assert resp.status_code == 201, resp.text
    tb_id = resp.json()["data"]["id"]

    assert (await client.delete(f"{BASE}/{tb_id}")).status_code == 200

    ds = (await client.get(
        f"{BASE}/danh-sach?tu-ngay={NGAY_TEST}&den-ngay={NGAY_TEST}")
          ).json()["data"]
    assert not [x for x in ds if x["id"] == tb_id]


async def test_ca_truc_sai_bi_tu_choi(client, admin_user, tru_so_chi_cuc,
                                      don_dep):
    resp = await client.post(f"{BASE}/",
                             json=_nguoi(tru_so_chi_cuc, ca_truc="NUA_DEM"))
    assert resp.status_code == 422


# ── nộp và khoá ───────────────────────────────────────────────────────

async def test_nop_roi_thi_khoa(client, admin_user, tru_so_chi_cuc, don_dep):
    tb = (await client.post(f"{BASE}/", json=_nguoi(tru_so_chi_cuc))
          ).json()["data"]

    resp = await client.post(f"{BASE}/nop", json={
        "ngay_truc": NGAY_TEST.isoformat(), "tru_so_id": tru_so_chi_cuc})
    assert resp.status_code == 200, resp.text
    assert resp.json()["data"]["is_locked"] is True

    # Đã khoá thì không sửa, không xoá, không thêm được nữa.
    r = await client.patch(f"{BASE}/{tb['id']}", json={"ho_ten": "đổi"})
    assert r.status_code == 409
    assert r.json()["detail"]["error"]["code"] == "DA_KHOA"

    assert (await client.delete(f"{BASE}/{tb['id']}")).status_code == 409
    assert (await client.post(f"{BASE}/", json=_nguoi(tru_so_chi_cuc))
            ).status_code == 409


async def test_khong_nop_duoc_o_trong(client, admin_user, tru_so_chi_cuc,
                                      don_dep):
    resp = await client.post(f"{BASE}/nop", json={
        "ngay_truc": "2026-12-06", "tru_so_id": tru_so_chi_cuc})
    assert resp.status_code == 400
    assert resp.json()["detail"]["error"]["code"] == "CHUA_CO_NGUOI_TRUC"


async def test_mo_khoa_roi_sua_lai_duoc(client, admin_user, tru_so_chi_cuc,
                                        don_dep):
    tb = (await client.post(f"{BASE}/", json=_nguoi(tru_so_chi_cuc))
          ).json()["data"]
    await client.post(f"{BASE}/nop", json={
        "ngay_truc": NGAY_TEST.isoformat(), "tru_so_id": tru_so_chi_cuc})

    resp = await client.post(f"{BASE}/mo-khoa", json={
        "ngay_truc": NGAY_TEST.isoformat(), "tru_so_id": tru_so_chi_cuc})
    assert resp.status_code == 200
    assert resp.json()["data"]["is_locked"] is False

    r = await client.patch(f"{BASE}/{tb['id']}",
                           json={"ho_ten": f"{TEN_TEST} đã sửa"})
    assert r.status_code == 200


async def test_nguoi_thuong_khong_mo_khoa_duoc(client, cbcc_user,
                                               tru_so_chi_cuc):
    resp = await client.post(f"{BASE}/mo-khoa", json={
        "ngay_truc": NGAY_TEST.isoformat(), "tru_so_id": tru_so_chi_cuc})
    assert resp.status_code == 403


async def test_nguoi_thuong_khong_sua_tru_so_chi_cuc(client, cbcc_user,
                                                     tru_so_chi_cuc):
    """Trụ sở Chi cục không thuộc đơn vị nào — chỉ quản trị lịch đụng được."""
    resp = await client.post(f"{BASE}/", json=_nguoi(tru_so_chi_cuc))
    assert resp.status_code == 403
    assert resp.json()["detail"]["error"]["code"] == "KHONG_DU_QUYEN"


# ── nhập từ Excel ─────────────────────────────────────────────────────

def _file_excel(hang: list[list], tieu_de: list[str] | None = None) -> bytes:
    from openpyxl import Workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "IMPORT_LICH_TRUC"
    ws.append(tieu_de or ["NGAY_TRUC", "UNIT_CODE", "HO_TEN", "CHUC_VU",
                          "SO_DIEN_THOAI", "GHI_CHU"])
    for h in hang:
        ws.append(h)
    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()


async def _gui(client, noi_dung: bytes):
    return await client.post(
        f"{BASE}/nhap/xem-truoc",
        files={"file": ("truc.xlsx", noi_dung,
                        "application/vnd.openxmlformats-officedocument"
                        ".spreadsheetml.sheet")})


async def test_xem_truoc_khong_ghi_gi(client, db_session, admin_user, don_dep):
    noi_dung = _file_excel([
        ["05/12/2026", "CHICUC", f"{TEN_TEST} Người 1", "Công chức",
         "0912345678", None],
    ])
    resp = await _gui(client, noi_dung)
    assert resp.status_code == 200, resp.text
    assert resp.json()["data"]["so_hop_le"] == 1

    con = (await db_session.execute(sa_text(
        "SELECT count(*) FROM meeting.truc_ban WHERE ho_ten LIKE :t"),
        {"t": f"{TEN_TEST}%"})).scalar()
    assert con == 0, "xem trước mà đã ghi vào CSDL"


async def test_mot_dong_hong_khong_lam_hong_ca_file(client, admin_user):
    noi_dung = _file_excel([
        ["05/12/2026", "CHICUC", f"{TEN_TEST} Đúng", "Công chức", "091", None],
        ["ngày sai", "CHICUC", f"{TEN_TEST} Sai ngày", "", "", None],
        ["06/12/2026", "KHONG_CO_MA", f"{TEN_TEST} Sai mã", "", "", None],
        ["06/12/2026", "CHICUC", "", "", "", None],
    ])
    d = (await _gui(client, noi_dung)).json()["data"]
    assert d["tong_dong"] == 4
    assert d["so_hop_le"] == 1
    assert d["so_loi"] == 3
    # Mỗi dòng hỏng phải nói rõ hỏng vì sao.
    assert all(x["loi"] for x in d["dong"] if not x["hop_le"])


async def test_nhan_bien_the_ten_cot(client, admin_user):
    """Mỗi đơn vị sửa file mẫu một kiểu — phải nhận được các biến thể."""
    noi_dung = _file_excel(
        [["05/12/2026", "CHICUC", f"{TEN_TEST} Biến thể", "Công chức",
          "0912345678", "ghi chú"]],
        tieu_de=["Ngày trực", "Mã trụ sở", "Họ và tên", "Chức danh",
                 "Điện thoại", "Ghi chú"])
    d = (await _gui(client, noi_dung)).json()["data"]
    assert d["so_hop_le"] == 1
    assert d["dong"][0]["ghi_chu"] == "ghi chú"


async def test_thieu_cot_bat_buoc_bi_tu_choi(client, admin_user):
    noi_dung = _file_excel([["05/12/2026", "Công chức"]],
                           tieu_de=["NGAY_TRUC", "CHUC_VU"])
    resp = await _gui(client, noi_dung)
    assert resp.status_code == 400
    assert resp.json()["detail"]["error"]["code"] == "THIEU_COT"


async def test_ghi_nhap_thuc_su_luu(client, db_session, admin_user, don_dep):
    noi_dung = _file_excel([
        ["05/12/2026", "CHICUC", f"{TEN_TEST} Ghi thật", "Công chức",
         "0912345678", None],
    ])
    xem = (await _gui(client, noi_dung)).json()["data"]

    resp = await client.post(f"{BASE}/nhap/ghi",
                             json={"dong": xem["dong"], "ghi_de": False})
    assert resp.status_code == 200, resp.text
    assert resp.json()["data"]["da_ghi"] == 1

    con = (await db_session.execute(sa_text(
        "SELECT count(*) FROM meeting.truc_ban "
        "WHERE ho_ten LIKE :t AND is_deleted = false"),
        {"t": f"{TEN_TEST}%"})).scalar()
    assert con == 1


async def test_ghi_de_xoa_ban_cu(client, db_session, admin_user,
                                 tru_so_chi_cuc, don_dep):
    await client.post(f"{BASE}/", json=_nguoi(
        tru_so_chi_cuc, ho_ten=f"{TEN_TEST} Bản cũ"))

    noi_dung = _file_excel([
        ["05/12/2026", "CHICUC", f"{TEN_TEST} Bản mới", "Công chức",
         "0912345678", None],
    ])
    xem = (await _gui(client, noi_dung)).json()["data"]
    await client.post(f"{BASE}/nhap/ghi",
                      json={"dong": xem["dong"], "ghi_de": True})

    con_lai = (await db_session.execute(sa_text(
        "SELECT ho_ten FROM meeting.truc_ban "
        "WHERE ho_ten LIKE :t AND is_deleted = false"),
        {"t": f"{TEN_TEST}%"})).scalars().all()
    assert con_lai == [f"{TEN_TEST} Bản mới"]


async def test_khong_ghi_khi_khong_co_dong_hop_le(client, admin_user):
    resp = await client.post(f"{BASE}/nhap/ghi", json={"dong": [], "ghi_de": False})
    assert resp.status_code == 400
    assert resp.json()["detail"]["error"]["code"] == "KHONG_CO_DONG_HOP_LE"


async def test_file_khong_phai_excel_bi_tu_choi(client, admin_user):
    resp = await client.post(
        f"{BASE}/nhap/xem-truoc",
        files={"file": ("truc.txt", b"khong phai excel", "text/plain")})
    assert resp.status_code == 400
    assert resp.json()["detail"]["error"]["code"] == "SAI_DINH_DANG"


# ── xuất ──────────────────────────────────────────────────────────────

async def test_xuat_excel(client, admin_user):
    resp = await client.get(f"{BASE}/xuat-excel?tuan=nay")
    assert resp.status_code == 200
    assert resp.content[:2] == b"PK"


async def test_tai_file_mau(client, admin_user):
    resp = await client.get(f"{BASE}/mau-import")
    assert resp.status_code == 200
    assert resp.content[:2] == b"PK"


async def test_van_ban_de_sao_chep(client, admin_user, tru_so_chi_cuc,
                                   don_dep):
    await client.post(f"{BASE}/", json=_nguoi(tru_so_chi_cuc))
    d = (await client.get(
        f"{BASE}/van-ban?tu-ngay={NGAY_TEST}&den-ngay={NGAY_TEST}")
         ).json()["data"]
    assert TEN_TEST in d["van_ban"]
    assert "Thứ Bảy" in d["van_ban"]


async def test_mac_dinh_lay_tuan_nay(client, admin_user):
    d = (await client.get(f"{BASE}/ma-tran")).json()["data"]
    dau, cuoi = tuan_chua(date.today())
    assert d["tu_ngay"] == dau.isoformat()
    assert d["den_ngay"] == cuoi.isoformat()
    assert (cuoi - dau) == timedelta(days=6)
