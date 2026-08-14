"""
common_service/services/zalo/templates.py
==========================================
Ánh xạ loại thông báo → template ZNS + bộ tham số.

CHÍNH SÁCH NỘI DUNG (đã chốt với đơn vị 31/07/2026): tin Zalo chỉ đóng vai
"chuông cửa", KHÔNG mang nội dung. Người nhận chỉ biết *có việc* và *khi nào*,
muốn xem chi tiết thì mở phần mềm. Vì vậy tuyệt đối KHÔNG đưa tiêu đề cuộc
họp, địa điểm, thành phần hay nội dung tài liệu vào tham số template.

Lý do làm vậy:
  1. Dữ liệu họp nội bộ không đi qua máy chủ bên thứ ba (VNG).
  2. Số điện thoại trong danh sách có thể đã đổi chủ — người lạ nhận được tin
     cũng không đọc được gì.
  3. Template ít tham số thì dễ được Zalo duyệt hơn.

Nếu sau này lãnh đạo muốn hiển thị tiêu đề cuộc họp, sửa ở đây là đủ — nhưng
phải xin ý kiến Phòng CNTT trước và tạo template ZNS mới.

TRẠNG THÁI (14/08/2026): chuyển sang bộ 4 template ZBS mới, tất cả ENABLE, ID
điền trong .env qua các biến ZALO_TPL_*. Bộ mới khắc phục hai hạn chế của bộ
cũ: `thoi_gian` khai STRING nên gửi được GIỜ họp (bộ cũ khai DATE, chỉ gửi
được ngày), và giấy mời cũng có `ma_hop` nên nút bấm dẫn thẳng vào cuộc họp.

Khi đơn vị sửa template thì chạy lại `python scripts/zalo_xem_template.py
--doi-chieu` và cập nhật cờ trong DANH_MUC_MAU cho khớp — bộ tham số phải
trùng khít với template, thừa hay thiếu đều bị Zalo từ chối cả tin.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, time
from typing import Any, Callable, Optional

# Giới hạn ký tự tham số `ho_ten` do template khai (xem scripts/zalo_xem_template.py)
MAX_HO_TEN = 30

# Thứ tự ưu tiên hiển thị mốc nhắc — dùng cho template nhắc họp gộp
_MOC_NHAC = {
    "NHAC_HOP_24H": "trước 24 giờ",
    "NHAC_HOP_1H": "trước 1 giờ",
    "NHAC_HOP_30P": "trước 30 phút",
}


@dataclass(frozen=True)
class ThongTinGui:
    """Dữ liệu thô lấy từ DB để dựng tham số template."""

    doi_tuong_type: str
    ho_ten: str
    ngay_hop: Optional[date]
    gio_bat_dau: Optional[time]
    link_url: Optional[str]
    cuoc_hop_id: Optional[Any] = None


def _them_moc(tt: ThongTinGui) -> dict[str, Any]:
    """Ba mốc nhắc dùng CHUNG một template, khác nhau ở tham số `moc`.

    Gộp lại để chỉ phải xin Zalo duyệt 1 template thay vì 3.
    """
    return {"moc": _MOC_NHAC.get(tt.doi_tuong_type, "")}


@dataclass(frozen=True)
class MauTin:
    """Một template ZNS + cách dựng bộ tham số cho nó.

    Hai cờ dưới đây PHẢI khớp đúng với template Zalo đã duyệt. ZNS từ chối cả
    tin nếu bộ tham số thừa, thiếu, hoặc sai định dạng so với khai báo — và từ
    chối lặng lẽ, từng tin một. Đối chiếu bằng:

        python scripts/zalo_xem_template.py --doi-chieu
    """

    khoa_config: str  # tên biến trong settings, ví dụ "zalo_tpl_moi_hop"
    mo_ta: str
    # Có khai tham số `ma_hop` (UUID cuộc họp, để nút bấm dẫn thẳng vào họp)
    co_ma_hop: bool = False
    # Template khai `thoi_gian` kiểu DATE → Zalo CHỈ nhận dd/mm/yyyy, giờ họp
    # không truyền được. Đổi template sang STRING thì đặt cờ này False.
    thoi_gian_kieu_date: bool = True
    # Tham số riêng của từng loại (hiện chỉ `moc` của nhóm nhắc họp)
    tham_so_rieng: Optional[Callable[[ThongTinGui], dict[str, Any]]] = None

    def thoi_gian(self, tt: ThongTinGui) -> str:
        """Giá trị tham số `thoi_gian`.

        - Template kiểu DATE   → "31/07/2026"        (mất giờ họp)
        - Template kiểu STRING → "14:00 31/07/2026"  (đầy đủ)
        Thiếu dữ liệu thì trả chuỗi rỗng, không ném lỗi.
        """
        if not tt.ngay_hop:
            return ""
        ngay = tt.ngay_hop.strftime("%d/%m/%Y")
        if self.thoi_gian_kieu_date or not tt.gio_bat_dau:
            return ngay
        return f"{tt.gio_bat_dau.strftime('%H:%M')} {ngay}"

    def tham_so(self, tt: ThongTinGui) -> dict[str, Any]:
        """Bộ tham số hoàn chỉnh gửi kèm template này."""
        # Cả 4 template khai ho_ten tối đa 30 ký tự. Người dài nhất hiện nay là
        # 25 ký tự, nhưng vượt hạn mức thì Zalo từ chối CẢ tin — thà tin nhắn
        # có tên bị cắt còn hơn người đó không nhận được gì.
        d: dict[str, Any] = {
            "ho_ten": (tt.ho_ten or "")[:MAX_HO_TEN],
            "thoi_gian": self.thoi_gian(tt),
        }
        if self.tham_so_rieng is not None:
            d.update(self.tham_so_rieng(tt))
        if self.co_ma_hop:
            # Mã cuộc họp để nút bấm dẫn thẳng vào đúng cuộc họp thay vì trang
            # chủ. KHÔNG vi phạm chính sách "chuông cửa": đây là chuỗi định
            # danh vô nghĩa với người ngoài, không lộ tiêu đề/địa điểm/thành
            # phần/tài liệu.
            d["ma_hop"] = str(tt.cuoc_hop_id or "")
        return d

    def thieu_du_lieu(self, tt: ThongTinGui) -> bool:
        """True nếu thiếu dữ liệu bắt buộc → gửi đi chắc chắn bị từ chối."""
        return self.co_ma_hop and not tt.cuoc_hop_id


# ---------------------------------------------------------------------------
# Registry: doi_tuong_type (trong common.thong_bao) → template ZNS
#
# Đối chiếu với template thật ngày 14/08/2026 (scripts/zalo_xem_template.py):
#   623165 Giấy mời họp        ho_ten, thoi_gian, ma_hop
#   623236 Nhắc họp không giấy ho_ten, thoi_gian, moc, ma_hop
#   623180 Thay đổi lịch họp   ho_ten, thoi_gian, ma_hop
#   623182 Hủy họp không giấy  ho_ten, thoi_gian, ma_hop
# Cả 4 đều ENABLE và khai `thoi_gian` kiểu STRING → gửi kèm được giờ họp.
# ---------------------------------------------------------------------------
DANH_MUC_MAU: dict[str, MauTin] = {
    "GIAY_MOI_HOP": MauTin(
        khoa_config="zalo_tpl_moi_hop",
        mo_ta="Giấy mời họp",
        co_ma_hop=True,
        thoi_gian_kieu_date=False,
    ),
    "NHAC_HOP_24H": MauTin(
        khoa_config="zalo_tpl_nhac_hop",
        mo_ta="Nhắc họp (dùng chung 3 mốc)",
        co_ma_hop=True,
        thoi_gian_kieu_date=False,
        tham_so_rieng=_them_moc,
    ),
    "NHAC_HOP_1H": MauTin(
        khoa_config="zalo_tpl_nhac_hop",
        mo_ta="Nhắc họp (dùng chung 3 mốc)",
        co_ma_hop=True,
        thoi_gian_kieu_date=False,
        tham_so_rieng=_them_moc,
    ),
    "NHAC_HOP_30P": MauTin(
        khoa_config="zalo_tpl_nhac_hop",
        mo_ta="Nhắc họp (dùng chung 3 mốc)",
        co_ma_hop=True,
        thoi_gian_kieu_date=False,
        tham_so_rieng=_them_moc,
    ),
    "THAY_DOI_HOP": MauTin(
        khoa_config="zalo_tpl_thay_doi_hop",
        mo_ta="Thay đổi lịch họp",
        co_ma_hop=True,
        thoi_gian_kieu_date=False,
    ),
    "HUY_HOP": MauTin(
        khoa_config="zalo_tpl_huy_hop",
        mo_ta="Hủy họp",
        co_ma_hop=True,
        thoi_gian_kieu_date=False,
    ),
}


def lay_mau(doi_tuong_type: Optional[str]) -> Optional[MauTin]:
    """Tra template theo doi_tuong_type. None nếu loại này không gửi Zalo."""
    if not doi_tuong_type:
        return None
    return DANH_MUC_MAU.get(doi_tuong_type)


def so_luong_template_can_duyet() -> int:
    """Số template PHÂN BIỆT cần xin Zalo duyệt (hiện là 4)."""
    return len({m.khoa_config for m in DANH_MUC_MAU.values()})
