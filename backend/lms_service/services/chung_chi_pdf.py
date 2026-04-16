"""
lms_service/services/chung_chi_pdf.py
=====================================
Sinh PDF chung chi hoan thanh khoa hoc.
Dung reportlab + font DejaVu (ho tro tieng Viet).
"""

import os
from datetime import datetime
from decimal import Decimal
from typing import Optional

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

# Dang ky font DejaVu (ho tro tieng Viet)
_FONT_REGISTERED = False
FONT_REGULAR = "DejaVuSans"
FONT_BOLD = "DejaVuSans-Bold"
FONT_SERIF = "DejaVuSerif"
FONT_SERIF_BOLD = "DejaVuSerif-Bold"


def _register_fonts():
    global _FONT_REGISTERED
    if _FONT_REGISTERED:
        return

    font_dir = "/usr/share/fonts/truetype/dejavu"
    pdfmetrics.registerFont(TTFont(FONT_REGULAR, f"{font_dir}/DejaVuSans.ttf"))
    pdfmetrics.registerFont(TTFont(FONT_BOLD, f"{font_dir}/DejaVuSans-Bold.ttf"))
    pdfmetrics.registerFont(TTFont(FONT_SERIF, f"{font_dir}/DejaVuSerif.ttf"))
    pdfmetrics.registerFont(TTFont(FONT_SERIF_BOLD, f"{font_dir}/DejaVuSerif-Bold.ttf"))
    _FONT_REGISTERED = True


def xep_loai_label(diem: Decimal) -> tuple[str, str]:
    """Tra ve (label, mau_hex) theo diem."""
    d = float(diem) if diem is not None else 0
    if d >= 90:
        return ("XUẤT SẮC", "#DC2626")  # red
    if d >= 80:
        return ("GIỎI", "#F59E0B")  # amber
    if d >= 65:
        return ("KHÁ", "#3B82F6")  # blue
    if d >= 50:
        return ("ĐẠT", "#10B981")  # green
    return ("KHÔNG ĐẠT", "#6B7280")  # gray


def generate_certificate_pdf(
    ma_chung_chi: str,
    ho_ten: str,
    ma_cc: str,
    ten_khoa_hoc: str,
    diem_dat: Decimal,
    ngay_cap: datetime,
    don_vi: Optional[str] = None,
    output_path: Optional[str] = None,
) -> bytes:
    """
    Sinh PDF chung chi.
    - output_path: neu co se ghi file; khong co chi tra ve bytes.
    Returns: bytes cua PDF.
    """
    _register_fonts()

    import io
    buffer = io.BytesIO()

    # A4 landscape
    width, height = landscape(A4)
    c = canvas.Canvas(buffer, pagesize=landscape(A4))

    # === BACKGROUND & BORDER ===
    # Khung ngoai
    c.setStrokeColor(HexColor("#1E40AF"))
    c.setLineWidth(4)
    c.rect(0.8 * cm, 0.8 * cm, width - 1.6 * cm, height - 1.6 * cm)

    # Khung trong (mong hon)
    c.setStrokeColor(HexColor("#93C5FD"))
    c.setLineWidth(1)
    c.rect(1.2 * cm, 1.2 * cm, width - 2.4 * cm, height - 2.4 * cm)

    # Corner decorations (4 goc)
    c.setStrokeColor(HexColor("#1E40AF"))
    c.setLineWidth(2)
    corner_size = 0.6 * cm
    for x, y in [(1.2, 1.2), (width / cm - 1.2, 1.2),
                  (1.2, height / cm - 1.2), (width / cm - 1.2, height / cm - 1.2)]:
        c.line(x * cm - corner_size, y * cm, x * cm + corner_size, y * cm)
        c.line(x * cm, y * cm - corner_size, x * cm, y * cm + corner_size)

    # === HEADER ===
    center_x = width / 2

    # Quoc hieu
    c.setFont(FONT_BOLD, 11)
    c.setFillColor(HexColor("#000000"))
    c.drawCentredString(center_x, height - 1.8 * cm, "CHI CỤC HẢI QUAN KHU VỰC VIII")
    c.setFont(FONT_REGULAR, 10)
    c.drawCentredString(center_x, height - 2.3 * cm, "Trung tâm Đào tạo trực tuyến")

    # Line divider
    c.setStrokeColor(HexColor("#CBD5E1"))
    c.setLineWidth(0.5)
    c.line(center_x - 4 * cm, height - 2.7 * cm, center_x + 4 * cm, height - 2.7 * cm)

    # === TITLE ===
    c.setFont(FONT_SERIF_BOLD, 40)
    c.setFillColor(HexColor("#1E40AF"))
    c.drawCentredString(center_x, height - 4.8 * cm, "CHỨNG NHẬN")

    c.setFont(FONT_BOLD, 16)
    c.setFillColor(HexColor("#374151"))
    c.drawCentredString(center_x, height - 5.8 * cm, "HOÀN THÀNH KHÓA HỌC")

    # === BODY ===
    # "Chung nhan ong/ba:"
    c.setFont(FONT_REGULAR, 13)
    c.setFillColor(HexColor("#4B5563"))
    c.drawCentredString(center_x, height - 7.2 * cm, "Chứng nhận Ông/Bà:")

    # Ho ten (big, bold)
    c.setFont(FONT_SERIF_BOLD, 28)
    c.setFillColor(HexColor("#111827"))
    c.drawCentredString(center_x, height - 8.5 * cm, ho_ten.upper())

    # Ma cc + don vi
    c.setFont(FONT_REGULAR, 11)
    c.setFillColor(HexColor("#6B7280"))
    info = f"Mã CC: {ma_cc}"
    if don_vi:
        info += f"  |  Đơn vị: {don_vi}"
    c.drawCentredString(center_x, height - 9.3 * cm, info)

    # "Da hoan thanh khoa hoc:"
    c.setFont(FONT_REGULAR, 12)
    c.setFillColor(HexColor("#4B5563"))
    c.drawCentredString(center_x, height - 10.5 * cm, "Đã hoàn thành khóa học:")

    # Ten khoa hoc (italic-like — dung serif)
    c.setFont(FONT_SERIF_BOLD, 17)
    c.setFillColor(HexColor("#1E40AF"))
    # Cat bot neu ten qua dai
    ten_display = ten_khoa_hoc if len(ten_khoa_hoc) <= 80 else ten_khoa_hoc[:77] + "..."
    c.drawCentredString(center_x, height - 11.5 * cm, f'"{ten_display}"')

    # === DIEM + XEP LOAI ===
    xep_loai, mau = xep_loai_label(diem_dat)
    c.setFont(FONT_REGULAR, 11)
    c.setFillColor(HexColor("#6B7280"))
    c.drawCentredString(center_x, height - 13 * cm,
                         f"Với số điểm: {float(diem_dat):.2f}  —  Xếp loại:")

    c.setFont(FONT_BOLD, 18)
    c.setFillColor(HexColor(mau))
    c.drawCentredString(center_x, height - 13.9 * cm, xep_loai)

    # === FOOTER ===
    footer_y = 2 * cm

    # Left: Ma chung chi
    c.setFont(FONT_REGULAR, 9)
    c.setFillColor(HexColor("#6B7280"))
    c.drawString(2 * cm, footer_y + 0.8 * cm, f"Mã chứng chỉ:")
    c.setFont(FONT_BOLD, 11)
    c.setFillColor(HexColor("#111827"))
    c.drawString(2 * cm, footer_y + 0.3 * cm, ma_chung_chi)

    # Right: Ngay cap
    c.setFont(FONT_REGULAR, 9)
    c.setFillColor(HexColor("#6B7280"))
    ngay_text = f"Ngày cấp: {ngay_cap.strftime('%d/%m/%Y')}"
    c.drawRightString(width - 2 * cm, footer_y + 0.8 * cm, ngay_text)

    # Center: verification note
    c.setFont(FONT_REGULAR, 8)
    c.setFillColor(HexColor("#9CA3AF"))
    c.drawCentredString(center_x, footer_y - 0.2 * cm,
                         f"Tra cứu chứng chỉ tại: kpihaiquan.vn/tra-cuu-chung-chi  —  Mã: {ma_chung_chi}")

    c.showPage()
    c.save()

    pdf_bytes = buffer.getvalue()
    buffer.close()

    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(pdf_bytes)

    return pdf_bytes
