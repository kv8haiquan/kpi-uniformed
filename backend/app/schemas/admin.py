"""
app/schemas/admin.py
====================
Pydantic schemas cho Admin Module.

Phiên bản: 1.0.0 (30/01/2026)

Bao gồm schemas cho:
- Quản lý User (CRUD, status, reset password, transfer)
- Quản lý SP Chuẩn (CRUD)
- Quản lý Cấp độ phức tạp (CRUD)
- Quản lý Danh mục công việc (CRUD)
- Lịch sử điều chuyển
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict, field_validator


# =============================================================================
# USER MANAGEMENT SCHEMAS
# =============================================================================

class UserCreateRequest(BaseModel):
    """Schema tạo mới tài khoản người dùng."""
    
    ma_cc: str = Field(
        ...,
        min_length=1,
        max_length=20,
        description="Mã công chức (unique)",
        examples=["CC550"]
    )
    ho_ten: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Họ tên đầy đủ",
        examples=["Nguyễn Văn A"]
    )
    don_vi_id: UUID = Field(
        ...,
        description="ID đơn vị"
    )
    vai_tro_id: UUID = Field(
        ...,
        description="ID vai trò"
    )
    email: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Email",
        examples=["a@customs.gov.vn"]
    )
    so_dien_thoai: Optional[str] = Field(
        default=None,
        max_length=20,
        description="Số điện thoại",
        examples=["0901234567"]
    )
    ngay_sinh: Optional[date] = Field(
        default=None,
        description="Ngày sinh"
    )
    gioi_tinh: Optional[str] = Field(
        default=None,
        description="Giới tính: NAM hoặc NU",
        examples=["NAM"]
    )
    chuc_vu: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Chức vụ hiển thị",
        examples=["Công chức"]
    )
    is_lanh_dao: bool = Field(
        default=False,
        description="Có phải lãnh đạo không"
    )
    
    @field_validator('gioi_tinh')
    @classmethod
    def validate_gioi_tinh(cls, v):
        if v is not None and v not in ['NAM', 'NU']:
            raise ValueError('Giới tính phải là NAM hoặc NU')
        return v
    
    @field_validator('ma_cc')
    @classmethod
    def validate_ma_cc(cls, v):
        # Loại bỏ khoảng trắng và chuyển uppercase
        return v.strip().upper()


class UserUpdateRequest(BaseModel):
    """Schema cập nhật thông tin người dùng."""
    
    ho_ten: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="Họ tên"
    )
    email: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Email"
    )
    so_dien_thoai: Optional[str] = Field(
        default=None,
        max_length=20,
        description="Số điện thoại"
    )
    ngay_sinh: Optional[date] = Field(
        default=None,
        description="Ngày sinh"
    )
    gioi_tinh: Optional[str] = Field(
        default=None,
        description="Giới tính: NAM hoặc NU"
    )
    chuc_vu: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Chức vụ"
    )
    ngay_vao_nganh: Optional[date] = Field(
        default=None,
        description="Ngày vào ngành"
    )
    ngay_vao_chi_cuc: Optional[date] = Field(
        default=None,
        description="Ngày vào Chi cục"
    )
    
    @field_validator('gioi_tinh')
    @classmethod
    def validate_gioi_tinh(cls, v):
        if v is not None and v not in ['NAM', 'NU']:
            raise ValueError('Giới tính phải là NAM hoặc NU')
        return v


class UserStatusRequest(BaseModel):
    """Schema thay đổi trạng thái tài khoản."""
    
    is_active: bool = Field(
        ...,
        description="True = kích hoạt, False = vô hiệu hóa"
    )
    ly_do: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Lý do thay đổi trạng thái"
    )


class UserTransferRequest(BaseModel):
    """Schema điều chuyển nhân sự."""
    
    don_vi_id_moi: Optional[UUID] = Field(
        default=None,
        description="ID đơn vị mới (nếu chuyển đơn vị)"
    )
    vai_tro_id_moi: Optional[UUID] = Field(
        default=None,
        description="ID vai trò mới (nếu thay đổi)"
    )
    chuc_vu_moi: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Chức vụ mới"
    )
    is_lanh_dao: Optional[bool] = Field(
        default=None,
        description="Có phải lãnh đạo không"
    )
    ly_do: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Lý do điều chuyển",
        examples=["Điều động theo QĐ số 123/QĐ-HQKV8"]
    )
    ngay_hieu_luc: Optional[date] = Field(
        default=None,
        description="Ngày có hiệu lực"
    )


class UserResponse(BaseModel):
    """Schema response cho User."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    ma_cc: str
    ho_ten: str
    email: Optional[str] = None
    so_dien_thoai: Optional[str] = None
    ngay_sinh: Optional[date] = None
    gioi_tinh: Optional[str] = None
    chuc_vu: Optional[str] = None
    is_lanh_dao: bool = False
    is_active: bool = True
    ngay_vao_nganh: Optional[date] = None
    ngay_vao_chi_cuc: Optional[date] = None
    last_login: Optional[datetime] = None
    
    # Đơn vị (flattened)
    don_vi_id: Optional[UUID] = None
    don_vi_ma: Optional[str] = None
    don_vi_ten: Optional[str] = None
    
    # Vai trò (flattened)
    vai_tro_id: Optional[UUID] = None
    vai_tro_ma: Optional[str] = None
    vai_tro_ten: Optional[str] = None
    
    created_at: Optional[datetime] = None


# =============================================================================
# LỊCH SỬ ĐIỀU CHUYỂN SCHEMAS
# =============================================================================

class LichSuDieuChuyenResponse(BaseModel):
    """Schema response cho lịch sử điều chuyển."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    cong_chuc_id: UUID
    
    # Đơn vị
    don_vi_cu_id: Optional[UUID] = None
    don_vi_cu_ten: Optional[str] = None
    don_vi_moi_id: Optional[UUID] = None
    don_vi_moi_ten: Optional[str] = None
    
    # Vai trò
    vai_tro_cu_id: Optional[UUID] = None
    vai_tro_cu_ten: Optional[str] = None
    vai_tro_moi_id: Optional[UUID] = None
    vai_tro_moi_ten: Optional[str] = None
    
    # Chức vụ
    chuc_vu_cu: Optional[str] = None
    chuc_vu_moi: Optional[str] = None
    
    ly_do: Optional[str] = None
    ngay_hieu_luc: Optional[date] = None
    
    # Người thực hiện
    nguoi_thuc_hien_id: Optional[UUID] = None
    nguoi_thuc_hien_ten: Optional[str] = None
    
    created_at: datetime


# =============================================================================
# SP CHUẨN SCHEMAS
# =============================================================================

class SpChuanCreateRequest(BaseModel):
    """Schema tạo mới SP Chuẩn."""
    
    ma_sp: str = Field(
        ...,
        min_length=1,
        max_length=10,
        description="Mã SP (unique)",
        examples=["SP5"]
    )
    ten_sp: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Tên sản phẩm chuẩn",
        examples=["Báo cáo phân tích"]
    )
    mo_ta: Optional[str] = Field(
        default=None,
        description="Mô tả chi tiết"
    )
    thoi_gian_phut: int = Field(
        ...,
        gt=0,
        description="Thời gian thực hiện (phút)",
        examples=[120]
    )
    he_so_quy_doi_sp1: Decimal = Field(
        ...,
        gt=0,
        description="Hệ số quy đổi về SP gốc (phải > 0)",
        examples=[24.0]
    )
    
    @field_validator('ma_sp')
    @classmethod
    def validate_ma_sp(cls, v):
        return v.strip().upper()
    
    @field_validator('he_so_quy_doi_sp1')
    @classmethod
    def validate_he_so(cls, v):
        if v <= 0:
            raise ValueError('Hệ số quy đổi phải > 0')
        return v


class SpChuanUpdateRequest(BaseModel):
    """Schema cập nhật SP Chuẩn."""
    
    ten_sp: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=200,
        description="Tên sản phẩm chuẩn"
    )
    mo_ta: Optional[str] = Field(
        default=None,
        description="Mô tả"
    )
    thoi_gian_phut: Optional[int] = Field(
        default=None,
        gt=0,
        description="Thời gian (phút)"
    )
    he_so_quy_doi_sp1: Optional[Decimal] = Field(
        default=None,
        gt=0,
        description="Hệ số quy đổi (> 0)"
    )
    
    @field_validator('he_so_quy_doi_sp1')
    @classmethod
    def validate_he_so(cls, v):
        if v is not None and v <= 0:
            raise ValueError('Hệ số quy đổi phải > 0')
        return v


class SpChuanResponse(BaseModel):
    """Schema response cho SP Chuẩn."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    ma_sp: str
    ten_sp: str
    mo_ta: Optional[str] = None
    thoi_gian_phut: int
    he_so_quy_doi_sp1: Decimal
    is_sp_goc: bool = False
    is_active: bool = True
    created_at: Optional[datetime] = None


# =============================================================================
# CẤP ĐỘ PHỨC TẠP SCHEMAS
# =============================================================================

class CapDoCreateRequest(BaseModel):
    """Schema tạo mới Cấp độ phức tạp."""
    
    ma_cap_do: str = Field(
        ...,
        min_length=1,
        max_length=10,
        description="Mã cấp độ (unique)",
        examples=["C6"]
    )
    ten_cap_do: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Tên cấp độ",
        examples=["Đặc biệt phức tạp"]
    )
    mo_ta: Optional[str] = Field(
        default=None,
        description="Mô tả tiêu chí"
    )
    he_so_sp1: Decimal = Field(
        ...,
        gt=0,
        description="Hệ số cho SP1 (> 0)",
        examples=[48.0]
    )
    he_so_sp2: Decimal = Field(
        ...,
        gt=0,
        description="Hệ số cho SP2/SP3/SP4 (> 0)",
        examples=[16.0]
    )
    is_theo_thuc_te: bool = Field(
        default=False,
        description="True = theo thực tế (như C5)"
    )
    thu_tu: int = Field(
        default=0,
        ge=0,
        description="Thứ tự hiển thị"
    )
    
    @field_validator('ma_cap_do')
    @classmethod
    def validate_ma(cls, v):
        return v.strip().upper()
    
    @field_validator('he_so_sp1', 'he_so_sp2')
    @classmethod
    def validate_he_so(cls, v):
        if v <= 0:
            raise ValueError('Hệ số phải > 0')
        return v


class CapDoUpdateRequest(BaseModel):
    """Schema cập nhật Cấp độ."""
    
    ten_cap_do: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Tên cấp độ"
    )
    mo_ta: Optional[str] = Field(
        default=None,
        description="Mô tả"
    )
    he_so_sp1: Optional[Decimal] = Field(
        default=None,
        gt=0,
        description="Hệ số SP1"
    )
    he_so_sp2: Optional[Decimal] = Field(
        default=None,
        gt=0,
        description="Hệ số SP2"
    )
    is_theo_thuc_te: Optional[bool] = Field(
        default=None,
        description="Theo thực tế"
    )
    thu_tu: Optional[int] = Field(
        default=None,
        ge=0,
        description="Thứ tự"
    )
    
    @field_validator('he_so_sp1', 'he_so_sp2')
    @classmethod
    def validate_he_so(cls, v):
        if v is not None and v <= 0:
            raise ValueError('Hệ số phải > 0')
        return v


class CapDoResponse(BaseModel):
    """Schema response cho Cấp độ."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    ma_cap_do: str
    ten_cap_do: str
    mo_ta: Optional[str] = None
    he_so_sp1: Decimal
    he_so_sp2: Decimal
    is_theo_thuc_te: bool = False
    thu_tu: int = 0
    is_active: bool = True
    created_at: Optional[datetime] = None


# =============================================================================
# DANH MỤC CÔNG VIỆC SCHEMAS
# =============================================================================

class DanhMucCvCreateRequest(BaseModel):
    """Schema tạo mới Danh mục công việc."""
    
    ma_danh_muc: str = Field(
        ...,
        min_length=1,
        max_length=20,
        description="Mã danh mục (unique)",
        examples=["CV047"]
    )
    ten_cong_viec: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Tên công việc",
        examples=["Kiểm tra sau thông quan"]
    )
    mo_ta: Optional[str] = Field(
        default=None,
        description="Mô tả chi tiết"
    )
    sp_chuan_id: UUID = Field(
        ...,
        description="ID SP Chuẩn áp dụng"
    )
    don_vi_ap_dung_id: Optional[UUID] = Field(
        default=None,
        description="ID đơn vị áp dụng (NULL = toàn Chi cục)"
    )
    nhom_cong_viec: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Nhóm công việc",
        examples=["Kiểm tra"]
    )
    
    @field_validator('ma_danh_muc')
    @classmethod
    def validate_ma(cls, v):
        return v.strip().upper()


class DanhMucCvUpdateRequest(BaseModel):
    """Schema cập nhật Danh mục công việc."""
    
    ten_cong_viec: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Tên công việc"
    )
    mo_ta: Optional[str] = Field(
        default=None,
        description="Mô tả"
    )
    sp_chuan_id: Optional[UUID] = Field(
        default=None,
        description="ID SP Chuẩn"
    )
    don_vi_ap_dung_id: Optional[UUID] = Field(
        default=None,
        description="ID đơn vị (NULL = toàn Chi cục)"
    )
    nhom_cong_viec: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Nhóm công việc"
    )


class DanhMucCvResponse(BaseModel):
    """Schema response cho Danh mục công việc."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    ma_danh_muc: str
    ten_cong_viec: str
    mo_ta: Optional[str] = None
    nhom_cong_viec: Optional[str] = None
    is_active: bool = True
    
    # SP Chuẩn
    sp_chuan_id: Optional[UUID] = None
    sp_chuan_ma: Optional[str] = None
    sp_chuan_ten: Optional[str] = None
    he_so_quy_doi: Optional[Decimal] = None
    
    # Đơn vị áp dụng
    don_vi_ap_dung_id: Optional[UUID] = None
    don_vi_ap_dung_ten: Optional[str] = None
    
    created_at: Optional[datetime] = None


# =============================================================================
# COMMON SCHEMAS
# =============================================================================

class AdminActionResponse(BaseModel):
    """Schema response chung cho các action Admin."""
    
    success: bool = True
    message: str
    data: Optional[dict] = None


class AdminStatsResponse(BaseModel):
    """Schema thống kê Admin."""
    
    tong_user: int = Field(..., description="Tổng số user")
    user_active: int = Field(..., description="User đang hoạt động")
    user_inactive: int = Field(..., description="User bị vô hiệu hóa")
    tong_don_vi: int = Field(..., description="Tổng số đơn vị")
    tong_sp_chuan: int = Field(..., description="Tổng SP chuẩn")
    tong_cap_do: int = Field(..., description="Tổng cấp độ")
    tong_danh_muc_cv: int = Field(..., description="Tổng danh mục CV")
