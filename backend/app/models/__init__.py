"""
app/models/__init__.py
======================
Export tất cả SQLAlchemy models.

QUAN TRỌNG: File này import từ các file models đã có sẵn trong project.
Không được viết lại models ở đây.

Phiên bản: 2.5.0 (26/01/2026)
- Thêm TieuChiChung (Master Data)
- Thêm TrangThaiTieuChi, LoaiLogicTieuChi enums
- Thêm helper functions từ kpi_assessment
"""

# Base classes
from app.models.base import (
    Base,
    BaseModel,
    BaseModelWithSoftDelete,
    BaseModelFull,
    TimestampMixin,
    SoftDeleteMixin,
    AuditMixin,
    UUIDPrimaryKeyMixin,
)

# User & Organization
from app.models.user_org import (
    # Enums
    LoaiDonVi,
    CapBacVaiTro,
    GioiTinh,
    # Models
    DonVi,
    VaiTro,
    CongChuc,
)

# Task Catalog
from app.models.task_catalog import (
    SpCongViecChuan,
    CapDoPhucTap,
    DanhMucSpCongViec,
    NhomCongViecPL3,  # PL3 V2 (28/04/2026)
)

# KPI Submission
from app.models.kpi_submission import (
    # Enums
    TrangThaiKeKhai,
    TrangThaiPheDuyet,
    # Models
    KeKhaiCongViec,
    PheDuyetSp,
)

# KPI Assessment (v2.5.0 - Full exports)
from app.models.kpi_assessment import (
    # Enums
    MucXepLoai,
    TrangThaiDanhGia,
    TrangThaiTieuChi,
    LoaiLogicTieuChi,
    # Models
    DanhGiaThang,
    TieuChiChung,           # ⭐ Master Data: Danh mục tiêu chí chung
    TieuChiChungDanhGia,    # Kết quả đánh giá tiêu chí chung
    LanhDaoChiSo,
    # Helper Constants & Functions
    DIEM_TOI_DA_TIEU_CHI,
    get_diem_toi_da,
    tinh_diem_tu_is_achieved,
)

# Leader KPI (v2.5 - 27/01/2026)
from app.models.leader_kpi import (
    # Enums
    TrangThaiHoanThanh,
    # Models
    KeKhaiLanhDao,
    DanhGiaDDE,
)

# Bao cao xep loai
from app.models.bao_cao_xep_loai import (
    BaoCaoXepLoai,
    ChiTietXepLoai,
    TrangThaiBaoCao,
    XepLoaiChatLuong,
    tinh_xep_loai,
)

# Bao cao xep loai quy
from app.models.bao_cao_xep_loai_quy import (
    BaoCaoXepLoaiQuy,
    ChiTietXepLoaiQuy,
)

# Leave Management (v2.3 - 25/01/2026)
from app.models.leave import (
    # Enums
    LoaiNghi,
    TrangThaiNghi,
    # Models
    DangKyNghi,
)

# Audit Log
from app.models.audit_log import (
    AuditAction,
    AuditLog,
)

from app.models.lich_su_dieu_chinh import (
    LoaiDoiTuongDieuChinh,
    LichSuDieuChinh,
)

# Phiếu đánh giá cá nhân theo quý (v4.1.0 - 17/04/2026)
# + theo tháng (08/05/2026)
from app.models.phieu_danh_gia import (
    PhieuDanhGiaQuy,
    PhieuDanhGiaThang,
    TrangThaiPhieuDanhGia,
)

# Công việc yêu thích (favorites cho /ke-khai-v2 - 30/04/2026)
from app.models.cong_viec_yeu_thich import CongViecYeuThich

# Phân công phụ trách (CCT/PCCT ↔ đơn vị, versioned — 05/05/2026)
from app.models.phan_cong_phu_trach import PhanCongPhuTrach

# Điều chỉnh KQCV (LĐ sửa CV của CC/cấp dưới — Yêu cầu 2, 06/05/2026)
from app.models.dieu_chinh_kqcv import DieuChinhKqcv

# HĐLĐ 111 — Bộ tiêu chí đánh giá theo QĐ 714/QĐ-CHQ (08/5/2026, áp dụng từ T5/2026)
from app.models.hdld import (
    TrangThaiHdldDanhGia,
    TEN_NHOM_HDLD,
    HdldTieuChi,
    HdldDanhGia,
    HdldDanhGiaChiTiet,
)

__all__ = [
    # ==========================================================================
    # BASE CLASSES
    # ==========================================================================
    "Base",
    "BaseModel",
    "BaseModelWithSoftDelete",
    "BaseModelFull",
    "TimestampMixin",
    "SoftDeleteMixin",
    "AuditMixin",
    "UUIDPrimaryKeyMixin",
    
    # ==========================================================================
    # USER & ORGANIZATION
    # ==========================================================================
    # Enums
    "LoaiDonVi",
    "CapBacVaiTro",
    "GioiTinh",
    # Models
    "DonVi",
    "VaiTro",
    "CongChuc",
    
    # ==========================================================================
    # TASK CATALOG
    # ==========================================================================
    "SpCongViecChuan",
    "CapDoPhucTap",
    "DanhMucSpCongViec",
    "NhomCongViecPL3",
    
    # ==========================================================================
    # KPI SUBMISSION
    # ==========================================================================
    # Enums
    "TrangThaiKeKhai",
    "TrangThaiPheDuyet",
    # Models
    "KeKhaiCongViec",
    "PheDuyetSp",
    
    # ==========================================================================
    # KPI ASSESSMENT (v2.5.0)
    # ==========================================================================
    # Enums
    "MucXepLoai",
    "TrangThaiDanhGia",
    "TrangThaiTieuChi",
    "LoaiLogicTieuChi",
    # Models
    "DanhGiaThang",
    "TieuChiChung",             # ⭐ Master Data
    "TieuChiChungDanhGia",
    "LanhDaoChiSo",
    # Helper Constants & Functions
    "DIEM_TOI_DA_TIEU_CHI",
    "get_diem_toi_da",
    "tinh_diem_tu_is_achieved",
    
    # ==========================================================================
    # LEAVE MANAGEMENT (v2.3)
    # ==========================================================================
    # Enums
    "LoaiNghi",
    "TrangThaiNghi",
    # Models
    "DangKyNghi",
    
    # ==========================================================================
    # AUDIT LOG
    # ==========================================================================
    "AuditAction",
    "AuditLog",
    # ==========================================================================
    # LEADER KPI (v2.5)
    # ==========================================================================
    "TrangThaiHoanThanh",
    "KeKhaiLanhDao",
    "DanhGiaDDE",
    
    # ==========================================================================
    # BAO CAO XEP LOAI
    # ==========================================================================
    "BaoCaoXepLoai",
    "ChiTietXepLoai",
    "TrangThaiBaoCao",
    "XepLoaiChatLuong",
    "tinh_xep_loai",

    # ==========================================================================
    # BAO CAO XEP LOAI QUY
    # ==========================================================================
    "BaoCaoXepLoaiQuy",
    "ChiTietXepLoaiQuy",

    # ==========================================================================
    # LICH SU DIEU CHINH
    # ==========================================================================
    "LoaiDoiTuongDieuChinh",
    "LichSuDieuChinh",

    # ==========================================================================
    # PHIEU DANH GIA CA NHAN THEO QUY (v4.1.0)
    # ==========================================================================
    "PhieuDanhGiaQuy",
    "PhieuDanhGiaThang",
    "TrangThaiPhieuDanhGia",

    # ==========================================================================
    # CONG VIEC YEU THICH (favorites — 30/04/2026)
    # ==========================================================================
    "CongViecYeuThich",

    # ==========================================================================
    # PHAN CONG PHU TRACH (CCT/PCCT ↔ đơn vị — 05/05/2026)
    # ==========================================================================
    "PhanCongPhuTrach",

    # ==========================================================================
    # DIEU CHINH KQCV (Yêu cầu 2 — 06/05/2026)
    # ==========================================================================
    "DieuChinhKqcv",

    # ==========================================================================
    # HĐLĐ 111 — Bộ tiêu chí VB714 (QĐ 714/QĐ-CHQ, 08/5/2026)
    # ==========================================================================
    "TrangThaiHdldDanhGia",
    "TEN_NHOM_HDLD",
    "HdldTieuChi",
    "HdldDanhGia",
    "HdldDanhGiaChiTiet",
]