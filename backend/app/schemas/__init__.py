"""
app/schemas/__init__.py
=======================
Export tất cả Pydantic schemas.

Phiên bản: 2.4.1 (26/01/2026)
- Thêm schemas mới cho Tiêu chí chung (Binary Scoring)
"""

# Token schemas
from app.schemas.token import Token, TokenPayload, TokenData

# Common schemas
from app.schemas.common import (
    ErrorDetail,
    ErrorResponse,
    DataResponse,
    DataListResponse,
    Pagination,
    PaginatedResponse,
    PaginationParams,
    SortParams,
    success_response,
    error_response,
)

# Master data schemas
from app.schemas.master_data import (
    # Don Vi
    DonViBase,
    DonViResponse,
    DonViDetailResponse,
    # Vai Tro
    VaiTroResponse,
    # Cong Chuc
    CongChucBriefResponse,
    CongChucResponse,
    CongChucDetailResponse,
    CongChucFilterParams,
    # SP Chuan
    SpChuanResponse,
    # Cap Do
    CapDoResponse,
    # Danh Muc
    DanhMucSpResponse,
    DanhMucSpBriefResponse,
    DanhMucSpFilterParams,
)

# KPI Submission schemas
from app.schemas.kpi_submission import (
    KeKhaiBase,
    KeKhaiCreate,
    KeKhaiUpdate,
    KeKhaiResponse,
    KeKhaiBriefResponse,
    ThongKeKeKhaiResponse,
    GuiDuyetRequest,
    GuiDuyetResponse,
    KeKhaiFilterParams,
)

# KPI Assessment schemas (v2.5.0 - Binary Scoring)
from app.schemas.kpi_assessment import (
    # Phê duyệt Kê khai
    PheDuyetAction,
    PheDuyetRequest,
    PheDuyetBulkRequest,
    PheDuyetResponse,
    KeKhaiPendingResponse,
    # Đánh giá tháng
    MucXepLoai,
    TrangThaiTieuChi,
    TrangThaiDanhGia,
    LoaiLogicTieuChi,
    DanhGiaThangResponse,
    DanhGiaThangBriefResponse,
    # Tiêu chí chung - Response (v2.5.0)
    TieuChiChungItem,
    TieuChiChungItemResponse,
    TieuChiChungMasterResponse as TieuChiMasterResponseV2,
    # Tiêu chí chung - Input (v2.5.0 Binary)
    TieuChiChungInputBinary,
    TuDanhGiaRequest,
    TieuChiChungInputLD,
    PheDuyetTieuChiRequest as PheDuyetTieuChiRequestV2,
    # Legacy (backward compatible)
    TieuChiChungUpdate,
    TieuChiChungInput,
    # Tổng hợp
    TongHopRequest,
    TongHopBulkRequest,
    DanhGiaFilterParams,
)

# =============================================================================
# ASSESSMENT SCHEMAS (v2.5.0 - Binary Scoring + Virtual Record)
# =============================================================================
from app.schemas.assessment import (
    # Enums
    TrangThaiTieuChiEnum,
    TrangThaiDanhGiaThangEnum,
    MucXepLoaiEnum,
    # Request - CC tự đánh giá (v2.5.0: is_achieved_cc, ghi_chu_cc)
    TieuChiItemInput,
    TuDanhGiaTieuChiRequest,
    # Request - LĐ phê duyệt
    DieuChinhTieuChiItem,
    PheDuyetTieuChiRequest,
    PheDuyetTieuChiBulkRequest,
    # Response - Tiêu chí chi tiết (v2.5.0: thêm is_achieved, diem, danh_gia_thang_id)
    TieuChiItemResponse,
    TieuChiChungTongHop,
    TuDanhGiaResponse,
    # Response - Đánh giá tháng (v2.5.0: Virtual Record support)
    DanhGiaThangTieuChiResponse,
    # Response - Danh sách chờ duyệt
    DanhSachChoPheDuyetItem,
    DanhSachChoPheDuyetResponse,
    ChiTietPheDuyetResponse,
    # Response - Phê duyệt
    PheDuyetTieuChiResponse,
    PheDuyetBulkResponse,
    # Response - Master data
    TieuChiChungMasterResponse,
    DanhMucTieuChiResponse,
    # Helper
    CongChucBriefForAssessment,
    NguoiPheDuyetOption,
    DanhSachNguoiPheDuyetResponse,
    # Thống kê
    ThongKeTieuChiChungDonVi,
    SoSanhCCvsLD,
    # Constants
    TIEU_CHI_DIEM_TOI_DA,
    TIEU_CHI_GIA_TRI_MAC_DINH,
    TIEU_CHI_NHOM,
    TIEU_CHI_TEN,
    tinh_diem_binary,
    build_virtual_tieu_chi_response,
    build_virtual_tong_hop,
)

# Leave Management schemas (v2.3 - 25/01/2026)
from app.schemas.leave import (
    # Enums
    LoaiNghiEnum,
    TrangThaiNghiEnum,
    # Create/Update
    NghiPhepBase,
    NghiPhepCreate,
    NghiPhepBulkCreate,
    NghiPhepUpdate,
    PheDuyetNghiPhepRequest,
    TuChoiNghiPhepRequest,
    # Response
    CongChucNghiPhepBrief,
    NghiPhepResponse,
    NghiPhepListResponse,
    NghiPhepBulkResponse,
    # Thống kê
    ThongKeNghiPhepLoai,
    ThongKeNghiPhepThang,
    ThongKeNghiPhepCaNhan,
    ThongKeNghiPhepDonVi,
    TongNgayNghiThangResponse,
)

from app.schemas.admin import (
    UserCreateRequest,
    UserUpdateRequest,
    UserStatusRequest,
    UserTransferRequest,
    UserResponse,
    LichSuDieuChuyenResponse,
    SpChuanCreateRequest,
    SpChuanUpdateRequest,
    SpChuanResponse,
    CapDoCreateRequest,
    CapDoUpdateRequest,
    CapDoResponse,
    DanhMucCvCreateRequest,
    DanhMucCvUpdateRequest,
    DanhMucCvResponse,
    AdminActionResponse,
    AdminStatsResponse,
)

__all__ = [
    # =========================================================================
    # TOKEN
    # =========================================================================
    "Token",
    "TokenPayload",
    "TokenData",
    
    # =========================================================================
    # COMMON
    # =========================================================================
    "ErrorDetail",
    "ErrorResponse",
    "DataResponse",
    "DataListResponse",
    "Pagination",
    "PaginatedResponse",
    "PaginationParams",
    "SortParams",
    "success_response",
    "error_response",
    
    # =========================================================================
    # MASTER DATA
    # =========================================================================
    "DonViBase",
    "DonViResponse",
    "DonViDetailResponse",
    "VaiTroResponse",
    "CongChucBriefResponse",
    "CongChucResponse",
    "CongChucDetailResponse",
    "CongChucFilterParams",
    "SpChuanResponse",
    "CapDoResponse",
    "DanhMucSpResponse",
    "DanhMucSpBriefResponse",
    "DanhMucSpFilterParams",
    
    # =========================================================================
    # KPI SUBMISSION
    # =========================================================================
    "KeKhaiBase",
    "KeKhaiCreate",
    "KeKhaiUpdate",
    "KeKhaiResponse",
    "KeKhaiBriefResponse",
    "ThongKeKeKhaiResponse",
    "GuiDuyetRequest",
    "GuiDuyetResponse",
    "KeKhaiFilterParams",
    
    # =========================================================================
    # KPI ASSESSMENT (v2.5.0 - Binary Scoring)
    # =========================================================================
    "PheDuyetAction",
    "PheDuyetRequest",
    "PheDuyetBulkRequest",
    "PheDuyetResponse",
    "KeKhaiPendingResponse",
    "MucXepLoai",
    "TrangThaiTieuChi",
    "TrangThaiDanhGia",
    "LoaiLogicTieuChi",
    "DanhGiaThangResponse",
    "DanhGiaThangBriefResponse",
    "TieuChiChungItem",
    "TieuChiChungItemResponse",
    "TieuChiMasterResponseV2",
    "TieuChiChungInputBinary",
    "TuDanhGiaRequest",
    "TieuChiChungInputLD",
    "PheDuyetTieuChiRequestV2",
    "TieuChiChungUpdate",
    "TieuChiChungInput",
    "TongHopRequest",
    "TongHopBulkRequest",
    "DanhGiaFilterParams",
    
    # =========================================================================
    # ASSESSMENT v2.5.0 (Binary Scoring + Virtual Record)
    # =========================================================================
    # Enums
    "TrangThaiTieuChiEnum",
    "TrangThaiDanhGiaThangEnum",
    "MucXepLoaiEnum",
    # Request - CC tự đánh giá
    "TieuChiItemInput",
    "TuDanhGiaTieuChiRequest",
    # Request - LĐ phê duyệt
    "DieuChinhTieuChiItem",
    "PheDuyetTieuChiRequest",
    "PheDuyetTieuChiBulkRequest",
    # Response - Tiêu chí chi tiết
    "TieuChiItemResponse",
    "TieuChiChungTongHop",
    "TuDanhGiaResponse",
    # Response - Đánh giá tháng (Virtual Record)
    "DanhGiaThangTieuChiResponse",
    # Response - Danh sách chờ duyệt
    "DanhSachChoPheDuyetItem",
    "DanhSachChoPheDuyetResponse",
    "ChiTietPheDuyetResponse",
    # Response - Phê duyệt
    "PheDuyetTieuChiResponse",
    "PheDuyetBulkResponse",
    # Response - Master data
    "TieuChiChungMasterResponse",
    "DanhMucTieuChiResponse",
    # Helper
    "CongChucBriefForAssessment",
    "NguoiPheDuyetOption",
    "DanhSachNguoiPheDuyetResponse",
    # Thống kê
    "ThongKeTieuChiChungDonVi",
    "SoSanhCCvsLD",
    # Constants & Functions
    "TIEU_CHI_DIEM_TOI_DA",
    "TIEU_CHI_GIA_TRI_MAC_DINH",
    "TIEU_CHI_NHOM",
    "TIEU_CHI_TEN",
    "tinh_diem_binary",
    "build_virtual_tieu_chi_response",
    "build_virtual_tong_hop",
    
    # =========================================================================
    # LEAVE MANAGEMENT (v2.3)
    # =========================================================================
    "LoaiNghiEnum",
    "TrangThaiNghiEnum",
    "NghiPhepBase",
    "NghiPhepCreate",
    "NghiPhepBulkCreate",
    "NghiPhepUpdate",
    "PheDuyetNghiPhepRequest",
    "TuChoiNghiPhepRequest",
    "CongChucNghiPhepBrief",
    "NghiPhepResponse",
    "NghiPhepListResponse",
    "NghiPhepBulkResponse",
    "ThongKeNghiPhepLoai",
    "ThongKeNghiPhepThang",
    "ThongKeNghiPhepCaNhan",
    "ThongKeNghiPhepDonVi",
    "TongNgayNghiThangResponse",
    
    # ADMIN MODULES
    "UserCreateRequest",
    "UserUpdateRequest",
    "UserStatusRequest",
    "UserTransferRequest",
    "UserResponse",
    "LichSuDieuChuyenResponse",
    "SpChuanCreateRequest",
    "SpChuanUpdateRequest",
    "SpChuanResponse",
    "CapDoCreateRequest",
    "CapDoUpdateRequest",
    "CapDoResponse",
    "DanhMucCvCreateRequest",
    "DanhMucCvUpdateRequest",
    "DanhMucCvResponse",
    "AdminActionResponse",
    "AdminStatsResponse",
]

