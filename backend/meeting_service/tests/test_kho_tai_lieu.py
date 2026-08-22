"""Kho tài liệu họp — `GET /tai-lieu/kho` (mục "HKG + Lịch công tác").

Màn hình này là chỗ DUY NHẤT xem được cả kho tài liệu mà không cần biết
trước tài liệu thuộc cuộc họp nào. Chính vì thế nó cũng là đường rò rỉ dễ
xảy ra nhất: một câu SQL gộp tất cả tài liệu lại, quên lọc quyền là lộ sạch
866 file cho toàn Chi cục.

Nên bộ test dưới đây gần như toàn bộ là test rò rỉ, kiểm hai tầng chặn:
  1. quyền xem CUỘC HỌP — họp HKG chỉ người được mời; sự kiện Lịch công tác
     là lịch nội bộ nên cả Chi cục xem được
  2. quyền xem TÀI LIỆU (G5.4) — lọc TRƯỚC khi phát token xem, vì mỗi dòng
     trả về đã nhúng sẵn `url_xem`

    DB_NAME=kpi_haiquan_test ALLOW_PROD_TEST=true \
    pytest meeting_service/tests/test_kho_tai_lieu.py -v
"""

from __future__ import annotations

import uuid
from datetime import date, time, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import text as sa_text
from sqlalchemy.ext.asyncio import AsyncSession

from meeting_service.tests.conftest import TEST_USERS, _make_user, _set_user

pytestmark = pytest.mark.asyncio

BASE = "/api/v1/hop-khong-giay/tai-lieu"
TIEN_TO = "TEST-KHO"

# Ngày trong tương lai xa để không lẫn với 866 tài liệu đã di trú thật:
# mọi truy vấn của test đều kẹp `tu-ngay` vào khoảng này.
NGAY = date.today() + timedelta(days=900)


async def _tao_hop(db: AsyncSession, seed, nguon: str, nguoi_tao) -> uuid.UUID:
    ch_id = uuid.uuid4()
    await db.execute(sa_text("""
        INSERT INTO meeting.cuoc_hop
            (id, tieu_de, ngay_hop, gio_bat_dau, trang_thai, nguon, ma_lich,
             loai_lich, created_by, don_vi_to_chuc_id, chu_toa_id)
        VALUES (:id, :td, :ngay, :gio, 'DA_THONG_BAO', :nguon, :ma,
                :loai, :nt, :dv, :ct)
    """), {
        "id": str(ch_id), "td": f"{TIEN_TO} {nguon}", "ngay": NGAY,
        "gio": time.fromisoformat("08:30"), "nguon": nguon,
        "ma": f"LH8{uuid.uuid4().hex[:5]}",
        # Hai nguồn có hai ràng buộc bắt buộc khác nhau:
        #   ck_cuoc_hop_lct_bat_buoc → LICH_CONG_TAC phải có ma_lich+loai_lich
        #   ck_cuoc_hop_hkg_bat_buoc → HKG phải có chu_toa_id+don_vi_to_chuc_id
        "loai": "HOP" if nguon == "LICH_CONG_TAC" else None,
        "ct": str(nguoi_tao) if nguon == "HKG" else None,
        "nt": str(nguoi_tao), "dv": str(seed["don_vi_a"]),
    })
    return ch_id


async def _tao_tai_lieu(db: AsyncSession, ch_id, nguoi_tao, *, ten: str,
                        muc: str = "CONG_KHAI") -> uuid.UUID:
    tl_id = uuid.uuid4()
    await db.execute(sa_text("""
        INSERT INTO meeting.tai_lieu
            (id, cuoc_hop_id, ten_tai_lieu, minio_key, file_size, extension,
             mime_type, phan_quyen, created_by)
        VALUES (:id, :ch, :ten, :key, 1024, 'pdf', 'application/pdf',
                :muc, :nt)
    """), {"id": str(tl_id), "ch": str(ch_id), "ten": ten,
           "key": f"test-kho/{tl_id}.pdf", "muc": muc, "nt": str(nguoi_tao)})
    return tl_id


async def _goi_kho(client: AsyncClient, **tham_so) -> list[dict]:
    """Luôn kẹp khoảng ngày để chỉ thấy dữ liệu của test này."""
    q = {"tu-ngay": NGAY.isoformat(), "den-ngay": NGAY.isoformat(),
         "so-dong": 100, **tham_so}
    r = await client.get(f"{BASE}/kho", params=q)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["success"] is True
    return body["data"]


@pytest.fixture
async def kho_mau(db_session: AsyncSession, seed_test_users):
    """Bốn tài liệu: 2 của họp HKG kín, 2 của sự kiện Lịch công tác."""
    nguoi_tao = TEST_USERS["TEST-G3-001"]
    hkg = await _tao_hop(db_session, seed_test_users, "HKG", nguoi_tao)
    lct = await _tao_hop(db_session, seed_test_users, "LICH_CONG_TAC", nguoi_tao)

    ids = {
        "hkg": hkg, "lct": lct,
        "hkg_cong_khai": await _tao_tai_lieu(
            db_session, hkg, nguoi_tao, ten=f"{TIEN_TO}-hkg-cong-khai.pdf"),
        "hkg_han_che": await _tao_tai_lieu(
            db_session, hkg, nguoi_tao, ten=f"{TIEN_TO}-hkg-mat.pdf",
            muc="LANH_DAO_CHI_CUC"),
        "lct_cong_khai": await _tao_tai_lieu(
            db_session, lct, nguoi_tao, ten=f"{TIEN_TO}-lct-cong-khai.pdf"),
        "lct_han_che": await _tao_tai_lieu(
            db_session, lct, nguoi_tao, ten=f"{TIEN_TO}-lct-mat.pdf",
            muc="LANH_DAO_CHI_CUC"),
    }
    await db_session.flush()
    return ids


# ── tầng 1: quyền xem cuộc họp ────────────────────────────────────────

async def test_cong_chuc_thuong_khong_thay_tai_lieu_hop_kin(
    client: AsyncClient, kho_mau, cbcc_user,
):
    """Không được mời họp HKG thì tài liệu của nó phải biến mất khỏi kho.

    Đây là test rò rỉ chính: kho gộp mọi tài liệu nên nếu quên tầng 1 thì
    người ngoài cuộc họp vẫn đọc được tài liệu của cuộc họp đó.
    """
    ten = {t["ten_tai_lieu"] for t in await _goi_kho(client)}
    assert not any(t.startswith(f"{TIEN_TO}-hkg") for t in ten), \
        "tài liệu họp HKG lọt ra ngoài danh sách người không dự"


async def test_su_kien_lich_cong_tac_ai_cung_xem_duoc(
    client: AsyncClient, kho_mau, cbcc_user,
):
    """Lịch công tác là lịch công khai nội bộ — khác hẳn họp HKG."""
    ten = {t["ten_tai_lieu"] for t in await _goi_kho(client)}
    assert f"{TIEN_TO}-lct-cong-khai.pdf" in ten


async def test_nguoi_du_hop_thay_tai_lieu_hop(
    client: AsyncClient, db_session: AsyncSession, kho_mau, seed_test_users,
    cbcc_user,
):
    """Mời vào họp là thấy — chứng minh tầng 1 chặn theo lời mời, không
    phải chặn cứng mọi tài liệu HKG."""
    await db_session.execute(sa_text("""
        INSERT INTO meeting.thanh_phan (cuoc_hop_id, cong_chuc_id, loai_tham_du)
        VALUES (:ch, :cc, 'BAT_BUOC') ON CONFLICT DO NOTHING
    """), {"ch": str(kho_mau["hkg"]), "cc": cbcc_user.sub})
    await db_session.flush()

    ten = {t["ten_tai_lieu"] for t in await _goi_kho(client)}
    assert f"{TIEN_TO}-hkg-cong-khai.pdf" in ten


# ── tầng 2: phân quyền tài liệu G5.4 ──────────────────────────────────

async def test_tai_lieu_han_che_khong_lot_vao_kho(
    client: AsyncClient, kho_mau, cbcc_user,
):
    """Mức LANH_DAO_CHI_CUC phải bị lọc trước khi phát token xem.

    Mỗi dòng trả về đã nhúng sẵn `url_xem` — lọt vào danh sách là mở được
    file, không cần bấm thêm gì.
    """
    ds = await _goi_kho(client)
    ten = {t["ten_tai_lieu"] for t in ds}
    assert f"{TIEN_TO}-lct-mat.pdf" not in ten
    assert all(t["phan_quyen"] == "CONG_KHAI" for t in ds
               if t["ten_tai_lieu"].startswith(TIEN_TO))


async def test_lanh_dao_chi_cuc_thay_tai_lieu_han_che(
    client: AsyncClient, kho_mau, seed_test_users,
):
    _set_user(_make_user("TEST-G3-003", seed_test_users["don_vi_b"],
                         vai_tro="PCCT", is_lanh_dao=True))
    ten = {t["ten_tai_lieu"] for t in await _goi_kho(client)}
    assert f"{TIEN_TO}-lct-mat.pdf" in ten


# ── bộ lọc và dữ liệu trả về ──────────────────────────────────────────

async def test_loc_theo_nguon(client: AsyncClient, kho_mau, admin_user):
    hkg = await _goi_kho(client, nguon="HKG")
    assert hkg and all(t["nguon"] == "HKG" for t in hkg)

    lct = await _goi_kho(client, nguon="LICH_CONG_TAC")
    assert lct and all(t["nguon"] == "LICH_CONG_TAC" for t in lct)


async def test_nguon_khong_hop_le_bi_chan(client: AsyncClient, admin_user):
    r = await client.get(f"{BASE}/kho", params={"nguon": "DRIVE"})
    assert r.status_code == 422
    assert r.json()["detail"]["error"]["code"] == "VALIDATION_ERROR"


async def test_tim_kiem_theo_ten_file_va_theo_cuoc_hop(
    client: AsyncClient, kho_mau, admin_user,
):
    """Người dùng nhớ tên cuộc họp nhiều hơn nhớ tên file — phải tìm được
    bằng cả hai."""
    theo_file = await _goi_kho(client, **{"tim-kiem": "lct-cong-khai"})
    assert [t["ten_tai_lieu"] for t in theo_file] == [
        f"{TIEN_TO}-lct-cong-khai.pdf"]

    theo_hop = await _goi_kho(client, **{"tim-kiem": f"{TIEN_TO} LICH_CONG_TAC"})
    assert {t["ten_tai_lieu"] for t in theo_hop} >= {
        f"{TIEN_TO}-lct-cong-khai.pdf", f"{TIEN_TO}-lct-mat.pdf"}


async def test_moi_dong_co_du_ngu_canh_cuoc_hop(
    client: AsyncClient, kho_mau, admin_user,
):
    """Thiếu đường dẫn cuộc họp là kho mất tác dụng tra cứu: tìm ra file
    nhưng không lần được về cuộc họp sinh ra nó."""
    ds = await _goi_kho(client, nguon="LICH_CONG_TAC")
    t = next(x for x in ds
             if x["ten_tai_lieu"] == f"{TIEN_TO}-lct-cong-khai.pdf")
    assert t["cuoc_hop_id"] == str(kho_mau["lct"])
    assert t["duong_dan_cuoc_hop"] == f"/lich-cong-tac/{kho_mau['lct']}"
    assert t["ma_lich"] and t["tieu_de"].startswith(TIEN_TO)
    assert t["ngay_hop"] == NGAY.isoformat()
    assert t["url_xem"].startswith(f"/api/v1/hop-khong-giay/tai-lieu/{t['id']}")


async def test_duong_dan_hkg_khac_lich_cong_tac(
    client: AsyncClient, kho_mau, admin_user,
):
    ds = await _goi_kho(client, nguon="HKG")
    t = next(x for x in ds
             if x["ten_tai_lieu"] == f"{TIEN_TO}-hkg-cong-khai.pdf")
    assert t["duong_dan_cuoc_hop"] == \
        f"/hop-khong-giay/chi-tiet/{kho_mau['hkg']}"


async def test_phan_trang_bao_con_nua(client: AsyncClient, kho_mau, admin_user):
    """`con_nua` tính bằng cách lấy dư 1 dòng — dễ lệch một đơn vị nên phải
    kiểm cả hai đầu."""
    q = {"tu-ngay": NGAY.isoformat(), "den-ngay": NGAY.isoformat(),
         "nguon": "LICH_CONG_TAC", "so-dong": 1}

    r1 = (await client.get(f"{BASE}/kho", params={**q, "trang": 1})).json()
    assert len(r1["data"]) == 1
    assert r1["pagination"]["con_nua"] is True

    r2 = (await client.get(f"{BASE}/kho", params={**q, "trang": 2})).json()
    assert len(r2["data"]) == 1
    assert r2["pagination"]["con_nua"] is False
    assert r2["data"][0]["id"] != r1["data"][0]["id"]


async def test_khong_lay_tai_lieu_da_xoa(
    client: AsyncClient, db_session: AsyncSession, kho_mau, admin_user,
):
    await db_session.execute(sa_text(
        "UPDATE meeting.tai_lieu SET is_deleted = true WHERE id = :id"
    ), {"id": str(kho_mau["lct_cong_khai"])})
    await db_session.flush()

    ten = {t["ten_tai_lieu"] for t in await _goi_kho(client)}
    assert f"{TIEN_TO}-lct-cong-khai.pdf" not in ten


async def test_thong_ke_dem_ca_hai_nguon(client: AsyncClient, kho_mau,
                                         admin_user):
    r = await client.get(f"{BASE}/kho/thong-ke")
    assert r.status_code == 200, r.text
    d = r.json()["data"]
    assert d["HKG"] >= 2 and d["LICH_CONG_TAC"] >= 2
    assert d["tong"] == d["HKG"] + d["LICH_CONG_TAC"]
