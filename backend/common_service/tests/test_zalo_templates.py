"""
Test ánh xạ template ZNS + khung giờ gửi + backoff.

Test thuần túy — không đụng DB, không gọi mạng.
Chạy: PYTHONPATH=$PWD pytest common_service/tests/test_zalo_templates.py -v
"""

from datetime import date, datetime, time, timezone

import pytest

from common_service.services.zalo.templates import (
    DANH_MUC_MAU,
    ThongTinGui,
    lay_mau,
    so_luong_template_can_duyet,
)

TT_MAU = ThongTinGui(
    doi_tuong_type="GIAY_MOI_HOP",
    ho_ten="Nguyễn Văn A",
    ngay_hop=date(2026, 7, 31),
    gio_bat_dau=time(14, 0),
    link_url="/hop-khong-giay/chi-tiet/abc",
)


class TestDanhMucMau:
    def test_phu_du_6_loai_thong_bao_cua_hkg(self):
        """6 loại doi_tuong_type HKG đang phát sinh phải có template."""
        thuc_te = {
            "GIAY_MOI_HOP", "NHAC_HOP_24H", "NHAC_HOP_1H",
            "NHAC_HOP_30P", "THAY_DOI_HOP", "HUY_HOP",
        }
        assert thuc_te == set(DANH_MUC_MAU.keys())

    def test_chi_can_duyet_4_template(self):
        """3 mốc nhắc họp dùng chung 1 template → chỉ phải xin duyệt 4."""
        assert so_luong_template_can_duyet() == 4

    def test_ba_moc_nhac_dung_chung_template(self):
        khoa = {
            DANH_MUC_MAU[k].khoa_config
            for k in ("NHAC_HOP_24H", "NHAC_HOP_1H", "NHAC_HOP_30P")
        }
        assert len(khoa) == 1

    def test_loai_khong_biet_tra_ve_none(self):
        assert lay_mau("LOAI_LA_HOAC") is None
        assert lay_mau(None) is None
        assert lay_mau("") is None


class TestThamSo:
    def test_tham_so_co_ban(self):
        mau = lay_mau("GIAY_MOI_HOP")
        ts = mau.dung_tham_so(TT_MAU)
        assert ts["ho_ten"] == "Nguyễn Văn A"
        assert ts["thoi_gian"] == "31/07/2026"  # kiểu DATE: chỉ ngày

    @pytest.mark.parametrize(
        "loai,moc",
        [
            ("NHAC_HOP_24H", "trước 24 giờ"),
            ("NHAC_HOP_1H", "trước 1 giờ"),
            ("NHAC_HOP_30P", "trước 30 phút"),
        ],
    )
    def test_moc_nhac_phan_biet_qua_tham_so(self, loai, moc):
        mau = lay_mau(loai)
        ts = mau.dung_tham_so(
            ThongTinGui(loai, "Trần Thị B", date(2026, 7, 31), time(8, 30), None)
        )
        assert ts["moc"] == moc
        assert ts["thoi_gian"] == "31/07/2026"

    def test_dinh_dang_dung_kieu_DATE_cua_zalo(self):
        """Zalo khai `thoi_gian` kiểu DATE → chỉ nhận đúng dd/mm/yyyy.

        Gửi kèm giờ ("14:00 ngày 31/07/2026") sẽ bị Zalo từ chối. Test này
        canh giữ điều đó; nếu đơn vị đổi template sang STRING thì sửa cờ
        templates.THOI_GIAN_KIEU_DATE và cập nhật test.
        """
        import re as _re

        for loai, mau in DANH_MUC_MAU.items():
            ts = mau.dung_tham_so(
                ThongTinGui(loai, "X", date(2026, 7, 31), time(14, 0), None)
            )
            assert _re.fullmatch(r"\d{2}/\d{2}/\d{4}", ts["thoi_gian"]), (
                f"{loai}: '{ts['thoi_gian']}' không đúng dạng dd/mm/yyyy"
            )

    def test_thieu_ngay_gio_khong_no(self):
        """Cuộc họp bị xóa hoặc dữ liệu thiếu → không được ném lỗi."""
        mau = lay_mau("HUY_HOP")
        ts = mau.dung_tham_so(ThongTinGui("HUY_HOP", "C", None, None, None))
        assert ts["thoi_gian"] == ""
        assert ts["ho_ten"] == "C"


class TestChinhSachChuongCua:
    """Chốt chính sách: tin Zalo KHÔNG mang nội dung cuộc họp.

    Đây là test canh giữ quyết định đã thống nhất với đơn vị — nếu ai đó
    sau này thêm tiêu đề/địa điểm/thành phần vào tham số template thì test
    này phải đỏ để buộc rà lại với Phòng CNTT.
    """

    KHOA_DUOC_PHEP = {"ho_ten", "thoi_gian", "moc"}

    def test_khong_co_truong_nao_ngoai_danh_sach_cho_phep(self):
        for loai, mau in DANH_MUC_MAU.items():
            ts = mau.dung_tham_so(
                ThongTinGui(loai, "X", date(2026, 1, 1), time(9, 0), "/link")
            )
            thua = set(ts.keys()) - self.KHOA_DUOC_PHEP
            assert not thua, f"{loai} lộ thêm trường: {thua}"

    def test_link_url_khong_bi_dua_vao_tham_so(self):
        """link_url chứa UUID cuộc họp — không cần và không nên gửi qua Zalo."""
        for loai, mau in DANH_MUC_MAU.items():
            ts = mau.dung_tham_so(
                ThongTinGui(loai, "X", date(2026, 1, 1), time(9, 0),
                            "/hop-khong-giay/chi-tiet/SECRET-UUID")
            )
            assert "SECRET-UUID" not in str(ts)


class TestKhungGioGui:
    """Không nhắn lúc rạng sáng — tin Zalo làm rung điện thoại."""

    def _moc(self):
        from common_service.services.zalo.outbox import _moc_gui_hop_le

        return _moc_gui_hop_le

    def _vn(self, gio, phut=0, ngay=31):
        from common_service.services.zalo.outbox import TZ_VN

        return datetime(2026, 7, ngay, gio, phut, tzinfo=TZ_VN).astimezone(timezone.utc)

    def test_gio_hanh_chinh_giu_nguyen(self):
        from common_service.services.zalo.outbox import TZ_VN

        moc = self._vn(14, 30)
        assert self._moc()(moc) == moc

    def test_rang_sang_bi_day_den_6h(self):
        from common_service.services.zalo.outbox import TZ_VN

        kq = self._moc()(self._vn(3, 0)).astimezone(TZ_VN)
        assert kq.hour == 6
        assert kq.day == 31

    def test_khuya_bi_day_sang_hom_sau(self):
        from common_service.services.zalo.outbox import TZ_VN

        kq = self._moc()(self._vn(23, 30)).astimezone(TZ_VN)
        assert kq.hour == 6
        assert kq.day == 1  # sang tháng 8

    def test_dung_6h_thi_gui_duoc(self):
        moc = self._vn(6, 0)
        assert self._moc()(moc) == moc


class TestBackoff:
    def test_gian_cach_tang_dan(self):
        from common_service.services.zalo.outbox import _backoff

        moc = [_backoff(i) for i in range(4)]
        assert moc == sorted(moc), "Backoff phải tăng dần"

    def test_khong_vuot_qua_bang(self):
        from common_service.services.zalo.outbox import _backoff

        # Gọi với số lần thử lớn không được ném IndexError
        assert _backoff(99) is not None
