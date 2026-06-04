"""
chi_tieu_service/constants.py
=============================
Hang so: trang thai, hanh dong, machine chuyen trang thai, tinh nhan danh gia.
"""

from decimal import Decimal
from typing import Optional


# ---- Trang thai vong doi ----
class TrangThai:
    NHAP = "NHAP"
    CHO_DUYET_DANG_KY = "CHO_DUYET_DANG_KY"
    DA_DUYET_DANG_KY = "DA_DUYET_DANG_KY"
    CHO_DUYET_SUA = "CHO_DUYET_SUA"
    CHO_DUYET_KET_QUA = "CHO_DUYET_KET_QUA"
    DA_DUYET_KET_QUA = "DA_DUYET_KET_QUA"


# ---- Hanh dong audit ----
class HanhDong:
    GUI_DANG_KY = "GUI_DANG_KY"
    DUYET_DANG_KY = "DUYET_DANG_KY"
    TU_CHOI_DANG_KY = "TU_CHOI_DANG_KY"
    GUI_SUA = "GUI_SUA"
    DUYET_SUA = "DUYET_SUA"
    TU_CHOI_SUA = "TU_CHOI_SUA"
    GUI_KET_QUA = "GUI_KET_QUA"
    DUYET_KET_QUA = "DUYET_KET_QUA"
    TU_CHOI_KET_QUA = "TU_CHOI_KET_QUA"
    MO_KHOA = "MO_KHOA"


# ---- Loai hang cho duyet (query param) -> trang thai cho tuong ung ----
LOAI_CHO_DUYET = {
    "DANG_KY": TrangThai.CHO_DUYET_DANG_KY,
    "SUA": TrangThai.CHO_DUYET_SUA,
    "KET_QUA": TrangThai.CHO_DUYET_KET_QUA,
}

# ---- Khi DUYET: trang thai hien tai -> trang thai sau ----
DUYET_TRANSITION = {
    TrangThai.CHO_DUYET_DANG_KY: TrangThai.DA_DUYET_DANG_KY,
    TrangThai.CHO_DUYET_SUA: TrangThai.DA_DUYET_DANG_KY,
    TrangThai.CHO_DUYET_KET_QUA: TrangThai.DA_DUYET_KET_QUA,
}

# ---- Khi TU CHOI: trang thai hien tai -> trang thai quay ve ----
# - Tu choi dang ky lan dau  -> ve NHAP (soan lai)
# - Tu choi yeu cau sua      -> ve DA_DUYET_DANG_KY (huy sua, giu gia tri cu)
# - Tu choi ket qua          -> ve DA_DUYET_DANG_KY (nhap lai ket qua, GIU gia_tri_ket_qua cu)
TU_CHOI_TRANSITION = {
    TrangThai.CHO_DUYET_DANG_KY: TrangThai.NHAP,
    TrangThai.CHO_DUYET_SUA: TrangThai.DA_DUYET_DANG_KY,
    TrangThai.CHO_DUYET_KET_QUA: TrangThai.DA_DUYET_DANG_KY,
}

# ---- Hanh dong audit tuong ung khi duyet/tu choi ----
HANH_DONG_DUYET = {
    TrangThai.CHO_DUYET_DANG_KY: HanhDong.DUYET_DANG_KY,
    TrangThai.CHO_DUYET_SUA: HanhDong.DUYET_SUA,
    TrangThai.CHO_DUYET_KET_QUA: HanhDong.DUYET_KET_QUA,
}
HANH_DONG_TU_CHOI = {
    TrangThai.CHO_DUYET_DANG_KY: HanhDong.TU_CHOI_DANG_KY,
    TrangThai.CHO_DUYET_SUA: HanhDong.TU_CHOI_SUA,
    TrangThai.CHO_DUYET_KET_QUA: HanhDong.TU_CHOI_KET_QUA,
}

# ---- Platform roles ----
ROLE_THEO_DOI = "THEO_DOI_CHI_TIEU"
ROLE_QUAN_TRI = "QT_CHI_TIEU"

# ---- Vai tro he thong duoc duyet (Truong don vi) ----
VAI_TRO_DUYET = {"TDV"}
# Vai tro duoc xem/mo khoa toan Chi cuc
VAI_TRO_LANH_DAO_CHI_CUC = {"CCT", "PCCT", "SUPER_ADMIN"}


def tinh_dat_phan_tram(
    gia_tri_ket_qua: Optional[Decimal], gia_tri_dang_ky: Optional[Decimal]
) -> Optional[Decimal]:
    """
    Dat%_thang = (ket qua / dang ky) * 100.
    Tra None neu khong dang ky hoac dang ky = 0 (khong tinh %).
    """
    if gia_tri_ket_qua is None or not gia_tri_dang_ky:
        return None
    if Decimal(gia_tri_dang_ky) == 0:
        return None
    return (Decimal(gia_tri_ket_qua) / Decimal(gia_tri_dang_ky) * 100).quantize(Decimal("0.01"))


def tinh_nhan_danh_gia_tu_dong(
    khong_dang_ky: bool,
    gia_tri_ket_qua: Optional[Decimal],
    gia_tri_dang_ky: Optional[Decimal],
) -> Optional[str]:
    """
    Tinh nhan goi y tu dong (danh_gia_tu_dong). Phai goi lai moi khi so lieu thay doi.
      - Khong dang ky                 -> "Khong dang ky"
      - Co dang ky, chua co ket qua    -> None (chua danh gia)
      - Ket qua = 0, co dang ky        -> "Chua dat"
      - Dat% >= 100                    -> "Vuot chi tieu (Dat {x}%)"
      - 0 < Dat% < 100                 -> "Dat {x}%"
    """
    if khong_dang_ky:
        return "Khong dang ky"
    if gia_tri_ket_qua is None:
        return None
    pct = tinh_dat_phan_tram(gia_tri_ket_qua, gia_tri_dang_ky)
    if pct is None:
        # Co ket qua nhung khong tinh duoc % (dang ky rong/0)
        if Decimal(gia_tri_ket_qua) == 0:
            return "Chua dat"
        return None
    if Decimal(gia_tri_ket_qua) == 0:
        return "Chua dat"
    pct_str = f"{pct.normalize():f}"
    if pct >= 100:
        return f"Vuot chi tieu (Dat {pct_str}%)"
    return f"Dat {pct_str}%"
