"""
tests/integration/test_moc_chot_don_vi_tai_thang.py
===================================================
Chốt hành vi MỐC CHỐT của `_don_vi_tai_thang_expr` sau đợt làm sạch
`lich_su_dieu_chuyen.ngay_hieu_luc` ngày 31/08/2026 (v2.1).

Điều được bảo vệ: mốc chốt là **cuối tháng M**, không phải cuối tháng M+1.
Nghĩa là quyết định có hiệu lực SAU khi tháng M kết thúc thì trong tháng M
công chức vẫn thuộc đơn vị CŨ. Nếu ai đó vô tình đưa `+ 1` trở lại, test này đỏ.

Trước 31/08/2026 mốc là cuối tháng M+1 — nới thêm trọn một tháng để BÙ cho việc
`ngay_hieu_luc` bị ghi bằng ngày nhập liệu (trễ 2–3 tuần so với QĐ). Dữ liệu đã
được làm sạch bằng `scripts/fix_ngay_dieu_chuyen_2026.py`, nên miếng vá đó phải bị bỏ.

⚠️ ĐIỀU CẦN BIẾT VỀ CƠ CHẾ BẦU PHIẾU (phát hiện khi viết test này):
    `v_ap` = COALESCE(đơn vị người duyệt, đơn vị hồ sơ) → **không bao giờ NULL**.
    Nên nhánh phá hòa `COALESCE(v_kk, v_ap, v_he)` KHÔNG BAO GIỜ chạm tới `v_he`.
    Hệ quả: **heuristic một mình không thể đổi kết quả** — nó chỉ thắng khi
    ĐỒNG Ý với phiếu kê-khai (hoặc trùng phiếu người-duyệt). Vì vậy mọi test về
    mốc chốt BẮT BUỘC phải có bản kê khai trong tháng, nếu không kết quả luôn là
    đơn vị hồ sơ hiện tại và test không phân biệt được mốc cũ/mốc mới.

Chạy trên kpi_haiquan_test:
    DB_NAME=kpi_haiquan_test pytest tests/integration/test_moc_chot_don_vi_tai_thang.py -v

Pattern: tự tạo/dọn dữ liệu, dùng năm test xa (2099) để không đụng dữ liệu thật.
"""
from __future__ import annotations

from datetime import date

import pytest
from sqlalchemy import select, text

import app.api.v1.endpoints.bao_cao_xep_loai as bc
from app.db.session import AsyncSessionLocal
from app.models.admin import LichSuDieuChuyen
from app.models.kpi_submission import KeKhaiCongViec
from app.models.user_org import CongChuc, DonVi

NAM_TEST = 2099
LY_DO_TEST = "TEST moc chot don vi tai thang"


# =============================================================================
# Helpers
# =============================================================================

async def _hai_don_vi(db) -> tuple[DonVi, DonVi]:
    """Hai đơn vị bất kỳ, khác nhau — đóng vai đơn vị cũ và đơn vị mới."""
    rows = (await db.execute(
        select(DonVi).order_by(DonVi.ma_don_vi).limit(2)
    )).scalars().all()
    assert len(rows) == 2, "DB test cần ít nhất 2 đơn vị"
    return rows[0], rows[1]


async def _cong_chuc_sach(db, don_vi: DonVi) -> CongChuc:
    """Công chức đang thuộc `don_vi` và CHƯA có bản ghi điều chuyển nào —
    để phép suy chỉ phụ thuộc vào dữ liệu mà test tự tạo."""
    cc_list = (await db.execute(
        select(CongChuc)
        .where(CongChuc.don_vi_id == don_vi.id, CongChuc.is_deleted == False)
        .order_by(CongChuc.ma_cc)
    )).scalars().all()
    for cc in cc_list:
        da_co = (await db.execute(
            select(LichSuDieuChuyen.id)
            .where(LichSuDieuChuyen.cong_chuc_id == cc.id).limit(1)
        )).scalar_one_or_none()
        if da_co is None:
            return cc
    pytest.skip(f"Không tìm được công chức ở {don_vi.ma_don_vi} chưa có lịch sử điều chuyển")


async def _mot_danh_muc_sp(db):
    ma_dm = (await db.execute(
        text("SELECT id FROM danh_muc_sp_cong_viec WHERE is_deleted = false LIMIT 1")
    )).scalar_one_or_none()
    if ma_dm is None:
        pytest.skip("DB test không có danh mục sản phẩm công việc")
    return ma_dm


async def _don_vi_tai_thang(db, cong_chuc_id, thang: int, nam: int):
    """Chạy chính biểu thức của báo cáo cho đúng một công chức."""
    return (await db.execute(
        select(bc._don_vi_tai_thang_expr(thang, nam)).where(CongChuc.id == cong_chuc_id)
    )).scalar_one()


class BoiCanh:
    """Dựng sẵn: 1 công chức ở đơn vị mới + 1 bản ghi điều chuyển + các bản kê khai."""

    def __init__(self, db, cc, dv_cu, dv_moi, danh_muc_id):
        self.db, self.cc = db, cc
        self.dv_cu, self.dv_moi = dv_cu, dv_moi
        self.danh_muc_id = danh_muc_id
        self.da_tao: list = []

    async def dieu_chuyen(self, ngay: date):
        r = LichSuDieuChuyen(
            loai="DIEU_CHUYEN",
            cong_chuc_id=self.cc.id,
            don_vi_cu_id=self.dv_cu.id,
            don_vi_moi_id=self.dv_moi.id,
            ngay_hieu_luc=ngay,
            ly_do=LY_DO_TEST,
        )
        self.db.add(r)
        self.da_tao.append(r)
        await self.db.flush()
        return r

    async def ke_khai(self, thang: int, don_vi: DonVi):
        r = KeKhaiCongViec(
            cong_chuc_id=self.cc.id,
            thang=thang,
            nam=NAM_TEST,
            danh_muc_sp_id=self.danh_muc_id,
            so_luong=1,
            don_vi_id_snapshot=don_vi.id,
            mo_ta_cong_viec=LY_DO_TEST,
        )
        self.db.add(r)
        self.da_tao.append(r)
        await self.db.flush()
        return r

    async def don(self):
        for r in reversed(self.da_tao):
            await self.db.delete(r)
        await self.db.commit()


# =============================================================================
# Tests
# =============================================================================

@pytest.mark.asyncio
async def test_hieu_luc_giua_thang_sau_thi_thang_truoc_van_o_don_vi_cu():
    """
    Ca thật đã gây lỗi (20ZZ-0508 Nguyễn Xuân Giáp): QĐ hiệu lực **15/5**,
    xét báo cáo **tháng 4**, kê khai tháng 4 nằm ở đơn vị cũ.

    Mốc cũ (cuối tháng M+1 = 31/5): 15/5 không > 31/5 → he = đơn vị MỚI
        → kê-khai(cũ) ≠ người-duyệt(mới), kê-khai ≠ he → người-duyệt == he
        → gán đơn vị MỚI ❌ (tháng 4 người này còn ở đơn vị cũ).
    Mốc mới (cuối tháng M = 30/4): 15/5 > 30/4 → he = đơn vị CŨ
        → kê-khai == he → đơn vị CŨ ✅
    """
    async with AsyncSessionLocal() as db:
        dv_cu, dv_moi = await _hai_don_vi(db)
        cc = await _cong_chuc_sach(db, dv_moi)
        danh_muc_id = await _mot_danh_muc_sp(db)
        bc_ = BoiCanh(db, cc, dv_cu, dv_moi, danh_muc_id)

        try:
            await bc_.dieu_chuyen(date(NAM_TEST, 5, 15))
            await bc_.ke_khai(4, dv_cu)   # tháng 4 còn làm ở đơn vị cũ
            await bc_.ke_khai(5, dv_moi)  # tháng 5 đã sang đơn vị mới
            await bc_.ke_khai(6, dv_moi)

            assert await _don_vi_tai_thang(db, cc.id, 4, NAM_TEST) == dv_cu.id, (
                "Tháng 4 phải thuộc đơn vị CŨ — mốc chốt có vẻ vẫn là cuối tháng M+1"
            )
            assert await _don_vi_tai_thang(db, cc.id, 5, NAM_TEST) == dv_moi.id
            assert await _don_vi_tai_thang(db, cc.id, 6, NAM_TEST) == dv_moi.id
        finally:
            await bc_.don()


@pytest.mark.asyncio
async def test_hieu_luc_ngay_dau_thang_la_bien_cua_moc_chot():
    """
    Hiệu lực đúng 01/6 → tháng 5 vẫn đơn vị cũ, tháng 6 đã là đơn vị mới.
    Chốt biên phép so sánh `>` với ngày CUỐI tháng.

    Mốc cũ (30/6) cho tháng 5: 01/6 không > 30/6 → he = mới → ra đơn vị MỚI ❌
    Mốc mới (31/5) cho tháng 5: 01/6 > 31/5 → he = cũ → kê-khai == he → CŨ ✅
    """
    async with AsyncSessionLocal() as db:
        dv_cu, dv_moi = await _hai_don_vi(db)
        cc = await _cong_chuc_sach(db, dv_moi)
        danh_muc_id = await _mot_danh_muc_sp(db)
        bc_ = BoiCanh(db, cc, dv_cu, dv_moi, danh_muc_id)

        try:
            await bc_.dieu_chuyen(date(NAM_TEST, 6, 1))
            await bc_.ke_khai(5, dv_cu)
            await bc_.ke_khai(6, dv_moi)

            assert await _don_vi_tai_thang(db, cc.id, 5, NAM_TEST) == dv_cu.id
            assert await _don_vi_tai_thang(db, cc.id, 6, NAM_TEST) == dv_moi.id
        finally:
            await bc_.don()


@pytest.mark.asyncio
async def test_ban_ghi_trang_thai_khong_lam_lech_phep_suy_don_vi():
    """VO_HIEU_HOA/KICH_HOAT không phải điều chuyển → không được cuộn ngược đơn vị."""
    async with AsyncSessionLocal() as db:
        dv_cu, dv_moi = await _hai_don_vi(db)
        cc = await _cong_chuc_sach(db, dv_moi)
        danh_muc_id = await _mot_danh_muc_sp(db)
        bc_ = BoiCanh(db, cc, dv_cu, dv_moi, danh_muc_id)

        try:
            r = LichSuDieuChuyen(
                loai="VO_HIEU_HOA",
                cong_chuc_id=cc.id,
                don_vi_cu_id=dv_cu.id,
                don_vi_moi_id=dv_moi.id,
                ngay_hieu_luc=date(NAM_TEST, 5, 15),
                ly_do=LY_DO_TEST,
            )
            db.add(r)
            bc_.da_tao.append(r)
            await db.flush()
            await bc_.ke_khai(4, dv_moi)

            assert await _don_vi_tai_thang(db, cc.id, 4, NAM_TEST) == dv_moi.id
        finally:
            await bc_.don()


@pytest.mark.asyncio
async def test_khong_co_lich_su_thi_lay_don_vi_hien_tai():
    """Công chức chưa từng điều chuyển → đơn vị-tại-tháng = đơn vị hồ sơ."""
    async with AsyncSessionLocal() as db:
        _dv_cu, dv_moi = await _hai_don_vi(db)
        cc = await _cong_chuc_sach(db, dv_moi)
        for thang in (1, 6, 12):
            assert await _don_vi_tai_thang(db, cc.id, thang, NAM_TEST) == dv_moi.id


@pytest.mark.asyncio
async def test_heuristic_mot_minh_khong_doi_duoc_ket_qua():
    """
    Chốt lại giới hạn đã phát hiện: KHÔNG có bản kê khai trong tháng thì
    `v_ap` (mặc định = đơn vị hồ sơ) luôn thắng, heuristic vô hiệu.

    Test này KHÔNG phải mong muốn nghiệp vụ — nó ghi lại hành vi thật để lần sau
    ai đọc `_don_vi_tai_thang_expr` không kỳ vọng sai. Nếu sau này nhánh phá hòa
    được sửa cho heuristic có tiếng nói, test này sẽ đỏ và cần cập nhật có ý thức.
    """
    async with AsyncSessionLocal() as db:
        dv_cu, dv_moi = await _hai_don_vi(db)
        cc = await _cong_chuc_sach(db, dv_moi)
        danh_muc_id = await _mot_danh_muc_sp(db)
        bc_ = BoiCanh(db, cc, dv_cu, dv_moi, danh_muc_id)

        try:
            await bc_.dieu_chuyen(date(NAM_TEST, 5, 15))
            # KHÔNG tạo kê khai tháng 4
            assert await _don_vi_tai_thang(db, cc.id, 4, NAM_TEST) == dv_moi.id
        finally:
            await bc_.don()
