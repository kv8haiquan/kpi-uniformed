"""
tests/integration/test_bao_cao_thang_chi_doc.py
==============================================
Báo cáo xếp loại THÁNG của kỳ đã chuyển sang QUÝ chỉ được XEM
(Công văn 21169/CHQ-TCCB, quyết định người dùng 21/09/2026).

Chạy trên kpi_haiquan_test — TUYỆT ĐỐI KHÔNG chạy trên kpi_haiquan (prod):
    DB_NAME=kpi_haiquan_test pytest tests/integration/test_bao_cao_thang_chi_doc.py -v

Vì sao phải chặn ở backend chứ không chỉ ẩn nút: `phe_duyet_bao_cao` đặt
`is_khoa = true` cho mọi bản ghi `danh_gia_thang` của tháng đó. Nếu tháng ấy là
THÁNG NEO (T9, T12…) thì phiếu tiêu chí của cả quý bị khoá, công chức không sửa
được nữa.
"""

from __future__ import annotations

import pytest
from fastapi import HTTPException
from sqlalchemy import select, text

from app.api.v1.endpoints.bao_cao_xep_loai import (
    de_xuat_xep_loai,
    get_bao_cao_don_vi,
    gui_duyet_bao_cao,
    ky_bao_cao_thang_chi_doc,
    phe_duyet_bao_cao,
    quyet_dinh_xep_loai,
    tra_lai_bao_cao,
)
from app.db.session import AsyncSessionLocal
from app.models.bao_cao_xep_loai import BaoCaoXepLoai, ChiTietXepLoai
from app.models.user_org import CongChuc


# =============================================================================
# Mốc kỳ
# =============================================================================

def test_moc_ky_chi_doc():
    """Đến hết Q2/2026 còn sửa được; từ Q3/2026 chỉ xem."""
    for thang in (1, 4, 5, 6):
        assert ky_bao_cao_thang_chi_doc(thang, 2026) is False
    assert ky_bao_cao_thang_chi_doc(12, 2025) is False
    for thang in (7, 8, 9, 10, 12):
        assert ky_bao_cao_thang_chi_doc(thang, 2026) is True
    assert ky_bao_cao_thang_chi_doc(1, 2027) is True


# =============================================================================
# Helpers
# =============================================================================

async def _lay_bao_cao(db, thang: int, nam: int = 2026):
    """Một báo cáo tháng có sẵn trong DB test, kèm Trưởng đơn vị và CCT của nó."""
    row = (await db.execute(text("""
        SELECT bc.id AS bc_id,
               (SELECT ct.id FROM chi_tiet_xep_loai ct WHERE ct.bao_cao_id = bc.id LIMIT 1) AS ct_id,
               (SELECT cc.id FROM cong_chuc cc JOIN vai_tro vt ON cc.vai_tro_id = vt.id
                 WHERE cc.don_vi_id = bc.don_vi_id AND vt.cap_bac = 'TRUONG_DON_VI'
                   AND cc.is_active AND NOT cc.is_deleted LIMIT 1) AS tdv_id
        FROM bao_cao_xep_loai bc
        WHERE bc.thang = :t AND bc.nam = :n AND bc.is_deleted = false
          AND EXISTS (SELECT 1 FROM chi_tiet_xep_loai ct WHERE ct.bao_cao_id = bc.id)
        LIMIT 1
    """), {"t": thang, "n": nam})).first()
    return row


async def _lay_cct(db) -> CongChuc:
    from sqlalchemy.orm import selectinload
    row = (await db.execute(text("""
        SELECT cc.id FROM cong_chuc cc JOIN vai_tro vt ON cc.vai_tro_id = vt.id
        WHERE vt.cap_bac = 'CHI_CUC_TRUONG' AND cc.is_active AND NOT cc.is_deleted LIMIT 1
    """))).first()
    assert row, "DB test không có Chi cục trưởng"
    return (await db.execute(
        select(CongChuc).options(selectinload(CongChuc.vai_tro)).where(CongChuc.id == row[0])
    )).scalar_one()


async def _lay_nguoi(db, cong_chuc_id) -> CongChuc:
    from sqlalchemy.orm import selectinload
    return (await db.execute(
        select(CongChuc).options(selectinload(CongChuc.vai_tro)).where(CongChuc.id == cong_chuc_id)
    )).scalar_one()


# =============================================================================
# Năm endpoint ghi đều bị chặn với kỳ từ Q3/2026
# =============================================================================

@pytest.mark.asyncio
async def test_nam_endpoint_ghi_deu_bi_chan():
    """Sửa đề xuất, gửi duyệt, quyết định, phê duyệt, trả lại → 400, dữ liệu không đổi."""
    from app.api.v1.endpoints.bao_cao_xep_loai import TraLaiBaoCaoRequest
    from app.schemas.bao_cao_xep_loai import (
        DeXuatXepLoaiRequest,
        PheDuyetBaoCaoRequest,
        QuyetDinhXepLoaiRequest,
    )

    async with AsyncSessionLocal() as db:
        row = await _lay_bao_cao(db, thang=7)
        if not row:
            pytest.skip("DB test không có báo cáo tháng 7/2026 kèm chi tiết")

        tdv = await _lay_nguoi(db, row.tdv_id) if row.tdv_id else None
        cct = await _lay_cct(db)

        truoc_bc = (await db.execute(
            select(BaoCaoXepLoai).where(BaoCaoXepLoai.id == row.bc_id)
        )).scalar_one()
        trang_thai_truoc = truoc_bc.trang_thai
        truoc_ct = (await db.execute(
            select(ChiTietXepLoai).where(ChiTietXepLoai.id == row.ct_id)
        )).scalar_one()
        de_xuat_truoc = truoc_ct.xep_loai_de_xuat
        quyet_dinh_truoc = truoc_ct.xep_loai_quyet_dinh

        # Chốt chặn ném lỗi TRƯỚC mọi thao tác ghi nên session không bẩn — không
        # rollback giữa chừng, vì rollback làm hết hạn các đối tượng ORM đã nạp
        # (user.vai_tro) và lần đọc sau sẽ nổ MissingGreenlet.
        async def _phai_400(coro, ten: str):
            with pytest.raises(HTTPException) as exc:
                await coro
            assert exc.value.status_code == 400, f"{ten} phải trả 400"
            assert "QUÝ" in str(exc.value.detail), f"{ten} phải nói rõ lý do"

        if tdv:
            await _phai_400(
                de_xuat_xep_loai(db, tdv, row.ct_id,
                                 DeXuatXepLoaiRequest(xep_loai_de_xuat="A", ly_do_dieu_chinh="test")),
                "de-xuat",
            )
            await _phai_400(gui_duyet_bao_cao(db, tdv, row.bc_id), "gui-duyet")

        await _phai_400(
            quyet_dinh_xep_loai(db, cct, row.ct_id,
                                QuyetDinhXepLoaiRequest(xep_loai_quyet_dinh="A", ly_do_dieu_chinh="test")),
            "quyet-dinh",
        )
        await _phai_400(
            phe_duyet_bao_cao(db, cct, row.bc_id, PheDuyetBaoCaoRequest(action="APPROVE")),
            "phe-duyet",
        )
        await _phai_400(
            tra_lai_bao_cao(db, cct, row.bc_id, TraLaiBaoCaoRequest(ly_do="test")),
            "tra-lai",
        )

        # Dữ liệu không suy suyển
        await db.rollback()
        sau_bc = (await db.execute(
            select(BaoCaoXepLoai).where(BaoCaoXepLoai.id == row.bc_id)
        )).scalar_one()
        sau_ct = (await db.execute(
            select(ChiTietXepLoai).where(ChiTietXepLoai.id == row.ct_id)
        )).scalar_one()
        assert sau_bc.trang_thai == trang_thai_truoc
        assert sau_ct.xep_loai_de_xuat == de_xuat_truoc
        assert sau_ct.xep_loai_quyet_dinh == quyet_dinh_truoc


@pytest.mark.asyncio
async def test_khong_khoa_nham_phieu_tieu_chi_quy():
    """Phê duyệt bị chặn ⇒ không bản ghi đánh giá nào của THÁNG NEO bị đặt is_khoa."""
    from app.schemas.bao_cao_xep_loai import PheDuyetBaoCaoRequest

    async with AsyncSessionLocal() as db:
        row = await _lay_bao_cao(db, thang=9)  # T9 = tháng neo của quý III
        if not row:
            pytest.skip("DB test không có báo cáo tháng 9/2026 kèm chi tiết")
        cct = await _lay_cct(db)

        khoa_truoc = (await db.execute(text("""
            SELECT count(*) FROM danh_gia_thang
            WHERE nam = 2026 AND thang = 9 AND is_khoa = true AND is_deleted = false
        """))).scalar()

        with pytest.raises(HTTPException) as exc:
            await phe_duyet_bao_cao(db, cct, row.bc_id, PheDuyetBaoCaoRequest(action="APPROVE"))
        assert exc.value.status_code == 400
        await db.rollback()

        khoa_sau = (await db.execute(text("""
            SELECT count(*) FROM danh_gia_thang
            WHERE nam = 2026 AND thang = 9 AND is_khoa = true AND is_deleted = false
        """))).scalar()
        assert khoa_sau == khoa_truoc, "Phiếu tiêu chí quý bị khoá nhầm"


# =============================================================================
# Vẫn XEM được, và cờ chỉ-đọc đúng
# =============================================================================

@pytest.mark.asyncio
async def test_van_xem_duoc_va_co_co_chi_doc():
    """GET báo cáo tháng của kỳ quý: 200, can_edit/can_approve = false, chi_doc = true."""
    async with AsyncSessionLocal() as db:
        row = (await db.execute(text("""
            SELECT cc.id FROM cong_chuc cc JOIN vai_tro vt ON cc.vai_tro_id = vt.id
            WHERE vt.cap_bac = 'TRUONG_DON_VI' AND cc.is_active AND NOT cc.is_deleted
              AND cc.don_vi_id IS NOT NULL LIMIT 1
        """))).first()
        assert row, "DB test không có Trưởng đơn vị"
        tdv = await _lay_nguoi(db, row[0])

        res = await get_bao_cao_don_vi(db, tdv, 8, 2026)
        assert res["success"] is True
        data = res["data"]
        assert data["chi_doc"] is True
        assert data["can_edit"] is False
        assert data["can_approve"] is False
        assert "QUÝ" in (data["ly_do_chi_doc"] or "")
        await db.rollback()


@pytest.mark.asyncio
async def test_thang_chua_co_bao_cao_van_dung_duoc_ban_nhap():
    """Quyết định 21/09: tháng chưa có báo cáo vẫn dựng bản nháp để xem (không còn chặn 400)."""
    async with AsyncSessionLocal() as db:
        row = (await db.execute(text("""
            SELECT cc.id, t.thang
            FROM cong_chuc cc
            JOIN vai_tro vt ON cc.vai_tro_id = vt.id
            CROSS JOIN generate_series(7, 12) AS t(thang)
            WHERE vt.cap_bac = 'TRUONG_DON_VI' AND cc.is_active AND NOT cc.is_deleted
              AND cc.don_vi_id IS NOT NULL
              AND NOT EXISTS (
                  SELECT 1 FROM bao_cao_xep_loai bc
                  WHERE bc.don_vi_id = cc.don_vi_id AND bc.thang = t.thang
                    AND bc.nam = 2026 AND bc.is_deleted = false)
            LIMIT 1
        """))).first()
        if not row:
            pytest.skip("Mọi đơn vị đều đã có báo cáo ở các tháng của kỳ quý")

        tdv = await _lay_nguoi(db, row[0])
        res = await get_bao_cao_don_vi(db, tdv, row[1], 2026)
        assert res["success"] is True
        assert res["data"]["chi_doc"] is True
        assert res["data"]["can_edit"] is False
        await db.rollback()


# =============================================================================
# Không hồi tố — kỳ cũ vẫn sửa bình thường
# =============================================================================

@pytest.mark.asyncio
async def test_khong_hoi_to_ky_cu():
    """Kỳ đến hết Q2/2026: chốt chặn không được đụng tới, vẫn sửa đề xuất được."""
    from app.schemas.bao_cao_xep_loai import DeXuatXepLoaiRequest

    async with AsyncSessionLocal() as db:
        row = None
        for thang in (6, 5, 4, 1):
            row = await _lay_bao_cao(db, thang=thang)
            if row and row.tdv_id:
                break
        if not row or not row.tdv_id:
            pytest.skip("DB test không có báo cáo kỳ cũ kèm Trưởng đơn vị")

        tdv = await _lay_nguoi(db, row.tdv_id)
        truoc = (await db.execute(
            select(ChiTietXepLoai).where(ChiTietXepLoai.id == row.ct_id)
        )).scalar_one()
        cu = truoc.xep_loai_de_xuat

        try:
            await de_xuat_xep_loai(
                db, tdv, row.ct_id,
                DeXuatXepLoaiRequest(xep_loai_de_xuat="B", ly_do_dieu_chinh="test không hồi tố"),
            )
        except HTTPException as exc:
            # Có thể vướng quy tắc nghiệp vụ khác (trạng thái báo cáo, khác đơn vị) —
            # miễn KHÔNG phải mã chặn theo kỳ là đạt.
            assert "QUÝ" not in str(exc.value if hasattr(exc, "value") else exc.detail), (
                "Kỳ cũ bị chặn nhầm bởi chế độ chỉ-đọc"
            )
        finally:
            await db.rollback()

        sau = (await db.execute(
            select(ChiTietXepLoai).where(ChiTietXepLoai.id == row.ct_id)
        )).scalar_one()
        assert sau.xep_loai_de_xuat == cu  # đã rollback, dữ liệu thật không đổi
