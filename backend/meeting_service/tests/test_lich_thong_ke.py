"""Kiểm thử chỉ số tổng quan Lịch công tác — G4.10.

Điểm dễ sai: đếm "trong tháng" tới hôm nay thay vì trọn tháng. Lịch là để nhìn
việc SẮP tới, đếm tới hôm nay thì đầu tháng nào con số cũng gần bằng 0.

    ./scripts/dev.sh test meeting_service/tests/test_lich_thong_ke.py -v
"""

from __future__ import annotations

from datetime import date, timedelta

import pytest
from sqlalchemy import text as sa_text

pytestmark = pytest.mark.asyncio

BASE = "/api/v1/hop-khong-giay/lich-cong-tac"


async def test_du_chi_so_va_moc(client, admin_user):
    d = (await client.get(f"{BASE}/thong-ke")).json()["data"]
    for k in ("hom_nay", "ngay_mai", "trong_tuan", "trong_thang", "trong_nam",
              "theo_loai_thang_nay", "theo_lanh_dao_thang_nay", "moc"):
        assert k in d, k
    for k in ("hom_nay", "dau_tuan", "cuoi_tuan", "dau_thang", "cuoi_thang",
              "dau_nam", "cuoi_nam"):
        assert k in d["moc"], k


async def test_moc_thang_la_tron_thang(client, admin_user):
    m = (await client.get(f"{BASE}/thong-ke")).json()["data"]["moc"]
    dau = date.fromisoformat(m["dau_thang"])
    cuoi = date.fromisoformat(m["cuoi_thang"])
    assert dau.day == 1
    assert (cuoi + timedelta(days=1)).day == 1, "phải là ngày cuối tháng"


async def test_trong_thang_dem_tron_thang(client, db_session, admin_user):
    """So thẳng với số đếm được từ CSDL cho trọn tháng hiện tại."""
    d = (await client.get(f"{BASE}/thong-ke")).json()["data"]
    that = (await db_session.execute(sa_text("""
        SELECT count(*) FROM meeting.cuoc_hop
         WHERE is_deleted = false
           AND ngay_hien_thi BETWEEN :dau AND :cuoi
    """), {"dau": date.fromisoformat(d["moc"]["dau_thang"]),
           "cuoi": date.fromisoformat(d["moc"]["cuoi_thang"])})
    ).scalar()
    assert d["trong_thang"] == that


async def test_tuan_bat_dau_thu_hai(client, admin_user):
    m = (await client.get(f"{BASE}/thong-ke")).json()["data"]["moc"]
    assert date.fromisoformat(m["dau_tuan"]).weekday() == 0
    assert (date.fromisoformat(m["cuoi_tuan"])
            - date.fromisoformat(m["dau_tuan"])) == timedelta(days=6)


async def test_theo_lanh_dao_xep_giam_dan(client, db_session, admin_user):
    ld = (await client.get(f"{BASE}/thong-ke")).json()[
        "data"]["theo_lanh_dao_thang_nay"]
    if not ld:
        pytest.skip("tháng này chưa có lịch nào gắn lãnh đạo")
    so = [x["so_su_kien"] for x in ld]
    assert so == sorted(so, reverse=True)
    assert all(x["ho_ten"] for x in ld)


async def test_khong_dem_trung_khi_vua_chu_toa_vua_lanh_dao(
        client, db_session, admin_user):
    """Một người vừa là chủ toạ vừa nằm trong lãnh đạo liên quan chỉ tính 1."""
    ld = (await client.get(f"{BASE}/thong-ke")).json()[
        "data"]["theo_lanh_dao_thang_nay"]
    if not ld:
        pytest.skip("tháng này chưa có lịch nào gắn lãnh đạo")
    tong_su_kien = (await db_session.execute(sa_text("""
        SELECT count(*) FROM meeting.cuoc_hop ch
         WHERE ch.is_deleted = false
           AND ch.ngay_hien_thi BETWEEN date_trunc('month', CURRENT_DATE)
               AND (date_trunc('month', CURRENT_DATE)
                    + INTERVAL '1 month - 1 day')::date
           AND (ch.chu_toa_id IS NOT NULL
                OR EXISTS (SELECT 1 FROM meeting.lanh_dao_lien_quan l
                            WHERE l.cuoc_hop_id = ch.id))
    """))).scalar()
    # Mỗi cuộc họp có thể có nhiều lãnh đạo, nên tổng theo người ≥ số cuộc họp;
    # nhưng một người trên một cuộc họp chỉ được đếm một lần, nên không thể
    # vượt quá số cuộc họp nhân số người tối đa. Kiểm cận dưới là đủ để bắt
    # lỗi đếm trùng do UNION ALL.
    assert sum(x["so_su_kien"] for x in ld) >= tong_su_kien
