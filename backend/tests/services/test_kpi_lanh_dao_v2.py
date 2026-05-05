"""
tests/services/test_kpi_lanh_dao_v2.py
======================================
Tests cho service KPI lãnh đạo công thức mới.

Chạy:
    cd backend && source venv/bin/activate
    pytest tests/services/test_kpi_lanh_dao_v2.py -v
"""

from datetime import date
from uuid import UUID

import pytest
import pytest_asyncio
from sqlalchemy import select

from app.core.kpi_lanh_dao_v2 import (
    KPI_LANH_DAO_V2_FROM_NAM,
    KPI_LANH_DAO_V2_FROM_THANG,
    _ngay_chot_cua_thang,
    calc_kpi_lanh_dao_v2,
    get_don_vi_phu_trach,
    is_kpi_lanh_dao_v2_active,
)
from app.db.session import AsyncSessionLocal
from app.models.phan_cong_phu_trach import PhanCongPhuTrach
from app.models.user_org import CapBacVaiTro, CongChuc, DonVi, VaiTro


# =============================================================================
# PURE FUNCTION TESTS
# =============================================================================

class TestFeatureFlag:
    def test_active_at_threshold_month(self):
        assert is_kpi_lanh_dao_v2_active(
            KPI_LANH_DAO_V2_FROM_THANG, KPI_LANH_DAO_V2_FROM_NAM
        )

    def test_active_after_threshold(self):
        assert is_kpi_lanh_dao_v2_active(12, KPI_LANH_DAO_V2_FROM_NAM)
        assert is_kpi_lanh_dao_v2_active(1, KPI_LANH_DAO_V2_FROM_NAM + 1)

    def test_inactive_before_threshold(self):
        assert not is_kpi_lanh_dao_v2_active(
            KPI_LANH_DAO_V2_FROM_THANG - 1, KPI_LANH_DAO_V2_FROM_NAM
        )
        assert not is_kpi_lanh_dao_v2_active(12, KPI_LANH_DAO_V2_FROM_NAM - 1)


class TestNgayChotCuaThang:
    def test_thang_thuong(self):
        assert _ngay_chot_cua_thang(4, 2026) == date(2026, 4, 30)
        assert _ngay_chot_cua_thang(2, 2026) == date(2026, 2, 28)

    def test_thang_12(self):
        assert _ngay_chot_cua_thang(12, 2026) == date(2026, 12, 31)

    def test_nam_nhuan_2024(self):
        assert _ngay_chot_cua_thang(2, 2024) == date(2024, 2, 29)


# =============================================================================
# DB INTEGRATION TESTS
# =============================================================================

@pytest_asyncio.fixture
async def db_session():
    async with AsyncSessionLocal() as s:
        yield s


@pytest_asyncio.fixture
async def cct_user(db_session):
    """Lấy CCT có sẵn trong DB."""
    stmt = (
        select(CongChuc)
        .join(VaiTro)
        .where(VaiTro.cap_bac == CapBacVaiTro.CHI_CUC_TRUONG, CongChuc.is_active == True)
    )
    return (await db_session.execute(stmt)).scalar_one()


@pytest_asyncio.fixture
async def tdv_user(db_session):
    """Lấy 1 TDV bất kỳ có dữ liệu kê khai."""
    stmt = (
        select(CongChuc)
        .join(VaiTro)
        .where(VaiTro.ma_vai_tro == "TDV", CongChuc.is_active == True)
        .limit(1)
    )
    return (await db_session.execute(stmt)).scalar_one()


@pytest_asyncio.fixture
async def phan_cong_seed(db_session, cct_user):
    """
    Seed 1 phân công CCT phụ trách HQCK-MC, hiệu lực 2026-04-01,
    cleanup sau test.
    """
    dv = (
        await db_session.execute(select(DonVi).where(DonVi.ma_don_vi == "HQCK-MC"))
    ).scalar_one()
    pc = PhanCongPhuTrach(
        lanh_dao_id=cct_user.id,
        don_vi_id=dv.id,
        hieu_luc_tu=date(2026, 4, 1),
        ghi_chu="pytest seed",
    )
    db_session.add(pc)
    await db_session.commit()
    await db_session.refresh(pc)
    yield pc, dv
    # Cleanup
    pc.is_deleted = True
    await db_session.commit()


# -----------------------------------------------------------------------------
# get_don_vi_phu_trach
# -----------------------------------------------------------------------------

class TestGetDonViPhuTrach:
    @pytest.mark.asyncio
    async def test_no_assignment(self, db_session, cct_user):
        # Khi chưa seed, scope rỗng (loại trừ phân công đang active của test khác)
        result = await get_don_vi_phu_trach(db_session, cct_user.id, date(2025, 1, 1))
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_with_seeded_assignment(self, db_session, cct_user, phan_cong_seed):
        pc, dv = phan_cong_seed
        # Sau ngày bắt đầu
        result = await get_don_vi_phu_trach(db_session, cct_user.id, date(2026, 4, 30))
        assert dv.id in result

    @pytest.mark.asyncio
    async def test_before_effective_date(self, db_session, cct_user, phan_cong_seed):
        pc, dv = phan_cong_seed
        result = await get_don_vi_phu_trach(db_session, cct_user.id, date(2026, 3, 1))
        assert dv.id not in result


# -----------------------------------------------------------------------------
# calc_kpi_lanh_dao_v2
# -----------------------------------------------------------------------------

class TestCalcKpiLanhDaoV2:

    @pytest.mark.asyncio
    async def test_invariants_pdv(self, db_session):
        """Lấy 1 PDV bất kỳ → KPI/a/b/c/d/đ/e đều ∈ [0, 1]."""
        stmt = select(CongChuc).join(VaiTro).where(VaiTro.ma_vai_tro == "PDV").limit(1)
        pdv = (await db_session.execute(stmt)).scalar_one()
        result = await calc_kpi_lanh_dao_v2(db_session, pdv.id, 5, 2026)

        assert result["cap_bac"] == "PDV"
        for key in ("a", "b", "c", "d", "dd", "e", "kpi_tong"):
            assert 0.0 <= result[key] <= 1.0, f"{key}={result[key]}"
        assert result["tong_sp_ke_khai"] >= 0
        assert result["tong_sp_hoan_thanh"] <= result["tong_sp_ke_khai"]

    @pytest.mark.asyncio
    async def test_invariants_tdv(self, db_session, tdv_user):
        result = await calc_kpi_lanh_dao_v2(db_session, tdv_user.id, 5, 2026)
        assert result["cap_bac"] == "TDV"
        for key in ("a", "b", "c", "d", "dd", "e", "kpi_tong"):
            assert 0.0 <= result[key] <= 1.0

    @pytest.mark.asyncio
    async def test_cct_no_assignment_empty_scope(self, db_session, cct_user):
        """CCT chưa có phân công → tổng SP = 0, KPI chỉ là (d+đ+e)/6."""
        result = await calc_kpi_lanh_dao_v2(db_session, cct_user.id, 5, 2026)
        assert result["cap_bac"] == "CCT"
        assert result["has_phan_cong"] is False
        assert result["tong_sp_ke_khai"] == 0
        assert result["a"] == 0.0
        assert result["b"] == 0.0
        assert result["c"] == 0.0
        # KPI = (0+0+0+1+1+1)/6 = 0.5 nếu d/đ/e mặc định 1.0
        assert result["kpi_tong"] == pytest.approx(0.5, abs=1e-3)

    @pytest.mark.asyncio
    async def test_cct_with_assignment_has_scope(self, db_session, cct_user, phan_cong_seed):
        # Dùng tháng 4/2026 (có dataset thực) — calc function không check feature flag
        result = await calc_kpi_lanh_dao_v2(db_session, cct_user.id, 4, 2026)
        assert result["cap_bac"] == "CCT"
        assert result["has_phan_cong"] is True
        # HQCK-MC là đơn vị to nhất → tong_sp_ke_khai > 0
        assert result["tong_sp_ke_khai"] > 0

    @pytest.mark.asyncio
    async def test_is_v2_active_flag(self, db_session, tdv_user):
        result_apr = await calc_kpi_lanh_dao_v2(db_session, tdv_user.id, 5, 2026)
        assert result_apr["is_v2_active"] is True

        result_mar = await calc_kpi_lanh_dao_v2(db_session, tdv_user.id, 3, 2026)
        assert result_mar["is_v2_active"] is False

    @pytest.mark.asyncio
    async def test_reject_non_leader(self, db_session):
        """Tính KPI v2 cho 1 CC thường → ValueError."""
        stmt = select(CongChuc).join(VaiTro).where(VaiTro.ma_vai_tro == "CC").limit(1)
        cc = (await db_session.execute(stmt)).scalar_one()
        with pytest.raises(ValueError):
            await calc_kpi_lanh_dao_v2(db_session, cc.id, 5, 2026)
