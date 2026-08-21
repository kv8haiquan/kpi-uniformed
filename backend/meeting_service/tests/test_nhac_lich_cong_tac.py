"""Nhắc lịch công tác qua Zalo — mở rộng bộ nhắc 3 tầng sang nguồn LICH_CONG_TAC.

Hai việc được chốt ở đây, mỗi việc một nhóm test:

  1. **Giờ họp là giờ Việt Nam.** Cho tới 21/08/2026 bộ nhắc ghép ngày + giờ
     họp với `tzinfo=utc`, lệch đúng 7 tiếng. Bằng chứng trên dữ liệu thật:
     tin "nhắc trước 30 phút" của cuộc họp 09:00 ngày 17/08 được gửi lúc
     15:25 cùng ngày — sau khi họp đã tan 6,4 giờ.

  2. **Người nhận lấy ở bảng khác nhau tuỳ nguồn.** HKG đọc
     `meeting.thanh_phan`; Lịch công tác đọc `meeting.lanh_dao_lien_quan`.
     Nhầm bảng thì sự kiện lịch không có ai để nhắc và im lặng bỏ qua.

    ./scripts/dev.sh test meeting_service/tests/test_nhac_lich_cong_tac.py -v
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, time, timedelta, timezone

import pytest
from sqlalchemy import text as sa_text
from sqlalchemy.ext.asyncio import AsyncSession

from meeting_service.services.scheduler_helpers import (
    GIO_VN,
    gio_bat_dau_utc,
    nhac_hop_3_tang_logic,
    reset_cache,
)

pytestmark = pytest.mark.asyncio

TIEN_TO = "TEST NHAC LCT"


async def _xoa_sach(db: AsyncSession) -> None:
    await db.execute(sa_text(f"""
        DELETE FROM common.thong_bao WHERE doi_tuong_id IN
          (SELECT id FROM meeting.cuoc_hop WHERE tieu_de LIKE '{TIEN_TO}%')"""))
    await db.execute(sa_text(f"""
        DELETE FROM meeting.lanh_dao_lien_quan WHERE cuoc_hop_id IN
          (SELECT id FROM meeting.cuoc_hop WHERE tieu_de LIKE '{TIEN_TO}%')"""))
    await db.execute(sa_text(f"""
        DELETE FROM meeting.thanh_phan WHERE cuoc_hop_id IN
          (SELECT id FROM meeting.cuoc_hop WHERE tieu_de LIKE '{TIEN_TO}%')"""))
    await db.execute(sa_text(
        f"DELETE FROM meeting.cuoc_hop WHERE tieu_de LIKE '{TIEN_TO}%'"))
    await db.commit()


@pytest.fixture(autouse=True)
async def don_dep(db_session: AsyncSession):
    await _xoa_sach(db_session)
    yield
    await _xoa_sach(db_session)


async def _tao_su_kien(
    db: AsyncSession, seed, *, nguon: str, ngay: date, gio: str,
    nguoi_nhan: list[str], hau_to: str = "",
) -> uuid.UUID:
    """Ghi thẳng vào bảng, không qua API — API của Lịch công tác không nhận
    `nguon` và API của HKG bắt buộc nhiều trường không liên quan test này."""
    ch_id = uuid.uuid4()
    nguoi_tao = "aaaaaaaa-0001-0000-0000-000000000001"
    await db.execute(sa_text("""
        INSERT INTO meeting.cuoc_hop
            (id, tieu_de, ngay_hop, gio_bat_dau, trang_thai, nguon, ma_lich,
             loai_lich, created_by, don_vi_to_chuc_id, chu_toa_id)
        VALUES (:id, :td, :ngay, :gio, 'DA_THONG_BAO', :nguon, :ma,
                :loai, :nt, :dv, :ct)
    """), {"id": str(ch_id), "td": f"{TIEN_TO} {nguon}{hau_to}", "ngay": ngay,
           "gio": time.fromisoformat(gio), "nguon": nguon,
           "ma": f"LH9{uuid.uuid4().hex[:5]}",
           # Hai nguồn có hai ràng buộc bắt buộc khác nhau:
           #   ck_cuoc_hop_lct_bat_buoc → LICH_CONG_TAC phải có ma_lich + loai_lich
           #   ck_cuoc_hop_hkg_bat_buoc → HKG phải có chu_toa_id + don_vi_to_chuc_id
           "loai": "HOP" if nguon == "LICH_CONG_TAC" else None,
           "ct": nguoi_tao if nguon == "HKG" else None,
           "nt": nguoi_tao, "dv": str(seed["don_vi_a"])})

    bang = ("meeting.thanh_phan" if nguon == "HKG"
            else "meeting.lanh_dao_lien_quan")
    for i, cc in enumerate(nguoi_nhan):
        if nguon == "HKG":
            await db.execute(sa_text(f"""
                INSERT INTO {bang} (cuoc_hop_id, cong_chuc_id, loai_tham_du)
                VALUES (:ch, :cc, 'BAT_BUOC')"""), {"ch": str(ch_id), "cc": cc})
        else:
            await db.execute(sa_text(f"""
                INSERT INTO {bang} (cuoc_hop_id, cong_chuc_id, thu_tu)
                VALUES (:ch, :cc, :i)"""), {"ch": str(ch_id), "cc": cc, "i": i})
    await db.flush()
    return ch_id


CC_A = "aaaaaaaa-0002-0000-0000-000000000002"
CC_B = "aaaaaaaa-0003-0000-0000-000000000003"


# ════════════════════════════════════════════════════════════════════
# 1. Giờ họp là giờ Việt Nam
# ════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("gio,mong_utc", [(time(9, 0), 2), (time(14, 30), 7)])
def test_gio_bat_dau_doi_dung_sang_utc(gio, mong_utc):
    """Giờ ta trừ 7 là giờ UTC. Trước fix, hàm này coi giờ ta là giờ UTC."""
    assert gio_bat_dau_utc(date(2026, 6, 15), gio).hour == mong_utc
    assert gio_bat_dau_utc(date(2026, 6, 15), time(9, 0)) == datetime(
        2026, 6, 15, 2, 0, tzinfo=timezone.utc)





async def test_nhac_dung_gio_theo_mui_gio_viet_nam(db_session, seed_test_users):
    """Nhắc phải nổ đúng 1 giờ trước giờ họp THẬT, không lệch 7 tiếng.

    Đây là ca tái hiện đúng sự cố đo được: cuộc họp 09:00 ngày 17/08 nhận tin
    "nhắc trước 30 phút" lúc 15:25 — sau khi đã tan họp.
    """
    reset_cache()
    ngay = date(2026, 6, 15)
    ch_id = await _tao_su_kien(db_session, seed_test_users, nguon="LICH_CONG_TAC",
                               ngay=ngay, gio="09:00", nguoi_nhan=[CC_A])

    hop_that = datetime(2026, 6, 15, 9, 0, tzinfo=GIO_VN)

    # Đúng 1 giờ trước giờ họp thật → phải gửi.
    reset_cache()
    n = await nhac_hop_3_tang_logic(
        db_session, now=hop_that - timedelta(hours=1, minutes=2))
    assert n == 1, "Phải nhắc đúng 1 giờ trước giờ họp giờ Việt Nam"

    # Mốc mà lỗi cũ sẽ nổ (09:00 hiểu nhầm thành UTC) → giờ đó họp đã tan lâu,
    # không được gửi gì nữa.
    reset_cache()
    hop_hieu_nham = datetime(2026, 6, 15, 9, 0, tzinfo=timezone.utc)
    n2 = await nhac_hop_3_tang_logic(
        db_session, now=hop_hieu_nham - timedelta(hours=1, minutes=2))
    assert n2 == 0, "Không được nhắc theo giờ đã hiểu nhầm là UTC"
    assert ch_id is not None


# ════════════════════════════════════════════════════════════════════
# 2. Nguồn LICH_CONG_TAC — người nhận ở bảng lanh_dao_lien_quan
# ════════════════════════════════════════════════════════════════════

async def test_su_kien_lich_cong_tac_duoc_nhac_du_ba_moc(
    db_session, seed_test_users
):
    """Lãnh đạo chốt giữ đủ ba mốc (21/08/2026)."""
    ngay = date(2026, 6, 20)
    ch_id = await _tao_su_kien(db_session, seed_test_users, nguon="LICH_CONG_TAC",
                               ngay=ngay, gio="14:30", nguoi_nhan=[CC_A, CC_B])
    hop = datetime(2026, 6, 20, 14, 30, tzinfo=GIO_VN)

    for lech, mong in ((timedelta(hours=24, minutes=2), 2),
                       (timedelta(hours=1, minutes=2), 2),
                       (timedelta(minutes=32), 2)):
        reset_cache()
        assert await nhac_hop_3_tang_logic(db_session, now=hop - lech) == mong

    res = await db_session.execute(sa_text("""
        SELECT doi_tuong_type, count(*) FROM common.thong_bao
         WHERE doi_tuong_id = :id GROUP BY 1"""), {"id": str(ch_id)})
    assert {r[0]: r[1] for r in res.fetchall()} == {
        "NHAC_HOP_24H": 2, "NHAC_HOP_1H": 2, "NHAC_HOP_30P": 2}


async def test_khong_gui_lai_khi_chay_tick_thu_hai(db_session, seed_test_users):
    """Bộ quét chạy mỗi phút — trong cùng một window phải chỉ gửi một lần."""
    ngay = date(2026, 6, 20)
    await _tao_su_kien(db_session, seed_test_users, nguon="LICH_CONG_TAC",
                       ngay=ngay, gio="14:30", nguoi_nhan=[CC_A])
    hop = datetime(2026, 6, 20, 14, 30, tzinfo=GIO_VN)

    reset_cache()
    assert await nhac_hop_3_tang_logic(
        db_session, now=hop - timedelta(hours=1, minutes=3)) == 1
    reset_cache()
    assert await nhac_hop_3_tang_logic(
        db_session, now=hop - timedelta(hours=1, minutes=1)) == 0


async def test_su_kien_khong_co_lanh_dao_thi_bo_qua(db_session, seed_test_users):
    """9% sự kiện lịch không ghi lãnh đạo nào — không có ai để nhắc."""
    await _tao_su_kien(db_session, seed_test_users, nguon="LICH_CONG_TAC",
                       ngay=date(2026, 6, 20), gio="14:30", nguoi_nhan=[])
    hop = datetime(2026, 6, 20, 14, 30, tzinfo=GIO_VN)
    reset_cache()
    assert await nhac_hop_3_tang_logic(
        db_session, now=hop - timedelta(hours=1, minutes=2)) == 0


async def test_chua_dang_thi_khong_nhac(db_session, seed_test_users):
    """Lịch còn ở trạng thái dự kiến thì chưa ai cần biết."""
    ch_id = await _tao_su_kien(db_session, seed_test_users, nguon="LICH_CONG_TAC",
                               ngay=date(2026, 6, 20), gio="14:30",
                               nguoi_nhan=[CC_A])
    await db_session.execute(sa_text(
        "UPDATE meeting.cuoc_hop SET trang_thai='LEN_KE_HOACH' WHERE id=:id"),
        {"id": str(ch_id)})
    await db_session.flush()
    hop = datetime(2026, 6, 20, 14, 30, tzinfo=GIO_VN)
    reset_cache()
    assert await nhac_hop_3_tang_logic(
        db_session, now=hop - timedelta(hours=1, minutes=2)) == 0


async def test_duong_dan_trong_thong_bao_theo_dung_nguon(
    db_session, seed_test_users
):
    """Hai nguồn có hai màn hình riêng — dẫn nhầm là người dùng nhận 403."""
    hop = datetime(2026, 6, 20, 14, 30, tzinfo=GIO_VN)
    lct = await _tao_su_kien(db_session, seed_test_users, nguon="LICH_CONG_TAC",
                             ngay=date(2026, 6, 20), gio="14:30",
                             nguoi_nhan=[CC_A], hau_to=" lct")
    hkg = await _tao_su_kien(db_session, seed_test_users, nguon="HKG",
                             ngay=date(2026, 6, 20), gio="14:30",
                             nguoi_nhan=[CC_B], hau_to=" hkg")
    reset_cache()
    await nhac_hop_3_tang_logic(db_session, now=hop - timedelta(hours=1, minutes=2))

    for ch_id, mong in ((lct, f"/lich-cong-tac/{lct}"),
                        (hkg, f"/hop-khong-giay/chi-tiet/{hkg}")):
        res = await db_session.execute(sa_text(
            "SELECT link_url FROM common.thong_bao WHERE doi_tuong_id=:id LIMIT 1"),
            {"id": str(ch_id)})
        assert res.scalar_one() == mong


async def test_ca_hai_nguon_cung_duoc_nhac_trong_mot_luot(
    db_session, seed_test_users
):
    """Mở rộng sang lịch công tác KHÔNG được làm mất phần nhắc của HKG."""
    hop = datetime(2026, 6, 20, 14, 30, tzinfo=GIO_VN)
    await _tao_su_kien(db_session, seed_test_users, nguon="LICH_CONG_TAC",
                       ngay=date(2026, 6, 20), gio="14:30",
                       nguoi_nhan=[CC_A], hau_to=" lct")
    await _tao_su_kien(db_session, seed_test_users, nguon="HKG",
                       ngay=date(2026, 6, 20), gio="14:30",
                       nguoi_nhan=[CC_B], hau_to=" hkg")
    reset_cache()
    assert await nhac_hop_3_tang_logic(
        db_session, now=hop - timedelta(hours=1, minutes=2)) == 2
