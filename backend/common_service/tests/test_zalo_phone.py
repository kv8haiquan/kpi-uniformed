"""
Test chuẩn hóa số điện thoại cho Zalo.

Test thuần túy — không đụng DB, không gọi mạng, không cần credential Zalo.
Chạy: PYTHONPATH=$PWD pytest common_service/tests/test_zalo_phone.py -v
"""

import pytest

from common_service.services.zalo.phone import (
    DAU_SO_LA,
    OK,
    OK_SO_CU,
    RONG,
    SAI_DINH_DANG,
    SO_CO_DINH,
    che_giau,
    chuan_hoa,
    hien_thi,
)


class TestDinhDangCoBan:
    @pytest.mark.parametrize(
        "dau_vao",
        [
            "0913048358",
            "0913 048 358",
            "0913.048.358",
            "0913-048-358",
            "+84913048358",
            "+84 913 048 358",
            "84913048358",
            "0084913048358",
            " 0913048358 ",
            "(091) 304 8358",
        ],
    )
    def test_cac_cach_viet_deu_ve_mot_dang(self, dau_vao):
        """Mọi cách viết thông dụng của cùng 1 số phải ra cùng kết quả."""
        kq = chuan_hoa(dau_vao)
        assert kq.hop_le, f"{dau_vao} bị loại: {kq.ghi_chu}"
        assert kq.so_chuan == "84913048358"

    def test_giu_lai_so_goc_de_doi_chieu(self):
        kq = chuan_hoa("+84 913 048 358")
        assert kq.so_goc == "+84 913 048 358"

    def test_excel_an_mat_so_0_dau(self):
        """Ô Excel để kiểu Number sẽ biến 0913048358 thành 913048358."""
        kq = chuan_hoa("913048358")
        assert kq.hop_le
        assert kq.so_chuan == "84913048358"
        assert "Thiếu số 0 đầu" in kq.ghi_chu


class TestSoCu11ChuSo:
    """Đầu số 11 chữ số đã được chuyển đổi từ 15/9/2018.

    Danh sách TCCB lưu lâu năm rất dễ còn sót số cũ.
    """

    @pytest.mark.parametrize(
        "cu,moi",
        [
            ("01631234567", "84331234567"),  # Viettel 0163 → 033
            ("01651234567", "84351234567"),
            ("01221234567", "84771234567"),  # VinaPhone 0122 → 077
            ("01231234567", "84831234567"),
            ("01881234567", "84581234567"),  # Vietnamobile 0188 → 058
            ("01991234567", "84591234567"),  # Gmobile 0199 → 059
        ],
    )
    def test_quy_doi_dau_so_cu(self, cu, moi):
        kq = chuan_hoa(cu)
        assert kq.hop_le
        assert kq.so_chuan == moi
        assert kq.trang_thai == OK_SO_CU
        assert "quy đổi 2018" in kq.ghi_chu

    def test_so_11_chu_so_dau_la_thi_loai(self):
        kq = chuan_hoa("01111234567")
        assert not kq.hop_le
        assert kq.trang_thai == DAU_SO_LA


class TestLoaiBoSoKhongDung:
    def test_o_trong(self):
        for x in ["", "   ", None]:
            assert chuan_hoa(x).trang_thai == RONG

    def test_khong_co_chu_so(self):
        assert chuan_hoa("khong co").trang_thai == SAI_DINH_DANG

    def test_do_dai_sai(self):
        for x in ["091304", "09130483581234"]:
            kq = chuan_hoa(x)
            assert not kq.hop_le
            assert kq.trang_thai == SAI_DINH_DANG

    def test_so_may_ban_bi_loai(self):
        """0203 là mã vùng Quảng Ninh — máy bàn không nhận được Zalo."""
        kq = chuan_hoa("02033826123")
        assert not kq.hop_le
        assert kq.trang_thai == SO_CO_DINH

    def test_dau_so_khong_ton_tai(self):
        kq = chuan_hoa("0413048358")  # 41 không phải đầu số di động
        assert not kq.hop_le
        assert kq.trang_thai == DAU_SO_LA


class TestDauSoNhaMang:
    @pytest.mark.parametrize(
        "dau", ["032", "086", "096", "098", "091", "094", "070", "090", "093",
                "052", "056", "059", "087", "081", "085", "088"]
    )
    def test_cac_dau_so_that_deu_duoc_chap_nhan(self, dau):
        kq = chuan_hoa(dau + "1234567")
        assert kq.hop_le, f"Đầu số {dau} bị loại nhầm"
        assert kq.trang_thai == OK


class TestHienThi:
    def test_hien_thi_cho_nguoi_doc(self):
        assert hien_thi("84913048358") == "0913 048 358"

    def test_hien_thi_chiu_duoc_dau_vao_rac(self):
        assert hien_thi(None) == ""
        assert hien_thi("abc") == "abc"

    def test_che_giau_khong_lo_so_day_du(self):
        """Log không được ghi nguyên số — dữ liệu cá nhân (NĐ 13/2023)."""
        ket_qua = che_giau("84913048358")
        assert ket_qua == "0913***358"
        assert "048" not in ket_qua

    def test_che_giau_dau_vao_ngan(self):
        assert che_giau(None) == "***"
        assert che_giau("123") == "***"


class TestSoThat:
    """6 số thật đang có trong public.cong_chuc phải xử lý được hết."""

    @pytest.mark.parametrize(
        "so",
        ["0913048358", "0936719858", "0988755568",
         "0989567855", "0913387231", "0913030388"],
    )
    def test_6_so_hien_co_deu_hop_le(self, so):
        kq = chuan_hoa(so)
        assert kq.hop_le
        assert kq.so_chuan is not None
        assert kq.so_chuan.startswith("84")
        assert len(kq.so_chuan) == 11
