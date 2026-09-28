"""
tests/integration/test_phieu_tong_hop.py
========================================
Tổng hợp phiếu đánh giá quý (Mẫu 02A/02B) toàn Chi cục — CHỈ ĐỌC.

Chạy trên kpi_haiquan_test — TUYỆT ĐỐI KHÔNG chạy trên kpi_haiquan (prod):
    DB_NAME=kpi_haiquan_test pytest tests/integration/test_phieu_tong_hop.py -v

Toàn bộ test dưới đây CHỈ ĐỌC, không ghi dòng nào.

Phạm vi:
1. Quyền — CCT/PCCT/TCCB/`can_view_all_units` xem được; CC thường và cả Trưởng
   đơn vị đều bị chặn (quyết định 29/09: TDV vẫn chỉ thấy đơn vị mình).
2. Phạm vi dữ liệu — đủ mọi công chức thuộc diện đánh giá, KHÔNG có CCT/TCCB/admin.
3. Người chưa soạn phiếu vẫn có dòng (trạng thái NHAP, id=None).
4. Bộ lọc đơn vị / trạng thái / xếp loại / tìm kiếm và số đếm `tong_hop`.
5. Quyền TẢI bản in: người xem toàn Chi cục tải được phiếu của bất kỳ ai; TDV
   đơn vị khác vẫn bị chặn.
"""

from __future__ import annotations

import pytest
from fastapi import HTTPException
from sqlalchemy import select, text

from app.api.v1.endpoints.in_bang_ke import _load_cc_cho_in_boi_tdv
from app.api.v1.endpoints.phieu_danh_gia_quy import (
    _thu_thap_phieu_toan_chi_cuc,
    get_phieu_toan_chi_cuc,
)
from app.core.quyen_xem_phieu import xem_duoc_toan_chi_cuc
from app.db.session import AsyncSessionLocal
from app.models.user_org import CapBacVaiTro, CongChuc

QUY_TEST = 3
NAM_TEST = 2026


async def _lay_cc_theo_cap_bac(db, cap_bac: CapBacVaiTro) -> CongChuc | None:
    row = (await db.execute(text("""
        SELECT cc.id FROM cong_chuc cc
        JOIN vai_tro vt ON vt.id = cc.vai_tro_id
        WHERE vt.cap_bac = :cb AND cc.is_active AND NOT cc.is_deleted
        LIMIT 1
    """), {"cb": cap_bac.value})).first()
    if not row:
        return None
    from sqlalchemy.orm import selectinload
    return (await db.execute(
        select(CongChuc)
        .options(selectinload(CongChuc.vai_tro), selectinload(CongChuc.don_vi))
        .where(CongChuc.id == row[0])
    )).scalar_one()


# =============================================================================
# 1. Quyền
# =============================================================================

@pytest.mark.asyncio
async def test_ai_duoc_xem_toan_chi_cuc():
    async with AsyncSessionLocal() as db:
        cct = await _lay_cc_theo_cap_bac(db, CapBacVaiTro.CHI_CUC_TRUONG)
        pcct = await _lay_cc_theo_cap_bac(db, CapBacVaiTro.PHO_CHI_CUC_TRUONG)
        tdv = await _lay_cc_theo_cap_bac(db, CapBacVaiTro.TRUONG_DON_VI)
        cc = await _lay_cc_theo_cap_bac(db, CapBacVaiTro.CONG_CHUC)

        assert xem_duoc_toan_chi_cuc(cct) is True
        assert xem_duoc_toan_chi_cuc(pcct) is True
        # Quyết định 29/09: KHÔNG mở cho Trưởng đơn vị xem đơn vị khác
        assert xem_duoc_toan_chi_cuc(tdv) is False
        assert xem_duoc_toan_chi_cuc(cc) is False


@pytest.mark.asyncio
async def test_cong_chuc_va_tdv_bi_chan():
    async with AsyncSessionLocal() as db:
        for cap_bac in (CapBacVaiTro.CONG_CHUC, CapBacVaiTro.TRUONG_DON_VI):
            nguoi = await _lay_cc_theo_cap_bac(db, cap_bac)
            with pytest.raises(HTTPException) as exc:
                await get_phieu_toan_chi_cuc(
                    db, nguoi, quy=QUY_TEST, nam=NAM_TEST,
                    don_vi_id=None, trang_thai=None, xep_loai=None, tim=None,
                    page=1, page_size=50,
                )
            assert exc.value.status_code == 403
            assert exc.value.detail["error"]["code"] == "PHIEU_010"


@pytest.mark.asyncio
async def test_co_can_view_all_units_thi_xem_duoc():
    """Cờ `can_view_all_units` là đường cấp quyền cho tài khoản không phải lãnh đạo."""
    async with AsyncSessionLocal() as db:
        cc = await _lay_cc_theo_cap_bac(db, CapBacVaiTro.CONG_CHUC)
        assert xem_duoc_toan_chi_cuc(cc) is False
        cc.can_view_all_units = True          # chỉ đổi trong bộ nhớ, KHÔNG commit
        try:
            assert xem_duoc_toan_chi_cuc(cc) is True
        finally:
            cc.can_view_all_units = False
            db.expunge(cc)


# =============================================================================
# 2 + 3. Phạm vi dữ liệu
# =============================================================================

@pytest.mark.asyncio
async def test_du_moi_cong_chuc_thuoc_dien_danh_gia():
    async with AsyncSessionLocal() as db:
        items = await _thu_thap_phieu_toan_chi_cuc(db, QUY_TEST, NAM_TEST)

        so_dien = (await db.execute(text("""
            SELECT count(*) FROM cong_chuc cc
            JOIN vai_tro vt ON vt.id = cc.vai_tro_id
            WHERE cc.is_active AND NOT cc.is_deleted
              AND vt.cap_bac NOT IN ('CHI_CUC_TRUONG', 'TCCB', 'SUPER_ADMIN')
        """))).scalar()

        assert len(items) == so_dien, (
            f"Bảng tổng hợp có {len(items)} dòng, trong khi diện đánh giá là {so_dien}"
        )
        assert so_dien > 100, "DB test có vẻ thiếu dữ liệu công chức"

        # Không được lọt CCT / TCCB / admin vào bảng
        assert all(it.vai_tro not in ("CCT", "TCCB", "ADMIN") for it in items)


@pytest.mark.asyncio
async def test_nguoi_chua_soan_phieu_van_co_dong():
    """Đây là nhóm TCCB cần thấy nhất — không được lọc mất."""
    async with AsyncSessionLocal() as db:
        items = await _thu_thap_phieu_toan_chi_cuc(db, QUY_TEST, NAM_TEST)
        chua_soan = [it for it in items if it.id is None]

        so_co_phieu = (await db.execute(text("""
            SELECT count(*) FROM phieu_danh_gia_quy p
            JOIN cong_chuc cc ON cc.id = p.cong_chuc_id
            JOIN vai_tro vt ON vt.id = cc.vai_tro_id
            WHERE p.quy = :q AND p.nam = :n AND cc.is_active AND NOT cc.is_deleted
              AND vt.cap_bac NOT IN ('CHI_CUC_TRUONG', 'TCCB', 'SUPER_ADMIN')
        """), {"q": QUY_TEST, "n": NAM_TEST})).scalar()

        assert len(items) - len(chua_soan) == so_co_phieu
        assert all(it.trang_thai == "NHAP" for it in chua_soan)


@pytest.mark.asyncio
async def test_noi_dung_phieu_duoc_tra_ve():
    """Cột chữ của Mẫu 02 phải có mặt — đó là lý do tồn tại của trang này."""
    async with AsyncSessionLocal() as db:
        row = (await db.execute(text("""
            SELECT p.cong_chuc_id::text, p.uu_diem
            FROM phieu_danh_gia_quy p
            WHERE p.quy = :q AND p.nam = :n
              AND p.uu_diem IS NOT NULL AND length(trim(p.uu_diem)) > 0
            LIMIT 1
        """), {"q": QUY_TEST, "n": NAM_TEST})).first()
        if not row:
            pytest.skip("DB test không có phiếu nào đã nhập ưu điểm")

        items = await _thu_thap_phieu_toan_chi_cuc(db, QUY_TEST, NAM_TEST)
        khop = [it for it in items if str(it.cong_chuc_id) == row[0]]
        assert khop, "Phiếu có nội dung nhưng không thấy trong bảng tổng hợp"
        assert khop[0].uu_diem == row[1]


# =============================================================================
# 4. Bộ lọc + số đếm
# =============================================================================

@pytest.mark.asyncio
async def test_loc_theo_don_vi_va_trang_thai():
    async with AsyncSessionLocal() as db:
        tat_ca = await _thu_thap_phieu_toan_chi_cuc(db, QUY_TEST, NAM_TEST)
        assert tat_ca

        don_vi_id = next(it.don_vi_id for it in tat_ca if it.don_vi_id)
        theo_dv = await _thu_thap_phieu_toan_chi_cuc(
            db, QUY_TEST, NAM_TEST, don_vi_id=don_vi_id
        )
        assert theo_dv
        assert all(it.don_vi_id == don_vi_id for it in theo_dv)
        assert len(theo_dv) == len([it for it in tat_ca if it.don_vi_id == don_vi_id])

        cho_duyet = await _thu_thap_phieu_toan_chi_cuc(
            db, QUY_TEST, NAM_TEST, trang_thai="CHO_PHE_DUYET"
        )
        assert all(it.trang_thai == "CHO_PHE_DUYET" for it in cho_duyet)
        assert len(cho_duyet) == len(
            [it for it in tat_ca if it.trang_thai == "CHO_PHE_DUYET"]
        )


@pytest.mark.asyncio
async def test_tim_kiem_theo_ten_va_ma():
    async with AsyncSessionLocal() as db:
        tat_ca = await _thu_thap_phieu_toan_chi_cuc(db, QUY_TEST, NAM_TEST)
        mau = tat_ca[0]

        theo_ma = await _thu_thap_phieu_toan_chi_cuc(
            db, QUY_TEST, NAM_TEST, tim=mau.ma_cc
        )
        assert any(it.ma_cc == mau.ma_cc for it in theo_ma)
        assert all(
            mau.ma_cc.lower() in it.ma_cc.lower()
            or mau.ma_cc.lower() in (it.ho_ten or "").lower()
            for it in theo_ma
        )


@pytest.mark.asyncio
async def test_tong_hop_dem_dung():
    async with AsyncSessionLocal() as db:
        cct = await _lay_cc_theo_cap_bac(db, CapBacVaiTro.CHI_CUC_TRUONG)
        kq = await get_phieu_toan_chi_cuc(
            db, cct, quy=QUY_TEST, nam=NAM_TEST,
            don_vi_id=None, trang_thai=None, xep_loai=None, tim=None,
            page=1, page_size=10,
        )
        data = kq["data"]
        th = data["tong_hop"]

        assert th["tong_so"] == data["pagination"]["total_items"]
        assert sum(th["theo_trang_thai"].values()) == th["tong_so"]
        assert (
            sum(th["theo_xep_loai"].values()) + th["chua_quyet_dinh_xep_loai"]
            == th["tong_so"]
        )
        # Phân trang phải cắt đúng, không trả cả nghìn dòng một lượt
        assert len(data["items"]) == min(10, th["tong_so"])


@pytest.mark.asyncio
async def test_trang_thai_va_xep_loai_sai_bi_tu_choi():
    async with AsyncSessionLocal() as db:
        cct = await _lay_cc_theo_cap_bac(db, CapBacVaiTro.CHI_CUC_TRUONG)
        for xau, ma_loi in (("LUNG_TUNG", "PHIEU_009"), (None, "PHIEU_011")):
            with pytest.raises(HTTPException) as exc:
                await get_phieu_toan_chi_cuc(
                    db, cct, quy=QUY_TEST, nam=NAM_TEST, don_vi_id=None,
                    trang_thai=xau if ma_loi == "PHIEU_009" else None,
                    xep_loai=None if ma_loi == "PHIEU_009" else "HANG_A",
                    tim=None, page=1, page_size=10,
                )
            assert exc.value.status_code == 400
            assert exc.value.detail["error"]["code"] == ma_loi


# =============================================================================
# 5. Quyền tải bản in
# =============================================================================

@pytest.mark.asyncio
async def test_nguoi_xem_toan_chi_cuc_tai_duoc_ban_in_cua_moi_nguoi():
    async with AsyncSessionLocal() as db:
        cct = await _lay_cc_theo_cap_bac(db, CapBacVaiTro.CHI_CUC_TRUONG)
        cc = await _lay_cc_theo_cap_bac(db, CapBacVaiTro.CONG_CHUC)

        # Trước 29/09 ca này bị 403: CCT chỉ tải được bản in của TDV/PCCT
        target = await _load_cc_cho_in_boi_tdv(db, cct, cc.id)
        assert target.id == cc.id


@pytest.mark.asyncio
async def test_tdv_van_khong_tai_duoc_ban_in_don_vi_khac():
    async with AsyncSessionLocal() as db:
        tdv = await _lay_cc_theo_cap_bac(db, CapBacVaiTro.TRUONG_DON_VI)
        row = (await db.execute(text("""
            SELECT cc.id FROM cong_chuc cc
            JOIN vai_tro vt ON vt.id = cc.vai_tro_id
            WHERE vt.cap_bac = 'CONG_CHUC' AND cc.is_active AND NOT cc.is_deleted
              AND cc.don_vi_id IS DISTINCT FROM :dv
            LIMIT 1
        """), {"dv": str(tdv.don_vi_id)})).first()
        if not row:
            pytest.skip("DB test không có công chức ở đơn vị khác")

        with pytest.raises(HTTPException) as exc:
            await _load_cc_cho_in_boi_tdv(db, tdv, row[0])
        assert exc.value.status_code == 403
