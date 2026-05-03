"""
tests/integration/test_kekhai_v2_flow.py
=========================================
Integration tests cho luồng kê khai V2 (PL3).

Pattern: mỗi test mở AsyncSession riêng (không share fixture session)
để tránh "another operation in progress" của asyncpg.

Test scope:
- Snapshot immutable: kê khai cũ KHÔNG bị ảnh hưởng khi admin sửa danh mục.
- Mẫu số = 0: KPI = 0 với ly_do='MAU_SO_BANG_0'.
- Tính KPI realistic: 3 kê khai V2 với hệ số khác nhau.
- V1 dispatcher giữ nguyên hành vi V1.
"""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID

import pytest
from sqlalchemy import select, text

from app.api.v1.endpoints.xep_loai_moi import tinh_diem_kpi_70, tinh_diem_kpi_70_v2
from app.core.kpi_calculator_v2 import calculate_so_sp_goc_quy_doi_v2
from app.db.session import AsyncSessionLocal
from app.models.kpi_submission import KeKhaiCongViec, TrangThaiKeKhai
from app.models.task_catalog import DanhMucSpCongViec


# Test month chọn xa data thực để cleanup an toàn
TEST_THANG = 11
TEST_NAM = 2026


# =============================================================================
# Helpers
# =============================================================================

async def _pick_test_cc(db) -> tuple[UUID, UUID]:
    """Lấy 1 CC bình thường có don_vi_id."""
    row = (await db.execute(text("""
        SELECT cc.id, cc.don_vi_id
        FROM cong_chuc cc
        JOIN vai_tro vt ON cc.vai_tro_id = vt.id
        WHERE vt.ma_vai_tro IN ('CONG_CHUC', 'CC')
          AND cc.is_active = true
          AND cc.is_deleted = false
        LIMIT 1
    """))).first()
    assert row, "Không tìm thấy CC test"
    return row[0], row[1]


async def _cleanup_kk(db, cong_chuc_id: UUID, thang: int, nam: int) -> None:
    await db.execute(text("""
        DELETE FROM phe_duyet_sp
        WHERE ke_khai_id IN (
            SELECT id FROM ke_khai_cong_viec
            WHERE cong_chuc_id = :cc AND thang = :thang AND nam = :nam
        )
    """), {"cc": str(cong_chuc_id), "thang": thang, "nam": nam})
    await db.execute(text("""
        DELETE FROM ke_khai_cong_viec
        WHERE cong_chuc_id = :cc AND thang = :thang AND nam = :nam
    """), {"cc": str(cong_chuc_id), "thang": thang, "nam": nam})
    await db.execute(text("""
        DELETE FROM danh_gia_thang
        WHERE cong_chuc_id = :cc AND thang = :thang AND nam = :nam
    """), {"cc": str(cong_chuc_id), "thang": thang, "nam": nam})
    await db.commit()


# =============================================================================
# Tests
# =============================================================================

@pytest.mark.asyncio
async def test_snapshot_immutable_when_admin_changes_danh_muc():
    """
    Tạo kê khai V2 với mục PL3 he_so=X. Admin sửa he_so danh mục thành Y.
    Tính KPI tháng → vẫn dùng snapshot X.
    """
    async with AsyncSessionLocal() as db:
        cc_id, don_vi_id = await _pick_test_cc(db)
        await _cleanup_kk(db, cc_id, TEST_THANG, TEST_NAM)

        dm = (await db.execute(
            select(DanhMucSpCongViec)
            .where(DanhMucSpCongViec.nguon_du_lieu == "PL3")
            .where(DanhMucSpCongViec.is_active == True)  # noqa: E712
            .limit(1)
        )).scalar_one()
        he_so_goc = dm.he_so_quy_doi
        diem_cham_goc = dm.diem_cham
        so_luong = 5
        so_sp_goc_expected = calculate_so_sp_goc_quy_doi_v2(so_luong, he_so_goc)

        kk = KeKhaiCongViec(
            cong_chuc_id=cc_id,
            don_vi_id_snapshot=don_vi_id,
            thang=TEST_THANG,
            nam=TEST_NAM,
            danh_muc_sp_id=dm.id,
            cap_do_id=None,
            so_luong=so_luong,
            nguoi_phe_duyet_id=cc_id,
            trang_thai=TrangThaiKeKhai.DA_PHE_DUYET,
            so_sp_goc_quy_doi=so_sp_goc_expected,
            so_sp_chat_luong=so_sp_goc_expected,
            so_sp_tien_do=so_sp_goc_expected,
            version_kekhai="V2_PL3",
            he_so_quy_doi_snapshot=he_so_goc,
            nhom_pl3_snapshot=dm.nhom_pl3,
            linh_vuc_snapshot=dm.linh_vuc,
            tu_danh_gia_chat_luong=0,
            tu_danh_gia_tien_do=0,
            is_doi_moi_sang_tao=False,
        )
        db.add(kk)
        await db.commit()

        try:
            result1 = await tinh_diem_kpi_70_v2(db, cc_id, TEST_THANG, TEST_NAM)
            assert abs(result1["tong_sp_ke_khai"] - float(so_sp_goc_expected)) < 1e-4

            # Admin "sửa" danh mục
            new_he_so = he_so_goc + Decimal("100")
            new_diem_cham = diem_cham_goc + 50
            await db.execute(text("""
                UPDATE danh_muc_sp_cong_viec
                SET he_so_quy_doi = :he_so, diem_cham = :dc
                WHERE id = :id
            """), {"he_so": new_he_so, "dc": new_diem_cham, "id": str(dm.id)})
            await db.commit()

            result2 = await tinh_diem_kpi_70_v2(db, cc_id, TEST_THANG, TEST_NAM)
            assert abs(result2["tong_sp_ke_khai"] - float(so_sp_goc_expected)) < 1e-4, \
                f"Snapshot bị broken: expected {so_sp_goc_expected}, got {result2['tong_sp_ke_khai']}"
        finally:
            # Restore danh mục
            await db.execute(text("""
                UPDATE danh_muc_sp_cong_viec
                SET he_so_quy_doi = :he_so, diem_cham = :dc
                WHERE id = :id
            """), {"he_so": he_so_goc, "dc": diem_cham_goc, "id": str(dm.id)})
            await db.commit()
            await _cleanup_kk(db, cc_id, TEST_THANG, TEST_NAM)


@pytest.mark.asyncio
async def test_mau_so_zero_returns_kpi_zero():
    """CC chưa kê khai gì → mẫu số = 0 → KPI = 0, ly_do='MAU_SO_BANG_0'."""
    async with AsyncSessionLocal() as db:
        cc_id, _ = await _pick_test_cc(db)
        thang_xa = 10
        nam_xa = 2027
        await _cleanup_kk(db, cc_id, thang_xa, nam_xa)

        result = await tinh_diem_kpi_70_v2(db, cc_id, thang_xa, nam_xa)
        assert result["tong_sp_ke_khai"] == 0.0
        assert result["diem_kpi"] == 0.0
        assert result["diem_70"] == 0.0
        assert result["ly_do_kpi_zero"] == "MAU_SO_BANG_0"


@pytest.mark.asyncio
async def test_realistic_v2_kpi_with_3_kekhai():
    """3 kê khai V2 hệ số khác nhau, không lỗi → kpi=1.0, diem_70=70.0."""
    async with AsyncSessionLocal() as db:
        cc_id, don_vi_id = await _pick_test_cc(db)
        await _cleanup_kk(db, cc_id, TEST_THANG, TEST_NAM)

        try:
            dm1 = (await db.execute(
                select(DanhMucSpCongViec)
                .where(DanhMucSpCongViec.nguon_du_lieu == "PL3")
                .where(DanhMucSpCongViec.nhom_pl3 == 1)
                .limit(1)
            )).scalar_one()
            dm2 = (await db.execute(
                select(DanhMucSpCongViec)
                .where(DanhMucSpCongViec.nguon_du_lieu == "PL3")
                .where(DanhMucSpCongViec.nhom_pl3 == 2)
                .limit(1)
            )).scalar_one()
            dm3 = (await db.execute(
                select(DanhMucSpCongViec)
                .where(DanhMucSpCongViec.nguon_du_lieu == "PL3")
                .where(DanhMucSpCongViec.nhom_pl3 == 3)
                .limit(1)
            )).scalar_one()

            sl1, sl2, sl3 = 2, 1, 1
            sp1 = calculate_so_sp_goc_quy_doi_v2(sl1, dm1.he_so_quy_doi)
            sp2 = calculate_so_sp_goc_quy_doi_v2(sl2, dm2.he_so_quy_doi)
            sp3 = calculate_so_sp_goc_quy_doi_v2(sl3, dm3.he_so_quy_doi)
            tong_expected = sp1 + sp2 + sp3

            for dm, sl, sp in [(dm1, sl1, sp1), (dm2, sl2, sp2), (dm3, sl3, sp3)]:
                kk = KeKhaiCongViec(
                    cong_chuc_id=cc_id,
                    don_vi_id_snapshot=don_vi_id,
                    thang=TEST_THANG,
                    nam=TEST_NAM,
                    danh_muc_sp_id=dm.id,
                    cap_do_id=None,
                    so_luong=sl,
                    nguoi_phe_duyet_id=cc_id,
                    trang_thai=TrangThaiKeKhai.DA_PHE_DUYET,
                    so_sp_goc_quy_doi=sp,
                    so_sp_chat_luong=sp,
                    so_sp_tien_do=sp,
                    version_kekhai="V2_PL3",
                    he_so_quy_doi_snapshot=dm.he_so_quy_doi,
                    nhom_pl3_snapshot=dm.nhom_pl3,
                    linh_vuc_snapshot=dm.linh_vuc,
                    tu_danh_gia_chat_luong=0,
                    tu_danh_gia_tien_do=0,
                    is_doi_moi_sang_tao=False,
                )
                db.add(kk)
            await db.commit()

            result = await tinh_diem_kpi_70_v2(db, cc_id, TEST_THANG, TEST_NAM)
            assert abs(result["tong_sp_ke_khai"] - float(tong_expected)) < 1e-4
            assert result["a_so_luong"] == 1.0
            assert result["b_chat_luong"] == 1.0
            assert result["c_tien_do"] == 1.0
            assert result["diem_kpi"] == 1.0
            assert result["diem_70"] == 70.0
            assert result["ly_do_kpi_zero"] is None
        finally:
            await _cleanup_kk(db, cc_id, TEST_THANG, TEST_NAM)


@pytest.mark.asyncio
async def test_v1_dispatcher_returns_v1_result():
    """CC có data V1 → dispatcher trả V1 result (KHÔNG chạy V2)."""
    async with AsyncSessionLocal() as db:
        row = (await db.execute(text("""
            SELECT cc.id, kk.thang, kk.nam
            FROM ke_khai_cong_viec kk
            JOIN cong_chuc cc ON kk.cong_chuc_id = cc.id
            WHERE kk.version_kekhai = 'V1' AND kk.trang_thai = 'DA_PHE_DUYET'
              AND kk.is_deleted = false AND cc.is_active = true
              AND COALESCE(cc.is_lanh_dao, false) = false
            GROUP BY cc.id, kk.thang, kk.nam
            HAVING COUNT(*) >= 3
            LIMIT 1
        """))).first()
        if not row:
            pytest.skip("Không có CC nào có V1 data")

        result = await tinh_diem_kpi_70(db, row[0], row[1], row[2])
        # V1 result KHÔNG có key 'version_tinh_diem' (chỉ V2 có)
        assert "version_tinh_diem" not in result
        assert "so_ngay_lam_viec" in result
        assert "sp_duoc_giao" in result
