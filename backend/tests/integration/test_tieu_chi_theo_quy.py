"""
tests/integration/test_tieu_chi_theo_quy.py
===========================================
Tests cho việc chuyển chấm TIÊU CHÍ CHUNG từ THÁNG sang QUÝ
(Công văn 21169/CHQ-TCCB, áp dụng từ quý III/2026).

Chạy trên kpi_haiquan_test — TUYỆT ĐỐI KHÔNG chạy trên kpi_haiquan (prod):
    DB_NAME=kpi_haiquan_test pytest tests/integration/test_tieu_chi_theo_quy.py -v

Phạm vi:
1. KHÔNG HỒI TỐ — các kỳ trước Q3/2026 đọc đúng bản ghi tháng đó (đo trên dữ
   liệu thật của DB test, chỉ đọc). Đây là phép thử quan trọng nhất.
2. Neo đúng chỗ — tự đánh giá với tháng bất kỳ trong quý ghi vào bản ghi tháng
   cuối quý, cờ la_phieu_tc_quy bật.
3. Ba tháng dùng chung một điểm — resolver trả cùng con số cho cả quý.
4. Chốt chặn — thao tác trên bản ghi không phải tháng neo bị từ chối.
5. Kỳ tháng hết hiệu lực — không lập mới báo cáo/phiếu tháng từ Q3/2026,
   nhưng bản ghi cũ vẫn đọc được.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import UUID

import pytest
from fastapi import HTTPException
from sqlalchemy import select, text

from app.api.v1.endpoints.danh_gia import (
    _chan_neu_khong_phai_thang_neo,
    kiem_tra_thoi_han_tu_danh_gia,
    tu_danh_gia_tieu_chi,
)
from app.api.v1.endpoints.xep_loai_quy_helpers import _lay_tc_chung_thang
from app.core import ky_tieu_chi as K
from app.db.session import AsyncSessionLocal
from app.models.kpi_assessment import DanhGiaThang
from app.models.user_org import CongChuc
from app.schemas.assessment import TuDanhGiaTieuChiRequest, TieuChiItemInput


# Quý III/2026 — kỳ đầu tiên áp dụng công văn. Tháng neo = 9.
QUY_TEST = 3
NAM_TEST = 2026
THANG_NEO_TEST = 9


# =============================================================================
# 1. Hàm thuần — mốc kỳ và tháng neo
# =============================================================================

def test_moc_ky_dung_theo_cong_van():
    """Q2/2026 trở về trước theo tháng; Q3/2026 trở đi theo quý."""
    assert K.TC_THEO_QUY_TU == (2026, 3)

    # Kỳ cũ — giữ nguyên hành vi tháng
    for thang in (1, 4, 5, 6):
        assert K.tc_theo_quy(thang, 2026) is False
        assert K.thang_neo(thang, 2026) == thang
        assert K.cac_thang_ap_dung(thang, 2026) == [thang]
        assert K.ky_thang_con_hieu_luc(thang, 2026) is True
    assert K.tc_theo_quy(12, 2025) is False

    # Kỳ mới — cả quý dùng chung một phiếu, neo ở tháng cuối quý
    for thang in (7, 8, 9):
        assert K.tc_theo_quy(thang, 2026) is True
        assert K.thang_neo(thang, 2026) == 9
        assert K.cac_thang_ap_dung(thang, 2026) == [7, 8, 9]
        assert K.nhan_ky(thang, 2026) == "Quý 3/2026"
        assert K.ky_thang_con_hieu_luc(thang, 2026) is False
    assert K.thang_neo(10, 2026) == 12
    assert K.thang_neo(1, 2027) == 3


def test_ky_da_bat_dau_cho_phep_thang_neo_tuong_lai():
    """Chấm Quý IV từ tháng 10 dù phiếu neo ở tháng 12; quý sau thì chưa."""
    hom_nay = date(2026, 10, 15)
    assert K.ky_da_bat_dau(12, 2026, hom_nay) is True   # quý IV đã bắt đầu
    assert K.ky_da_bat_dau(3, 2027, hom_nay) is False   # quý I/2027 chưa
    # Kỳ tháng giữ nguyên: tháng tương lai vẫn bị chặn
    assert K.ky_da_bat_dau(6, 2026, date(2026, 5, 20)) is False


def test_thoi_han_tu_danh_gia_theo_ky():
    """Tháng neo của quý hiện tại luôn mở; kỳ cũ giữ nguyên quy tắc."""
    hom_nay = date.today()
    thang_neo_hien_tai = K.thang_neo(hom_nay.month, hom_nay.year)
    assert kiem_tra_thoi_han_tu_danh_gia(thang_neo_hien_tai, hom_nay.year) is True
    # Quý của năm sau chưa bắt đầu → chặn
    assert kiem_tra_thoi_han_tu_danh_gia(3, hom_nay.year + 1) is False


# =============================================================================
# 2. KHÔNG HỒI TỐ — kỳ cũ đọc đúng bản ghi tháng đó (dữ liệu thật, chỉ đọc)
# =============================================================================

@pytest.mark.asyncio
async def test_khong_hoi_to_ky_cu():
    """
    Với mọi kỳ trước Q3/2026, `_lay_tc_chung_thang` phải trả về ĐÚNG điểm của
    chính tháng đó — không được nhảy sang tháng khác.

    Đo trên dữ liệu thật của DB test (chỉ đọc), 40 bản ghi mỗi tháng.
    """
    async with AsyncSessionLocal() as db:
        da_kiem_tra = 0
        for thang in (1, 4, 5, 6):
            rows = (await db.execute(text("""
                SELECT cong_chuc_id, diem_tieu_chi_chung
                FROM danh_gia_thang
                WHERE thang = :t AND nam = 2026 AND is_deleted = false
                  AND diem_tieu_chi_chung IS NOT NULL
                ORDER BY cong_chuc_id
                LIMIT 40
            """), {"t": thang})).all()
            assert rows, f"DB test không có dữ liệu tháng {thang}/2026 để đối chiếu"

            for cong_chuc_id, diem_goc in rows:
                diem_resolver = await _lay_tc_chung_thang(db, cong_chuc_id, thang, 2026)
                assert diem_resolver == diem_goc, (
                    f"Kỳ cũ bị lệch: CC {cong_chuc_id} tháng {thang}/2026 "
                    f"gốc {diem_goc} nhưng resolver trả {diem_resolver}"
                )
                da_kiem_tra += 1

        assert da_kiem_tra >= 100, "Mẫu đối chiếu quá nhỏ"


# =============================================================================
# Helpers cho các test ghi dữ liệu
# =============================================================================

async def _pick_cc_sach(db) -> CongChuc:
    """CC thường CHƯA có bản ghi đánh giá nào trong quý III/2026 (để test sạch)."""
    row = (await db.execute(text("""
        SELECT cc.id FROM cong_chuc cc
        JOIN vai_tro vt ON cc.vai_tro_id = vt.id
        WHERE vt.cap_bac = 'CONG_CHUC' AND cc.is_active = true AND cc.is_deleted = false
          AND cc.don_vi_id IS NOT NULL
          AND NOT EXISTS (
              SELECT 1 FROM danh_gia_thang dg
              WHERE dg.cong_chuc_id = cc.id AND dg.nam = 2026 AND dg.thang IN (7, 8, 9)
          )
        LIMIT 1
    """))).first()
    assert row, "Không tìm thấy công chức chưa có dữ liệu quý III/2026 trong DB test"
    return (await db.execute(select(CongChuc).where(CongChuc.id == row[0]))).scalar_one()


async def _cleanup_quy(db, cong_chuc_id: UUID) -> None:
    await db.execute(text("""
        DELETE FROM tieu_chi_chung_danh_gia WHERE danh_gia_thang_id IN (
            SELECT id FROM danh_gia_thang
            WHERE cong_chuc_id = :cc AND nam = :n AND thang IN (7, 8, 9))
    """), {"cc": str(cong_chuc_id), "n": NAM_TEST})
    await db.execute(text("""
        DELETE FROM danh_gia_thang
        WHERE cong_chuc_id = :cc AND nam = :n AND thang IN (7, 8, 9)
    """), {"cc": str(cong_chuc_id), "n": NAM_TEST})
    await db.commit()


def _payload_tu_cham(thang: int) -> TuDanhGiaTieuChiRequest:
    """Bộ 10 tiêu chí: nhóm I và II đạt tối đa, nhóm III để 0 → tổng 20 điểm."""
    diem = {
        "1.1": 5.0, "1.2": 5.0,
        "2.1": 2.5, "2.2": 2.5, "2.3": 2.5, "2.4": 2.5,
        "3.1": 0.0, "3.2": 0.0, "3.3": 0.0, "3.4": 0.0,
    }
    return TuDanhGiaTieuChiRequest(
        thang=thang,
        nam=NAM_TEST,
        gui_phe_duyet=False,
        tieu_chi=[
            TieuChiItemInput(ma_tieu_chi=ma, diem_tu_cham=d, is_achieved_cc=d > 0)
            for ma, d in diem.items()
        ],
    )


# =============================================================================
# 3. Neo đúng chỗ + ba tháng dùng chung một điểm
# =============================================================================

@pytest.mark.asyncio
async def test_tu_cham_thang_bat_ky_trong_quy_ghi_vao_thang_neo():
    """Gửi tháng 7 → phiếu nằm ở bản ghi tháng 9, cờ la_phieu_tc_quy bật."""
    async with AsyncSessionLocal() as db:
        cc = await _pick_cc_sach(db)
        await _cleanup_quy(db, cc.id)
        try:
            await tu_danh_gia_tieu_chi(db, cc, _payload_tu_cham(thang=7))
            await db.commit()

            rows = (await db.execute(
                select(DanhGiaThang)
                .where(DanhGiaThang.cong_chuc_id == cc.id)
                .where(DanhGiaThang.nam == NAM_TEST)
                .where(DanhGiaThang.thang.in_([7, 8, 9]))
            )).scalars().all()

            assert len(rows) == 1, "Phải chỉ tạo đúng MỘT bản ghi cho cả quý"
            dg = rows[0]
            assert dg.thang == THANG_NEO_TEST, "Phiếu phải neo ở tháng cuối quý"
            assert dg.la_phieu_tc_quy is True
            assert len(dg.tieu_chi_chungs) == 10
        finally:
            await _cleanup_quy(db, cc.id)


@pytest.mark.asyncio
async def test_ba_thang_trong_quy_dung_chung_mot_diem():
    """Sau khi phiếu quý có điểm, cả T7, T8, T9 đọc ra cùng một con số."""
    async with AsyncSessionLocal() as db:
        cc = await _pick_cc_sach(db)
        await _cleanup_quy(db, cc.id)
        try:
            await tu_danh_gia_tieu_chi(db, cc, _payload_tu_cham(thang=8))
            dg = (await db.execute(
                select(DanhGiaThang)
                .where(DanhGiaThang.cong_chuc_id == cc.id)
                .where(DanhGiaThang.nam == NAM_TEST)
                .where(DanhGiaThang.thang == THANG_NEO_TEST)
            )).scalar_one()
            # Giả lập trưởng đơn vị duyệt xong: chốt điểm quý
            dg.diem_tieu_chi_chung = Decimal("23.50")
            await db.commit()

            diem = [await _lay_tc_chung_thang(db, cc.id, t, NAM_TEST) for t in (7, 8, 9)]
            assert diem == [Decimal("23.50")] * 3, f"Ba tháng lệch nhau: {diem}"

            # Trung bình quý (mục 5 của tinh_diem_quy) bằng chính điểm quý
            assert sum(diem) / 3 == Decimal("23.50")
        finally:
            await _cleanup_quy(db, cc.id)


# =============================================================================
# 4. Chốt chặn — không thao tác trên bản ghi khác tháng neo
# =============================================================================

@pytest.mark.asyncio
async def test_chan_thao_tac_tren_thang_khong_phai_neo():
    """Bản ghi T7/2026 (kỳ quý) bị chặn; bản ghi T9 và kỳ cũ thì không."""
    async with AsyncSessionLocal() as db:
        cc = await _pick_cc_sach(db)

        dg_t7 = DanhGiaThang(cong_chuc_id=cc.id, thang=7, nam=NAM_TEST)
        with pytest.raises(HTTPException) as exc:
            _chan_neu_khong_phai_thang_neo(dg_t7)
        assert exc.value.status_code == 400
        assert "quý" in str(exc.value.detail).lower()

        # Tháng neo → không chặn
        _chan_neu_khong_phai_thang_neo(
            DanhGiaThang(cong_chuc_id=cc.id, thang=9, nam=NAM_TEST)
        )
        # Kỳ cũ → không chặn (mọi tháng đều tự chấm như trước)
        _chan_neu_khong_phai_thang_neo(
            DanhGiaThang(cong_chuc_id=cc.id, thang=5, nam=2026)
        )


# =============================================================================
# 5. Kỳ tháng hết hiệu lực từ Q3/2026
# =============================================================================

@pytest.mark.asyncio
async def test_khong_lap_moi_bao_cao_xep_loai_thang():
    """Báo cáo xếp loại tháng 7/2026 chưa có → từ chối tạo mới, kèm hướng dẫn."""
    from app.api.v1.endpoints.bao_cao_xep_loai import get_bao_cao_don_vi

    async with AsyncSessionLocal() as db:
        # Tìm một cặp (Trưởng đơn vị, tháng thuộc kỳ quý) CHƯA có báo cáo tháng
        row = (await db.execute(text("""
            SELECT cc.id, t.thang
            FROM cong_chuc cc
            JOIN vai_tro vt ON cc.vai_tro_id = vt.id
            CROSS JOIN generate_series(7, 12) AS t(thang)
            WHERE vt.cap_bac = 'TRUONG_DON_VI' AND cc.is_active = true
              AND cc.is_deleted = false AND cc.don_vi_id IS NOT NULL
              AND NOT EXISTS (
                  SELECT 1 FROM bao_cao_xep_loai bc
                  WHERE bc.don_vi_id = cc.don_vi_id AND bc.thang = t.thang
                    AND bc.nam = 2026 AND bc.is_deleted = false)
            LIMIT 1
        """))).first()
        assert row, "DB test không còn tháng nào của kỳ quý để thử tạo báo cáo mới"

        tdv = (await db.execute(select(CongChuc).where(CongChuc.id == row[0]))).scalar_one()
        with pytest.raises(HTTPException) as exc:
            await get_bao_cao_don_vi(db, tdv, row[1], 2026)
        assert exc.value.status_code == 400
        assert "QUÝ" in str(exc.value.detail)
        await db.rollback()


@pytest.mark.asyncio
async def test_van_doc_duoc_bao_cao_thang_cu():
    """Báo cáo tháng đã tồn tại (kỳ cũ) vẫn mở được bình thường."""
    from app.api.v1.endpoints.bao_cao_xep_loai import get_bao_cao_don_vi

    async with AsyncSessionLocal() as db:
        row = (await db.execute(text("""
            SELECT cc.id, bc.thang FROM bao_cao_xep_loai bc
            JOIN cong_chuc cc ON cc.don_vi_id = bc.don_vi_id
            JOIN vai_tro vt ON cc.vai_tro_id = vt.id
            WHERE bc.nam = 2026 AND bc.thang <= 6 AND bc.is_deleted = false
              AND vt.cap_bac = 'TRUONG_DON_VI' AND cc.is_active = true
            LIMIT 1
        """))).first()
        if not row:
            pytest.skip("DB test không có báo cáo tháng cũ để đối chiếu")

        tdv = (await db.execute(select(CongChuc).where(CongChuc.id == row[0]))).scalar_one()
        res = await get_bao_cao_don_vi(db, tdv, row[1], 2026)
        assert res["success"] is True
        await db.rollback()


@pytest.mark.asyncio
async def test_khong_tao_moi_phieu_danh_gia_thang():
    """Phiếu cá nhân tháng 8/2026 → từ chối, hướng sang Mẫu 02A/02B quý."""
    from app.api.v1.endpoints.phieu_danh_gia_thang import upsert_phieu_nhap
    from app.schemas.phieu_danh_gia import UpsertPhieuThangRequest

    async with AsyncSessionLocal() as db:
        cc = await _pick_cc_sach(db)
        payload = UpsertPhieuThangRequest(
            thang=8, nam=2026, uu_diem="test", han_che="test"
        )
        with pytest.raises(HTTPException) as exc:
            await upsert_phieu_nhap(payload, db, cc)
        assert exc.value.status_code == 400
        assert "QUÝ" in str(exc.value.detail)
        await db.rollback()
