"""
tests/integration/test_bo_ke_khai_lai_dd.py
===========================================
Gỡ tính năng "kê khai lại tiêu chí đ cấp quý" (quyết định 29/09/2026).

Chạy trên kpi_haiquan_test — TUYỆT ĐỐI KHÔNG chạy trên kpi_haiquan (prod):
    DB_NAME=kpi_haiquan_test pytest tests/integration/test_bo_ke_khai_lai_dd.py -v

Toàn bộ test dưới đây CHỈ ĐỌC.

Miếng vá này sinh ra để chữa chuyện MIN ba tháng kéo cả quý xuống 50%. Từ Q3/2026
d/đ/e kê một lần cho cả quý nên không còn MIN, miếng vá thành thừa.

Phạm vi CỐ Ý HẸP — gỡ KHÔNG hồi tố:
1. API không còn nhận `dd_quy_ke_khai` / `dd_quy_ghi_chu` / `dd_quy_phe_duyet`.
2. Kỳ TỪ Q3/2026: điểm quý KHÔNG còn bị miếng vá nâng lên.
3. Kỳ TRƯỚC Q3/2026: điểm giữ NGUYÊN — gỡ hồi tố sẽ làm 20ZZ-0084 tụt A xuống B.
"""

from __future__ import annotations

import pytest
from sqlalchemy import text

from app.api.v1.endpoints.xep_loai_quy_helpers import tinh_diem_quy
from app.core.ky_tieu_chi import DDE_THEO_QUY_TU
from app.db.session import AsyncSessionLocal
from app.schemas.phieu_danh_gia import PheDuyetPhieuRequest, UpsertPhieuQuyRequest


# =============================================================================
# 1. API không còn nhận trường nào của miếng vá
# =============================================================================

def test_schema_khong_con_truong_dd_quy():
    for truong in ("dd_quy_ke_khai", "dd_quy_ghi_chu"):
        assert truong not in UpsertPhieuQuyRequest.model_fields, (
            f"UpsertPhieuQuyRequest vẫn còn {truong}"
        )
    assert "dd_quy_phe_duyet" not in PheDuyetPhieuRequest.model_fields


def test_gui_truong_da_go_thi_bi_bo_qua():
    """Client cũ còn gửi trường này lên thì phải bị bỏ qua, không được lưu."""
    req = UpsertPhieuQuyRequest(
        quy=3, nam=2026, uu_diem="x", dd_quy_ke_khai=100, dd_quy_ghi_chu="y"
    )
    assert not hasattr(req, "dd_quy_ke_khai")
    assert not hasattr(req, "dd_quy_ghi_chu")


# =============================================================================
# 2. Kỳ TỪ mốc — miếng vá không còn tác dụng
# =============================================================================

@pytest.mark.asyncio
async def test_tu_moc_tro_di_khong_con_ap_mieng_va():
    """
    Lấy người CÓ kê khai lại đ ở kỳ ≥ mốc, đối chiếu đ của điểm quý với giá trị
    trên phiếu d/đ/e quý. Hai số phải khớp — tức miếng vá không xen vào nữa.
    """
    nam_moc, quy_moc = DDE_THEO_QUY_TU
    async with AsyncSessionLocal() as db:
        rows = (await db.execute(text("""
            SELECT p.cong_chuc_id, p.quy, p.nam
            FROM phieu_danh_gia_quy p
            WHERE (p.dd_quy_ke_khai IS NOT NULL OR p.dd_quy_phe_duyet IS NOT NULL)
              AND (p.nam > :nam OR (p.nam = :nam AND p.quy >= :quy))
        """), {"nam": nam_moc, "quy": quy_moc})).all()
        if not rows:
            pytest.skip("DB test không có phiếu nào kê khai lại đ ở kỳ từ mốc")

        for cc_id, quy, nam in rows:
            kq = await tinh_diem_quy(db, cc_id, quy, nam, tam_tinh=True)
            if kq is None or not kq.get("is_lanh_dao"):
                continue

            thang_neo = quy * 3
            dd_phieu = (await db.execute(text("""
                SELECT COALESCE(dd_phe_duyet, dd_to_chuc_trien_khai)
                FROM danh_gia_dde
                WHERE cong_chuc_id = :c AND nam = :n AND thang = :t
                  AND trang_thai = 'DA_PHE_DUYET'
            """), {"c": cc_id, "n": nam, "t": thang_neo})).scalar()
            mong_doi = float(dd_phieu) / 100 if dd_phieu is not None else 1.0

            assert kq["dd_to_chuc"] == mong_doi, (
                f"CC {cc_id} quý {quy}/{nam}: đ = {kq['dd_to_chuc']} nhưng phiếu "
                f"d/đ/e quý ghi {mong_doi} — miếng vá vẫn còn tác dụng"
            )


# =============================================================================
# 3. Kỳ TRƯỚC mốc — điểm giữ nguyên
# =============================================================================

@pytest.mark.asyncio
async def test_truoc_moc_van_giu_mieng_va():
    """
    Người kê khai lại đ ở kỳ trước mốc mà MIN ba tháng thấp hơn thì đ của điểm
    quý phải vẫn bằng giá trị kê khai lại — nếu không, họ bị tụt điểm hồi tố.
    """
    nam_moc, quy_moc = DDE_THEO_QUY_TU
    async with AsyncSessionLocal() as db:
        rows = (await db.execute(text("""
            SELECT p.cong_chuc_id, p.quy, p.nam,
                   COALESCE(p.dd_quy_phe_duyet, p.dd_quy_ke_khai) AS dd_ke_khai,
                   p.trang_thai
            FROM phieu_danh_gia_quy p
            WHERE COALESCE(p.dd_quy_phe_duyet, p.dd_quy_ke_khai) IS NOT NULL
              AND (p.nam < :nam OR (p.nam = :nam AND p.quy < :quy))
              AND p.trang_thai IN ('CHO_PHE_DUYET', 'DA_PHE_DUYET')
        """), {"nam": nam_moc, "quy": quy_moc})).all()
        if not rows:
            pytest.skip("DB test không có phiếu kê khai lại đ ở kỳ trước mốc")

        da_kiem = 0
        for cc_id, quy, nam, dd_ke_khai, _ in rows:
            kq = await tinh_diem_quy(db, cc_id, quy, nam, tam_tinh=True)
            if kq is None or not kq.get("is_lanh_dao"):
                continue

            dd_min = (await db.execute(text("""
                SELECT MIN(COALESCE(dd_phe_duyet, dd_to_chuc_trien_khai))
                FROM danh_gia_dde
                WHERE cong_chuc_id = :c AND nam = :n
                  AND thang BETWEEN :t1 AND :t2 AND trang_thai = 'DA_PHE_DUYET'
            """), {"c": cc_id, "n": nam, "t1": (quy - 1) * 3 + 1, "t2": quy * 3})).scalar()
            min_val = float(dd_min) / 100 if dd_min is not None else 1.0
            mong_doi = max(min_val, float(dd_ke_khai) / 100)

            assert kq["dd_to_chuc"] == mong_doi, (
                f"CC {cc_id} quý {quy}/{nam}: đ = {kq['dd_to_chuc']}, đáng lẽ "
                f"{mong_doi} (MIN {min_val}, kê khai lại {float(dd_ke_khai)/100}) "
                f"— kỳ trước mốc KHÔNG được đổi điểm"
            )
            da_kiem += 1

        assert da_kiem > 0, "Không kiểm được ca nào ở kỳ trước mốc"
