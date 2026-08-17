"""Bảng ánh xạ dữ liệu lichkv8 → nền tảng. Kết quả khảo sát G1.4 (17/08/2026).

Ba hệ mã đơn vị khác nhau cùng tồn tại, không hệ nào trùng hệ nào:

  1. public.don_vi.ma_don_vi   — 15 đơn vị trên nền tảng (CNTT, HQCK-VG, KSHQ…)
  2. DEPT.MA_DON_VI            — 13 mã của lichkv8   (HQKV8, VP, HQCK_MC…)
  3. DUTY_ENTRY.UNIT_CODE      —  9 mã TRỤ SỞ        (CHICUC, VANGIA, KSHQ_HL…)

Điểm quan trọng: hệ thứ 3 là **trụ sở vật lý**, KHÔNG phải đơn vị. `UNIT_NAME`
trong dữ liệu ghi rõ "Trụ sở HQCK cảng Vạn Gia", "Trụ sở Chi cục HQKV VIII".
Quan hệ trụ sở ↔ đơn vị không phải 1:1:

  - 6 trụ sở cửa khẩu  → khớp 1:1 với đơn vị HQCK tương ứng
  - KSHQ_HL + KSHQ_MC  → CÙNG một đơn vị KSHQ (nhiều trụ sở, một đơn vị)
  - CHICUC             → trụ sở dùng chung của VP, LDCC, CNTT, NVHQ, TCCB,
                         QLRR, PTSTQ — không ứng với một đơn vị nào

Vì vậy bảng trực ban phải khoá theo `tru_so_id`, không phải `don_vi_id`.
"""

from __future__ import annotations

# --- Trụ sở trực ban -------------------------------------------------------
# ma_tru_so → (tên hiển thị, ma_don_vi phụ trách hoặc None, thứ tự, số bản ghi 17/08)
TRU_SO = {
    "CHICUC":  ("Trụ sở Chi cục HQKV VIII",                    None,       1, 50),
    "HONGAI":  ("Trụ sở HQCK cảng Hòn Gai",                    "HQCK-HG",  2, 44),
    "CAMPHA":  ("Trụ sở HQCK cảng Cẩm Phả",                    "HQCK-CP",  3, 22),
    "VANGIA":  ("Trụ sở HQCK cảng Vạn Gia",                    "HQCK-VG",  4, 62),
    "HOANHMO": ("Trụ sở HQCK Hoành Mô",                        "HQCK-HM",  5, 24),
    "BPS":     ("Trụ sở HQCK Bắc Phong Sinh",                  "HQCK-BPS", 6, 28),
    "MONGCAI": ("Trụ sở HQCK quốc tế Móng Cái",                "HQCK-MC",  7, 59),
    "KSHQ_HL": ("Đội Kiểm soát Hải quan - Khu vực Hạ Long",    "KSHQ",     8, 22),
    "KSHQ_MC": ("Đội Kiểm soát Hải quan - Khu vực Móng Cái",   "KSHQ",     9, 22),
}

# Trụ sở CHICUC do Văn phòng điều phối (mã nguồn cũ cấp quyền qua regex
# "van phong" trong isDutyAdmin_ — nay chuyển thành quyền tường minh).
DON_VI_DIEU_PHOI_CHICUC = "VP"

# --- Đơn vị: DEPT.MA_DON_VI (lichkv8) → public.don_vi.ma_don_vi ------------
# HQKV8 là chính Chi cục, không phải một đơn vị trong don_vi → None.
DON_VI = {
    "HQKV8":    None,
    "VP":       "VP",
    "CNTT":     "CNTT",
    "NV":       "NVHQ",
    "TCCB":     "TCCB",
    "QLRR":     "QLRR",
    "DOI_KSHQ": "KSHQ",
    "HQCK_MC":  "HQCK-MC",
    "HQCK_HG":  "HQCK-HG",
    "HQCK_CP":  "HQCK-CP",
    "HQCK_VG":  "HQCK-VG",
    "HQCK_HM":  "HQCK-HM",
    "HQCK_BPS": "HQCK-BPS",
}

# Đơn vị trên nền tảng KHÔNG có trong DEPT của lichkv8 — không cần ánh xạ ngược.
DON_VI_CHI_CO_TREN_NEN_TANG = ["DEPT-ADMIN", "LDCC", "PTSTQ"]

# --- Trạng thái cuộc họp: MEETING.TRANG_THAI → cuoc_hop.trang_thai --------
TRANG_THAI = {
    "PUBLISHED": "DA_THONG_BAO",   # 461 bản ghi
    "CANCELLED": "HUY",            #  16
    "DRAFT":     "LEN_KE_HOACH",   #  10
}

# --- Loại lịch: giữ nguyên 6 giá trị đang chạy ----------------------------
# Không trùng với cột `khoi` của HKG (DANG/CHUYEN_MON/HANH_CHINH/BAN_NHOM).
LOAI_LICH = {
    "HOP":        ("Họp",              232),
    "TRUC_BAN":   ("Trực ban",          85),
    "HOI_NGHI":   ("Hội nghị",          69),
    "LAM_VIEC":   ("Làm việc",          46),
    "CONG_TAC":   ("Đi công tác",       37),
    "LICH_KHAC":  ("Lịch khác",         18),
}

# --- Vai trò: USER.ROLE (lichkv8) → quyền trên nền tảng ------------------
# lichkv8 khớp nhiều biến thể hoa/thường cho cùng vai trò; chuẩn hoá ở đây.
VAI_TRO = {
    "SuperAdmin":    ("ADMIN",  "toàn quyền, gồm quản trị người dùng",   2),
    "Admin":         ("ADMIN",  "quản trị lịch và danh mục",             0),
    "Lanhdaochicuc": ("LD_CC",  "lãnh đạo Chi cục, xem mọi tài liệu",    4),
    "Lanhdaophong":  ("LD_DV",  "lãnh đạo Phòng",                       18),
    "Lanhdaodoi":    ("LD_DV",  "lãnh đạo Đội",                         32),
    "Thuky":         ("THU_KY", "tác nghiệp lịch, không quản trị hệ thống", 6),
    "Congchuc":      ("CC",     "chỉ xem",                             486),
    "Viewer":        ("CC",     "chỉ xem",                               0),
    "DauMoiDonVi":   ("CC",     "đầu mối đơn vị — khai báo nhưng không ai dùng", 0),
}

# --- Tài khoản đặc biệt ---------------------------------------------------
# 547/548 dòng USER có USER_ID đúng dạng ma_cc → ánh xạ trực tiếp.
# Ngoại lệ duy nhất:
USER_KHONG_ANH_XA = ["superadmin"]  # USER_ID = U0001, không phải công chức

# Người rà màn hình đối soát tài liệu (quyết định 17/08/2026).
NGUOI_DOI_SOAT_MA_CC = "20ZZ-0097"  # Tống Thị Thái Hà, Chánh Văn phòng (lichkv8: hattt)
