"""
app/core/ky_tieu_chi.py
=======================
Kỳ chấm TIÊU CHÍ CHUNG (30 điểm): theo THÁNG (cũ) hay theo QUÝ (mới).

Căn cứ: Công văn 21169/CHQ-TCCB ngày 28/8/2026 của Cục Hải quan và Công văn
triển khai của Chi cục Hải quan khu vực VIII — "Từ quý III/2026, kỳ đánh giá,
xếp loại trên Phần mềm được thiết lập theo quý".

CÁCH LÀM — "phiếu tiêu chí của quý neo ở THÁNG CUỐI QUÝ":
    Từ kỳ >= TC_THEO_QUY_TU, việc chấm và duyệt tiêu chí chung chỉ diễn ra trên
    MỘT bản ghi `danh_gia_thang` — bản ghi của tháng cuối quý (T3, T6, T9, T12),
    gọi là THÁNG NEO, đánh dấu bằng cờ `danh_gia_thang.la_phieu_tc_quy`.
    Hai tháng còn lại của quý không chấm nữa; mọi nơi cần điểm/chi tiết tiêu chí
    của chúng đọc xuyên sang bản ghi neo qua các hàm trong module này.

    Ví dụ Quý III/2026: T7 và T8 đọc sang bản ghi T9.

NGUYÊN TẮC AN TOÀN:
    Chỉ đổi nơi ĐỌC. KHÔNG ghi đè điểm/trạng thái tiêu chí của các tháng cũ —
    dữ liệu đã chấm theo tháng (kể cả T7, T8/2026) giữ nguyên để tra cứu.

QUAY LUI:
    Đặt TC_THEO_QUY_TU = (9999, 1) rồi phát hành lại → toàn hệ thống trở về chấm
    theo tháng ngay lập tức, dữ liệu phiếu quý nằm im, không cần migration ngược.

Phiên bản: 1.0.0 (18/09/2026)
"""

from datetime import date
from typing import List, Optional, Tuple

# (năm, quý) — mọi kỳ TỪ mốc này trở đi chấm tiêu chí chung theo QUÝ.
# Quý III/2026 theo Công văn 21169.
TC_THEO_QUY_TU: Tuple[int, int] = (2026, 3)

QUY_TO_THANG = {1: [1, 2, 3], 2: [4, 5, 6], 3: [7, 8, 9], 4: [10, 11, 12]}


def quy_cua_thang(thang: int) -> int:
    """Quý chứa tháng: 7 → 3."""
    return (int(thang) - 1) // 3 + 1


def cac_thang_trong_quy(quy: int) -> List[int]:
    """Ba tháng của quý: 3 → [7, 8, 9]."""
    return list(QUY_TO_THANG.get(int(quy), []))


def thang_cuoi_quy(quy: int) -> int:
    """Tháng cuối quý: 3 → 9."""
    return int(quy) * 3


def tc_theo_quy(thang: int, nam: int) -> bool:
    """True nếu kỳ (tháng/năm) này chấm tiêu chí chung THEO QUÝ."""
    return (int(nam), quy_cua_thang(thang)) >= TC_THEO_QUY_TU


def tc_theo_quy_cua_quy(quy: int, nam: int) -> bool:
    """Bản dùng trực tiếp với (quý, năm) — cho các luồng cấp quý."""
    return (int(nam), int(quy)) >= TC_THEO_QUY_TU


def thang_neo(thang: int, nam: int) -> int:
    """
    Tháng chứa phiếu tiêu chí của kỳ.

    - Kỳ theo quý  → tháng cuối quý (7, 8, 9 → 9).
    - Kỳ theo tháng → chính tháng đó (giữ nguyên hành vi cũ).
    """
    if tc_theo_quy(thang, nam):
        return thang_cuoi_quy(quy_cua_thang(thang))
    return int(thang)


def la_thang_neo(thang: int, nam: int) -> bool:
    """True nếu bản ghi tháng này là nơi chấm tiêu chí của kỳ."""
    return int(thang) == thang_neo(thang, nam)


def cac_thang_ap_dung(thang: int, nam: int) -> List[int]:
    """Các tháng dùng chung điểm tiêu chí của kỳ (kỳ tháng → chỉ chính nó)."""
    if tc_theo_quy(thang, nam):
        return cac_thang_trong_quy(quy_cua_thang(thang))
    return [int(thang)]


def nhan_ky(thang: int, nam: int) -> str:
    """Nhãn hiển thị: 'Quý 3/2026' hoặc 'Tháng 5/2026'."""
    if tc_theo_quy(thang, nam):
        return f"Quý {quy_cua_thang(thang)}/{nam}"
    return f"Tháng {thang}/{nam}"


def loai_ky(thang: int, nam: int) -> str:
    """'QUY' hoặc 'THANG' — FE dùng để đổi bộ chọn kỳ."""
    return "QUY" if tc_theo_quy(thang, nam) else "THANG"


def thong_tin_ky(thang: int, nam: int) -> dict:
    """Gói thông tin kỳ trả về cho FE (đính kèm mọi response tiêu chí chung)."""
    return {
        "ky": loai_ky(thang, nam),
        "quy": quy_cua_thang(thang) if tc_theo_quy(thang, nam) else None,
        "thang_neo": thang_neo(thang, nam),
        "cac_thang_ap_dung": cac_thang_ap_dung(thang, nam),
        "nhan_ky": nhan_ky(thang, nam),
    }


def ky_thang_con_hieu_luc(thang: int, nam: int) -> bool:
    """
    Kỳ đánh giá, xếp loại THÁNG còn hiệu lực với tháng/năm này không.

    CV 21169 thay thế các văn bản hướng dẫn đánh giá hằng tháng của Chi cục, và
    "từ quý III/2026 kỳ đánh giá, xếp loại trên Phần mềm được thiết lập theo quý"
    → từ mốc TC_THEO_QUY_TU, KHÔNG lập mới báo cáo/phiếu đánh giá theo tháng nữa.
    Dữ liệu tháng đã có vẫn đọc và in được bình thường.
    """
    return not tc_theo_quy(thang, nam)


def ky_da_bat_dau(thang: int, nam: int, hom_nay: Optional[date] = None) -> bool:
    """
    Kỳ đã bắt đầu hay chưa (dùng thay cho phép so sánh tháng <= hôm nay).

    Với kỳ theo quý, phiếu neo ở THÁNG CUỐI quý nên tháng neo có thể nằm ở
    tương lai trong khi quý đã bắt đầu (ví dụ chấm Quý IV vào tháng 10, phiếu
    neo ở T12). Khi đó vẫn phải cho chấm.
    """
    hom_nay = hom_nay or date.today()
    if tc_theo_quy(thang, nam):
        return (int(nam), quy_cua_thang(thang)) <= (
            hom_nay.year,
            quy_cua_thang(hom_nay.month),
        )
    return (int(nam), int(thang)) <= (hom_nay.year, hom_nay.month)
