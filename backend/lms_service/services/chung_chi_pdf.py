"""
lms_service/services/chung_chi_pdf.py
=====================================
Sinh PDF chung chi hoan thanh khoa hoc.
Dung reportlab + font DejaVu (ho tro tieng Viet).

Thiet ke bam theo mau giay chung nhan cua Chi cuc (docs/lms/Them-tinh-nang/):
khung vien vang doi, nep goc xanh-vang, an Hai quan chim giua trang, huy hieu
vang goc duoi phai. Khac mau giay o cho: mau la phoi de dien tay nen co dong
cham cham, con file nay dien san du lieu that nen bo het dong cham.
"""

import io
import os
from datetime import datetime
from decimal import Decimal
from functools import lru_cache
from typing import Optional

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

# Dang ky font DejaVu (ho tro tieng Viet)
_FONT_REGISTERED = False
FONT_REGULAR = "DejaVuSans"
FONT_BOLD = "DejaVuSans-Bold"
FONT_SERIF = "DejaVuSerif"
FONT_SERIF_BOLD = "DejaVuSerif-Bold"

# ── Bang mau ─────────────────────────────────────────────────────────────────
# Lay tu mau giay: vang an cua khung, xanh muc cua nep goc, do co cua chu tieu de
VANG_DAM = HexColor("#C19A2E")     # nep vien ngoai
VANG_NHAT = HexColor("#DCC06A")    # nep vien trong
XANH_MUC = HexColor("#14306B")     # nep goc + chu hanh chinh
XANH_NHAT = HexColor("#2C4B8C")
DO_CO = HexColor("#A5161B")        # "CHỨNG NHẬN"
MUC_DEN = HexColor("#101B33")      # ho ten
XAM_CHU = HexColor("#4A5568")      # dong phu
XAM_NHAT = HexColor("#8A94A6")     # dong tra cuu
NEN_GIAY = HexColor("#FFFDF7")

# Duong dan an chim — dat trong package de di theo code khi trien khai.
# Truoc day tro sang frontend/public/, duong dan do vo khi service chay tu thu
# muc khac; nay nam canh module nen luon tim thay.
DUONG_DAN_AN = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "logo-hai-quan.png")

# Do dam cua an chim. Cao hon thi at chu, thap hon thi mat tich khi in.
# 0.09 tung lam vong do cua an cat ngang dong ten khoa hoc — ha xuong 0.055.
DO_MO_AN = 0.045


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
    """Tra ve (label, mau_hex) theo diem (thang 100, da chuan hoa ve %)."""
    d = float(diem) if diem is not None else 0
    if d >= 90:
        return ("XUẤT SẮC", "#A5161B")
    if d >= 80:
        return ("GIỎI", "#B8860B")
    if d >= 65:
        return ("KHÁ", "#14306B")
    if d >= 50:
        return ("ĐẠT", "#0F7B4F")
    # Giu nguyen nhanh cu: doi thang nay la doi NOI DUNG giay to chinh thuc,
    # khong phai viec cua mot dot sua giao dien. Xem ghi chu ben duoi.
    return ("KHÔNG ĐẠT", "#6B7280")


# =============================================================================
# TIEN ICH VE
# =============================================================================

# Canh an chim khi nhung vao PDF (pixel). An in ra 11,5cm nen 640px ~ 140 dpi —
# du cho mot hinh mo nhat, va giu file nho.
CANH_AN_PX = 640


@lru_cache(maxsize=1)
def _an_chim() -> Optional[ImageReader]:
    """Ban an Hai quan da lam mo san, cache lai vi moi cert deu dung.

    Lam mo bang PIL thay vi setFillAlpha cua reportlab: alpha cua reportlab
    ap qua ExtGState, ket qua khac nhau giua cac trinh xem PDF va co trinh in
    bo qua han. Nung san vao anh thi in ra giong het cai nhin tren man hinh.
    Thieu file anh thi bo qua an chim, KHONG lam hong ca cai chung chi.

    Anh duoc BET SAN len mau nen giay roi bo kenh alpha, luu JPEG:
    ban dau giu nguyen PNG 826x826 co alpha, moi chung chi phinh tu 68KB len
    1,0MB — 405 chung chi hien co se thanh ~410MB thay vi 27MB. Ep phang thanh
    JPEG mo nhat thi nhin y het (an nam trên đúng mau nen do) ma file nho lai.
    """
    try:
        from PIL import Image

        anh = Image.open(DUONG_DAN_AN).convert("RGBA")
        anh = anh.resize((CANH_AN_PX, CANH_AN_PX), Image.LANCZOS)

        alpha = anh.getchannel("A").point(lambda v: int(v * DO_MO_AN))
        anh.putalpha(alpha)

        # Bet len dung mau giay → khong con can kenh trong suot
        nen = Image.new("RGB", anh.size, tuple(int(v * 255) for v in NEN_GIAY.rgb()))
        nen.paste(anh, (0, 0), anh)

        dem = io.BytesIO()
        nen.save(dem, format="JPEG", quality=82, optimize=True)
        dem.seek(0)
        return ImageReader(dem)
    except Exception:
        return None


def _co_chu_vua_khung(text: str, font: str, rong_toi_da: float,
                      co_dau: float, co_toi_thieu: float) -> float:
    """Thu nho co chu cho tới khi text lot vao khung.

    Ho ten va ten khoa hoc do nguoi dung nhap nen dai ngan tuy y — ban cu cat
    cut ten khoa hoc o ky tu thu 80 va them "...", lam mat thong tin tren giay
    to chinh thuc. Nay thu nho chu truoc, chi xuong dong khi that su can.
    """
    co = co_dau
    while co > co_toi_thieu and pdfmetrics.stringWidth(text, font, co) > rong_toi_da:
        co -= 0.5
    return co


def _ngat_dong(text: str, font: str, co: float, rong_toi_da: float,
               so_dong_toi_da: int = 2) -> list[str]:
    """Ngat text thanh toi da `so_dong_toi_da` dong theo bien tu."""
    tu = text.split()
    dong: list[str] = []
    hien_tai = ""
    for t in tu:
        thu = f"{hien_tai} {t}".strip()
        if pdfmetrics.stringWidth(thu, font, co) <= rong_toi_da or not hien_tai:
            hien_tai = thu
        else:
            dong.append(hien_tai)
            hien_tai = t
            if len(dong) == so_dong_toi_da - 1:
                break
    con_lai = " ".join(tu[sum(len(d.split()) for d in dong):]) if dong else hien_tai
    dong.append(con_lai.strip() if dong else hien_tai)
    return [d for d in dong if d][:so_dong_toi_da]


def _ve_nep_goc(c: canvas.Canvas, x: float, y: float, dx: int, dy: int, canh: float):
    """Ve nep goc xanh-vang. (x, y) la dinh goc; dx/dy = ±1 chi huong vao trong."""
    # Tam giac xanh lon
    c.setFillColor(XANH_MUC)
    p = c.beginPath()
    p.moveTo(x, y)
    p.lineTo(x + dx * canh, y)
    p.lineTo(x, y + dy * canh)
    p.close()
    c.drawPath(p, stroke=0, fill=1)

    # Nep vang mong chay cheo, lech vao trong mot chut
    c.setFillColor(VANG_DAM)
    lech = canh * 0.42
    day = canh * 0.30
    p2 = c.beginPath()
    p2.moveTo(x + dx * lech, y)
    p2.lineTo(x + dx * (lech + day), y)
    p2.lineTo(x, y + dy * (lech + day))
    p2.lineTo(x, y + dy * lech)
    p2.close()
    c.drawPath(p2, stroke=0, fill=1)


def _ve_sao_nho(c: canvas.Canvas, cx: float, cy: float, r: float):
    """Ngoi sao 4 canh nho ngan cach phan quoc hieu va tieu de."""
    c.setFillColor(VANG_DAM)
    p = c.beginPath()
    p.moveTo(cx, cy + r)
    p.lineTo(cx + r * 0.28, cy + r * 0.28)
    p.lineTo(cx + r, cy)
    p.lineTo(cx + r * 0.28, cy - r * 0.28)
    p.lineTo(cx, cy - r)
    p.lineTo(cx - r * 0.28, cy - r * 0.28)
    p.lineTo(cx - r, cy)
    p.lineTo(cx - r * 0.28, cy + r * 0.28)
    p.close()
    c.drawPath(p, stroke=0, fill=1)


def _ve_huy_hieu(c: canvas.Canvas, cx: float, cy: float, r: float):
    """Huy hieu vang co dai ruy bang — goc duoi phai, nhu tren mau giay."""
    # Hai dai ruy bang xanh xoe xuong duoi
    c.setFillColor(XANH_MUC)
    for huong in (-1, 1):
        p = c.beginPath()
        p.moveTo(cx + huong * r * 0.30, cy - r * 0.35)
        p.lineTo(cx + huong * r * 0.95, cy - r * 2.05)
        p.lineTo(cx + huong * r * 0.30, cy - r * 1.75)
        p.lineTo(cx + huong * r * 0.02, cy - r * 2.05)
        p.close()
        c.drawPath(p, stroke=0, fill=1)

    # Than huy hieu: vong ngoai vang dam, long trong vang nhat
    c.setFillColor(VANG_DAM)
    c.circle(cx, cy, r, stroke=0, fill=1)
    c.setFillColor(VANG_NHAT)
    c.circle(cx, cy, r * 0.72, stroke=0, fill=1)
    c.setStrokeColor(VANG_DAM)
    c.setLineWidth(1)
    c.circle(cx, cy, r * 0.46, stroke=1, fill=0)


# =============================================================================
# SINH PDF
# =============================================================================

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

    buffer = io.BytesIO()
    width, height = landscape(A4)
    c = canvas.Canvas(buffer, pagesize=landscape(A4))
    giua = width / 2

    # ── NEN GIAY ─────────────────────────────────────────────────────────────
    c.setFillColor(NEN_GIAY)
    c.rect(0, 0, width, height, stroke=0, fill=1)

    # ── AN CHIM ──────────────────────────────────────────────────────────────
    # Ve TRUOC khung vien va chu de moi thu khac nam de len tren.
    an = _an_chim()
    if an is not None:
        canh_an = 11.5 * cm
        c.drawImage(an, giua - canh_an / 2, height / 2 - canh_an / 2 - 0.6 * cm,
                    width=canh_an, height=canh_an)

    # ── NEP GOC ──────────────────────────────────────────────────────────────
    # Ban cu ve dau cong THO RA ngoai khung, nhin nhu dau cat giay. Nay la nep
    # goc xanh-vang neo o goc TRANG, ve TRUOC khung vien de hai duong vang chay
    # lien mach vong quanh thay vi bi nep goc cat dut o bon goc.
    canh_goc = 3.2 * cm
    _ve_nep_goc(c, 0, height, +1, -1, canh_goc)           # trai tren
    _ve_nep_goc(c, width, height, -1, -1, canh_goc)       # phai tren
    _ve_nep_goc(c, 0, 0, +1, +1, canh_goc)                # trai duoi
    _ve_nep_goc(c, width, 0, -1, +1, canh_goc)            # phai duoi

    # ── KHUNG VIEN VANG DOI ──────────────────────────────────────────────────
    c.setStrokeColor(VANG_DAM)
    c.setLineWidth(5)
    c.rect(0.75 * cm, 0.75 * cm, width - 1.5 * cm, height - 1.5 * cm, stroke=1, fill=0)

    c.setStrokeColor(VANG_NHAT)
    c.setLineWidth(1.2)
    c.rect(1.15 * cm, 1.15 * cm, width - 2.3 * cm, height - 2.3 * cm, stroke=1, fill=0)

    # ── QUOC HIEU ────────────────────────────────────────────────────────────
    c.setFont(FONT_SERIF_BOLD, 13.5)
    c.setFillColor(XANH_MUC)
    c.drawCentredString(giua, height - 1.95 * cm, "CHI CỤC HẢI QUAN KHU VỰC VIII")

    c.setFont(FONT_SERIF, 11)
    c.setFillColor(XANH_NHAT)
    c.drawCentredString(giua, height - 2.60 * cm, "Trung tâm Đào tạo trực tuyến")

    # Sao nho + hai vach vang hai ben
    y_sao = height - 3.25 * cm
    _ve_sao_nho(c, giua, y_sao, 0.16 * cm)
    c.setStrokeColor(VANG_NHAT)
    c.setLineWidth(0.8)
    c.line(giua - 3.2 * cm, y_sao, giua - 0.5 * cm, y_sao)
    c.line(giua + 0.5 * cm, y_sao, giua + 3.2 * cm, y_sao)

    # ── TIEU DE ──────────────────────────────────────────────────────────────
    y_tieu_de = height - 5.15 * cm
    # Bong chu mo phia sau cho chu day dan, giong hieu ung tren mau giay
    c.setFont(FONT_SERIF_BOLD, 46)
    c.setFillColor(HexColor("#EFE7D8"))
    c.drawCentredString(giua + 0.8, y_tieu_de - 0.8, "CHỨNG NHẬN")
    c.setFillColor(DO_CO)
    c.drawCentredString(giua, y_tieu_de, "CHỨNG NHẬN")

    c.setFont(FONT_SERIF_BOLD, 17)
    c.setFillColor(XANH_MUC)
    c.drawCentredString(giua, height - 6.20 * cm, "HOÀN THÀNH KHÓA HỌC")

    # ── HO TEN ───────────────────────────────────────────────────────────────
    c.setFont(FONT_SERIF, 12.5)
    c.setFillColor(XAM_CHU)
    c.drawCentredString(giua, height - 7.75 * cm, "Chứng nhận Ông/Bà:")

    ten_hoa = ho_ten.upper()
    co_ten = _co_chu_vua_khung(ten_hoa, FONT_SERIF_BOLD, width - 8 * cm, 29, 17)
    c.setFont(FONT_SERIF_BOLD, co_ten)
    c.setFillColor(MUC_DEN)
    c.drawCentredString(giua, height - 9.05 * cm, ten_hoa)

    # Vach vang duoi ten
    c.setStrokeColor(VANG_NHAT)
    c.setLineWidth(0.9)
    c.line(giua - 7 * cm, height - 9.45 * cm, giua + 7 * cm, height - 9.45 * cm)

    # ── MA CC + DON VI ───────────────────────────────────────────────────────
    c.setFont(FONT_SERIF, 11)
    c.setFillColor(XAM_CHU)
    thong_tin = f"Mã CC: {ma_cc}"
    if don_vi:
        thong_tin += f"    |    Đơn vị: {don_vi}"
    c.drawCentredString(giua, height - 10.15 * cm, thong_tin)

    # ── TEN KHOA HOC ─────────────────────────────────────────────────────────
    c.setFont(FONT_SERIF, 12.5)
    c.setFillColor(XAM_CHU)
    c.drawCentredString(giua, height - 11.45 * cm, "Đã hoàn thành khóa học:")

    rong_kh = width - 7 * cm
    co_kh = _co_chu_vua_khung(f'"{ten_khoa_hoc}"', FONT_SERIF_BOLD, rong_kh, 17, 13)
    y_kh = height - 12.55 * cm
    c.setFillColor(XANH_MUC)

    if pdfmetrics.stringWidth(f'"{ten_khoa_hoc}"', FONT_SERIF_BOLD, co_kh) <= rong_kh:
        c.setFont(FONT_SERIF_BOLD, co_kh)
        c.drawCentredString(giua, y_kh, f'"{ten_khoa_hoc}"')
        y_sau_kh = y_kh
    else:
        # Ten qua dai → ngat 2 dong thay vi cat cut
        cac_dong = _ngat_dong(ten_khoa_hoc, FONT_SERIF_BOLD, co_kh, rong_kh, 2)
        c.setFont(FONT_SERIF_BOLD, co_kh)
        for i, dong in enumerate(cac_dong):
            noi_dung = dong
            if i == 0:
                noi_dung = f'"{noi_dung}'
            if i == len(cac_dong) - 1:
                noi_dung = f'{noi_dung}"'
            c.drawCentredString(giua, y_kh - i * (co_kh + 6), noi_dung)
        y_sau_kh = y_kh - (len(cac_dong) - 1) * (co_kh + 6)

    # ── DIEM + XEP LOAI (cung mot dong) ──────────────────────────────────────
    # Ban cu tach "Xếp loại:" va gia tri thanh hai dong, doc roi rac. Nay ghep
    # mot dong roi can giua theo tong be rong.
    xep_loai, mau = xep_loai_label(diem_dat)
    phan_dau = f"Với số điểm: {float(diem_dat):.2f}    —    Xếp loại: "
    rong_dau = pdfmetrics.stringWidth(phan_dau, FONT_SERIF, 12)
    rong_xl = pdfmetrics.stringWidth(xep_loai, FONT_SERIF_BOLD, 15)
    x_bat_dau = giua - (rong_dau + rong_xl) / 2
    y_diem = y_sau_kh - 1.65 * cm

    c.setFont(FONT_SERIF, 12)
    c.setFillColor(XAM_CHU)
    c.drawString(x_bat_dau, y_diem, phan_dau)
    c.setFont(FONT_SERIF_BOLD, 15)
    c.setFillColor(HexColor(mau))
    c.drawString(x_bat_dau + rong_dau, y_diem, xep_loai)

    # ── HUY HIEU ─────────────────────────────────────────────────────────────
    _ve_huy_hieu(c, width - 3.3 * cm, 3.9 * cm, 0.85 * cm)

    # ── NGAY CAP ─────────────────────────────────────────────────────────────
    c.setFont(FONT_SERIF, 11)
    c.setFillColor(XAM_CHU)
    c.drawRightString(
        width - 2.2 * cm, 5.6 * cm,
        f"Ngày {ngay_cap.day:02d} tháng {ngay_cap.month:02d} năm {ngay_cap.year}",
    )

    # ── MA CHUNG CHI ─────────────────────────────────────────────────────────
    c.setFont(FONT_SERIF, 9.5)
    c.setFillColor(XAM_CHU)
    c.drawString(2.2 * cm, 3.55 * cm, "Mã chứng chỉ:")
    c.setFont(FONT_SERIF_BOLD, 12)
    c.setFillColor(MUC_DEN)
    c.drawString(2.2 * cm, 2.95 * cm, ma_chung_chi)

    # ── DONG TRA CUU ─────────────────────────────────────────────────────────
    c.setFont(FONT_REGULAR, 8)
    c.setFillColor(XAM_NHAT)
    c.drawCentredString(
        giua, 1.75 * cm,
        f"Tra cứu chứng chỉ tại: kpihaiquan.vn/tra-cuu-chung-chi  —  Mã: {ma_chung_chi}",
    )

    c.showPage()
    c.save()

    pdf_bytes = buffer.getvalue()
    buffer.close()

    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(pdf_bytes)

    return pdf_bytes
