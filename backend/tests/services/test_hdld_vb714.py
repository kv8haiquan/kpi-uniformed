"""
tests/services/test_hdld_vb714.py
=================================
Tests cho Bộ tiêu chí đánh giá HĐLĐ 111 theo VB714 (QĐ 714/QĐ-CHQ).

Chạy:
    cd backend && venv/bin/pytest tests/services/test_hdld_vb714.py -v

Chỉ test hàm thuần + validator schema (KHÔNG ghi DB production).
"""
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.core.hdld_vb714 import (
    HDLD_VB714_FROM_NAM,
    HDLD_VB714_FROM_THANG,
    is_hdld_vb714_active,
    tb_3_tieu_chi,
    kpi_70_tu_tb,
)
from app.schemas.hdld import (
    HdldTuDanhGiaRequest,
    HdldChiTietTuDanhGia,
    HdldDuyetRequest,
    HdldChiTietDuyet,
)


# ===================== FEATURE FLAG (mốc T5/2026) ===================== #

class TestFeatureFlag:
    def test_active_tai_moc(self):
        assert is_hdld_vb714_active(HDLD_VB714_FROM_THANG, HDLD_VB714_FROM_NAM)

    def test_active_sau_moc(self):
        assert is_hdld_vb714_active(6, 2026)
        assert is_hdld_vb714_active(1, 2027)

    def test_khong_active_truoc_moc(self):
        assert not is_hdld_vb714_active(4, 2026)
        assert not is_hdld_vb714_active(12, 2025)


# ===================== CÔNG THỨC ĐIỂM ===================== #

class TestCongThuc:
    def test_tb_3_tieu_chi_du(self):
        assert tb_3_tieu_chi([Decimal("100"), Decimal("80"), Decimal("90")]) == Decimal("90.00")

    def test_tb_thieu_diem_tra_none(self):
        assert tb_3_tieu_chi([Decimal("100"), None, Decimal("90")]) is None
        assert tb_3_tieu_chi([Decimal("100"), Decimal("90")]) is None

    def test_kpi_70_tu_tb(self):
        assert kpi_70_tu_tb(Decimal("100")) == Decimal("70.00")
        assert kpi_70_tu_tb(Decimal("90")) == Decimal("63.00")
        assert kpi_70_tu_tb(Decimal("0")) == Decimal("0.00")

    def test_kpi_70_none(self):
        assert kpi_70_tu_tb(None) is None

    def test_full_chain_85(self):
        tb = tb_3_tieu_chi([Decimal("85"), Decimal("85"), Decimal("85")])
        assert tb == Decimal("85.00")
        assert kpi_70_tu_tb(tb) == Decimal("59.50")


# ===================== VALIDATOR: TỰ ĐÁNH GIÁ ===================== #

class TestTuDanhGiaValidator:
    def _ct(self, sott, diem, ghi_chu=None):
        return HdldChiTietTuDanhGia(so_tt=sott, diem_tu=Decimal(str(diem)), ghi_chu_tu=ghi_chu)

    def test_hop_le_100(self):
        req = HdldTuDanhGiaRequest(
            nhom_nghe="I",
            chi_tiets=[self._ct(1, 100), self._ct(2, 100), self._ct(3, 100)],
        )
        assert req.nhom_nghe == "I"

    def test_duoi_100_phai_ghi_chu(self):
        with pytest.raises(ValidationError, match="ghi chú"):
            HdldTuDanhGiaRequest(
                nhom_nghe="II",
                chi_tiets=[self._ct(1, 80), self._ct(2, 100), self._ct(3, 100)],
            )

    def test_duoi_100_co_ghi_chu_ok(self):
        req = HdldTuDanhGiaRequest(
            nhom_nghe="II",
            chi_tiets=[self._ct(1, 80, "Có sự cố tháng này"), self._ct(2, 100), self._ct(3, 100)],
        )
        assert req.chi_tiets[0].diem_tu == Decimal("80")

    def test_nhom_khong_hop_le(self):
        with pytest.raises(ValidationError):
            HdldTuDanhGiaRequest(
                nhom_nghe="VII",
                chi_tiets=[self._ct(1, 100), self._ct(2, 100), self._ct(3, 100)],
            )

    def test_thieu_tieu_chi(self):
        with pytest.raises(ValidationError, match="đủ 3 tiêu chí"):
            HdldTuDanhGiaRequest(
                nhom_nghe="I",
                chi_tiets=[self._ct(1, 100), self._ct(1, 100), self._ct(3, 100)],
            )

    def test_diem_ngoai_khoang(self):
        with pytest.raises(ValidationError):
            HdldChiTietTuDanhGia(so_tt=1, diem_tu=Decimal("120"))


# ===================== VALIDATOR: DUYỆT ===================== #

class TestDuyetValidator:
    def test_du_3_tieu_chi(self):
        req = HdldDuyetRequest(chi_tiets=[
            HdldChiTietDuyet(so_tt=1, diem_ql=Decimal("90")),
            HdldChiTietDuyet(so_tt=2, diem_ql=Decimal("90")),
            HdldChiTietDuyet(so_tt=3, diem_ql=Decimal("90")),
        ])
        assert len(req.chi_tiets) == 3

    def test_thieu_tieu_chi(self):
        with pytest.raises(ValidationError):
            HdldDuyetRequest(chi_tiets=[
                HdldChiTietDuyet(so_tt=1, diem_ql=Decimal("90")),
                HdldChiTietDuyet(so_tt=2, diem_ql=Decimal("90")),
            ])
