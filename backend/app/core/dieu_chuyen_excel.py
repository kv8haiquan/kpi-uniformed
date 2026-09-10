"""
app/core/dieu_chuyen_excel.py
=============================
Sinh file mẫu và đọc file điều chuyển hàng loạt theo quyết định.

VÌ SAO CÓ MODULE NÀY
--------------------
Một quyết định điều động là MỘT sự kiện: một ngày hiệu lực, một danh sách người.
Giao diện cũ bắt nhập lẻ từng người, và hậu quả đo được trên dữ liệu thật:

    • đợt 04/02/2026 — bỏ quên trọn 62 người, không ai vào hệ thống
    • đợt 03/7/2026  — nhập được 1/3 người
    • đợt 15/5/2026  — ngày hiệu lực rải ra 6 ngày vì nhập nhiều buổi
    • 4 người nhập nhầm đơn vị, phải chuyển đi/chuyển lại → 8 bản ghi rác

(chi tiết: `docs/Fix-dieu-chuyen-don-vi/PLAN_SUA_NGAY_DIEU_CHUYEN.md`)

VÌ SAO KHÓA LÀ `Mã CC`, KHÔNG PHẢI HỌ TÊN
------------------------------------------
File theo dõi điều động của TCCB chỉ có cột `Họ và tên`, không có mã. Khớp theo
tên đã hỏng ở đợt 2026: 5 người không khớp vì DB gắn hậu tố năm sinh
("Nguyễn Viết Cường 1971") còn Excel ghi tên trần; 8/142 dòng có nhiều người
trùng tên gốc; một ca phải tra bốn nguồn mới tách được. Bỏ dấu còn nguy hiểm hơn
— "Trần Văn Tuyên" và "Trần Văn Tuyển" giống nhau tới 93%.

Nên module này KHÔNG khớp theo tên. Mã CC gõ sai thì hoặc không tìm thấy (báo
lỗi to), hoặc trỏ sang người khác — mà bảng xem trước dội lại họ tên + đơn vị
hiện tại nên người nhập nhìn là thấy. Khác hẳn khớp theo tên: sai mà im lặng.

Mẫu có 4 sheet. Chỉ `Nhap lieu` được đọc; ba sheet còn lại là tra cứu cho người
điền, hệ thống bỏ qua hoàn toàn.
"""

from __future__ import annotations

import io
import re
import unicodedata
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

# =============================================================================
# HẰNG SỐ
# =============================================================================

SHEET_NHAP_LIEU = "Nhap lieu"
SHEET_HUONG_DAN = "Huong dan"
SHEET_DANH_SACH = "Danh sach cong chuc"
SHEET_MA_DON_VI = "Ma don vi"

COT_MA_CC = "Mã CC"
COT_DON_VI_DEN = "Đơn vị đến"
COT_NGAY_HIEU_LUC = "Ngày hiệu lực"
COT_SO_QD = "Số QĐ"

TIEU_DE_NHAP_LIEU = [COT_MA_CC, COT_DON_VI_DEN, COT_NGAY_HIEU_LUC, COT_SO_QD]

# Chặn file khổng lồ / bảng tính rác. Đợt lớn nhất từng có là 142 người.
GIOI_HAN_DONG = 1000

# Lệch quá ngần này ngày so với hôm nay thì cảnh báo (không chặn) — dấu hiệu
# nhập muộn cả đợt hoặc gõ nhầm tháng/năm. Cùng ngưỡng với form nhập lẻ.
NGUONG_CANH_BAO_NGAY = 15

MAU_TIEU_DE = PatternFill("solid", fgColor="1F4E79")
MAU_O_PHAI_DIEN = PatternFill("solid", fgColor="FFF2CC")
MAU_O_TRA_CUU = PatternFill("solid", fgColor="F2F2F2")


# =============================================================================
# KẾT QUẢ ĐỌC FILE
# =============================================================================

class TrangThaiDong:
    """Trạng thái một dòng sau khi đối chiếu với DB."""

    GHI_MOI = "GHI_MOI"          # ✅ hợp lệ, sẽ ghi
    BO_QUA = "BO_QUA"            # ⏭️ đã ở đúng đơn vị rồi
    LOI = "LOI"                  # ❌ không ghi được


@dataclass
class DongNhap:
    """Một dòng của sheet `Nhap lieu`, đã đối chiếu với DB."""

    dong_excel: int
    ma_cc: str
    don_vi_den_nhap: str
    ngay_hieu_luc: Optional[date]
    so_qd: Optional[str]

    # Điền sau khi đối chiếu DB
    trang_thai: str = TrangThaiDong.LOI
    ho_ten: Optional[str] = None
    don_vi_hien_tai: Optional[str] = None
    cong_chuc_id: Optional[object] = None
    don_vi_den_id: Optional[object] = None
    don_vi_den_ma: Optional[str] = None
    loi: list[str] = field(default_factory=list)
    canh_bao: list[str] = field(default_factory=list)


@dataclass
class KetQuaDoc:
    dong: list[DongNhap] = field(default_factory=list)
    loi_chung: list[str] = field(default_factory=list)

    @property
    def so_ghi_moi(self) -> int:
        return sum(1 for d in self.dong if d.trang_thai == TrangThaiDong.GHI_MOI)

    @property
    def so_bo_qua(self) -> int:
        return sum(1 for d in self.dong if d.trang_thai == TrangThaiDong.BO_QUA)

    @property
    def so_loi(self) -> int:
        return sum(1 for d in self.dong if d.trang_thai == TrangThaiDong.LOI)

    @property
    def ghi_duoc(self) -> bool:
        """Chỉ cho ghi khi KHÔNG còn dòng lỗi — thà bắt sửa file còn hơn ghi
        một nửa rồi để người dùng tự đoán nửa nào đã vào."""
        return not self.loi_chung and self.so_loi == 0 and self.so_ghi_moi > 0


# =============================================================================
# SINH FILE MẪU
# =============================================================================

def _dat_tieu_de(ws, tieu_de: list[str], do_rong: list[int]) -> None:
    for i, (ten, rong) in enumerate(zip(tieu_de, do_rong), start=1):
        o = ws.cell(row=1, column=i, value=ten)
        o.font = Font(bold=True, color="FFFFFF")
        o.fill = MAU_TIEU_DE
        o.alignment = Alignment(horizontal="center", vertical="center")
        ws.column_dimensions[get_column_letter(i)].width = rong
    ws.freeze_panes = "A2"


def _sheet_nhap_lieu(wb: Workbook, so_don_vi: int) -> None:
    ws = wb.create_sheet(SHEET_NHAP_LIEU)
    _dat_tieu_de(ws, TIEU_DE_NHAP_LIEU, [14, 18, 16, 28])

    # Tô vàng vùng cần điền để người dùng biết gõ vào đâu.
    for hang in range(2, 202):
        for cot in range(1, 5):
            ws.cell(row=hang, column=cot).fill = MAU_O_PHAI_DIEN
        ws.cell(row=hang, column=3).number_format = "DD/MM/YYYY"

    # Dropdown đơn vị đến, trỏ sang sheet tra cứu.
    # Đây là TIỆN LỢI, không phải bảo đảm: copy-paste đè lên là mất validation.
    # Lưới an toàn thật là bảng xem trước trước khi ghi.
    dv = DataValidation(
        type="list",
        formula1=f"'{SHEET_MA_DON_VI}'!$A$2:$A${so_don_vi + 1}",
        allow_blank=True,
        showDropDown=False,   # False = CÓ hiện mũi tên (openpyxl đặt tên ngược)
    )
    dv.error = "Chọn viết tắt đơn vị trong danh sách (xem sheet 'Ma don vi')"
    dv.errorTitle = "Đơn vị không hợp lệ"
    ws.add_data_validation(dv)
    dv.add(f"B2:B{201}")


def _sheet_huong_dan(wb: Workbook) -> None:
    ws = wb.create_sheet(SHEET_HUONG_DAN)
    ws.column_dimensions["A"].width = 4
    ws.column_dimensions["B"].width = 104

    dong = [
        ("tieu_de", "HƯỚNG DẪN ĐIỀN FILE ĐIỀU CHUYỂN HÀNG LOẠT"),
        ("trong", ""),
        ("muc", "1. Chỉ điền vào sheet 'Nhap lieu'"),
        ("thuong", "Ba sheet còn lại là để tra cứu. Hệ thống KHÔNG đọc chúng."),
        ("trong", ""),
        ("muc", "2. Bốn cột cần điền"),
        ("thuong", "• Mã CC — BẮT BUỘC. Copy từ sheet 'Danh sach cong chuc', đừng gõ tay."),
        ("thuong", "• Đơn vị đến — BẮT BUỘC. Chọn viết tắt từ danh sách xổ xuống."),
        ("thuong", "• Ngày hiệu lực — BẮT BUỘC. Ngày ghi TRONG QUYẾT ĐỊNH, không phải ngày nhập."),
        ("thuong", "• Số QĐ — không bắt buộc. Điền được thì sau này tra cứu dễ hơn nhiều."),
        ("trong", ""),
        ("muc", "3. Mỗi dòng một ngày hiệu lực riêng"),
        ("thuong", "Một file chứa được nhiều đợt cùng lúc. Không cần tải mẫu nhiều lần."),
        ("trong", ""),
        ("muc", "4. Dòng trống thì bỏ qua"),
        ("thuong", "Không cần xoá dòng thừa. Dòng nào không điền Mã CC thì hệ thống bỏ qua."),
        ("trong", ""),
        ("muc", "5. Ví dụ"),
        ("vidu", "    Mã CC        | Đơn vị đến | Ngày hiệu lực | Số QĐ"),
        ("vidu", "    20ZZ-0399    | HM         | 04/02/2026    | 45/QĐ-HQKV8"),
        ("vidu", "    20ZZ-0374    | BPS        | 04/02/2026    | 45/QĐ-HQKV8"),
        ("vidu", "    20ZZ-0527    | KS         | 03/07/2026    | 78/QĐ-HQKV8"),
        ("thuong", "(Ví dụ để ở đây, KHÔNG để trên sheet nhập — tránh có lần quên xoá rồi nhập nhầm vào thật.)"),
        ("trong", ""),
        ("muc", "6. Sau khi điền xong"),
        ("thuong", "Tải file lên, hệ thống hiện BẢNG XEM TRƯỚC: mã CC, họ tên, đơn vị hiện tại → đơn vị đến."),
        ("thuong", "ĐỐI CHIẾU HỌ TÊN trong bảng đó trước khi bấm xác nhận — gõ nhầm một chữ số"),
        ("thuong", "trong mã CC sẽ trỏ sang người khác, và đây là chỗ duy nhất phát hiện được."),
        ("thuong", "Còn dòng lỗi thì hệ thống không cho ghi; sửa file rồi tải lại."),
    ]

    kieu = {
        "tieu_de": Font(bold=True, size=14, color="1F4E79"),
        "muc": Font(bold=True, size=11),
        "thuong": Font(size=11),
        "vidu": Font(size=10, name="Consolas"),
    }
    for i, (loai, text) in enumerate(dong, start=1):
        if loai == "trong":
            continue
        o = ws.cell(row=i, column=2, value=text)
        o.font = kieu[loai]
        o.alignment = Alignment(vertical="center", wrap_text=False)


def _sheet_danh_sach(wb: Workbook, cong_chuc: list[tuple[str, str, str]]) -> None:
    """cong_chuc: [(ma_cc, ho_ten, ma_don_vi_hien_tai)] — đã lọc người còn làm việc."""
    ws = wb.create_sheet(SHEET_DANH_SACH)
    _dat_tieu_de(ws, ["Mã CC", "Họ và tên", "Đơn vị hiện tại"], [14, 30, 18])
    for i, (ma_cc, ho_ten, ma_dv) in enumerate(cong_chuc, start=2):
        ws.cell(row=i, column=1, value=ma_cc).fill = MAU_O_TRA_CUU
        ws.cell(row=i, column=2, value=ho_ten).fill = MAU_O_TRA_CUU
        ws.cell(row=i, column=3, value=ma_dv).fill = MAU_O_TRA_CUU
    ws.auto_filter.ref = f"A1:C{max(len(cong_chuc) + 1, 2)}"


def _sheet_ma_don_vi(wb: Workbook, don_vi: list[tuple[str, str]]) -> None:
    """don_vi: [(ma_don_vi, ten_don_vi)]"""
    ws = wb.create_sheet(SHEET_MA_DON_VI)
    _dat_tieu_de(ws, ["Viết tắt", "Tên đơn vị"], [16, 46])
    for i, (ma, ten) in enumerate(don_vi, start=2):
        ws.cell(row=i, column=1, value=ma).fill = MAU_O_TRA_CUU
        ws.cell(row=i, column=2, value=ten).fill = MAU_O_TRA_CUU


def sinh_file_mau(
    cong_chuc: list[tuple[str, str, str]],
    don_vi: list[tuple[str, str]],
) -> bytes:
    """
    Sinh file mẫu 4 sheet.

    Sheet `Nhap lieu` để TRỐNG hoàn toàn — danh sách công chức nằm ở sheet tra
    cứu riêng, để người điền copy mã sang. Như vậy không ai phải gõ mã CC bằng
    tay, mà sheet nhập vẫn sạch.
    """
    wb = Workbook()
    wb.remove(wb.active)  # bỏ sheet mặc định

    _sheet_nhap_lieu(wb, so_don_vi=len(don_vi))
    _sheet_huong_dan(wb)
    _sheet_danh_sach(wb, cong_chuc)
    _sheet_ma_don_vi(wb, don_vi)

    wb.active = 0  # mở lên là thấy sheet nhập liệu

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


# =============================================================================
# ĐỌC FILE NGƯỜI DÙNG TẢI LÊN
# =============================================================================

def _chuan_hoa(s) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", str(s)).strip())


def _khong_dau_hoa(s) -> str:
    s = _chuan_hoa(s).lower().replace("đ", "d")
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def _doc_ngay(gia_tri) -> tuple[Optional[date], Optional[str]]:
    """Trả (ngày, lỗi). Nhận cả ô kiểu ngày của Excel lẫn chuỗi dd/mm/yyyy."""
    if gia_tri is None or _chuan_hoa(gia_tri) == "":
        return None, "thiếu ngày hiệu lực"
    if isinstance(gia_tri, datetime):
        return gia_tri.date(), None
    if isinstance(gia_tri, date):
        return gia_tri, None

    chuoi = _chuan_hoa(gia_tri)
    for dinh_dang in ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%d/%m/%y"):
        try:
            return datetime.strptime(chuoi, dinh_dang).date(), None
        except ValueError:
            continue
    return None, f"ngày hiệu lực không đọc được: {chuoi!r} (dùng dạng dd/mm/yyyy)"


def doc_sheet_nhap_lieu(noi_dung: bytes) -> tuple[list[DongNhap], list[str]]:
    """
    Đọc sheet `Nhap lieu`. Trả (danh sách dòng, lỗi chung).

    Ở bước này chỉ kiểm tra ĐỊNH DẠNG — chưa đụng DB. Việc đối chiếu mã CC và
    đơn vị nằm ở `doi_chieu_voi_db`.
    """
    try:
        wb = load_workbook(io.BytesIO(noi_dung), data_only=True, read_only=True)
    except Exception as e:
        return [], [f"Không mở được file Excel: {e}"]

    if SHEET_NHAP_LIEU not in wb.sheetnames:
        return [], [
            f"File thiếu sheet '{SHEET_NHAP_LIEU}'. "
            f"Hãy tải lại file mẫu và điền vào đó (các sheet hiện có: {', '.join(wb.sheetnames)})"
        ]

    ws = wb[SHEET_NHAP_LIEU]
    cac_dong: list[DongNhap] = []
    loi_chung: list[str] = []

    for chi_so, hang in enumerate(ws.iter_rows(min_row=2, max_col=4, values_only=True), start=2):
        if chi_so - 1 > GIOI_HAN_DONG:
            loi_chung.append(f"File quá {GIOI_HAN_DONG} dòng — kiểm tra lại, có thể sai file")
            break

        ma_cc_raw, don_vi_raw, ngay_raw, so_qd_raw = (list(hang) + [None] * 4)[:4]

        # Dòng trống hoàn toàn → bỏ qua, không báo lỗi (mẫu để sẵn 200 dòng)
        if all(x is None or _chuan_hoa(x) == "" for x in (ma_cc_raw, don_vi_raw, ngay_raw)):
            continue

        d = DongNhap(
            dong_excel=chi_so,
            ma_cc=_chuan_hoa(ma_cc_raw).upper() if ma_cc_raw is not None else "",
            don_vi_den_nhap=_chuan_hoa(don_vi_raw) if don_vi_raw is not None else "",
            ngay_hieu_luc=None,
            so_qd=_chuan_hoa(so_qd_raw) if so_qd_raw not in (None, "") else None,
        )
        if not d.ma_cc:
            d.loi.append("thiếu Mã CC")
        if not d.don_vi_den_nhap:
            d.loi.append("thiếu Đơn vị đến")

        ngay, loi_ngay = _doc_ngay(ngay_raw)
        d.ngay_hieu_luc = ngay
        if loi_ngay:
            d.loi.append(loi_ngay)

        cac_dong.append(d)

    wb.close()
    return cac_dong, loi_chung


def doi_chieu_voi_db(
    cac_dong: list[DongNhap],
    cong_chuc_theo_ma: dict,      # ma_cc -> đối tượng có .id .ho_ten .don_vi_id .is_active .ma_cc
    don_vi_theo_ma: dict,         # ma_don_vi (chữ hoa) -> đối tượng có .id .ma_don_vi .ten_don_vi
    ma_don_vi_theo_id: dict,      # id -> ma_don_vi
    ma_cc_cam: set[str],
    hom_nay: Optional[date] = None,
) -> KetQuaDoc:
    """
    Đối chiếu từng dòng với DB và gán trạng thái.

    Nguyên tắc: KHÔNG đoán. Dòng nào không chắc thì báo lỗi để người dùng sửa
    file, chứ không tự chọn giúp.
    """
    hom_nay = hom_nay or date.today()
    kq = KetQuaDoc(dong=cac_dong)

    # Trùng mã CC trong cùng file: hai dòng cho một người là mâu thuẫn, không
    # thể biết dòng nào đúng → bắt sửa file.
    dem_ma: dict[str, int] = {}
    for d in cac_dong:
        if d.ma_cc:
            dem_ma[d.ma_cc] = dem_ma.get(d.ma_cc, 0) + 1

    # Tra đơn vị theo viết tắt, có nới cho người gõ tên đầy đủ
    dv_theo_ten_khong_dau = {
        _khong_dau_hoa(dv.ten_don_vi): dv for dv in don_vi_theo_ma.values()
    }

    for d in cac_dong:
        if d.ma_cc and dem_ma.get(d.ma_cc, 0) > 1:
            d.loi.append(f"Mã CC xuất hiện {dem_ma[d.ma_cc]} lần trong file")

        # --- Công chức ---
        cc = cong_chuc_theo_ma.get(d.ma_cc) if d.ma_cc else None
        if d.ma_cc and cc is None:
            d.loi.append(f"không có công chức nào mã {d.ma_cc}")
        elif cc is not None:
            d.ho_ten = cc.ho_ten
            d.cong_chuc_id = cc.id
            d.don_vi_hien_tai = ma_don_vi_theo_id.get(cc.don_vi_id)
            if cc.ma_cc in ma_cc_cam:
                d.loi.append("không thao tác được với tài khoản này")
            elif not cc.is_active:
                d.loi.append("công chức đã ngừng hoạt động")

        # --- Đơn vị đến ---
        if d.don_vi_den_nhap:
            khoa = d.don_vi_den_nhap.upper()
            dv = don_vi_theo_ma.get(khoa) or dv_theo_ten_khong_dau.get(
                _khong_dau_hoa(d.don_vi_den_nhap)
            )
            if dv is None:
                d.loi.append(f"đơn vị đến không hợp lệ: {d.don_vi_den_nhap!r}")
            else:
                d.don_vi_den_id = dv.id
                d.don_vi_den_ma = dv.ma_don_vi

        # --- Ngày ---
        if d.ngay_hieu_luc:
            lech = (d.ngay_hieu_luc - hom_nay).days
            if lech > NGUONG_CANH_BAO_NGAY:
                d.canh_bao.append(f"ngày hiệu lực ở {lech} ngày trong tương lai")
            elif lech < -NGUONG_CANH_BAO_NGAY:
                d.canh_bao.append(f"nhập muộn {abs(lech)} ngày so với ngày hiệu lực")

        # --- Kết luận ---
        if d.loi:
            d.trang_thai = TrangThaiDong.LOI
        elif cc is not None and d.don_vi_den_id == cc.don_vi_id:
            d.trang_thai = TrangThaiDong.BO_QUA
            d.canh_bao.append("đã ở đúng đơn vị này rồi")
        else:
            d.trang_thai = TrangThaiDong.GHI_MOI

    return kq
