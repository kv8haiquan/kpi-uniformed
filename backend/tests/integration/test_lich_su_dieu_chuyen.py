"""
tests/integration/test_lich_su_dieu_chuyen.py
=============================================
Integration tests cho:
- Vô hiệu hóa/kích hoạt có NGÀY HIỆU LỰC → ghi bản ghi trạng thái vào
  lich_su_dieu_chuyen (loai VO_HIEU_HOA / KICH_HOAT).
- Điều chỉnh lịch sử (sửa/xóa) có tùy chọn đồng bộ hồ sơ hiện tại.
- Biểu thức báo cáo _active_tai_thang_expr tôn trọng ngày hiệu lực.
- Heuristic _don_vi_tai_thang_expr KHÔNG bị bản ghi trạng thái làm lệch.

Chạy trên kpi_haiquan_test:
    DB_NAME=kpi_haiquan_test pytest tests/integration/test_lich_su_dieu_chuyen.py -v

Pattern: gọi trực tiếp endpoint function, tự tạo/dọn dữ liệu, dùng tháng test
xa (2099) để không đụng dữ liệu thật. Mỗi test snapshot + khôi phục hồ sơ CC.
"""
from __future__ import annotations

from datetime import date
from uuid import UUID

import pytest
from fastapi import HTTPException
from sqlalchemy import select, text
from sqlalchemy.orm import selectinload

from app.api.v1.endpoints.admin import (
    update_user_status,
    update_transfer_history,
    delete_transfer_history,
)
import app.api.v1.endpoints.bao_cao_xep_loai as bc
from app.db.session import AsyncSessionLocal
from app.models.admin import LichSuDieuChuyen
from app.models.user_org import CongChuc, DonVi
from app.schemas.admin import UserStatusRequest, LichSuDieuChuyenUpdateRequest


# =============================================================================
# Helpers
# =============================================================================

async def _pick_cc(db) -> CongChuc:
    """Một công chức thường, active, có đơn vị — làm đối tượng test."""
    row = (await db.execute(text("""
        SELECT cc.id FROM cong_chuc cc JOIN vai_tro vt ON cc.vai_tro_id = vt.id
        WHERE vt.cap_bac = 'CONG_CHUC' AND cc.is_active = true AND cc.is_deleted = false
          AND cc.don_vi_id IS NOT NULL AND cc.ma_cc <> 'ADMIN-001' LIMIT 1
    """))).first()
    assert row, "Không tìm thấy công chức test"
    return (await db.execute(
        select(CongChuc).options(selectinload(CongChuc.don_vi), selectinload(CongChuc.vai_tro))
        .where(CongChuc.id == row[0])
    )).scalar_one()


async def _pick_admin(db, tru_id: UUID) -> CongChuc:
    row = (await db.execute(text("""
        SELECT id FROM cong_chuc WHERE is_active = true AND is_deleted = false
          AND id <> :x LIMIT 1
    """), {"x": str(tru_id)})).first()
    return (await db.execute(select(CongChuc).where(CongChuc.id == row[0]))).scalar_one()


async def _don_vi_khac(db, don_vi_id: UUID) -> DonVi:
    row = (await db.execute(text("""
        SELECT id FROM don_vi WHERE is_deleted = false AND id <> :dv LIMIT 1
    """), {"dv": str(don_vi_id)})).first()
    return (await db.execute(select(DonVi).where(DonVi.id == row[0]))).scalar_one()


def _snapshot(cc: CongChuc) -> dict:
    return {"don_vi_id": cc.don_vi_id, "vai_tro_id": cc.vai_tro_id,
            "chuc_vu": cc.chuc_vu, "is_active": cc.is_active}


async def _restore(db, cc_id: UUID, snap: dict) -> None:
    await db.execute(text("""
        UPDATE cong_chuc SET don_vi_id=:dv, vai_tro_id=:vt, chuc_vu=:cv, is_active=:act
        WHERE id=:id
    """), {"dv": str(snap["don_vi_id"]), "vt": str(snap["vai_tro_id"]),
           "cv": snap["chuc_vu"], "act": snap["is_active"], "id": str(cc_id)})
    await db.execute(text("DELETE FROM lich_su_dieu_chuyen WHERE cong_chuc_id = :cc"),
                     {"cc": str(cc_id)})
    await db.commit()


# =============================================================================
# 1. Vô hiệu hóa / kích hoạt có ngày hiệu lực → ghi lịch sử trạng thái
# =============================================================================

@pytest.mark.asyncio
async def test_vo_hieu_hoa_ghi_lich_su_co_ngay_hieu_luc():
    async with AsyncSessionLocal() as db:
        cc = await _pick_cc(db)
        admin = await _pick_admin(db, cc.id)
        snap = _snapshot(cc)
        await db.execute(text("DELETE FROM lich_su_dieu_chuyen WHERE cong_chuc_id=:c"), {"c": str(cc.id)})
        await db.commit()
        try:
            await update_user_status(
                cc.id, UserStatusRequest(is_active=False, ngay_hieu_luc=date(2099, 5, 15),
                                         ly_do="Nghỉ hưu test"),
                db, admin)
            await db.commit()

            rows = (await db.execute(select(LichSuDieuChuyen)
                    .where(LichSuDieuChuyen.cong_chuc_id == cc.id))).scalars().all()
            assert len(rows) == 1
            assert rows[0].loai == "VO_HIEU_HOA"
            assert rows[0].ngay_hieu_luc == date(2099, 5, 15)
            assert rows[0].don_vi_cu_id == snap["don_vi_id"]  # trạng thái không đổi đơn vị

            cc2 = (await db.execute(select(CongChuc).where(CongChuc.id == cc.id))).scalar_one()
            assert cc2.is_active is False

            # Kích hoạt lại → bản ghi KICH_HOAT
            await update_user_status(
                cc.id, UserStatusRequest(is_active=True, ngay_hieu_luc=date(2099, 6, 1)),
                db, admin)
            await db.commit()
            rows = (await db.execute(select(LichSuDieuChuyen)
                    .where(LichSuDieuChuyen.cong_chuc_id == cc.id)
                    .order_by(LichSuDieuChuyen.created_at))).scalars().all()
            assert [r.loai for r in rows] == ["VO_HIEU_HOA", "KICH_HOAT"]
        finally:
            await _restore(db, cc.id, snap)


@pytest.mark.asyncio
async def test_trang_thai_khong_doi_thi_khong_ghi_lich_su():
    async with AsyncSessionLocal() as db:
        cc = await _pick_cc(db)  # đang active
        admin = await _pick_admin(db, cc.id)
        snap = _snapshot(cc)
        await db.execute(text("DELETE FROM lich_su_dieu_chuyen WHERE cong_chuc_id=:c"), {"c": str(cc.id)})
        await db.commit()
        try:
            # Gọi kích hoạt trong khi đã active → không đổi → không ghi
            await update_user_status(cc.id, UserStatusRequest(is_active=True), db, admin)
            await db.commit()
            rows = (await db.execute(select(LichSuDieuChuyen)
                    .where(LichSuDieuChuyen.cong_chuc_id == cc.id))).scalars().all()
            assert len(rows) == 0
        finally:
            await _restore(db, cc.id, snap)


# =============================================================================
# 2. _active_tai_thang_expr tôn trọng ngày hiệu lực
# =============================================================================

@pytest.mark.asyncio
async def test_active_tai_thang_theo_ngay_hieu_luc():
    async with AsyncSessionLocal() as db:
        cc = await _pick_cc(db)
        admin = await _pick_admin(db, cc.id)
        snap = _snapshot(cc)
        await db.execute(text("DELETE FROM lich_su_dieu_chuyen WHERE cong_chuc_id=:c"), {"c": str(cc.id)})
        await db.commit()
        try:
            # Vô hiệu hóa hiệu lực 2099-05-15
            db.add(LichSuDieuChuyen(loai="VO_HIEU_HOA", cong_chuc_id=cc.id,
                                    don_vi_cu_id=cc.don_vi_id, don_vi_moi_id=cc.don_vi_id,
                                    ngay_hieu_luc=date(2099, 5, 15), nguoi_thuc_hien_id=admin.id))
            await db.commit()

            async def active_in(thang, nam):
                q = select(CongChuc.id).where(CongChuc.id == cc.id,
                                              bc._active_tai_thang_expr(thang, nam))
                return (await db.execute(q)).first() is not None

            assert await active_in(4, 2099) is True   # trước hiệu lực → còn active
            assert await active_in(5, 2099) is False   # trong tháng hiệu lực → đã vô hiệu
            assert await active_in(6, 2099) is False   # sau hiệu lực → vô hiệu
        finally:
            await _restore(db, cc.id, snap)


# =============================================================================
# 3. _don_vi_tai_thang_expr KHÔNG bị bản ghi trạng thái làm lệch
# =============================================================================

@pytest.mark.asyncio
async def test_heuristic_khong_bi_ban_ghi_trang_thai_lam_lech():
    async with AsyncSessionLocal() as db:
        cc = await _pick_cc(db)
        admin = await _pick_admin(db, cc.id)
        snap = _snapshot(cc)
        dv_khac = await _don_vi_khac(db, cc.don_vi_id)
        await db.execute(text("DELETE FROM lich_su_dieu_chuyen WHERE cong_chuc_id=:c"), {"c": str(cc.id)})
        await db.commit()
        try:
            # Bản ghi VO_HIEU_HOA có don_vi_moi_id = đơn vị hồ sơ, hiệu lực xa trong tương lai.
            # Nếu heuristic KHÔNG lọc loai, roll sẽ nhặt don_vi_cu_id (= đơn vị khác) làm lệch.
            db.add(LichSuDieuChuyen(loai="VO_HIEU_HOA", cong_chuc_id=cc.id,
                                    don_vi_cu_id=dv_khac.id, don_vi_moi_id=cc.don_vi_id,
                                    ngay_hieu_luc=date(2099, 12, 31), nguoi_thuc_hien_id=admin.id))
            await db.commit()

            q = select(bc._don_vi_tai_thang_expr(1, 2099)).where(CongChuc.id == cc.id)
            dv_tai_thang = (await db.execute(q)).scalar_one()
            # Phải vẫn là đơn vị hồ sơ (bản ghi trạng thái bị bỏ qua), KHÔNG phải dv_khac
            assert dv_tai_thang == cc.don_vi_id
        finally:
            await _restore(db, cc.id, snap)


# =============================================================================
# 4. Sửa lịch sử + đồng bộ hồ sơ hiện tại (bản ghi mới nhất)
# =============================================================================

@pytest.mark.asyncio
async def test_sua_lich_su_dong_bo_hien_tai():
    async with AsyncSessionLocal() as db:
        cc = await _pick_cc(db)
        admin = await _pick_admin(db, cc.id)
        snap = _snapshot(cc)
        dv_khac = await _don_vi_khac(db, cc.don_vi_id)
        await db.execute(text("DELETE FROM lich_su_dieu_chuyen WHERE cong_chuc_id=:c"), {"c": str(cc.id)})
        await db.commit()
        try:
            ls = LichSuDieuChuyen(loai="DIEU_CHUYEN", cong_chuc_id=cc.id,
                                  don_vi_cu_id=cc.don_vi_id, don_vi_moi_id=cc.don_vi_id,
                                  ngay_hieu_luc=date(2099, 1, 1), nguoi_thuc_hien_id=admin.id)
            db.add(ls)
            await db.commit()
            ls_id = ls.id

            # Sửa đơn vị mới thành dv_khac + đồng bộ hồ sơ
            await update_transfer_history(
                cc.id, ls_id,
                LichSuDieuChuyenUpdateRequest(don_vi_moi_id=dv_khac.id, dong_bo_hien_tai=True),
                db, admin)
            await db.commit()

            cc2 = (await db.execute(select(CongChuc).where(CongChuc.id == cc.id))).scalar_one()
            assert cc2.don_vi_id == dv_khac.id  # hồ sơ đã đồng bộ theo bản ghi

            # Xóa bản ghi mới nhất + đồng bộ → hoàn tác về đơn vị cũ
            await delete_transfer_history(cc.id, ls_id, db, admin, dong_bo_hien_tai=True)
            await db.commit()
            cc3 = (await db.execute(select(CongChuc).where(CongChuc.id == cc.id))).scalar_one()
            assert cc3.don_vi_id == snap["don_vi_id"]  # về đơn vị cũ (don_vi_cu_id)
        finally:
            await _restore(db, cc.id, snap)


@pytest.mark.asyncio
async def test_sua_lich_su_cc_khong_khop_404():
    async with AsyncSessionLocal() as db:
        cc = await _pick_cc(db)
        admin = await _pick_admin(db, cc.id)
        other = await _pick_admin(db, cc.id)  # 1 CC khác
        await db.execute(text("DELETE FROM lich_su_dieu_chuyen WHERE cong_chuc_id=:c"), {"c": str(cc.id)})
        await db.commit()
        snap = _snapshot(cc)
        try:
            ls = LichSuDieuChuyen(loai="DIEU_CHUYEN", cong_chuc_id=cc.id,
                                  don_vi_cu_id=cc.don_vi_id, don_vi_moi_id=cc.don_vi_id,
                                  nguoi_thuc_hien_id=admin.id)
            db.add(ls)
            await db.commit()
            with pytest.raises(HTTPException) as ei:
                # history_id thuộc cc, nhưng user_id truyền vào là other → không khớp
                await update_transfer_history(
                    other.id, ls.id, LichSuDieuChuyenUpdateRequest(ly_do="x"), db, admin)
            assert ei.value.status_code == 404
        finally:
            await _restore(db, cc.id, snap)
