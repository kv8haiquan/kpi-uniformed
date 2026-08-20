"""
Chấm sao công tác chuẩn bị cuộc họp — G5.3.

Trọng tâm: đúng người mới chấm được, và xem thì ai cũng xem được. Hệ cũ phân
quyền bằng cách dò chuỗi trên họ tên + chức vụ nên vừa lọt vừa sót; ở đây
kiểm bằng vai trò, nên phải có test cho cả hai chiều.
"""

from datetime import date, time, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import text as sa_text
from sqlalchemy.ext.asyncio import AsyncSession

from meeting_service.tests.conftest import TEST_USERS, _make_user, _set_user

BASE = "/api/v1/hop-khong-giay/danh-gia-chuan-bi"
BASE_LICH = "/api/v1/hop-khong-giay/lich-cong-tac"


def _doi_user(ma_cc: str, don_vi_id, **kw):
    u = _make_user(ma_cc, don_vi_id, **kw)
    _set_user(u)
    return u


async def _tao_cuoc_hop(db: AsyncSession, don_vi_id, *, ngay=None,
                        don_vi_chuan_bi="Văn phòng") -> str:
    """Chèn thẳng một sự kiện lịch — không đi qua API để test khỏi phụ thuộc
    quyền tạo lịch."""
    ngay = ngay or date.today()
    row = await db.execute(sa_text("""
        INSERT INTO meeting.cuoc_hop
            (tieu_de, ngay_hop, gio_bat_dau, nguon, ma_lich, loai_lich,
             ngay_hien_thi, don_vi_chuan_bi, trang_thai, don_vi_to_chuc_id,
             created_by)
        VALUES (:td, :ngay, :gio, 'LICH_CONG_TAC', :ma, 'HOP',
                :ngay, :dv, 'DA_THONG_BAO', :dvtc, :nguoi)
        RETURNING id
    """), {"td": "Test G5.3 — chấm điểm chuẩn bị", "ngay": ngay,
           "gio": time(8, 0),
           # ma_lich là UNIQUE nên phải khác nhau giữa các cuộc họp cùng ngày.
           "ma": f"LHTEST{ngay.strftime('%m%d')}{don_vi_chuan_bi[:3]}",
           "dv": don_vi_chuan_bi, "dvtc": str(don_vi_id),
           "nguoi": str(TEST_USERS["TEST-G3-001"])})
    await db.flush()
    return str(row.scalar_one())


# ── quyền ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_cong_chuc_thuong_khong_duoc_cham(
    client: AsyncClient, db_session: AsyncSession, cbcc_user, seed_test_users,
):
    ch = await _tao_cuoc_hop(db_session, seed_test_users["don_vi_b"])

    assert (await client.get(f"{BASE}/quyen")
            ).json()["data"]["duoc_cham"] is False

    r = await client.put(f"{BASE}/{ch}", json={"diem": 5})
    assert r.status_code == 403
    assert r.json()["detail"]["error"]["code"] == "RATE_FORBIDDEN"


@pytest.mark.asyncio
async def test_truong_don_vi_cung_khong_duoc_cham(
    client: AsyncClient, db_session: AsyncSession, chu_toa_user,
    seed_test_users,
):
    """`chu_toa_user` là TDV, lãnh đạo đơn vị chứ không phải lãnh đạo Chi cục."""
    ch = await _tao_cuoc_hop(db_session, seed_test_users["don_vi_a"])
    assert (await client.get(f"{BASE}/quyen")
            ).json()["data"]["duoc_cham"] is False
    assert (await client.put(f"{BASE}/{ch}", json={"diem": 4})
            ).status_code == 403


@pytest.mark.asyncio
async def test_pho_chi_cuc_truong_cham_duoc(
    client: AsyncClient, db_session: AsyncSession, cbcc_user, seed_test_users,
):
    ch = await _tao_cuoc_hop(db_session, seed_test_users["don_vi_b"])
    _doi_user("TEST-G3-002", seed_test_users["don_vi_a"], vai_tro="PCCT",
              is_lanh_dao=True)

    assert (await client.get(f"{BASE}/quyen")
            ).json()["data"]["duoc_cham"] is True

    r = await client.put(f"{BASE}/{ch}",
                         json={"diem": 5, "ghi_chu": "Tài liệu gửi sớm"})
    assert r.status_code == 200, r.text
    d = r.json()["data"]
    assert d["diem_cua_toi"] == 5
    assert d["ghi_chu_cua_toi"] == "Tài liệu gửi sớm"
    assert d["so_luot"] == 1 and d["diem_tb"] == 5.0


@pytest.mark.asyncio
async def test_quan_tri_cham_duoc(
    client: AsyncClient, db_session: AsyncSession, admin_user, seed_test_users,
):
    ch = await _tao_cuoc_hop(db_session, seed_test_users["don_vi_a"])
    assert (await client.get(f"{BASE}/quyen")
            ).json()["data"]["duoc_cham"] is True
    assert (await client.put(f"{BASE}/{ch}", json={"diem": 3})
            ).status_code == 200


# ── chấm và sửa ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_cham_lai_la_ghi_de_khong_nhan_dong(
    client: AsyncClient, db_session: AsyncSession, cbcc_user, seed_test_users,
):
    ch = await _tao_cuoc_hop(db_session, seed_test_users["don_vi_b"])
    _doi_user("TEST-G3-002", seed_test_users["don_vi_a"], vai_tro="PCCT")

    await client.put(f"{BASE}/{ch}", json={"diem": 3})
    d = (await client.put(f"{BASE}/{ch}", json={"diem": 5})).json()["data"]
    assert d["diem_cua_toi"] == 5 and d["so_luot"] == 1

    dem = await db_session.scalar(sa_text(
        "SELECT count(*) FROM meeting.danh_gia_cuoc_hop WHERE cuoc_hop_id=:i"),
        {"i": ch})
    assert dem == 1


@pytest.mark.asyncio
async def test_diem_ngoai_khoang_bi_chan(
    client: AsyncClient, db_session: AsyncSession, admin_user, seed_test_users,
):
    ch = await _tao_cuoc_hop(db_session, seed_test_users["don_vi_a"])
    for sai in (0, 6, -1):
        assert (await client.put(f"{BASE}/{ch}", json={"diem": sai})
                ).status_code == 422, f"điểm {sai} phải bị chặn"


@pytest.mark.asyncio
async def test_cuoc_hop_khong_ton_tai_thi_404(
    client: AsyncClient, admin_user, seed_test_users,
):
    ma = "00000000-0000-0000-0000-000000000000"
    assert (await client.get(f"{BASE}/{ma}")).status_code == 404
    assert (await client.put(f"{BASE}/{ma}", json={"diem": 4})
            ).status_code == 404


@pytest.mark.asyncio
async def test_bo_cham(
    client: AsyncClient, db_session: AsyncSession, admin_user, seed_test_users,
):
    ch = await _tao_cuoc_hop(db_session, seed_test_users["don_vi_a"])
    await client.put(f"{BASE}/{ch}", json={"diem": 4})

    d = (await client.delete(f"{BASE}/{ch}")).json()["data"]
    assert d["diem_cua_toi"] is None and d["so_luot"] == 0
    # Rút lần nữa thì không còn gì để rút.
    assert (await client.delete(f"{BASE}/{ch}")).status_code == 404


@pytest.mark.asyncio
async def test_khong_ai_xoa_duoc_diem_nguoi_khac(
    client: AsyncClient, db_session: AsyncSession, cbcc_user, seed_test_users,
):
    ch = await _tao_cuoc_hop(db_session, seed_test_users["don_vi_b"])
    _doi_user("TEST-G3-002", seed_test_users["don_vi_a"], vai_tro="PCCT")
    await client.put(f"{BASE}/{ch}", json={"diem": 5})

    # Quản trị cũng chỉ rút được điểm của chính mình.
    _doi_user("TEST-G3-001", seed_test_users["don_vi_a"], vai_tro="ADMIN",
              is_admin=True)
    assert (await client.delete(f"{BASE}/{ch}")).status_code == 404
    assert (await client.get(f"{BASE}/{ch}")).json()["data"]["so_luot"] == 1


# ── xem ───────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_ai_cung_xem_duoc_diem_da_cham(
    client: AsyncClient, db_session: AsyncSession, cbcc_user, seed_test_users,
):
    ch = await _tao_cuoc_hop(db_session, seed_test_users["don_vi_b"])
    _doi_user("TEST-G3-002", seed_test_users["don_vi_a"], vai_tro="PCCT")
    await client.put(f"{BASE}/{ch}", json={"diem": 4})

    _set_user(cbcc_user)
    d = (await client.get(f"{BASE}/{ch}")).json()["data"]
    assert d["duoc_cham"] is False          # thấy nhưng không chấm được
    assert d["so_luot"] == 1 and d["diem_tb"] == 4.0
    assert d["diem_cua_toi"] is None
    assert d["danh_sach"][0]["la_cua_toi"] is False


@pytest.mark.asyncio
async def test_diem_trung_binh_gop_nhieu_nguoi(
    client: AsyncClient, db_session: AsyncSession, cbcc_user, seed_test_users,
):
    ch = await _tao_cuoc_hop(db_session, seed_test_users["don_vi_b"])
    _doi_user("TEST-G3-002", seed_test_users["don_vi_a"], vai_tro="PCCT")
    await client.put(f"{BASE}/{ch}", json={"diem": 5})
    _doi_user("TEST-G3-003", seed_test_users["don_vi_b"], vai_tro="CCT")
    d = (await client.put(f"{BASE}/{ch}", json={"diem": 4})).json()["data"]

    assert d["so_luot"] == 2 and d["diem_tb"] == 4.5
    assert d["diem_cua_toi"] == 4


@pytest.mark.asyncio
async def test_diem_hien_tren_the_lich(
    client: AsyncClient, db_session: AsyncSession, cbcc_user, seed_test_users,
):
    """Hệ cũ hiện sao ngay trên thẻ lịch — giữ đúng chỗ đó."""
    ngay = date.today() + timedelta(days=3)
    ch = await _tao_cuoc_hop(db_session, seed_test_users["don_vi_b"], ngay=ngay)
    _doi_user("TEST-G3-002", seed_test_users["don_vi_a"], vai_tro="PCCT")
    await client.put(f"{BASE}/{ch}", json={"diem": 5})

    r = await client.get(f"{BASE_LICH}/", params={"tu-ngay": ngay.isoformat(),
                                            "den-ngay": ngay.isoformat()})
    sk = next(x for x in r.json()["data"] if x["id"] == ch)
    assert sk["diem_chuan_bi"] == 5.0 and sk["so_luot_cham"] == 1


# ── tổng hợp ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_tong_hop_theo_don_vi_chuan_bi(
    client: AsyncClient, db_session: AsyncSession, cbcc_user, seed_test_users,
):
    ngay = date.today() + timedelta(days=5)
    a = await _tao_cuoc_hop(db_session, seed_test_users["don_vi_b"], ngay=ngay,
                            don_vi_chuan_bi="Đội Test G5.3")
    b = await _tao_cuoc_hop(db_session, seed_test_users["don_vi_b"],
                            ngay=ngay + timedelta(days=1),
                            don_vi_chuan_bi="Đội Test G5.3")
    _doi_user("TEST-G3-002", seed_test_users["don_vi_a"], vai_tro="PCCT")
    await client.put(f"{BASE}/{a}", json={"diem": 5})
    await client.put(f"{BASE}/{b}", json={"diem": 3})

    d = (await client.get(f"{BASE}/tong-hop",
                          params={"tu-ngay": ngay.isoformat()})).json()["data"]
    dv = next(x for x in d["theo_don_vi"] if x["don_vi"] == "Đội Test G5.3")
    assert dv["so_cuoc_hop"] == 2 and dv["diem_tb"] == 4.0
    assert {x["cuoc_hop_id"] for x in d["cuoc_hop"]} >= {a, b}
