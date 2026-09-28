"""
app/core/quyen_xem_phieu.py
============================
Ai được XEM phiếu đánh giá (Mẫu 02A/02B) của TOÀN CHI CỤC.

Trước 29/09/2026, phiếu chỉ nhìn được trong phạm vi DUYỆT: Trưởng đơn vị thấy
công chức + phó đơn vị của đơn vị mình, Chi cục trưởng thấy trưởng đơn vị + phó
Chi cục trưởng. Hệ quả đo ngày 28/09: trong 450 phiếu quý III thì 439 phiếu chỉ
mỗi Trưởng đơn vị của người đó nhìn thấy, còn TCCB — nơi phải tổng hợp hồ sơ nộp
ngày 23 tháng cuối quý — không xem được phiếu nào.

Quyết định 29/09/2026: mở quyền XEM (CHỈ ĐỌC) toàn Chi cục cho CCT, PCCT, TCCB và
tài khoản có cờ `can_view_all_units`. CỐ Ý KHÔNG mở cho Trưởng đơn vị xem đơn vị
khác — phiếu chứa nhận xét cá nhân và phần "hạn chế, khuyết điểm" của từng người.

Quyền XEM ở đây KHÔNG kéo theo quyền duyệt. Việc duyệt vẫn do `_co_quyen_duyet`
trong `phieu_danh_gia_quy.py` quyết định, không đụng tới.
"""

from app.models.user_org import CapBacVaiTro, CongChuc

# Các cấp bậc được xem phiếu của mọi công chức trong Chi cục.
CAP_BAC_XEM_TOAN_CHI_CUC = (
    CapBacVaiTro.CHI_CUC_TRUONG,
    CapBacVaiTro.PHO_CHI_CUC_TRUONG,
    CapBacVaiTro.TCCB,
)


def xem_duoc_toan_chi_cuc(user: CongChuc) -> bool:
    """True nếu `user` được xem phiếu đánh giá của mọi công chức (chỉ đọc)."""
    if getattr(user, "is_system_admin", False):
        return True
    if getattr(user, "can_view_all_units", False):
        return True
    if not user.vai_tro:
        return False
    return user.vai_tro.cap_bac in CAP_BAC_XEM_TOAN_CHI_CUC
