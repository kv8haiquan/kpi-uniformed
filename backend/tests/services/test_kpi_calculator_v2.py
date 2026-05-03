"""
tests/test_kpi_calculator_v2.py
================================
Unit tests cho kpi_calculator_v2.

Chạy:
    cd backend && source venv/bin/activate
    pytest tests/test_kpi_calculator_v2.py -v
"""

from decimal import Decimal

import pytest

from app.core.kpi_calculator_v2 import (
    calculate_so_sp_goc_quy_doi_v2,
    calculate_sp_dat_v2,
    calculate_kpi_score_v2,
)


# =============================================================================
# calculate_so_sp_goc_quy_doi_v2
# =============================================================================

class TestCalculateSoSpGocQuyDoiV2:
    def test_basic(self):
        assert calculate_so_sp_goc_quy_doi_v2(5, Decimal("8")) == Decimal("40")

    def test_decimal_he_so(self):
        # 5 × 6.4 = 32 (đặc trưng PL3 nhóm 2)
        assert calculate_so_sp_goc_quy_doi_v2(5, Decimal("6.4")) == Decimal("32.0")

    def test_he_so_thap_phan_chinh_xac(self):
        # 3 × 9.2 = 27.6
        assert calculate_so_sp_goc_quy_doi_v2(3, Decimal("9.2")) == Decimal("27.6")

    def test_so_luong_zero_raises(self):
        with pytest.raises(ValueError):
            calculate_so_sp_goc_quy_doi_v2(0, Decimal("1"))

    def test_so_luong_negative_raises(self):
        with pytest.raises(ValueError):
            calculate_so_sp_goc_quy_doi_v2(-1, Decimal("1"))

    def test_he_so_zero_raises(self):
        with pytest.raises(ValueError):
            calculate_so_sp_goc_quy_doi_v2(5, Decimal("0"))


# =============================================================================
# calculate_sp_dat_v2
# =============================================================================

class TestCalculateSpDatV2:
    def test_no_loi(self):
        # so_luong=5, he_so=8, loi=0 → sp_dat = 8 × 5 = 40
        assert calculate_sp_dat_v2(5, Decimal("8"), 0) == Decimal("40")

    def test_decimal_he_so_with_loi(self):
        # so_luong=5, he_so=6.4, loi=3
        # max_loi = 20, loi_tinh = 3
        # factor = 5 - 0.25 × 3 = 5 - 0.75 = 4.25
        # sp_dat = 6.4 × 4.25 = 27.2
        result = calculate_sp_dat_v2(5, Decimal("6.4"), 3)
        assert result == Decimal("27.200")

    def test_loi_capped_at_so_luong_x_4(self):
        # so_luong=5, he_so=8, loi=20 → loi cap ở 5×4=20, factor=0, sp_dat=0
        assert calculate_sp_dat_v2(5, Decimal("8"), 20) == Decimal("0")

    def test_loi_exceed_cap(self):
        # so_luong=5, he_so=8, loi=100 → vẫn cap ở 20, sp_dat=0
        assert calculate_sp_dat_v2(5, Decimal("8"), 100) == Decimal("0")

    def test_so_luong_1_he_so_20_loi_3(self):
        # max_loi = 4, loi_tinh = 3
        # factor = 1 - 0.25 × 3 = 0.25
        # sp_dat = 20 × 0.25 = 5
        assert calculate_sp_dat_v2(1, Decimal("20"), 3) == Decimal("5.00")

    def test_loi_negative_treated_as_zero(self):
        assert calculate_sp_dat_v2(5, Decimal("8"), -3) == Decimal("40")

    def test_so_luong_zero_returns_zero(self):
        assert calculate_sp_dat_v2(0, Decimal("8"), 1) == Decimal("0")

    def test_he_so_zero_returns_zero(self):
        assert calculate_sp_dat_v2(5, Decimal("0"), 0) == Decimal("0")

    def test_full_loi_at_max(self):
        # so_luong=2, he_so=10, loi=8 (max 2×4=8)
        # factor = 2 - 0.25 × 8 = 0
        assert calculate_sp_dat_v2(2, Decimal("10"), 8) == Decimal("0")

    def test_partial_loi_decimal(self):
        # so_luong=10, he_so=4.04, loi=5
        # max_loi=40, loi_tinh=5
        # factor = 10 - 1.25 = 8.75
        # sp_dat = 4.04 × 8.75 = 35.35
        result = calculate_sp_dat_v2(10, Decimal("4.04"), 5)
        assert result == Decimal("35.3500")


# =============================================================================
# calculate_kpi_score_v2
# =============================================================================

class TestCalculateKpiScoreV2:
    def test_perfect_score(self):
        # mọi tử số = mẫu số → a=b=c=1, kpi=1
        result = calculate_kpi_score_v2(
            Decimal("100"), Decimal("100"), Decimal("100"), Decimal("100")
        )
        assert result["a"] == Decimal("1")
        assert result["b"] == Decimal("1")
        assert result["c"] == Decimal("1")
        assert result["kpi"] == Decimal("1")
        assert result["ly_do"] is None

    def test_zero_mau_so_returns_zero_with_ly_do(self):
        # LOCKED 5: mẫu số = 0 → kpi = 0, ly_do = MAU_SO_BANG_0
        result = calculate_kpi_score_v2(
            Decimal("0"), Decimal("0"), Decimal("0"), Decimal("0")
        )
        assert result["a"] == Decimal("0")
        assert result["b"] == Decimal("0")
        assert result["c"] == Decimal("0")
        assert result["kpi"] == Decimal("0")
        assert result["ly_do"] == "MAU_SO_BANG_0"

    def test_partial_quality_loss(self):
        # 100 SP kê khai, 100 hoàn thành, 80 đạt CL, 100 đạt TĐ
        # a=1.0, b=0.8, c=1.0 → kpi = 2.8/3 ≈ 0.9333
        result = calculate_kpi_score_v2(
            Decimal("100"), Decimal("80"), Decimal("100"), Decimal("100")
        )
        assert result["a"] == Decimal("1")
        assert result["b"] == Decimal("0.8")
        assert result["c"] == Decimal("1")
        # kpi = (1 + 0.8 + 1) / 3 = 0.9333...
        expected_kpi = Decimal("2.8") / Decimal("3")
        assert result["kpi"] == expected_kpi

    def test_decimal_mau_so(self):
        # 27.2 SP kê khai → mẫu số thập phân
        result = calculate_kpi_score_v2(
            Decimal("27.2"), Decimal("27.2"), Decimal("27.2"), Decimal("27.2")
        )
        assert result["a"] == Decimal("1")
        assert result["kpi"] == Decimal("1")

    def test_cap_at_one_defensive(self):
        # Edge: tử số > mẫu số (không nên xảy ra) → cap về 1
        result = calculate_kpi_score_v2(
            Decimal("150"), Decimal("100"), Decimal("100"), Decimal("100")
        )
        assert result["a"] == Decimal("1")  # cap ≤ 1
        assert result["b"] == Decimal("1")
        assert result["c"] == Decimal("1")
        assert result["kpi"] == Decimal("1")

    def test_realistic_pl3_scenario(self):
        # CC kê khai 3 mục PL3:
        #   Mục 1: nhóm 1, he_so=3.0, sl=2 → sp_goc = 6.0
        #   Mục 2: nhóm 2, he_so=6.4, sl=1 → sp_goc = 6.4
        #   Mục 3: nhóm 3, he_so=11.2, sl=1 → sp_goc = 11.2
        # Tổng mẫu số = 23.6
        # Giả sử mục 2 có 1 lỗi CL → sp_dat_cl(mục 2) = 6.4 × (1 - 0.25) = 4.8
        # Tổng đạt CL = 6.0 + 4.8 + 11.2 = 22.0
        # Tổng đạt TĐ = 6.0 + 6.4 + 11.2 = 23.6
        # Tổng hoàn thành (đã duyệt) = 23.6
        result = calculate_kpi_score_v2(
            tong_sp_hoan_thanh_quy_doi=Decimal("23.6"),
            tong_sp_dat_cl_quy_doi=Decimal("22.0"),
            tong_sp_dat_td_quy_doi=Decimal("23.6"),
            tong_sp_ke_khai=Decimal("23.6"),
        )
        assert result["a"] == Decimal("1")
        # b = 22.0 / 23.6 ≈ 0.9322
        expected_b = Decimal("22.0") / Decimal("23.6")
        assert result["b"] == expected_b
        assert result["c"] == Decimal("1")

    def test_negative_mau_so_treated_as_zero(self):
        # Defensive: mẫu số âm (không hợp lệ) → trả về 0
        result = calculate_kpi_score_v2(
            Decimal("100"), Decimal("100"), Decimal("100"), Decimal("-1")
        )
        assert result["ly_do"] == "MAU_SO_BANG_0"
        assert result["kpi"] == Decimal("0")
