"""
shared/constants.py
===================
Hằng số dùng chung cho toàn bộ platform.
"""

# Platform roles — vai trò bổ sung cho nền tảng mở rộng
PLATFORM_ROLES = [
    "GIANG_VIEN",        # Giảng viên kiêm nhiệm (LMS)
    "QT_DAO_TAO",        # Quản trị đào tạo (LMS)
    "BIEN_TAP",          # Biên tập viên (Legal, Portal)
    "DIEU_PHOI_FORUM",   # Điều phối diễn đàn (Forum)
    "CHUYEN_GIA",        # Chuyên gia nghiệp vụ (Forum, Common)
    "QT_NOI_DUNG",       # Quản trị nội dung (Portal)
    "QT_ATTT",           # Quản trị ATTT (ALL)
]

# Error codes chuẩn
ERROR_CODES = {
    # Auth
    "AUTH_001": "Token không hợp lệ hoặc đã hết hạn",
    "AUTH_002": "Không có quyền truy cập",
    "AUTH_003": "Sai tên đăng nhập hoặc mật khẩu",
    "AUTH_004": "Tài khoản đã bị khóa",
    # Validation
    "VAL_001": "Dữ liệu đầu vào không hợp lệ",
    "VAL_002": "Thiếu field bắt buộc",
    # Business
    "BIZ_001": "Không tìm thấy dữ liệu",
    "BIZ_002": "Trạng thái không cho phép thao tác này",
    # Permission
    "PERM_001": "Không có quyền truy cập chức năng này",
    "PERM_002": "Vai trò không phù hợp",
    # System
    "SYS_001": "Lỗi hệ thống",
}

# Pagination defaults
DEFAULT_PAGE = 1
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100
