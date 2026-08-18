"""Kiểm chứng quy tắc phân loại giấy mời được port ĐÚNG từ lichkv8.

Đây là quy tắc nghiệp vụ, không phải chi tiết hiển thị: nó quyết định báo cáo
"Thống kê tài liệu họp" có báo đơn vị là đã nộp tài liệu hay chưa. Bình luận
V145 trong mã gốc ghi rõ từng có sự cố "báo oan đơn vị chưa nộp tài liệu".

Các ca dưới đây lấy từ TÊN FILE THẬT trong kho 1.225 tài liệu, không phải ví dụ
bịa. Nếu ai đó sửa quy tắc, test này sẽ chỉ ra chính xác hành vi nào đổi.

    ./scripts/dev.sh test meeting_service/tests/test_quy_tac_giay_moi.py -v
"""

from __future__ import annotations

import pytest

from meeting_service.services.quy_tac_giay_moi import (
    chuan_hoa,
    dem_tai_lieu_chuan_bi,
    la_giay_moi_thuan,
    ten_goc,
)


# ── chuẩn hoá phải khớp normalizeText_() của lichkv8 ──────────────────

@pytest.mark.parametrize("vao,ra", [
    ("Báo cáo kết quả.pdf", "bao cao ket qua pdf"),
    # Bước [^a-z0-9]→' ' là quan trọng nhất: thiếu nó thì dấu gạch và gạch dưới
    # phá vỡ mọi biểu thức có \b…\b.
    ("bao-cao.pdf", "bao cao pdf"),
    ("Bao_cao_ket_qua.docx", "bao cao ket qua docx"),
    ("Đề án chuyển đổi số", "de an chuyen doi so"),
    ("2.GM 219.pdf", "2 gm 219 pdf"),
])
def test_chuan_hoa_khop_ban_goc(vao, ra):
    assert chuan_hoa(vao) == ra


# ── bỏ tiền tố hệ thống tự thêm khi upload ────────────────────────────

@pytest.mark.parametrize("vao,ra", [
    ("LH0282_GIAY_MOI_V03_Giay moi so 108.pdf", "Giay moi so 108.pdf"),
    ("LH0277_TAI_LIEU_HOP_V02_Tham luan.docx", "Tham luan.docx"),
    ("Bao cao thang 5.pdf", "Bao cao thang 5.pdf"),
])
def test_bo_tien_to_he_thong(vao, ra):
    assert ten_goc(vao) == ra


# ── giấy mời thuần: KHÔNG tính là tài liệu chuẩn bị ───────────────────

@pytest.mark.parametrize("ten", [
    "6.Giay moi so 108.pdf",
    "2.GM 219.pdf",
    "1. GM 245.pdf",
    "GM 267.pdf",
    "Thu moi hop.pdf",
    "Giay trieu tap.pdf",
])
def test_giay_moi_thuan_bi_loai(ten):
    assert la_giay_moi_thuan(ten) is True


# ── tài liệu chuyên môn: PHẢI tính ────────────────────────────────────

@pytest.mark.parametrize("ten", [
    "Bao cao ket qua quy I.pdf",
    "Phu luc 1 danh muc nhiem vu.xlsx",
    "Du thao nghi quyet.docx",
    "Ke hoach trien khai 2026.doc",
    "Tham luan tai hoi nghi.docx",
    "Bien ban hop.pdf",
    "De an mo hinh tang truong.doc",
])
def test_tai_lieu_chuyen_mon_duoc_tinh(ten):
    assert la_giay_moi_thuan(ten) is False


# ── ĐIỂM MẤU CHỐT của V145 ────────────────────────────────────────────

@pytest.mark.parametrize("ten", [
    # Nằm trong nhóm GIAY_MOI nhưng tên rõ là tài liệu → vẫn phải tính.
    "LH0282_GIAY_MOI_V01_Bao cao tinh hinh KTXH.pdf",
    "LH0300_GIAY_MOI_V02_Phu luc bieu mau.xlsx",
    # Có cả tín hiệu tài liệu lẫn số giấy mời → tín hiệu tài liệu THẮNG.
    "5. TAI LIEU GM 245.pdf",
    "Tai lieu hop theo GM 219.docx",
])
def test_tin_hieu_tai_lieu_thang_tin_hieu_giay_moi(ten):
    """Mập mờ thì ưu tiên tính là tài liệu thật — thà tính dư còn hơn báo oan.

    Đây chính là điều bình luận V145 mô tả: bỏ nhánh suy đoán theo nhóm file
    lúc upload, chỉ xét tên file.
    """
    assert la_giay_moi_thuan(ten) is False


# ── hạn chế đã biết của quy tắc gốc ───────────────────────────────────

@pytest.mark.parametrize("ten", [
    "2. TL GM 245.doc",
    "TL hop GM 1308 BQL ve giam phi dich vu.doc",
    "GM 600 -TL UBND tinh ngay 05.5.26.docx",
])
def test_viet_tat_TL_khong_duoc_nhan_dien(ten):
    """Quy tắc gốc nhận 'tai lieu' nhưng KHÔNG nhận viết tắt 'TL'.

    35/1.225 file thật rơi vào ca này — tên có 'TL' (gần như chắc chắn là
    'Tài liệu') kèm số giấy mời, nên bị xếp thành giấy mời thuần và không được
    tính là đã nộp tài liệu.

    Test này ghi lại hành vi HIỆN TẠI, khớp đúng lichkv8. KHÔNG tự ý sửa: thêm
    'tl' vào danh sách tín hiệu sẽ làm số liệu báo cáo khác đi so với hệ cũ mà
    Văn phòng đang quen. Muốn đổi thì phải là quyết định nghiệp vụ có người duyệt.
    """
    assert la_giay_moi_thuan(ten) is True


# ── đếm tổng hợp ──────────────────────────────────────────────────────

def test_dem_tai_lieu_chuan_bi():
    ds = [
        "Bao cao quy I.pdf",        # tính
        "Phu luc 1.xlsx",           # tính
        "6.Giay moi so 108.pdf",    # không
        "GM 267.pdf",               # không
    ]
    assert dem_tai_lieu_chuan_bi(ds) == 2


def test_cuoc_hop_chi_co_giay_moi_la_chua_nop():
    """Nộp mỗi giấy mời thì vẫn là chưa hoàn thành nghĩa vụ chuẩn bị."""
    assert dem_tai_lieu_chuan_bi(["GM 245.pdf", "Giay moi 108.pdf"]) == 0


def test_ten_rong_khong_vo():
    assert la_giay_moi_thuan("") is False
    assert la_giay_moi_thuan(None) is False  # type: ignore[arg-type]
