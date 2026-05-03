"""
app/core/kpi_calculator_v2.py
=============================
Helper tính toán KPI cho phiên bản V2_PL3 (28/04/2026).

Khác với V1:
- Mẫu số = SUM(so_sp_goc_quy_doi) của bản kê khai đã phê duyệt trong tháng
  (V1: ngày làm việc × 96).
- Hệ số quy đổi đọc thẳng từ danh_muc_sp_cong_viec.he_so_quy_doi
  (V1: nhân với cap_do.he_so_sp1/sp2).
- Công thức trừ điểm tuyến tính GIỮ NGUYÊN từ V1 (LOCKED 3).

Decimal xuyên suốt mọi tính toán; làm tròn chỉ ở display layer.

LOCKED references:
  - 1: Mẫu số V2 = SUM(so_sp_goc_quy_doi) bản đã duyệt
  - 2: Hệ số V2 lấy thẳng từ danh_muc_sp_cong_viec.he_so_quy_doi
  - 3: Công thức trừ điểm CL/TĐ tuyến tính giữ nguyên
  - 5: Mẫu số = 0 → KPI = 0 → tự xếp D
"""

from decimal import Decimal
from typing import Optional


# Hằng số dùng nhiều lần
_HALF = Decimal("0.25")
_FOUR = Decimal("4")
_ZERO = Decimal("0")
_ONE = Decimal("1")
_THREE = Decimal("3")


def calculate_so_sp_goc_quy_doi_v2(
    so_luong: int,
    he_so_quy_doi: Decimal,
) -> Decimal:
    """
    V2: số SP gốc quy đổi = số lượng × hệ số (lấy thẳng từ PL3).

    KHÔNG nhân thêm hệ số cấp độ như V1 (V2 không dùng C1-C5).

    Args:
        so_luong: Số lượng công việc kê khai (≥ 1, nguyên — LOCKED 17).
        he_so_quy_doi: Hệ số quy đổi từ danh_muc_sp_cong_viec.he_so_quy_doi
                       (= diem_cham / 25). Decimal(8, 4).

    Returns:
        Số SP gốc quy đổi (Decimal).

    Raises:
        ValueError: Nếu so_luong ≤ 0 hoặc he_so_quy_doi ≤ 0.
    """
    if so_luong <= 0:
        raise ValueError(f"so_luong phải > 0, nhận {so_luong}")
    if he_so_quy_doi <= _ZERO:
        raise ValueError(f"he_so_quy_doi phải > 0, nhận {he_so_quy_doi}")
    return Decimal(str(so_luong)) * he_so_quy_doi


def calculate_sp_dat_v2(
    so_luong: int,
    he_so_quy_doi: Decimal,
    so_lan_loi: int,
) -> Decimal:
    """
    Tính SP đạt CL hoặc đạt TĐ sau khi trừ lỗi.

    Công thức tuyến tính (LOCKED 3 — y nguyên V1):
        sp_dat = he_so × (so_luong - 0.25 × min(so_lan_loi, so_luong × 4))

    Mỗi lần lỗi trừ 25% của 1 đơn vị; tối đa 4 lỗi/đơn vị (= -100%).
    Kết quả không âm.

    Hoạt động đúng với he_so thập phân (vd 6.4, 9.2 — đặc trưng của PL3).

    Args:
        so_luong: Số lượng kê khai (> 0).
        he_so_quy_doi: Hệ số quy đổi PL3.
        so_lan_loi: Số lần lỗi (≥ 0).

    Returns:
        SP đạt sau khi trừ lỗi (Decimal, ≥ 0).
    """
    if so_luong <= 0 or he_so_quy_doi <= _ZERO:
        return _ZERO
    if so_lan_loi < 0:
        so_lan_loi = 0

    so_luong_d = Decimal(str(so_luong))
    so_lan_loi_d = Decimal(str(so_lan_loi))
    max_loi = so_luong_d * _FOUR
    loi_tinh = min(so_lan_loi_d, max_loi)

    factor = so_luong_d - _HALF * loi_tinh
    result = he_so_quy_doi * factor
    return max(result, _ZERO)


def calculate_kpi_score_v2(
    tong_sp_hoan_thanh_quy_doi: Decimal,
    tong_sp_dat_cl_quy_doi: Decimal,
    tong_sp_dat_td_quy_doi: Decimal,
    tong_sp_ke_khai: Decimal,
) -> dict:
    """
    Tính 3 chỉ số a, b, c và điểm KPI tổng (tỷ lệ 0-1).

    Công thức:
        a = tong_sp_hoan_thanh / tong_sp_ke_khai
        b = tong_sp_dat_cl    / tong_sp_ke_khai  (chất lượng)
        c = tong_sp_dat_td    / tong_sp_ke_khai  (tiến độ)
        kpi = (a + b + c) / 3

    Edge case (LOCKED 5):
        tong_sp_ke_khai == 0 → trả về tất cả 0 với ly_do='MAU_SO_BANG_0'.
        Caller sẽ tự xếp mức D theo nghiệp vụ.

    Cap defensive: a, b, c đều cap ≤ 1.0 (mặc dù mathematically ≤ 1
    do cùng tập kê khai, nhưng vẫn cap để an toàn).

    Args:
        tong_sp_hoan_thanh_quy_doi: SUM(so_sp_goc_quy_doi) bản đã duyệt.
        tong_sp_dat_cl_quy_doi: SUM(so_sp_chat_luong) bản đã duyệt.
        tong_sp_dat_td_quy_doi: SUM(so_sp_tien_do) bản đã duyệt.
        tong_sp_ke_khai: Mẫu số V2 (= tong_sp_hoan_thanh_quy_doi nhưng
                         được truyền vào tường minh để dễ test).

    Returns:
        dict với keys: a, b, c, kpi (Decimal), ly_do (str|None).
    """
    if tong_sp_ke_khai <= _ZERO:
        return {
            "a": _ZERO,
            "b": _ZERO,
            "c": _ZERO,
            "kpi": _ZERO,
            "ly_do": "MAU_SO_BANG_0",
        }

    a = min(_ONE, tong_sp_hoan_thanh_quy_doi / tong_sp_ke_khai)
    b = min(_ONE, tong_sp_dat_cl_quy_doi / tong_sp_ke_khai)
    c = min(_ONE, tong_sp_dat_td_quy_doi / tong_sp_ke_khai)
    kpi = (a + b + c) / _THREE

    return {
        "a": a,
        "b": b,
        "c": c,
        "kpi": kpi,
        "ly_do": None,
    }
