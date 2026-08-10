"""
common_service/services/zalo/phone.py
======================================
Chuẩn hóa số điện thoại Việt Nam về định dạng ZNS yêu cầu: 84xxxxxxxxx.

Module thuần túy — không đụng DB, không gọi mạng, nên test được đầy đủ mà
chưa cần credential Zalo.

Dữ liệu số điện thoại do người nhập tay (danh sách TCCB, Excel) thường lẫn:
    0913000001      → 84913000001
    +84 913 000 001 → 84913000001
    0084913000001   → 84913000001
    913000001       → 84913000001   (thiếu số 0 đầu do Excel ăn mất)
    0163.123.4567   → 84331234567   (số 11 chữ số cũ, đã chuyển đổi năm 2018)
    0203 3826 xxx   → LOẠI (số cố định, không có Zalo)
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

# --- Kết quả chuẩn hóa ------------------------------------------------------
OK = "OK"
OK_SO_CU = "OK_SO_CU"  # hợp lệ nhưng là số 11 chữ số cũ đã được chuyển đổi
RONG = "RONG"
SAI_DINH_DANG = "SAI_DINH_DANG"
SO_CO_DINH = "SO_CO_DINH"
DAU_SO_LA = "DAU_SO_LA"


@dataclass(frozen=True)
class KetQuaChuanHoa:
    """Kết quả chuẩn hóa 1 số điện thoại."""

    so_goc: str
    so_chuan: Optional[str]  # dạng 84xxxxxxxxx, None nếu không hợp lệ
    trang_thai: str
    ghi_chu: str = ""

    @property
    def hop_le(self) -> bool:
        return self.trang_thai in (OK, OK_SO_CU)


# Bảng chuyển đổi đầu số 11 chữ số → 10 chữ số (áp dụng từ 15/9/2018).
# Khóa là 4 ký tự đầu (gồm số 0), giá trị là đầu số mới 3 ký tự (gồm số 0).
_DAU_SO_CU_MOI = {
    # Viettel: 016x → 03x
    "0162": "032", "0163": "033", "0164": "034", "0165": "035",
    "0166": "036", "0167": "037", "0168": "038", "0169": "039",
    # VinaPhone: 0120-0129 → 08x
    "0120": "070", "0121": "079", "0122": "077", "0126": "076", "0128": "078",
    "0123": "083", "0124": "084", "0125": "085", "0127": "081", "0129": "082",
    # Vietnamobile / Gmobile
    "0186": "056", "0188": "058", "0199": "059",
}

# Đầu số di động hợp lệ (2 chữ số đầu của phần 9 chữ số, tức sau mã 84)
_DAU_SO_DI_DONG = {
    # Viettel
    "32", "33", "34", "35", "36", "37", "38", "39", "86", "96", "97", "98",
    # VinaPhone
    "81", "82", "83", "84", "85", "88", "91", "94",
    # MobiFone
    "70", "76", "77", "78", "79", "89", "90", "93",
    # Vietnamobile
    "52", "56", "58", "92",
    # Gmobile
    "59", "99",
    # Itelecom
    "87",
}


def chuan_hoa(so: Optional[str]) -> KetQuaChuanHoa:
    """Chuẩn hóa 1 số điện thoại về dạng 84xxxxxxxxx.

    Trả về KetQuaChuanHoa — luôn giữ lại số gốc để đối chiếu khi cần.
    """
    so_goc = (so or "").strip()
    if not so_goc:
        return KetQuaChuanHoa(so_goc, None, RONG, "Ô trống")

    # Bỏ mọi ký tự không phải chữ số, trừ dấu + ở đầu
    s = re.sub(r"[^\d+]", "", so_goc)
    if s.startswith("+"):
        s = s[1:]
    s = re.sub(r"\D", "", s)

    if not s:
        return KetQuaChuanHoa(so_goc, None, SAI_DINH_DANG, "Không chứa chữ số nào")

    ghi_chu = ""

    # 0084xxxxxxxxx → 84xxxxxxxxx
    if s.startswith("0084"):
        s = s[2:]

    # Số cố định phải loại SỚM, trước nhánh quy đổi số 11 chữ số: máy bàn cũng
    # dài 11 chữ số (ví dụ 0203 3826 123 của Quảng Ninh) nên nếu để xuống dưới
    # sẽ bị bảng quy đổi 2018 bắt nhầm và báo sai lý do.
    if (s.startswith("0") and s[1:2] == "2") or (s.startswith("84") and s[2:3] == "2"):
        return KetQuaChuanHoa(
            so_goc, None, SO_CO_DINH, "Số máy bàn, không nhận được tin Zalo"
        )

    # Số 11 chữ số cũ (bắt đầu bằng 0, dài 11) → tra bảng chuyển đổi 2018
    if len(s) == 11 and s.startswith("0"):
        dau_cu = s[:4]
        dau_moi = _DAU_SO_CU_MOI.get(dau_cu)
        if dau_moi:
            s = dau_moi + s[4:]
            ghi_chu = f"Số cũ {dau_cu} đã chuyển thành {dau_moi} (quy đổi 2018)"
        else:
            return KetQuaChuanHoa(
                so_goc, None, DAU_SO_LA,
                f"Số 11 chữ số với đầu {dau_cu} không có trong bảng quy đổi",
            )

    # Đưa về dạng 84 + 9 chữ số
    if s.startswith("84") and len(s) == 11:
        phan_thue_bao = s[2:]
    elif s.startswith("0") and len(s) == 10:
        phan_thue_bao = s[1:]
    elif len(s) == 9:
        # Excel hay ăn mất số 0 đứng đầu khi ô để kiểu Number
        phan_thue_bao = s
        ghi_chu = (ghi_chu + "; " if ghi_chu else "") + "Thiếu số 0 đầu, đã tự bù"
    else:
        return KetQuaChuanHoa(
            so_goc, None, SAI_DINH_DANG,
            f"Độ dài {len(s)} chữ số không khớp định dạng số Việt Nam",
        )

    # Số cố định bắt đầu bằng 2 (ví dụ 0203 của Quảng Ninh) — không dùng Zalo được
    if phan_thue_bao.startswith("2"):
        return KetQuaChuanHoa(
            so_goc, None, SO_CO_DINH, "Số máy bàn, không nhận được tin Zalo"
        )

    if phan_thue_bao[:2] not in _DAU_SO_DI_DONG:
        return KetQuaChuanHoa(
            so_goc, None, DAU_SO_LA,
            f"Đầu số {phan_thue_bao[:2]} không thuộc nhà mạng di động Việt Nam",
        )

    so_chuan = "84" + phan_thue_bao
    trang_thai = OK_SO_CU if "quy đổi 2018" in ghi_chu else OK
    return KetQuaChuanHoa(so_goc, so_chuan, trang_thai, ghi_chu)


# Dấu ngăn giữa NHIỀU số trong cùng một ô. KHÔNG gồm khoảng trắng và dấu chấm
# vì hai ký tự đó là định dạng BÊN TRONG một số ("0913 000 001", "0913.000.001").
_DAU_NGAN = re.compile(r"[;\n\r,/|]+")


def tach_nhieu(chuoi: Optional[str]) -> list[str]:
    """Tách ô có thể chứa nhiều số thành danh sách chuỗi con.

    Thực tế danh sách do đơn vị lập: 56/548 người khai 2 số trong cùng một ô,
    ngăn bằng dấu ';' hoặc xuống dòng.
    """
    if not chuoi:
        return []
    return [p.strip() for p in _DAU_NGAN.split(str(chuoi)) if p.strip()]


def chuan_hoa_uu_tien(chuoi: Optional[str]) -> tuple[KetQuaChuanHoa, list[str]]:
    """Chuẩn hóa ô có thể chứa nhiều số.

    Trả về (số hợp lệ ĐẦU TIÊN, danh sách các số hợp lệ còn lại).
    Lấy số đầu vì đó thường là số chính người ta khai trước.
    Nếu không số nào hợp lệ thì trả về kết quả lỗi của số đầu tiên để giữ
    nguyên lý do cụ thể (rỗng / sai định dạng / máy bàn / đầu số lạ).
    """
    phan = tach_nhieu(chuoi)
    if not phan:
        return chuan_hoa(chuoi), []

    ket_qua = [chuan_hoa(p) for p in phan]
    hop_le = [k for k in ket_qua if k.hop_le]
    if not hop_le:
        return ket_qua[0], []
    return hop_le[0], [k.so_chuan for k in hop_le[1:] if k.so_chuan]


def hien_thi(so_chuan: Optional[str]) -> str:
    """Đổi 84913000001 → 0913 000 001 để hiển thị cho người dùng đọc."""
    if not so_chuan or not so_chuan.startswith("84") or len(so_chuan) != 11:
        return so_chuan or ""
    tb = so_chuan[2:]
    return f"0{tb[:3]} {tb[3:6]} {tb[6:]}"


def che_giau(so_chuan: Optional[str]) -> str:
    """Che bớt số để ghi log/hiển thị: 84913000001 → 0913***001.

    Dùng khi in ra log — số điện thoại là dữ liệu cá nhân theo Nghị định
    13/2023/NĐ-CP, không nên ghi nguyên vẹn vào file log.
    """
    if not so_chuan or len(so_chuan) < 7:
        return "***"
    tb = so_chuan[2:] if so_chuan.startswith("84") else so_chuan
    return f"0{tb[:3]}***{tb[-3:]}"
