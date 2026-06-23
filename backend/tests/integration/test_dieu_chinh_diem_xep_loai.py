"""
tests/integration/test_dieu_chinh_diem_xep_loai.py
===================================================
Integration tests cho tính năng lãnh đạo sửa điểm tổng trong báo cáo xếp loại.

Pattern: gọi trực tiếp endpoint function (bỏ qua HTTP/auth wiring) trên DB test,
mỗi test tự tạo báo cáo và cleanup. Chạy trên kpi_haiquan_test:

    DB_NAME=kpi_haiquan_test pytest tests/integration/test_dieu_chinh_diem_xep_loai.py -v

Scope:
- Sửa điểm hợp lệ → diem_tong_dieu_chinh lưu đúng, diem_tong hệ thống KHÔNG đổi.
- Thiếu lý do khi đặt điểm → HTTPException 400.
- Điểm ngoài [0,100] → ValidationError ở schema.
- diem_tong=None → gỡ điều chỉnh.
- Không phải TDV/CCT → HTTPException 403.
- Override tồn tại qua cap_nhat_chi_tiet_tu_du_lieu (tính lại điểm).
"""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID

import pytest
from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import select, text
from sqlalchemy.orm import selectinload

from app.api.v1.endpoints.bao_cao_xep_loai import (
    tao_bao_cao_xep_loai,
    cap_nhat_chi_tiet_tu_du_lieu,
    dieu_chinh_diem,
)
from app.db.session import AsyncSessionLocal
from app.models.bao_cao_xep_loai import BaoCaoXepLoai, ChiTietXepLoai
from app.models.user_org import CongChuc
from app.schemas.bao_cao_xep_loai import DieuChinhDiemRequest


# Tháng/năm test chọn xa data thực để cleanup an toàn
TEST_THANG = 12
TEST_NAM = 2099


# =============================================================================
# Helpers
# =============================================================================

async def _pick_tdv(db) -> CongChuc:
    """Lấy 1 Trưởng đơn vị (có vai_tro loaded) thuộc đơn vị có CC."""
    row = (await db.execute(text("""
        SELECT cc.id
        FROM cong_chuc cc
        JOIN vai_tro vt ON cc.vai_tro_id = vt.id
        WHERE vt.cap_bac = 'TRUONG_DON_VI'
          AND cc.is_active = true AND cc.is_deleted = false
          AND cc.don_vi_id IS NOT NULL
        LIMIT 1
    """))).first()
    assert row, "Không tìm thấy Trưởng đơn vị test"
    return (await db.execute(
        select(CongChuc).options(selectinload(CongChuc.vai_tro)).where(CongChuc.id == row[0])
    )).scalar_one()


async def _pick_cong_chuc(db) -> CongChuc:
    """Lấy 1 CC thường (không phải lãnh đạo) — dùng test quyền 403."""
    row = (await db.execute(text("""
        SELECT cc.id
        FROM cong_chuc cc
        JOIN vai_tro vt ON cc.vai_tro_id = vt.id
        WHERE vt.cap_bac = 'CONG_CHUC'
          AND cc.is_active = true AND cc.is_deleted = false
        LIMIT 1
    """))).first()
    assert row, "Không tìm thấy CC thường test"
    return (await db.execute(
        select(CongChuc).options(selectinload(CongChuc.vai_tro)).where(CongChuc.id == row[0])
    )).scalar_one()


async def _cleanup_bao_cao(db, don_vi_id: UUID) -> None:
    """Xóa báo cáo test (+ chi tiết) của đơn vị cho tháng/năm test."""
    await db.execute(text("""
        DELETE FROM chi_tiet_xep_loai
        WHERE bao_cao_id IN (
            SELECT id FROM bao_cao_xep_loai
            WHERE don_vi_id = :dv AND thang = :thang AND nam = :nam
        )
    """), {"dv": str(don_vi_id), "thang": TEST_THANG, "nam": TEST_NAM})
    await db.execute(text("""
        DELETE FROM bao_cao_xep_loai
        WHERE don_vi_id = :dv AND thang = :thang AND nam = :nam
    """), {"dv": str(don_vi_id), "thang": TEST_THANG, "nam": TEST_NAM})
    await db.commit()


async def _reload_ct(db, ct_id: UUID) -> ChiTietXepLoai:
    return (await db.execute(
        select(ChiTietXepLoai).where(ChiTietXepLoai.id == ct_id)
    )).scalar_one()


# =============================================================================
# Tests
# =============================================================================

@pytest.mark.asyncio
async def test_sua_diem_hop_le_giu_nguyen_diem_he_thong():
    """Sửa điểm hợp lệ → override lưu đúng, diem_tong hệ thống không đổi."""
    async with AsyncSessionLocal() as db:
        tdv = await _pick_tdv(db)
        await _cleanup_bao_cao(db, tdv.don_vi_id)
        bao_cao = await tao_bao_cao_xep_loai(db, tdv.don_vi_id, TEST_THANG, TEST_NAM, tdv.id)
        await db.commit()

        ct = (await db.execute(
            select(ChiTietXepLoai).where(ChiTietXepLoai.bao_cao_id == bao_cao.id).limit(1)
        )).scalar_one()
        diem_he_thong_truoc = ct.diem_tong

        await dieu_chinh_diem(
            db, tdv, ct.id,
            DieuChinhDiemRequest(diem_tong=Decimal("88.5"), ly_do_dieu_chinh_diem="Bổ sung thành tích"),
        )

        ct2 = await _reload_ct(db, ct.id)
        assert ct2.diem_tong_dieu_chinh == Decimal("88.50")
        assert ct2.ly_do_dieu_chinh_diem == "Bổ sung thành tích"
        assert ct2.diem_tong == diem_he_thong_truoc  # điểm hệ thống KHÔNG đổi

        await _cleanup_bao_cao(db, tdv.don_vi_id)


@pytest.mark.asyncio
async def test_thieu_ly_do_khi_dat_diem_bao_400():
    async with AsyncSessionLocal() as db:
        tdv = await _pick_tdv(db)
        await _cleanup_bao_cao(db, tdv.don_vi_id)
        bao_cao = await tao_bao_cao_xep_loai(db, tdv.don_vi_id, TEST_THANG, TEST_NAM, tdv.id)
        await db.commit()
        ct = (await db.execute(
            select(ChiTietXepLoai).where(ChiTietXepLoai.bao_cao_id == bao_cao.id).limit(1)
        )).scalar_one()

        with pytest.raises(HTTPException) as exc:
            await dieu_chinh_diem(
                db, tdv, ct.id,
                DieuChinhDiemRequest(diem_tong=Decimal("70"), ly_do_dieu_chinh_diem="   "),
            )
        assert exc.value.status_code == 400

        await _cleanup_bao_cao(db, tdv.don_vi_id)


@pytest.mark.asyncio
async def test_diem_ngoai_khoang_bao_validation_error():
    """diem_tong > 100 → Pydantic ValidationError ngay khi tạo request."""
    with pytest.raises(ValidationError):
        DieuChinhDiemRequest(diem_tong=Decimal("150"), ly_do_dieu_chinh_diem="x")
    with pytest.raises(ValidationError):
        DieuChinhDiemRequest(diem_tong=Decimal("-1"), ly_do_dieu_chinh_diem="x")


@pytest.mark.asyncio
async def test_diem_none_go_dieu_chinh():
    """diem_tong=None → gỡ điều chỉnh, về điểm hệ thống."""
    async with AsyncSessionLocal() as db:
        tdv = await _pick_tdv(db)
        await _cleanup_bao_cao(db, tdv.don_vi_id)
        bao_cao = await tao_bao_cao_xep_loai(db, tdv.don_vi_id, TEST_THANG, TEST_NAM, tdv.id)
        await db.commit()
        ct = (await db.execute(
            select(ChiTietXepLoai).where(ChiTietXepLoai.bao_cao_id == bao_cao.id).limit(1)
        )).scalar_one()

        # Đặt điểm trước
        await dieu_chinh_diem(
            db, tdv, ct.id,
            DieuChinhDiemRequest(diem_tong=Decimal("60"), ly_do_dieu_chinh_diem="tạm"),
        )
        # Gỡ điều chỉnh
        await dieu_chinh_diem(db, tdv, ct.id, DieuChinhDiemRequest(diem_tong=None))

        ct2 = await _reload_ct(db, ct.id)
        assert ct2.diem_tong_dieu_chinh is None
        assert ct2.ly_do_dieu_chinh_diem is None

        await _cleanup_bao_cao(db, tdv.don_vi_id)


@pytest.mark.asyncio
async def test_cong_chuc_thuong_khong_co_quyen():
    async with AsyncSessionLocal() as db:
        tdv = await _pick_tdv(db)
        cc_thuong = await _pick_cong_chuc(db)
        await _cleanup_bao_cao(db, tdv.don_vi_id)
        bao_cao = await tao_bao_cao_xep_loai(db, tdv.don_vi_id, TEST_THANG, TEST_NAM, tdv.id)
        await db.commit()
        ct = (await db.execute(
            select(ChiTietXepLoai).where(ChiTietXepLoai.bao_cao_id == bao_cao.id).limit(1)
        )).scalar_one()

        with pytest.raises(HTTPException) as exc:
            await dieu_chinh_diem(
                db, cc_thuong, ct.id,
                DieuChinhDiemRequest(diem_tong=Decimal("80"), ly_do_dieu_chinh_diem="x"),
            )
        assert exc.value.status_code == 403

        await _cleanup_bao_cao(db, tdv.don_vi_id)


@pytest.mark.asyncio
async def test_override_ton_tai_qua_tinh_lai_diem():
    """Cốt lõi: cap_nhat_chi_tiet_tu_du_lieu tính lại diem_tong nhưng GIỮ override."""
    async with AsyncSessionLocal() as db:
        tdv = await _pick_tdv(db)
        await _cleanup_bao_cao(db, tdv.don_vi_id)
        bao_cao = await tao_bao_cao_xep_loai(db, tdv.don_vi_id, TEST_THANG, TEST_NAM, tdv.id)
        await db.commit()
        ct = (await db.execute(
            select(ChiTietXepLoai).where(ChiTietXepLoai.bao_cao_id == bao_cao.id).limit(1)
        )).scalar_one()

        await dieu_chinh_diem(
            db, tdv, ct.id,
            DieuChinhDiemRequest(diem_tong=Decimal("95"), ly_do_dieu_chinh_diem="giữ qua recalc"),
        )
        await db.flush()

        # Tính lại điểm toàn báo cáo
        await cap_nhat_chi_tiet_tu_du_lieu(db, bao_cao, tdv)

        ct2 = await _reload_ct(db, ct.id)
        assert ct2.diem_tong_dieu_chinh == Decimal("95.00")  # override còn nguyên
        assert ct2.ly_do_dieu_chinh_diem == "giữ qua recalc"

        await _cleanup_bao_cao(db, tdv.don_vi_id)
