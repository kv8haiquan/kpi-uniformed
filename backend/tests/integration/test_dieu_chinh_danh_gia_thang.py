"""
tests/integration/test_dieu_chinh_danh_gia_thang.py
====================================================
Integration tests cho tính năng lãnh đạo chỉnh điểm 'Đánh giá tháng' của tiêu chí
chung ở giai đoạn báo cáo xếp loại.

Chạy trên kpi_haiquan_test:
    DB_NAME=kpi_haiquan_test pytest tests/integration/test_dieu_chinh_danh_gia_thang.py -v

Pattern: gọi trực tiếp endpoint function, tự tạo danh_gia_thang + 2 dòng tiêu chí cho
tháng test (12/2099 — không đụng dữ liệu thật), cleanup sau mỗi test.

Scope:
- Sửa 1 tiêu chí → diem_danh_gia_thang lưu đúng, diem_phe_duyet (Trưởng duyệt) KHÔNG đổi.
- danh_gia_thang.diem_tieu_chi_chung = tổng COALESCE(diem_danh_gia_thang, diem_phe_duyet, diem_tu_cham).
- Gửi null 1 dòng → về Trưởng duyệt.
- Điểm vượt mức tối đa → ValidationError ở schema.
- Không phải lãnh đạo đúng đơn vị → 403.
- Báo cáo DA_PHE_DUYET → 400.
"""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID

import pytest
from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import select, text
from sqlalchemy.orm import selectinload

from app.api.v1.endpoints.danh_gia import dieu_chinh_danh_gia_thang
from app.db.session import AsyncSessionLocal
from app.models.bao_cao_xep_loai import BaoCaoXepLoai, TrangThaiBaoCao
from app.models.kpi_assessment import DanhGiaThang, TieuChiChung, TieuChiChungDanhGia
from app.models.user_org import CongChuc
from app.schemas.assessment import DieuChinhDanhGiaThangRequest, DanhGiaThangItem


TEST_THANG = 12
TEST_NAM = 2099


# =============================================================================
# Helpers
# =============================================================================

async def _pick_tdv(db) -> CongChuc:
    row = (await db.execute(text("""
        SELECT cc.id FROM cong_chuc cc JOIN vai_tro vt ON cc.vai_tro_id = vt.id
        WHERE vt.cap_bac = 'TRUONG_DON_VI' AND cc.is_active = true
          AND cc.is_deleted = false AND cc.don_vi_id IS NOT NULL LIMIT 1
    """))).first()
    assert row, "Không tìm thấy Trưởng đơn vị test"
    return (await db.execute(
        select(CongChuc).options(selectinload(CongChuc.vai_tro)).where(CongChuc.id == row[0])
    )).scalar_one()


async def _pick_cc_khac_don_vi(db, don_vi_id: UUID) -> CongChuc:
    row = (await db.execute(text("""
        SELECT cc.id FROM cong_chuc cc JOIN vai_tro vt ON cc.vai_tro_id = vt.id
        WHERE vt.cap_bac = 'CONG_CHUC' AND cc.is_active = true AND cc.is_deleted = false
          AND cc.don_vi_id != :dv LIMIT 1
    """), {"dv": str(don_vi_id)})).first()
    assert row, "Không tìm thấy CC thường khác đơn vị"
    return (await db.execute(
        select(CongChuc).options(selectinload(CongChuc.vai_tro)).where(CongChuc.id == row[0])
    )).scalar_one()


async def _cleanup(db, cong_chuc_id: UUID, don_vi_id: UUID) -> None:
    await db.execute(text("""
        DELETE FROM tieu_chi_chung_danh_gia WHERE danh_gia_thang_id IN (
            SELECT id FROM danh_gia_thang WHERE cong_chuc_id = :cc AND thang = :t AND nam = :n)
    """), {"cc": str(cong_chuc_id), "t": TEST_THANG, "n": TEST_NAM})
    await db.execute(text("""
        DELETE FROM danh_gia_thang WHERE cong_chuc_id = :cc AND thang = :t AND nam = :n
    """), {"cc": str(cong_chuc_id), "t": TEST_THANG, "n": TEST_NAM})
    await db.execute(text("""
        DELETE FROM chi_tiet_xep_loai WHERE bao_cao_id IN (
            SELECT id FROM bao_cao_xep_loai WHERE don_vi_id = :dv AND thang = :t AND nam = :n)
    """), {"dv": str(don_vi_id), "t": TEST_THANG, "n": TEST_NAM})
    await db.execute(text("""
        DELETE FROM bao_cao_xep_loai WHERE don_vi_id = :dv AND thang = :t AND nam = :n
    """), {"dv": str(don_vi_id), "t": TEST_THANG, "n": TEST_NAM})
    await db.commit()


async def _setup_danh_gia(db, cong_chuc_id: UUID) -> tuple[DanhGiaThang, dict]:
    """Tạo danh_gia_thang + 2 dòng tiêu chí. Trả (danh_gia, {ma: diem_phe_duyet})."""
    masters = (await db.execute(
        select(TieuChiChung).where(TieuChiChung.ma_tieu_chi.in_(["1.1", "2.1"]))
    )).scalars().all()
    masters = {m.ma_tieu_chi: m for m in masters}
    assert "1.1" in masters and "2.1" in masters, "Thiếu tiêu chí master 1.1/2.1"

    dg = DanhGiaThang(cong_chuc_id=cong_chuc_id, thang=TEST_THANG, nam=TEST_NAM,
                      diem_tieu_chi_chung=Decimal("0"))
    db.add(dg)
    await db.flush()

    # 1.1: CC 5.0, Trưởng duyệt 4.0 ; 2.1: CC 2.5, Trưởng duyệt 2.0
    pd = {"1.1": Decimal("4.0"), "2.1": Decimal("2.0")}
    tc_cham = {"1.1": Decimal("5.0"), "2.1": Decimal("2.5")}
    for ma in ("1.1", "2.1"):
        db.add(TieuChiChungDanhGia(
            danh_gia_thang_id=dg.id, tieu_chi_id=masters[ma].id,
            is_achieved_cc=True, diem_tu_cham=tc_cham[ma], diem_phe_duyet=pd[ma],
        ))
    dg.diem_tieu_chi_chung = pd["1.1"] + pd["2.1"]  # 6.0 (theo Trưởng duyệt)
    await db.commit()
    return dg, pd


# =============================================================================
# Tests
# =============================================================================

@pytest.mark.asyncio
async def test_sua_diem_giu_nguyen_truong_duyet():
    async with AsyncSessionLocal() as db:
        tdv = await _pick_tdv(db)
        await _cleanup(db, tdv.id, tdv.don_vi_id)
        dg, pd = await _setup_danh_gia(db, tdv.id)

        # Sửa 1.1 từ 4.0 (Trưởng duyệt) → 4.5
        await dieu_chinh_danh_gia_thang(
            dg.id,
            DieuChinhDanhGiaThangRequest(tieu_chi=[
                DanhGiaThangItem(ma_tieu_chi="1.1", diem_danh_gia_thang=4.5),
            ]),
            db, tdv,
        )

        rows = (await db.execute(
            select(TieuChiChungDanhGia)
            .options(selectinload(TieuChiChungDanhGia.tieu_chi))
            .where(TieuChiChungDanhGia.danh_gia_thang_id == dg.id)
        )).scalars().all()
        by_ma = {r.tieu_chi.ma_tieu_chi: r for r in rows}
        assert by_ma["1.1"].diem_danh_gia_thang == Decimal("4.50")
        assert by_ma["1.1"].diem_phe_duyet == pd["1.1"]  # Trưởng duyệt KHÔNG đổi
        assert by_ma["2.1"].diem_danh_gia_thang is None

        dg2 = (await db.execute(select(DanhGiaThang).where(DanhGiaThang.id == dg.id))).scalar_one()
        # tổng = 4.5 (đánh giá tháng 1.1) + 2.0 (Trưởng duyệt 2.1) = 6.5
        assert dg2.diem_tieu_chi_chung == Decimal("6.50")

        await _cleanup(db, tdv.id, tdv.don_vi_id)


@pytest.mark.asyncio
async def test_null_go_dieu_chinh():
    async with AsyncSessionLocal() as db:
        tdv = await _pick_tdv(db)
        await _cleanup(db, tdv.id, tdv.don_vi_id)
        dg, pd = await _setup_danh_gia(db, tdv.id)

        await dieu_chinh_danh_gia_thang(
            dg.id, DieuChinhDanhGiaThangRequest(tieu_chi=[
                DanhGiaThangItem(ma_tieu_chi="1.1", diem_danh_gia_thang=5.0)]), db, tdv)
        await dieu_chinh_danh_gia_thang(
            dg.id, DieuChinhDanhGiaThangRequest(tieu_chi=[
                DanhGiaThangItem(ma_tieu_chi="1.1", diem_danh_gia_thang=None)]), db, tdv)

        row = (await db.execute(
            select(TieuChiChungDanhGia).options(selectinload(TieuChiChungDanhGia.tieu_chi))
            .where(TieuChiChungDanhGia.danh_gia_thang_id == dg.id)
        )).scalars().all()
        by_ma = {r.tieu_chi.ma_tieu_chi: r for r in row}
        assert by_ma["1.1"].diem_danh_gia_thang is None
        dg2 = (await db.execute(select(DanhGiaThang).where(DanhGiaThang.id == dg.id))).scalar_one()
        assert dg2.diem_tieu_chi_chung == pd["1.1"] + pd["2.1"]  # về tổng Trưởng duyệt 6.0

        await _cleanup(db, tdv.id, tdv.don_vi_id)


@pytest.mark.asyncio
async def test_diem_vuot_toi_da_validation_error():
    # 1.1 tối đa 5.0 → 6.0 phải lỗi ngay ở schema
    with pytest.raises(ValidationError):
        DanhGiaThangItem(ma_tieu_chi="1.1", diem_danh_gia_thang=6.0)
    # bội 0.5
    with pytest.raises(ValidationError):
        DanhGiaThangItem(ma_tieu_chi="1.1", diem_danh_gia_thang=1.3)


@pytest.mark.asyncio
async def test_khong_dung_don_vi_bao_403():
    async with AsyncSessionLocal() as db:
        tdv = await _pick_tdv(db)
        cc_khac = await _pick_cc_khac_don_vi(db, tdv.don_vi_id)
        await _cleanup(db, tdv.id, tdv.don_vi_id)
        dg, _ = await _setup_danh_gia(db, tdv.id)

        with pytest.raises(HTTPException) as exc:
            await dieu_chinh_danh_gia_thang(
                dg.id, DieuChinhDanhGiaThangRequest(tieu_chi=[
                    DanhGiaThangItem(ma_tieu_chi="1.1", diem_danh_gia_thang=4.5)]), db, cc_khac)
        assert exc.value.status_code == 403

        await _cleanup(db, tdv.id, tdv.don_vi_id)


@pytest.mark.asyncio
async def test_bao_cao_da_phe_duyet_bao_400():
    async with AsyncSessionLocal() as db:
        tdv = await _pick_tdv(db)
        await _cleanup(db, tdv.id, tdv.don_vi_id)
        dg, _ = await _setup_danh_gia(db, tdv.id)

        # Tạo báo cáo DA_PHE_DUYET cho đơn vị/tháng test
        db.add(BaoCaoXepLoai(
            don_vi_id=tdv.don_vi_id, thang=TEST_THANG, nam=TEST_NAM,
            nguoi_lap_id=tdv.id, trang_thai=TrangThaiBaoCao.DA_PHE_DUYET.value,
            tong_cong_chuc=0,
        ))
        await db.commit()

        with pytest.raises(HTTPException) as exc:
            await dieu_chinh_danh_gia_thang(
                dg.id, DieuChinhDanhGiaThangRequest(tieu_chi=[
                    DanhGiaThangItem(ma_tieu_chi="1.1", diem_danh_gia_thang=4.5)]), db, tdv)
        assert exc.value.status_code == 400

        await _cleanup(db, tdv.id, tdv.don_vi_id)
