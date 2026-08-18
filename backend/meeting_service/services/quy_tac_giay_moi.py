"""Quy tắc phân loại giấy mời — PORT NGUYÊN VĂN từ lichkv8.

⚠️ KHÔNG viết lại theo mô tả. Ba hàm dưới đây được port từng biểu thức chính
quy từ `Mã.gs` dòng 1513–1543 của lichkv8, vì đây là quy tắc nghiệp vụ đã được
tinh chỉnh sau sự cố thật, không phải chi tiết hiển thị.

Bối cảnh: báo cáo "Thống kê tài liệu họp" theo dõi đơn vị được giao chuẩn bị đã
nộp tài liệu chưa. Giấy mời thuần KHÔNG được tính là đã hoàn thành nghĩa vụ
chuẩn bị — nộp mỗi giấy mời thì vẫn là chưa nộp tài liệu.

Bình luận V145 trong mã gốc ghi rõ hệ quả của việc làm sai:

    "tên file mập mờ + lỡ chọn nhầm loại 'Giấy mời' từng khiến tài liệu thật
     bị loại khỏi thống kê, báo oan đơn vị 'chưa nộp tài liệu'"

Nên THỨ TỰ ƯU TIÊN là phần quan trọng nhất:
  1. Tên file có tín hiệu tài liệu chuyên môn → TÍNH, kể cả khi nằm trong nhóm
     GIAY_MOI hoặc do Văn phòng tải lên thay đơn vị.
  2. Chỉ loại trừ khi CHÍNH TÊN FILE thể hiện rõ là giấy mời.
  3. Mập mờ thì ưu tiên tính là tài liệu thật — thà tính dư còn hơn báo oan.

Quy mô ảnh hưởng: 279/587 file mang nhóm GIAY_MOI, tức quy tắc này chi phối
gần một nửa báo cáo.
"""

from __future__ import annotations

import re
import unicodedata

# Tín hiệu tài liệu chuyên môn — port từ hasMeetingDocsMaterialSignal_()
_TIN_HIEU_TAI_LIEU = re.compile(
    r"\btai lieu\b|\btai lieu hop\b|\bbao cao\b|(^|\s)bc(\s|$)|\bphu luc\b"
    r"|\bdu thao\b|\bto trinh\b|\bnghi quyet\b|(^|\s)nq\s*\d*|\bket luan\b"
    r"|\bde an\b|\bke hoach\b|\bchuong trinh\b|\bbien ban\b|\bbieu mau\b"
    r"|\btong hop\b|\btham luan\b|\bslide\b|\bppt\b|\bpresentation\b"
    r"|\bduthao\b|\bbckt\b|\bkbt\b"
)

# Tín hiệu giấy mời — port từ hasInvitationSignal_()
_TIN_HIEU_GIAY_MOI = re.compile(
    r"\bgiay moi\b|\bthu moi\b|\bcong van moi\b|\bcv moi\b|\bmoi hop\b"
    r"|\bgiay trieu tap\b|\bthu trieu tap\b|\binvitation\b"
)
# Mã giấy mời dạng GM-0178, GM 769, 762gm.pdf…
_MA_GM = re.compile(r"(^|[^a-z])gm($|[^a-z])")

# Tiền tố hệ thống tự thêm khi upload: LH0282_GIAY_MOI_V03_<tên gốc>
_TIEN_TO_MA_LICH = re.compile(r"^LH\d{3,6}[_\-\s]+", re.IGNORECASE)
_TIEN_TO_NHOM = re.compile(
    r"^(?:GIAY[_\-\s]*MOI|TAI[_\-\s]*LIEU[_\-\s]*HOP|BAO[_\-\s]*CAO"
    r"|PHU[_\-\s]*LUC|DINH[_\-\s]*KEM|KHAC|TAI[_\-\s]*LIEU|VAN[_\-\s]*BAN)"
    r"[_\-\s]+V\d{1,3}[_\-\s]+",
    re.IGNORECASE,
)


def chuan_hoa(s: str) -> str:
    """Port CHÍNH XÁC normalizeText_() của lichkv8 (Mã.gs dòng 2053).

    Bước quan trọng nhất là `[^a-z0-9]+ → ' '`: mọi ký tự không phải chữ số đều
    thành khoảng trắng. Thiếu bước này thì `bao-cao.pdf` không khớp `\\bbao cao\\b`
    và bị xếp nhầm — vì dấu gạch không phải khoảng trắng.

        toLowerCase → NFD → bỏ dấu → đ→d → [^a-z0-9]→' ' → gộp → trim
    """
    s = str(s or "").lower()
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = s.replace("đ", "d")
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def ten_goc(ten_file: str) -> str:
    """Bỏ tiền tố hệ thống, trả lại tên người dùng đặt ban đầu.

    Port từ cleanMeetingDocsReportFileName_(). Hệ thống thêm tiền tố dạng
    `LH0282_GIAY_MOI_V03_` khi upload; thống kê phải xét tên gốc, nếu không thì
    mọi file trong nhóm GIAY_MOI đều bị coi là giấy mời.
    """
    s = (ten_file or "").strip()
    if not s:
        return ""
    s = _TIEN_TO_MA_LICH.sub("", s)
    s = _TIEN_TO_NHOM.sub("", s)
    return s.strip(" _")


def co_tin_hieu_tai_lieu(ten_da_lam_sach: str) -> bool:
    s = chuan_hoa(ten_da_lam_sach)
    return bool(s) and bool(_TIN_HIEU_TAI_LIEU.search(s))


def co_tin_hieu_giay_moi(ten_da_lam_sach: str) -> bool:
    s = chuan_hoa(ten_da_lam_sach)
    if not s:
        return False
    return bool(_TIN_HIEU_GIAY_MOI.search(s)) or bool(_MA_GM.search(s))


def la_giay_moi_thuan(ten_file: str) -> bool:
    """File này có phải giấy mời thuần không — tức KHÔNG tính là tài liệu chuẩn bị.

    Port từ isInvitationDocFile_(). Giữ nguyên thứ tự ưu tiên: tín hiệu tài liệu
    chuyên môn thắng tín hiệu giấy mời.
    """
    sach = ten_goc(ten_file)
    # Tên đã thể hiện rõ là báo cáo, phụ lục, tài liệu họp… thì phải tính,
    # kể cả khi nằm trong nhóm GIAY_MOI.
    if co_tin_hieu_tai_lieu(sach):
        return False
    return co_tin_hieu_giay_moi(sach)


def dem_tai_lieu_chuan_bi(ten_cac_file: list[str]) -> int:
    """Số file được tính là tài liệu chuẩn bị (đã loại giấy mời thuần)."""
    return sum(1 for t in ten_cac_file if not la_giay_moi_thuan(t))
