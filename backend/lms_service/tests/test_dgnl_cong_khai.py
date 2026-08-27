"""
lms_service/tests/test_dgnl_cong_khai.py
========================================
Test API cong khai cau hoi DGNL hang ngay (chatbot Zalo).

CHAY:  cd backend && source venv/bin/activate
       DB_NAME=kpi_haiquan_test pytest lms_service/tests/test_dgnl_cong_khai.py -v

⚠️ Service tu goi commit() nen test GHI THAT vao DB dang tro toi. BAT BUOC
   chay tren kpi_haiquan_test. Fixture `don_ngay_test` xoa sach cac ngay test
   truoc va sau moi bai.
"""

import uuid
from datetime import date

import pytest
import pytest_asyncio
from sqlalchemy import delete, select

from lms_service.config import settings
from lms_service.models.cau_hoi_dgnl import CauHoiDgnl
from lms_service.models.cau_hoi_hang_ngay import CauHoiHangNgay
from lms_service.models.linh_vuc import LinhVuc
from lms_service.services.cau_hoi_hang_ngay_service import LOAI_PHAT_DUOC

KHOA = "khoa-bot-dung-cho-test"
URL_CAU_HOI = "/api/v1/lms/dgnl/cong-khai/cau-hoi-hang-ngay"
URL_DAP_AN = "/api/v1/lms/dgnl/cong-khai/dap-an"

# Ngay gia dinh trong TUONG LAI XA — hai ly do:
#   - khong de len ban ghi cua ngay that
#   - la ban ghi MOI NHAT, nen test duoc duong "khong truyen cau_hoi_id thi
#     lay cau phat gan nhat" ma khong phu thuoc DB dang co san gi
NGAY_TEST = date(2099, 3, 17)
NGAY_TEST_2 = date(2099, 3, 18)


@pytest.fixture(autouse=True)
def bat_khoa_bot(monkeypatch):
    """Bat tinh nang bang cach dat khoa bot (mac dinh rong = tat)."""
    monkeypatch.setattr(settings, "zalo_bot_api_key", KHOA, raising=False)


@pytest_asyncio.fixture(autouse=True)
async def don_ngay_test(db_session):
    """Xoa ban ghi cua cac ngay test truoc va sau moi bai."""
    async def _xoa():
        await db_session.execute(
            delete(CauHoiHangNgay).where(
                CauHoiHangNgay.ngay.in_([NGAY_TEST, NGAY_TEST_2])
            )
        )
        await db_session.commit()

    await _xoa()
    yield
    await _xoa()


# =========================================================================
# XAC THUC
# =========================================================================

@pytest.mark.asyncio
async def test_thieu_khoa_thi_tu_choi(client):
    r = await client.get(URL_CAU_HOI, params={"ngay": NGAY_TEST.isoformat()})
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_sai_khoa_thi_tu_choi(client):
    r = await client.get(
        URL_CAU_HOI,
        params={"ngay": NGAY_TEST.isoformat()},
        headers={"X-Bot-Key": "khoa-sai"},
    )
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_khoa_rong_la_tat_han_tinh_nang(client, monkeypatch):
    """Chua dat khoa trong .env thi khong ai goi duoc, ke ca gui header rong."""
    monkeypatch.setattr(settings, "zalo_bot_api_key", "", raising=False)
    r = await client.get(
        URL_CAU_HOI,
        params={"ngay": NGAY_TEST.isoformat()},
        headers={"X-Bot-Key": ""},
    )
    assert r.status_code == 401


# =========================================================================
# CAU HOI CUA NGAY
# =========================================================================

@pytest.mark.asyncio
async def test_lay_cau_hoi_thanh_cong(client):
    r = await client.get(
        URL_CAU_HOI,
        params={"ngay": NGAY_TEST.isoformat()},
        headers={"X-Bot-Key": KHOA},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["success"] is True
    data = body["data"]
    assert data["ngay"] == NGAY_TEST.isoformat()
    assert data["cau_hoi_id"]
    assert data["noi_dung"]
    assert len(data["lua_chon"]) >= 2
    assert data["text_zalo"]


@pytest.mark.asyncio
async def test_khong_lo_dap_an_dung(client):
    """Endpoint cau hoi TUYET DOI khong duoc chua dap an dung."""
    r = await client.get(
        URL_CAU_HOI,
        params={"ngay": NGAY_TEST.isoformat()},
        headers={"X-Bot-Key": KHOA},
    )
    assert "dap_an_dung" not in r.text
    assert "giai_thich" not in r.text


@pytest.mark.asyncio
async def test_goi_hai_lan_cung_mot_cau(client):
    """Bot thu lai / nhieu nguoi cung nhan deu phai ra dung mot cau."""
    lan1 = await client.get(
        URL_CAU_HOI,
        params={"ngay": NGAY_TEST.isoformat()},
        headers={"X-Bot-Key": KHOA},
    )
    lan2 = await client.get(
        URL_CAU_HOI,
        params={"ngay": NGAY_TEST.isoformat()},
        headers={"X-Bot-Key": KHOA},
    )
    assert lan1.json()["data"]["cau_hoi_id"] == lan2.json()["data"]["cau_hoi_id"]


@pytest.mark.asyncio
async def test_hai_ngay_khac_nhau_khong_lap_cau(client):
    n1 = await client.get(
        URL_CAU_HOI,
        params={"ngay": NGAY_TEST.isoformat()},
        headers={"X-Bot-Key": KHOA},
    )
    n2 = await client.get(
        URL_CAU_HOI,
        params={"ngay": NGAY_TEST_2.isoformat()},
        headers={"X-Bot-Key": KHOA},
    )
    assert n1.json()["data"]["cau_hoi_id"] != n2.json()["data"]["cau_hoi_id"]


@pytest.mark.asyncio
async def test_cau_hoi_thuoc_9_linh_vuc_va_dung_loai(client, db_session):
    r = await client.get(
        URL_CAU_HOI,
        params={"ngay": NGAY_TEST.isoformat()},
        headers={"X-Bot-Key": KHOA},
    )
    data = r.json()["data"]
    assert data["linh_vuc_ma"] in settings.dgnl_daily_linh_vuc_list
    assert data["loai"] in LOAI_PHAT_DUOC

    # Doi chieu lai voi DB — khong tin moi mot minh response
    ch = (
        await db_session.execute(
            select(CauHoiDgnl, LinhVuc)
            .join(LinhVuc, CauHoiDgnl.linh_vuc_id == LinhVuc.id)
            .where(CauHoiDgnl.id == uuid.UUID(data["cau_hoi_id"]))
        )
    ).first()
    assert ch is not None
    assert ch[0].is_active is True
    assert ch[1].ma_linh_vuc in settings.dgnl_daily_linh_vuc_list


# =========================================================================
# DINH DANG ZALO
# =========================================================================

@pytest.mark.asyncio
async def test_dinh_dang_zalo_co_nut_bam(client):
    r = await client.get(
        URL_CAU_HOI,
        params={"ngay": NGAY_TEST.isoformat(), "dinh_dang": "zalo"},
        headers={"X-Bot-Key": KHOA},
    )
    assert r.status_code == 200
    body = r.json()
    # Object `message` tran — khong boc trong {success, data}
    assert "success" not in body
    assert body["text"]
    nut = body["attachment"]["payload"]["buttons"]
    assert len(nut) >= 2
    for n in nut:
        assert n["type"] == "oa.query.hide"
        assert len(n["title"]) <= 100
        # Payload chi la chu cai de mot quy tac tu khoa lo duoc ca nut bam
        # lan nguoi go tay tren Zalo may tinh
        assert n["payload"]["content"] == n["title"]
    # Gioi han text cua Zalo
    assert len(body["text"]) <= 2000


@pytest.mark.asyncio
async def test_payload_nut_khop_lua_chon(client):
    """Payload moi nut phai la dung key cua phuong an tuong ung."""
    chuan = await client.get(
        URL_CAU_HOI,
        params={"ngay": NGAY_TEST.isoformat()},
        headers={"X-Bot-Key": KHOA},
    )
    keys = [lc["key"] for lc in chuan.json()["data"]["lua_chon"]]

    zalo = await client.get(
        URL_CAU_HOI,
        params={"ngay": NGAY_TEST.isoformat(), "dinh_dang": "zalo"},
        headers={"X-Bot-Key": KHOA},
    )
    nut = zalo.json()["attachment"]["payload"]["buttons"]
    assert [n["payload"]["content"] for n in nut] == keys


# =========================================================================
# DAP AN
# =========================================================================

@pytest.mark.asyncio
async def test_dap_an_cau_chua_phat_thi_404(client):
    """Chan moc ca ngan hang de: chi tra dap an cho cau da tung phat."""
    r = await client.get(
        URL_DAP_AN,
        params={"cau_hoi_id": str(uuid.uuid4())},
        headers={"X-Bot-Key": KHOA},
    )
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_dap_an_cau_co_that_nhung_chua_phat_thi_404(client, db_session):
    """Cau ton tai trong ngan hang nhung chua phat ngay nao -> van 404."""
    da_phat = select(CauHoiHangNgay.cau_hoi_id)
    chua_phat = (
        await db_session.execute(
            select(CauHoiDgnl.id)
            .where(CauHoiDgnl.is_active == True, CauHoiDgnl.id.notin_(da_phat))  # noqa: E712
            .limit(1)
        )
    ).scalar_one_or_none()
    assert chua_phat is not None, "Ngan hang phai con cau chua phat de test"

    r = await client.get(
        URL_DAP_AN,
        params={"cau_hoi_id": str(chua_phat)},
        headers={"X-Bot-Key": KHOA},
    )
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_dap_an_dung_va_cham_diem(client, db_session):
    hoi = await client.get(
        URL_CAU_HOI,
        params={"ngay": NGAY_TEST.isoformat()},
        headers={"X-Bot-Key": KHOA},
    )
    cau_hoi_id = hoi.json()["data"]["cau_hoi_id"]

    ch = (
        await db_session.execute(
            select(CauHoiDgnl).where(CauHoiDgnl.id == uuid.UUID(cau_hoi_id))
        )
    ).scalar_one()
    key_dung = ch.dap_an["dap_an_dung"]
    key_sai = next(
        lc["key"] for lc in ch.dap_an["lua_chon"] if lc["key"] != key_dung
    )

    r_dung = await client.get(
        URL_DAP_AN,
        params={"cau_hoi_id": cau_hoi_id, "chon": key_dung},
        headers={"X-Bot-Key": KHOA},
    )
    assert r_dung.status_code == 200
    d = r_dung.json()["data"]
    assert d["dap_an_dung"] == key_dung
    assert d["da_chon"] == key_dung
    assert d["dung"] is True

    r_sai = await client.get(
        URL_DAP_AN,
        params={"cau_hoi_id": cau_hoi_id, "chon": key_sai},
        headers={"X-Bot-Key": KHOA},
    )
    assert r_sai.json()["data"]["dung"] is False


@pytest.mark.asyncio
async def test_dap_an_khong_truyen_chon_thi_khong_cham(client):
    hoi = await client.get(
        URL_CAU_HOI,
        params={"ngay": NGAY_TEST.isoformat()},
        headers={"X-Bot-Key": KHOA},
    )
    cau_hoi_id = hoi.json()["data"]["cau_hoi_id"]

    r = await client.get(
        URL_DAP_AN,
        params={"cau_hoi_id": cau_hoi_id},
        headers={"X-Bot-Key": KHOA},
    )
    d = r.json()["data"]
    assert d["dung"] is None
    assert d["da_chon"] is None
    assert d["dap_an_dung"]


@pytest.mark.asyncio
async def test_dap_an_chap_nhan_chu_thuong(client, db_session):
    """Bot co the gui 'b' thay vi 'B' — khong duoc cham sai vi le do."""
    hoi = await client.get(
        URL_CAU_HOI,
        params={"ngay": NGAY_TEST.isoformat()},
        headers={"X-Bot-Key": KHOA},
    )
    cau_hoi_id = hoi.json()["data"]["cau_hoi_id"]
    ch = (
        await db_session.execute(
            select(CauHoiDgnl).where(CauHoiDgnl.id == uuid.UUID(cau_hoi_id))
        )
    ).scalar_one()

    r = await client.get(
        URL_DAP_AN,
        params={"cau_hoi_id": cau_hoi_id, "chon": ch.dap_an["dap_an_dung"].lower()},
        headers={"X-Bot-Key": KHOA},
    )
    assert r.json()["data"]["dung"] is True


@pytest.mark.asyncio
async def test_dap_an_dinh_dang_zalo(client):
    hoi = await client.get(
        URL_CAU_HOI,
        params={"ngay": NGAY_TEST.isoformat()},
        headers={"X-Bot-Key": KHOA},
    )
    cau_hoi_id = hoi.json()["data"]["cau_hoi_id"]

    r = await client.get(
        URL_DAP_AN,
        params={"cau_hoi_id": cau_hoi_id, "chon": "A", "dinh_dang": "zalo"},
        headers={"X-Bot-Key": KHOA},
    )
    body = r.json()
    assert "success" not in body
    assert body["text"]
    assert len(body["text"]) <= 2000


# =========================================================================
# GO TAY THAY VI BAM NUT (Zalo may tinh khong hien nut)
# =========================================================================

@pytest.mark.asyncio
async def test_dap_an_khong_truyen_id_lay_cau_phat_gan_nhat(client):
    """Nguoi go 'A' tren Zalo may tinh: kich ban khong biet cau_hoi_id."""
    moi_nhat = await client.get(
        URL_CAU_HOI,
        params={"ngay": NGAY_TEST_2.isoformat()},
        headers={"X-Bot-Key": KHOA},
    )
    cau_moi_nhat = moi_nhat.json()["data"]["cau_hoi_id"]

    r = await client.get(
        URL_DAP_AN, params={"chon": "A"}, headers={"X-Bot-Key": KHOA}
    )
    assert r.status_code == 200
    assert r.json()["data"]["cau_hoi_id"] == cau_moi_nhat


@pytest.mark.asyncio
@pytest.mark.parametrize("go", ["a", "A.", "(a)", " a ", "A)"])
async def test_dap_an_chap_nhan_cac_kieu_go_tay(client, db_session, go):
    """Nguoi dung go tay kieu gi cung phai cham dung."""
    hoi = await client.get(
        URL_CAU_HOI,
        params={"ngay": NGAY_TEST.isoformat()},
        headers={"X-Bot-Key": KHOA},
    )
    cau_hoi_id = hoi.json()["data"]["cau_hoi_id"]
    ch = (
        await db_session.execute(
            select(CauHoiDgnl).where(CauHoiDgnl.id == uuid.UUID(cau_hoi_id))
        )
    ).scalar_one()

    r = await client.get(
        URL_DAP_AN,
        params={"cau_hoi_id": cau_hoi_id, "chon": go},
        headers={"X-Bot-Key": KHOA},
    )
    assert r.json()["data"]["da_chon"] == "A"
    assert r.json()["data"]["dung"] is (ch.dap_an["dap_an_dung"] == "A")


@pytest.mark.asyncio
async def test_nhan_nut_chi_con_chu_cai(client):
    """Nhan nut rut gon: noi dung phuong an da co o than tin, khong lap lai."""
    r = await client.get(
        URL_CAU_HOI,
        params={"ngay": NGAY_TEST.isoformat(), "dinh_dang": "zalo"},
        headers={"X-Bot-Key": KHOA},
    )
    for n in r.json()["attachment"]["payload"]["buttons"]:
        assert len(n["title"]) == 1
        assert n["title"].isalnum()


@pytest.mark.asyncio
async def test_text_nhac_go_tay_cho_nguoi_dung_may_tinh(client):
    r = await client.get(
        URL_CAU_HOI,
        params={"ngay": NGAY_TEST.isoformat()},
        headers={"X-Bot-Key": KHOA},
    )
    assert "máy tính" in r.json()["data"]["text_zalo"]


@pytest.mark.asyncio
async def test_chon_van_hieu_neu_kich_ban_chuyen_nguyen_payload_cu(client):
    """Phong khi kich ban chuyen nguyen chuoi "DGNL|<id>|A" vao `chon`.

    Khong co nhanh xu ly "|" thi ky tu dau se ra "D" (cua DGNL) -> cham sai het.
    """
    hoi = await client.get(
        URL_CAU_HOI,
        params={"ngay": NGAY_TEST.isoformat()},
        headers={"X-Bot-Key": KHOA},
    )
    cau_hoi_id = hoi.json()["data"]["cau_hoi_id"]

    r = await client.get(
        URL_DAP_AN,
        params={"cau_hoi_id": cau_hoi_id, "chon": f"DGNL|{cau_hoi_id}|C"},
        headers={"X-Bot-Key": KHOA},
    )
    assert r.json()["data"]["da_chon"] == "C"


@pytest.mark.asyncio
@pytest.mark.parametrize("rac", ["xin chào", "Z", "123", "?!"])
async def test_go_linh_tinh_thi_khong_cham_bua(client, rac):
    """Go vao khung chat chu khong phai chon menu — phai chiu duoc moi thu.

    Truoc khi vá: "xin chào" -> lay ky tu dau "X" -> bao "Ban chon X, dap an
    dung la B", vo nghia voi nguoi doc.
    """
    await client.get(
        URL_CAU_HOI,
        params={"ngay": NGAY_TEST.isoformat()},
        headers={"X-Bot-Key": KHOA},
    )
    r = await client.get(
        URL_DAP_AN, params={"chon": rac}, headers={"X-Bot-Key": KHOA}
    )
    assert r.status_code == 200
    d = r.json()["data"]
    assert d["da_chon"] is None
    assert d["dung"] is None
    assert d["dap_an_dung"]


# =========================================================================
# BAM NUT: Zalo gui ve nguyen object payload dang chuoi
# =========================================================================

@pytest.mark.asyncio
@pytest.mark.parametrize(
    "gui_ve,mong_doi",
    [
        ('{"content":"A"}', "A"),
        ('{"content": "B"}', "B"),
        ('{ "content" : "C" }', "C"),
        ("A", "A"),                       # go tay
        ('{"content":"DGNL|abc|D"}', "D"),  # phong khi quay lai payload cu
    ],
)
async def test_boc_dung_phuong_an_tu_payload_nut(client, gui_ve, mong_doi):
    """Doi chung that 27/08: bam nut A -> Zalo gui '{"content":"A"}'.

    Khong boc `content` thi con "contentA" -> ky tu dau "C" -> MOI lan bam nut
    deu cham thanh C. Loi im lang, ket qua van trong hop ly.
    """
    await client.get(
        URL_CAU_HOI,
        params={"ngay": NGAY_TEST.isoformat()},
        headers={"X-Bot-Key": KHOA},
    )
    r = await client.get(
        URL_DAP_AN, params={"chon": gui_ve}, headers={"X-Bot-Key": KHOA}
    )
    assert r.json()["data"]["da_chon"] == mong_doi


@pytest.mark.asyncio
async def test_payload_hong_thi_khong_cham_con_hon_cham_nham(client):
    await client.get(
        URL_CAU_HOI,
        params={"ngay": NGAY_TEST.isoformat()},
        headers={"X-Bot-Key": KHOA},
    )
    r = await client.get(
        URL_DAP_AN,
        params={"chon": '{"khong_phai_content":"A"}'},
        headers={"X-Bot-Key": KHOA},
    )
    assert r.json()["data"]["da_chon"] is None
