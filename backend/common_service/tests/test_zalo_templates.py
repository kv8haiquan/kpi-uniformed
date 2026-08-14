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
        ts = mau.tham_so(TT_MAU)
        assert ts["ho_ten"] == "Nguyễn Văn A"
        assert ts["thoi_gian"] == "14:00 31/07/2026"  # kiểu STRING: có giờ

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
        ts = mau.tham_so(
            ThongTinGui(loai, "Trần Thị B", date(2026, 7, 31), time(8, 30), None)
        )
        assert ts["moc"] == moc
        assert ts["thoi_gian"] == "08:30 31/07/2026"

    def test_dinh_dang_thoi_gian_dung_theo_kieu_template_khai(self):
        """Định dạng `thoi_gian` phải do cờ của CHÍNH template đó quyết định.

        - Template khai DATE   → Zalo chỉ nhận đúng dd/mm/yyyy, kèm giờ là bị
          từ chối cả tin.
        - Template khai STRING → gửi kèm giờ được, và nên gửi.

        Test lái theo cờ chứ không chốt cứng một dạng, để lúc đơn vị chuyển đổi
        dần từng template thì test vẫn đúng. Nguồn sự thật là
        `python scripts/zalo_xem_template.py --doi-chieu`.
        """
        import re as _re

        for loai, mau in DANH_MUC_MAU.items():
            ts = mau.tham_so(
                ThongTinGui(loai, "X", date(2026, 7, 31), time(14, 0), None)
            )
            mong_doi = (
                r"\d{2}/\d{2}/\d{4}"
                if mau.thoi_gian_kieu_date
                else r"\d{2}:\d{2} \d{2}/\d{2}/\d{4}"
            )
            assert _re.fullmatch(mong_doi, ts["thoi_gian"]), (
                f"{loai}: '{ts['thoi_gian']}' không khớp kiểu template đã khai"
            )

    def test_ca_4_template_hien_dang_gui_kem_gio(self):
        """Bộ template ZBS dùng từ 14/08/2026 khai STRING cả 4 → phải có giờ."""
        assert all(not m.thoi_gian_kieu_date for m in DANH_MUC_MAU.values())
        assert lay_mau("GIAY_MOI_HOP").tham_so(TT_MAU)["thoi_gian"] == (
            "14:00 31/07/2026"
        )

    def test_doi_ve_kieu_DATE_thi_mat_gio(self):
        """Cờ đặt theo TỪNG template, đổi cái này không đụng cái kia."""
        import dataclasses

        goc = lay_mau("GIAY_MOI_HOP")
        cu = dataclasses.replace(goc, thoi_gian_kieu_date=True)

        assert cu.tham_so(TT_MAU)["thoi_gian"] == "31/07/2026"
        assert lay_mau("HUY_HOP").thoi_gian_kieu_date is False

    def test_kieu_STRING_thieu_gio_van_khong_no(self):
        """Họp chưa có giờ bắt đầu → lùi về chỉ ngày, không ném lỗi."""
        tt = ThongTinGui("HUY_HOP", "C", date(2026, 7, 31), None, None)
        assert lay_mau("HUY_HOP").tham_so(tt)["thoi_gian"] == "31/07/2026"

    def test_ho_ten_qua_dai_bi_cat_thay_vi_bi_zalo_tu_choi(self):
        """Template khai ho_ten tối đa 30 ký tự — vượt là mất cả tin."""
        from common_service.services.zalo.templates import MAX_HO_TEN

        dai = "Nguyễn Trần Lê Hoàng Phương Thảo Vy Anh"
        assert len(dai) > MAX_HO_TEN
        ts = lay_mau("HUY_HOP").tham_so(
            ThongTinGui("HUY_HOP", dai, date(2026, 7, 31), time(9, 0), None,
                        cuoc_hop_id="abc")
        )
        assert len(ts["ho_ten"]) == MAX_HO_TEN
        assert dai.startswith(ts["ho_ten"])

    def test_thieu_ngay_gio_khong_no(self):
        """Cuộc họp bị xóa hoặc dữ liệu thiếu → không được ném lỗi."""
        mau = lay_mau("HUY_HOP")
        ts = mau.tham_so(ThongTinGui("HUY_HOP", "C", None, None, None))
        assert ts["thoi_gian"] == ""
        assert ts["ho_ten"] == "C"


class TestChinhSachChuongCua:
    """Chốt chính sách: tin Zalo KHÔNG mang nội dung cuộc họp.

    Đây là test canh giữ quyết định đã thống nhất với đơn vị — nếu ai đó
    sau này thêm tiêu đề/địa điểm/thành phần vào tham số template thì test
    này phải đỏ để buộc rà lại với Phòng CNTT.
    """

    # `ma_hop` được phép: là UUID cuộc họp, dùng để nút bấm dẫn thẳng vào
    # đúng cuộc họp. Chuỗi này vô nghĩa với người ngoài — không lộ tiêu đề,
    # địa điểm, thành phần hay tài liệu — nên vẫn đúng tinh thần "chuông cửa".
    KHOA_DUOC_PHEP = {"ho_ten", "thoi_gian", "moc", "ma_hop"}

    def test_khong_co_truong_nao_ngoai_danh_sach_cho_phep(self):
        for loai, mau in DANH_MUC_MAU.items():
            ts = mau.tham_so(
                ThongTinGui(loai, "X", date(2026, 1, 1), time(9, 0), "/link",
                            cuoc_hop_id="abc-123")
            )
            thua = set(ts.keys()) - self.KHOA_DUOC_PHEP
            assert not thua, f"{loai} lộ thêm trường: {thua}"

    def test_link_url_khong_bi_dua_vao_tham_so(self):
        """link_url chứa UUID cuộc họp — không cần và không nên gửi qua Zalo."""
        for loai, mau in DANH_MUC_MAU.items():
            ts = mau.tham_so(
                ThongTinGui(loai, "X", date(2026, 1, 1), time(9, 0),
                            "/hop-khong-giay/chi-tiet/SECRET-UUID")
            )
            assert "SECRET-UUID" not in str(ts)


class TestKhopVoiTemplateDaDuyet:
    """Bộ tham số sinh ra phải TRÙNG KHÍT template Zalo đã duyệt.

    Zalo từ chối cả tin nếu thừa HOẶC thiếu tham số. Bảng dưới chép từ
    `scripts/zalo_xem_template.py` chạy ngày 14/08/2026 — nếu đơn vị sửa
    template thì chạy lại script đó và cập nhật cả hai nơi.
    """

    # doi_tuong_type → bộ tham số bắt buộc của template tương ứng
    THAM_SO_THAT = {
        "GIAY_MOI_HOP": {"ho_ten", "thoi_gian", "ma_hop"},  # 623165
        "NHAC_HOP_24H": {"ho_ten", "thoi_gian", "moc", "ma_hop"},  # 623236
        "NHAC_HOP_1H": {"ho_ten", "thoi_gian", "moc", "ma_hop"},
        "NHAC_HOP_30P": {"ho_ten", "thoi_gian", "moc", "ma_hop"},
        "THAY_DOI_HOP": {"ho_ten", "thoi_gian", "ma_hop"},  # 623180
        "HUY_HOP": {"ho_ten", "thoi_gian", "ma_hop"},  # 623182
    }

    def test_bo_tham_so_khop_tung_template(self):
        assert set(self.THAM_SO_THAT) == set(DANH_MUC_MAU), (
            "Có loại thông báo chưa được đối chiếu với template thật"
        )
        for loai, mong_doi in self.THAM_SO_THAT.items():
            ts = DANH_MUC_MAU[loai].tham_so(
                ThongTinGui(loai, "X", date(2026, 1, 1), time(9, 0), "/l",
                            cuoc_hop_id="7279683b-49fb-446d-aa48-6e66f155f314")
            )
            assert set(ts) == mong_doi, (
                f"{loai}: gửi {sorted(ts)}, template cần {sorted(mong_doi)}"
            )

    def test_moi_hop_cung_gui_ma_hop(self):
        """623165 có khai ma_hop → nút bấm dẫn thẳng vào đúng cuộc họp."""
        ts = DANH_MUC_MAU["GIAY_MOI_HOP"].tham_so(
            ThongTinGui("GIAY_MOI_HOP", "X", date(2026, 1, 1), time(9, 0), "/l",
                        cuoc_hop_id="7279683b-49fb-446d-aa48-6e66f155f314")
        )
        assert ts["ma_hop"] == "7279683b-49fb-446d-aa48-6e66f155f314"

    def test_ma_hop_dung_bang_uuid_cuoc_hop(self):
        ts = DANH_MUC_MAU["HUY_HOP"].tham_so(
            ThongTinGui("HUY_HOP", "X", date(2026, 1, 1), time(9, 0), "/l",
                        cuoc_hop_id="7279683b-49fb-446d-aa48-6e66f155f314")
        )
        assert ts["ma_hop"] == "7279683b-49fb-446d-aa48-6e66f155f314"
        assert len(ts["ma_hop"]) <= 200, "Template giới hạn ma_hop 200 ký tự"

    def test_thieu_ma_hop_thi_bao_thieu_du_lieu(self):
        """Không có cuoc_hop_id → phải chặn từ đầu, đừng để Zalo từ chối."""
        tt = ThongTinGui("HUY_HOP", "X", date(2026, 1, 1), time(9, 0), "/l",
                         cuoc_hop_id=None)
        assert DANH_MUC_MAU["HUY_HOP"].thieu_du_lieu(tt) is True

    def test_moi_hop_cung_can_ma_hop(self):
        """Cả 4 template hiện đều bắt buộc ma_hop → thiếu là phải chặn."""
        for loai in DANH_MUC_MAU:
            tt = ThongTinGui(loai, "X", date(2026, 1, 1), time(9, 0), "/l",
                             cuoc_hop_id=None)
            assert DANH_MUC_MAU[loai].thieu_du_lieu(tt) is True, loai

    def test_moc_la_chuoi_khong_qua_30_ky_tu(self):
        """622517 khai `moc` kiểu STRING, tối đa 30 ký tự."""
        for loai in ("NHAC_HOP_24H", "NHAC_HOP_1H", "NHAC_HOP_30P"):
            ts = DANH_MUC_MAU[loai].tham_so(
                ThongTinGui(loai, "X", date(2026, 1, 1), time(9, 0), "/l",
                            cuoc_hop_id="abc")
            )
            assert isinstance(ts["moc"], str) and ts["moc"]
            assert len(ts["moc"]) <= 30, f"{loai}: moc dài quá {len(ts['moc'])}"


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
