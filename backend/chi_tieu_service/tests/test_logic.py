"""
chi_tieu_service/tests/test_logic.py
====================================
Unit test logic THUAN (khong DB): state machine + cong thuc tinh.
Day la phan nghiep vu cot loi — chay duoc moi noi, KHONG dung production DB.

Chay: pytest chi_tieu_service/tests/test_logic.py -v
"""

import sys
import os
from decimal import Decimal

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import pytest

from chi_tieu_service.constants import (
    DUYET_TRANSITION, HANH_DONG_DUYET, HANH_DONG_TU_CHOI, HanhDong,
    LOAI_CHO_DUYET, TU_CHOI_TRANSITION, TrangThai,
    tinh_dat_phan_tram, tinh_nhan_danh_gia_tu_dong,
)


# =========================================================================
# STATE MACHINE — DUYET
# =========================================================================
class TestDuyetTransition:
    def test_duyet_dang_ky(self):
        assert DUYET_TRANSITION[TrangThai.CHO_DUYET_DANG_KY] == TrangThai.DA_DUYET_DANG_KY

    def test_duyet_sua_ve_da_duyet_dang_ky(self):
        assert DUYET_TRANSITION[TrangThai.CHO_DUYET_SUA] == TrangThai.DA_DUYET_DANG_KY

    def test_duyet_ket_qua_chot(self):
        assert DUYET_TRANSITION[TrangThai.CHO_DUYET_KET_QUA] == TrangThai.DA_DUYET_KET_QUA

    def test_chi_duyet_duoc_3_trang_thai_cho(self):
        assert set(DUYET_TRANSITION.keys()) == {
            TrangThai.CHO_DUYET_DANG_KY, TrangThai.CHO_DUYET_SUA, TrangThai.CHO_DUYET_KET_QUA,
        }

    def test_khong_duyet_duoc_trang_thai_nhap(self):
        assert TrangThai.NHAP not in DUYET_TRANSITION

    def test_khong_duyet_duoc_da_chot(self):
        assert TrangThai.DA_DUYET_KET_QUA not in DUYET_TRANSITION


# =========================================================================
# STATE MACHINE — TU CHOI (diem 4 da chot voi user)
# =========================================================================
class TestTuChoiTransition:
    def test_tu_choi_dang_ky_lan_dau_ve_nhap(self):
        # Dang ky chua tung duyet -> ve NHAP
        assert TU_CHOI_TRANSITION[TrangThai.CHO_DUYET_DANG_KY] == TrangThai.NHAP

    def test_tu_choi_sua_ve_da_duyet_dang_ky(self):
        # Huy yeu cau sua, giu ban ghi cu
        assert TU_CHOI_TRANSITION[TrangThai.CHO_DUYET_SUA] == TrangThai.DA_DUYET_DANG_KY

    def test_tu_choi_ket_qua_ve_da_duyet_dang_ky(self):
        # KHONG ve NHAP (giu dang ky da duyet) — nhap lai ket qua
        assert TU_CHOI_TRANSITION[TrangThai.CHO_DUYET_KET_QUA] == TrangThai.DA_DUYET_DANG_KY

    def test_tu_choi_phu_3_trang_thai_cho(self):
        assert set(TU_CHOI_TRANSITION.keys()) == set(DUYET_TRANSITION.keys())


# =========================================================================
# MAP HANH DONG / LOAI CHO DUYET
# =========================================================================
class TestMappings:
    def test_loai_cho_duyet(self):
        assert LOAI_CHO_DUYET["DANG_KY"] == TrangThai.CHO_DUYET_DANG_KY
        assert LOAI_CHO_DUYET["SUA"] == TrangThai.CHO_DUYET_SUA
        assert LOAI_CHO_DUYET["KET_QUA"] == TrangThai.CHO_DUYET_KET_QUA

    def test_hanh_dong_duyet_phu_het(self):
        assert set(HANH_DONG_DUYET.keys()) == set(DUYET_TRANSITION.keys())
        assert HANH_DONG_DUYET[TrangThai.CHO_DUYET_KET_QUA] == HanhDong.DUYET_KET_QUA

    def test_hanh_dong_tu_choi_phu_het(self):
        assert set(HANH_DONG_TU_CHOI.keys()) == set(TU_CHOI_TRANSITION.keys())
        assert HANH_DONG_TU_CHOI[TrangThai.CHO_DUYET_KET_QUA] == HanhDong.TU_CHOI_KET_QUA


# =========================================================================
# CONG THUC — Dat% thang
# =========================================================================
class TestTinhDatPhanTram:
    def test_co_ban(self):
        assert tinh_dat_phan_tram(Decimal("150"), Decimal("100")) == Decimal("150.00")

    def test_vuot(self):
        assert tinh_dat_phan_tram(Decimal("684"), Decimal("482")) == Decimal("141.91")

    def test_ket_qua_none(self):
        assert tinh_dat_phan_tram(None, Decimal("100")) is None

    def test_dang_ky_none(self):
        assert tinh_dat_phan_tram(Decimal("100"), None) is None

    def test_dang_ky_zero(self):
        # Khong chia cho 0
        assert tinh_dat_phan_tram(Decimal("100"), Decimal("0")) is None

    def test_ket_qua_zero(self):
        assert tinh_dat_phan_tram(Decimal("0"), Decimal("100")) == Decimal("0.00")


# =========================================================================
# CONG THUC — Nhan danh gia tu dong (diem 6)
# =========================================================================
class TestNhanDanhGia:
    def test_khong_dang_ky(self):
        assert tinh_nhan_danh_gia_tu_dong(True, None, None) == "Khong dang ky"

    def test_khong_dang_ky_uu_tien_hon_ket_qua(self):
        # khong_dang_ky=True luon thang
        assert tinh_nhan_danh_gia_tu_dong(True, Decimal("50"), Decimal("100")) == "Khong dang ky"

    def test_chua_co_ket_qua(self):
        assert tinh_nhan_danh_gia_tu_dong(False, None, Decimal("100")) is None

    def test_ket_qua_0_co_dang_ky_chua_dat(self):
        assert tinh_nhan_danh_gia_tu_dong(False, Decimal("0"), Decimal("100")) == "Chua dat"

    def test_dat_duoi_100(self):
        assert tinh_nhan_danh_gia_tu_dong(False, Decimal("80"), Decimal("100")) == "Dat 80%"

    def test_vuot_chi_tieu(self):
        nhan = tinh_nhan_danh_gia_tu_dong(False, Decimal("120"), Decimal("100"))
        assert nhan.startswith("Vuot chi tieu")
        assert "120%" in nhan

    def test_dat_dung_100_la_vuot(self):
        nhan = tinh_nhan_danh_gia_tu_dong(False, Decimal("100"), Decimal("100"))
        assert nhan.startswith("Vuot chi tieu")

    def test_co_ket_qua_nhung_khong_co_dang_ky(self):
        # Co ket qua > 0, dang ky rong -> khong tinh duoc % -> None
        assert tinh_nhan_danh_gia_tu_dong(False, Decimal("50"), None) is None


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
