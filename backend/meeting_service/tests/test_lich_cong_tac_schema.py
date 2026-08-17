"""Kiểm chứng ràng buộc schema sau khi hợp nhất Lịch công tác vào cuoc_hop.

Trọng tâm: chứng minh việc nới `chu_toa_id` thành nullable KHÔNG làm mất khả
năng ép buộc của HKG. Ràng buộc `ck_cuoc_hop_hkg_bat_buoc` phải chặn được dòng
HKG thiếu chủ trì, trong khi vẫn cho dòng Lịch công tác lịch sử đi qua.

Đây là lập luận trung tâm của phương án một-bảng (xem
docs/lich-cong-tac/KE_HOACH_TRIEN_KHAI.md §0 và §G2.1) nên phải có test, không
được tin vào thiết kế trên giấy.

Chạy:  DB_NAME=kpi_haiquan_test ALLOW_PROD_TEST=true \
       pytest meeting_service/tests/test_lich_cong_tac_schema.py -v
"""

from __future__ import annotations

import uuid
from datetime import date, timedelta

import pytest
from sqlalchemy import text as sa_text
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = pytest.mark.asyncio


INSERT_CUOC_HOP = sa_text("""
    INSERT INTO meeting.cuoc_hop
        (tieu_de, ngay_hop, ngay_ket_thuc, gio_bat_dau, created_by,
         nguon, chu_toa_id, don_vi_to_chuc_id, ma_lich, loai_lich)
    VALUES
        (:tieu_de, :ngay_hop, :ngay_ket_thuc, '08:00', :created_by,
         :nguon, :chu_toa_id, :don_vi_to_chuc_id, :ma_lich, :loai_lich)
    RETURNING id
""")


async def _ids(session: AsyncSession) -> tuple[uuid.UUID, uuid.UUID]:
    """Một cong_chuc và một don_vi thật để làm FK hợp lệ."""
    cc = (await session.execute(sa_text(
        "SELECT id FROM public.cong_chuc WHERE is_active LIMIT 1"))).scalar_one()
    dv = (await session.execute(sa_text(
        "SELECT id FROM public.don_vi LIMIT 1"))).scalar_one()
    return cc, dv


async def _them(session: AsyncSession, **kw):
    cc, dv = await _ids(session)
    tham_so = {
        "tieu_de": "test lịch công tác",
        "ngay_hop": date.today(),
        "ngay_ket_thuc": None,
        "created_by": cc,
        "nguon": "HKG",
        "chu_toa_id": cc,
        "don_vi_to_chuc_id": dv,
        "ma_lich": None,
        "loai_lich": None,
    }
    tham_so.update(kw)
    return await session.execute(INSERT_CUOC_HOP, tham_so)


# ════════════════════════════════════════════════════════════════════
# Ràng buộc của HKG vẫn còn hiệu lực
# ════════════════════════════════════════════════════════════════════

async def test_hkg_thieu_chu_toa_bi_chan(db_session: AsyncSession):
    """Đây là test quan trọng nhất của cả migration 016."""
    with pytest.raises((IntegrityError, DBAPIError)) as e:
        await _them(db_session, chu_toa_id=None)
    assert "ck_cuoc_hop_hkg_bat_buoc" in str(e.value)


async def test_hkg_thieu_don_vi_to_chuc_bi_chan(db_session: AsyncSession):
    with pytest.raises((IntegrityError, DBAPIError)) as e:
        await _them(db_session, don_vi_to_chuc_id=None)
    assert "ck_cuoc_hop_hkg_bat_buoc" in str(e.value)


async def test_hkg_du_thong_tin_thi_qua(db_session: AsyncSession):
    row = await _them(db_session)
    assert row.scalar_one() is not None


# ════════════════════════════════════════════════════════════════════
# Dòng Lịch công tác đi qua được dù thiếu chủ trì
# ════════════════════════════════════════════════════════════════════

async def test_lich_cong_tac_khong_chu_toa_van_qua(db_session: AsyncSession):
    """117/489 cuộc họp lịch sử không có chủ trì — phải nạp được."""
    row = await _them(
        db_session, nguon="LICH_CONG_TAC", chu_toa_id=None,
        don_vi_to_chuc_id=None, ma_lich="LH9001", loai_lich="HOP",
    )
    assert row.scalar_one() is not None


async def test_lich_cong_tac_thieu_ma_lich_bi_chan(db_session: AsyncSession):
    with pytest.raises((IntegrityError, DBAPIError)) as e:
        await _them(db_session, nguon="LICH_CONG_TAC", chu_toa_id=None,
                    don_vi_to_chuc_id=None, ma_lich=None, loai_lich="HOP")
    assert "ck_cuoc_hop_lct_bat_buoc" in str(e.value)


async def test_lich_cong_tac_thieu_loai_lich_bi_chan(db_session: AsyncSession):
    with pytest.raises((IntegrityError, DBAPIError)) as e:
        await _them(db_session, nguon="LICH_CONG_TAC", chu_toa_id=None,
                    don_vi_to_chuc_id=None, ma_lich="LH9002", loai_lich=None)
    assert "ck_cuoc_hop_lct_bat_buoc" in str(e.value)


# ════════════════════════════════════════════════════════════════════
# Mã lịch: unique nhưng chỉ trên dòng có mã
# ════════════════════════════════════════════════════════════════════

async def test_ma_lich_trung_bi_chan(db_session: AsyncSession):
    await _them(db_session, nguon="LICH_CONG_TAC", chu_toa_id=None,
                don_vi_to_chuc_id=None, ma_lich="LH9100", loai_lich="HOP")
    with pytest.raises((IntegrityError, DBAPIError)) as e:
        await _them(db_session, nguon="LICH_CONG_TAC", chu_toa_id=None,
                    don_vi_to_chuc_id=None, ma_lich="LH9100", loai_lich="HOP")
    assert "uq_cuoc_hop_ma_lich" in str(e.value)


async def test_nhieu_dong_hkg_cung_ma_lich_null(db_session: AsyncSession):
    """Unique có điều kiện: dòng HKG để ma_lich NULL, không được xung đột."""
    await _them(db_session, tieu_de="hkg 1")
    row = await _them(db_session, tieu_de="hkg 2")
    assert row.scalar_one() is not None


# ════════════════════════════════════════════════════════════════════
# Danh mục và khoảng ngày
# ════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize(
    "loai", ["HOP", "TRUC_BAN", "HOI_NGHI", "LAM_VIEC", "CONG_TAC", "LICH_KHAC"])
async def test_sau_loai_lich_dang_chay_deu_hop_le(db_session: AsyncSession, loai):
    row = await _them(db_session, nguon="LICH_CONG_TAC", chu_toa_id=None,
                      don_vi_to_chuc_id=None, ma_lich=f"LH92{loai[:2]}",
                      loai_lich=loai)
    assert row.scalar_one() is not None


async def test_loai_lich_ngoai_danh_muc_bi_chan(db_session: AsyncSession):
    with pytest.raises((IntegrityError, DBAPIError)) as e:
        await _them(db_session, nguon="LICH_CONG_TAC", chu_toa_id=None,
                    don_vi_to_chuc_id=None, ma_lich="LH9300",
                    loai_lich="KHONG_TON_TAI")
    assert "ck_cuoc_hop_loai_lich" in str(e.value)


async def test_ngay_ket_thuc_truoc_ngay_hop_bi_chan(db_session: AsyncSession):
    with pytest.raises((IntegrityError, DBAPIError)) as e:
        await _them(db_session, ngay_ket_thuc=date.today() - timedelta(days=1))
    assert "ck_cuoc_hop_khoang_ngay" in str(e.value)


async def test_lich_nhieu_ngay_hop_le(db_session: AsyncSession):
    row = await _them(db_session, ngay_ket_thuc=date.today() + timedelta(days=3))
    assert row.scalar_one() is not None


async def test_nguon_ngoai_danh_muc_bi_chan(db_session: AsyncSession):
    with pytest.raises((IntegrityError, DBAPIError)) as e:
        await _them(db_session, nguon="SAI")
    assert "ck_cuoc_hop_nguon" in str(e.value)


# ════════════════════════════════════════════════════════════════════
# Trụ sở trực ban
# ════════════════════════════════════════════════════════════════════

async def test_seed_du_9_tru_so(db_session: AsyncSession):
    n = (await db_session.execute(sa_text(
        "SELECT count(*) FROM meeting.tru_so WHERE is_active"))).scalar_one()
    assert n == 9


async def test_hai_tru_so_kiem_soat_cung_mot_don_vi(db_session: AsyncSession):
    """KSHQ_HL và KSHQ_MC là hai trụ sở của CÙNG đơn vị KSHQ — lý do phải khoá
    trực ban theo tru_so_id chứ không theo don_vi_id."""
    rows = (await db_session.execute(sa_text("""
        SELECT t.ma_tru_so, d.ma_don_vi
        FROM meeting.tru_so t JOIN public.don_vi d ON d.id = t.don_vi_id
        WHERE t.ma_tru_so IN ('KSHQ_HL', 'KSHQ_MC')
    """))).all()
    assert len(rows) == 2
    assert {r.ma_don_vi for r in rows} == {"KSHQ"}


async def test_tru_so_chi_cuc_khong_gan_don_vi(db_session: AsyncSession):
    """CHICUC là trụ sở dùng chung của 7 phòng/đội → don_vi_id phải NULL."""
    dv = (await db_session.execute(sa_text(
        "SELECT don_vi_id FROM meeting.tru_so WHERE ma_tru_so = 'CHICUC'"
    ))).scalar_one()
    assert dv is None


async def test_ma_tru_so_trung_bi_chan(db_session: AsyncSession):
    with pytest.raises((IntegrityError, DBAPIError)) as e:
        await db_session.execute(sa_text(
            "INSERT INTO meeting.tru_so (ma_tru_so, ten_tru_so) "
            "VALUES ('CHICUC', 'trùng mã')"))
    assert "uq_tru_so_ma" in str(e.value)


# ════════════════════════════════════════════════════════════════════
# Ghi chú, chia sẻ, đánh giá
# ════════════════════════════════════════════════════════════════════

async def test_khong_chia_se_ghi_chu_cho_chinh_minh(db_session: AsyncSession):
    cc, _ = await _ids(db_session)
    gc = (await db_session.execute(sa_text(
        "INSERT INTO meeting.ghi_chu (tieu_de, cong_chuc_id) "
        "VALUES ('note', :cc) RETURNING id"), {"cc": cc})).scalar_one()
    with pytest.raises((IntegrityError, DBAPIError)) as e:
        await db_session.execute(sa_text(
            "INSERT INTO meeting.ghi_chu_chia_se "
            "(ghi_chu_id, nguoi_gui_id, nguoi_nhan_id) "
            "VALUES (:gc, :cc, :cc)"), {"gc": gc, "cc": cc})
    assert "ck_ghi_chu_chia_se_khac_nguoi" in str(e.value)


async def test_ghi_chu_doc_lap_khong_gan_cuoc_hop(db_session: AsyncSession):
    cc, _ = await _ids(db_session)
    gc = (await db_session.execute(sa_text(
        "INSERT INTO meeting.ghi_chu (tieu_de, cong_chuc_id, cuoc_hop_id) "
        "VALUES ('độc lập', :cc, NULL) RETURNING id"), {"cc": cc})).scalar_one()
    assert gc is not None


@pytest.mark.parametrize("diem,hop_le", [(1, True), (5, True), (0, False), (6, False)])
async def test_diem_danh_gia_trong_khoang_1_5(db_session: AsyncSession, diem, hop_le):
    cc, _ = await _ids(db_session)
    ch = (await _them(db_session)).scalar_one()
    sql = sa_text(
        "INSERT INTO meeting.danh_gia_cuoc_hop (cuoc_hop_id, cong_chuc_id, diem) "
        "VALUES (:ch, :cc, :d)")
    if hop_le:
        await db_session.execute(sql, {"ch": ch, "cc": cc, "d": diem})
    else:
        with pytest.raises((IntegrityError, DBAPIError)) as e:
            await db_session.execute(sql, {"ch": ch, "cc": cc, "d": diem})
        assert "ck_danh_gia_diem" in str(e.value)


# ════════════════════════════════════════════════════════════════════
# Tài liệu: thuộc cuộc họp HOẶC ghi chú, không cả hai
# ════════════════════════════════════════════════════════════════════

async def test_tai_lieu_khong_thuoc_ca_hai_chu_the(db_session: AsyncSession):
    cc, _ = await _ids(db_session)
    ch = (await _them(db_session)).scalar_one()
    gc = (await db_session.execute(sa_text(
        "INSERT INTO meeting.ghi_chu (tieu_de, cong_chuc_id) "
        "VALUES ('n', :cc) RETURNING id"), {"cc": cc})).scalar_one()
    with pytest.raises((IntegrityError, DBAPIError)) as e:
        await db_session.execute(sa_text("""
            INSERT INTO meeting.tai_lieu
                (cuoc_hop_id, ghi_chu_id, ten_tai_lieu, minio_key, file_size, created_by)
            VALUES (:ch, :gc, 'f.pdf', 'k', 1, :cc)
        """), {"ch": ch, "gc": gc, "cc": cc})
    assert "ck_tai_lieu_chu_the" in str(e.value)


async def test_tai_lieu_thuoc_ghi_chu(db_session: AsyncSession):
    cc, _ = await _ids(db_session)
    gc = (await db_session.execute(sa_text(
        "INSERT INTO meeting.ghi_chu (tieu_de, cong_chuc_id) "
        "VALUES ('n', :cc) RETURNING id"), {"cc": cc})).scalar_one()
    tl = (await db_session.execute(sa_text("""
        INSERT INTO meeting.tai_lieu
            (cuoc_hop_id, ghi_chu_id, ten_tai_lieu, minio_key, file_size, created_by)
        VALUES (NULL, :gc, 'f.pdf', 'k', 1, :cc) RETURNING id
    """), {"gc": gc, "cc": cc})).scalar_one()
    assert tl is not None


# ════════════════════════════════════════════════════════════════════
# Không làm vỡ dữ liệu HKG sẵn có
# ════════════════════════════════════════════════════════════════════

async def test_cuoc_hop_hkg_san_co_duoc_gan_nguon_va_ngay_hien_thi(
        db_session: AsyncSession):
    """Migration 016 backfill ngay_hien_thi = ngay_hop cho dòng cũ, nếu không
    thì cuộc họp HKG hiện có sẽ không hiện lên Lịch công tác."""
    row = (await db_session.execute(sa_text("""
        SELECT count(*) AS tong,
               count(*) FILTER (WHERE nguon = 'HKG') AS hkg,
               count(*) FILTER (WHERE ngay_hien_thi IS NULL) AS thieu_ngay
        FROM meeting.cuoc_hop
        WHERE is_deleted = FALSE
    """))).one()
    assert row.tong == row.hkg, "dữ liệu sẵn có phải đều là nguồn HKG"
    assert row.thieu_ngay == 0, "phải backfill hết ngay_hien_thi"
