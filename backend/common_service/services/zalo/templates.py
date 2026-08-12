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

TRẠNG THÁI: template_id đang là PLACEHOLDER. Sau khi Zalo duyệt template thật,
điền ID vào .env (ZALO_TPL_*) — không sửa code.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, time
from typing import Any, Callable, Optional

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


@dataclass(frozen=True)
class MauTin:
    """Một template ZNS + hàm dựng tham số."""

    khoa_config: str  # tên biến trong settings, ví dụ "zalo_tpl_moi_hop"
    mo_ta: str
    dung_tham_so: Callable[[ThongTinGui], dict[str, Any]]


# Tham số `thoi_gian` của template ZNS hiện đang khai kiểu **DATE**, nên Zalo
# CHỈ chấp nhận đúng dạng dd/mm/yyyy (dữ liệu mẫu Zalo trả về: "01/01/1970").
# Gửi "14:00 ngày 31/07/2026" sẽ bị từ chối với lỗi tham số không hợp lệ.
#
# Hệ quả: giờ họp KHÔNG truyền được — người nhận chỉ biết ngày.
# Muốn hiển thị cả giờ thì đơn vị phải sửa template, đổi `thoi_gian` sang kiểu
# STRING rồi gửi duyệt lại; khi đó chỉ cần đặt cờ dưới đây thành False.
THOI_GIAN_KIEU_DATE = True


def _thoi_gian_hop(tt: ThongTinGui) -> str:
    """Dựng giá trị cho tham số `thoi_gian`.

    - Template khai kiểu DATE  → "31/07/2026"        (mất giờ họp)
    - Template khai kiểu STRING → "14:00 31/07/2026" (đầy đủ)
    Thiếu dữ liệu thì trả chuỗi rỗng.
    """
    if not tt.ngay_hop:
        return ""
    ngay = tt.ngay_hop.strftime("%d/%m/%Y")
    if THOI_GIAN_KIEU_DATE or not tt.gio_bat_dau:
        return ngay
    return f"{tt.gio_bat_dau.strftime('%H:%M')} {ngay}"


def _tham_so_co_ban(tt: ThongTinGui) -> dict[str, Any]:
    return {"ho_ten": tt.ho_ten, "thoi_gian": _thoi_gian_hop(tt)}


def _tham_so_nhac_hop(tt: ThongTinGui) -> dict[str, Any]:
    """Ba mốc nhắc dùng CHUNG một template, khác nhau ở tham số `moc`.

    Gộp lại để chỉ phải xin Zalo duyệt 1 template thay vì 3.
    """
    d = _tham_so_co_ban(tt)
    d["moc"] = _MOC_NHAC.get(tt.doi_tuong_type, "")
    return d


# ---------------------------------------------------------------------------
# Registry: doi_tuong_type (trong common.thong_bao) → template ZNS
# ---------------------------------------------------------------------------
DANH_MUC_MAU: dict[str, MauTin] = {
    "GIAY_MOI_HOP": MauTin(
        khoa_config="zalo_tpl_moi_hop",
        mo_ta="Giấy mời họp",
        dung_tham_so=_tham_so_co_ban,
    ),
    "NHAC_HOP_24H": MauTin(
        khoa_config="zalo_tpl_nhac_hop",
        mo_ta="Nhắc họp (dùng chung 3 mốc)",
        dung_tham_so=_tham_so_nhac_hop,
    ),
    "NHAC_HOP_1H": MauTin(
        khoa_config="zalo_tpl_nhac_hop",
        mo_ta="Nhắc họp (dùng chung 3 mốc)",
        dung_tham_so=_tham_so_nhac_hop,
    ),
    "NHAC_HOP_30P": MauTin(
        khoa_config="zalo_tpl_nhac_hop",
        mo_ta="Nhắc họp (dùng chung 3 mốc)",
        dung_tham_so=_tham_so_nhac_hop,
    ),
    "THAY_DOI_HOP": MauTin(
        khoa_config="zalo_tpl_thay_doi_hop",
        mo_ta="Thay đổi lịch họp",
        dung_tham_so=_tham_so_co_ban,
    ),
    "HUY_HOP": MauTin(
        khoa_config="zalo_tpl_huy_hop",
        mo_ta="Hủy họp",
        dung_tham_so=_tham_so_co_ban,
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
