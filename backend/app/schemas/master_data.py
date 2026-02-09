"""
app/schemas/master_data.py
==========================
Pydantic schemas cho Master Data (Dữ liệu nền tảng).

Bao gồm schemas cho:
- DonVi: Đơn vị
- VaiTro: Vai trò
- CongChuc: Công chức
- SpCongViecChuan: Sản phẩm chuẩn (SP1-SP4)
- CapDoPhucTap: Cấp độ phức tạp (C1-C5)
- DanhMucSpCongViec: Danh mục sản phẩm/công việc
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


# =============================================================================
# DON VI SCHEMAS
# =============================================================================

class DonViBase(BaseModel):
    """Base schema cho DonVi."""
    ma_don_vi: str = Field(..., max_length=20, description="Mã đơn vị")
    ten_don_vi: str = Field(..., max_length=200, description="Tên đơn vị")
    ten_viet_tat: Optional[str] = Field(default=None, max_length=50, description="Tên viết tắt")
    loai_don_vi: str = Field(..., description="Loại đơn vị: PHONG, DOI, HAI_QUAN_CUA_KHAU")


class DonViResponse(DonViBase):
    """Schema response cho DonVi."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID = Field(..., description="ID đơn vị (UUID)")
    parent_id: Optional[UUID] = Field(default=None, description="ID đơn vị cha")
    thu_tu_hien_thi: int = Field(default=0, description="Thứ tự hiển thị")
    is_active: bool = Field(default=True, description="Đơn vị còn hoạt động")


class DonViDetailResponse(DonViResponse):
    """Schema response chi tiết cho DonVi (kèm thống kê)."""
    so_cong_chuc: Optional[int] = Field(default=0, description="Số công chức thuộc đơn vị")
    truong_don_vi: Optional["CongChucBriefResponse"] = Field(
        default=None, description="Trưởng đơn vị"
    )
    pho_don_vi: Optional[List["CongChucBriefResponse"]] = Field(
        default=None, description="Danh sách Phó đơn vị"
    )


# =============================================================================
# VAI TRO SCHEMAS
# =============================================================================

class VaiTroResponse(BaseModel):
    """Schema response cho VaiTro."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID = Field(..., description="ID vai trò")
    ma_vai_tro: str = Field(..., description="Mã vai trò: CCT, PCCT, TDV, PDV, CC")
    ten_vai_tro: str = Field(..., description="Tên vai trò")
    cap_bac: str = Field(..., description="Cấp bậc trong hệ thống")
    is_lanh_dao: bool = Field(default=False, description="Có phải lãnh đạo không")


# =============================================================================
# CONG CHUC SCHEMAS
# =============================================================================

class CongChucBriefResponse(BaseModel):
    """Schema response tóm tắt cho CongChuc (dùng trong nested)."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID = Field(..., description="ID công chức")
    ma_cc: str = Field(..., description="Mã công chức")
    ho_ten: str = Field(..., description="Họ tên")


class CongChucResponse(BaseModel):
    """Schema response đầy đủ cho CongChuc."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID = Field(..., description="ID công chức")
    ma_cc: str = Field(..., description="Mã công chức")
    ho_ten: str = Field(..., description="Họ tên")
    ngay_sinh: Optional[date] = Field(default=None, description="Ngày sinh")
    gioi_tinh: Optional[str] = Field(default=None, description="Giới tính: NAM, NU")
    so_dien_thoai: Optional[str] = Field(default=None, description="Số điện thoại")
    email: Optional[str] = Field(default=None, description="Email")
    
    # Thông tin đơn vị (flattened)
    don_vi_id: Optional[UUID] = Field(default=None, description="ID đơn vị")
    don_vi_ten: Optional[str] = Field(default=None, description="Tên đơn vị")
    don_vi_ma: Optional[str] = Field(default=None, description="Mã đơn vị")
    
    # Thông tin vai trò (flattened)
    vai_tro_id: Optional[UUID] = Field(default=None, description="ID vai trò")
    vai_tro_ma: Optional[str] = Field(default=None, description="Mã vai trò")
    vai_tro_ten: Optional[str] = Field(default=None, description="Tên vai trò")
    
    chuc_vu: Optional[str] = Field(default=None, description="Chức vụ hiển thị")
    is_lanh_dao: bool = Field(default=False, description="Là lãnh đạo")
    is_active: bool = Field(default=True, description="Tài khoản active")
    
    ngay_vao_nganh: Optional[date] = Field(default=None, description="Ngày vào ngành")
    ngay_vao_chi_cuc: Optional[date] = Field(default=None, description="Ngày vào Chi cục")


class CongChucDetailResponse(CongChucResponse):
    """Schema response chi tiết cho CongChuc (kèm nested objects)."""
    don_vi: Optional[DonViResponse] = Field(default=None, description="Thông tin đơn vị")
    vai_tro: Optional[VaiTroResponse] = Field(default=None, description="Thông tin vai trò")
    last_login: Optional[datetime] = Field(default=None, description="Lần đăng nhập cuối")


# =============================================================================
# SP CONG VIEC CHUAN SCHEMAS (SP1-SP4)
# =============================================================================

class SpChuanResponse(BaseModel):
    """Schema response cho SpCongViecChuan (SP1-SP4)."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID = Field(..., description="ID sản phẩm chuẩn")
    ma_sp: str = Field(..., description="Mã SP: SP1, SP2, SP3, SP4")
    ten_sp: str = Field(..., description="Tên sản phẩm chuẩn")
    mo_ta: Optional[str] = Field(default=None, description="Mô tả")
    thoi_gian_phut: int = Field(..., description="Thời gian thực hiện (phút)")
    he_so_quy_doi_sp1: Decimal = Field(..., description="Hệ số quy đổi về SP gốc")
    is_sp_goc: bool = Field(default=False, description="Là SP gốc (SP1)")
    is_active: bool = Field(default=True, description="Còn sử dụng")


# =============================================================================
# CAP DO PHUC TAP SCHEMAS (C1-C5)
# =============================================================================

class CapDoResponse(BaseModel):
    """Schema response cho CapDoPhucTap (C1-C5)."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID = Field(..., description="ID cấp độ")
    ma_cap_do: str = Field(..., description="Mã cấp độ: C1, C2, C3, C4, C5")
    ten_cap_do: str = Field(..., description="Tên cấp độ")
    mo_ta: Optional[str] = Field(default=None, description="Mô tả tiêu chí")
    he_so_sp1: Decimal = Field(..., description="Hệ số nhân cho SP1")
    he_so_sp2: Decimal = Field(..., description="Hệ số nhân cho SP2/SP3/SP4")
    is_theo_thuc_te: bool = Field(default=False, description="C5 - theo thực tế")
    thu_tu: int = Field(..., description="Thứ tự sắp xếp")
    is_active: bool = Field(default=True, description="Còn sử dụng")


# =============================================================================
# DANH MUC SP CONG VIEC SCHEMAS
# =============================================================================

class DanhMucSpResponse(BaseModel):
    """Schema response cho DanhMucSpCongViec."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID = Field(..., description="ID danh mục")
    ma_danh_muc: str = Field(..., description="Mã danh mục")
    ten_cong_viec: str = Field(..., description="Tên công việc")
    mo_ta: Optional[str] = Field(default=None, description="Mô tả chi tiết")
    nhom_cong_viec: Optional[str] = Field(default=None, description="Nhóm công việc")
    is_active: bool = Field(default=True, description="Còn sử dụng")
    
    # Nested SP chuẩn
    sp_chuan: Optional[SpChuanResponse] = Field(
        default=None, description="Thông tin SP chuẩn (SP1-SP4)"
    )
    
    # Đơn vị áp dụng (nếu có)
    don_vi_ap_dung_id: Optional[UUID] = Field(
        default=None, description="ID đơn vị áp dụng (NULL = toàn Chi cục)"
    )
    don_vi_ap_dung_ten: Optional[str] = Field(
        default=None, description="Tên đơn vị áp dụng"
    )


class DanhMucSpBriefResponse(BaseModel):
    """Schema response tóm tắt cho DanhMucSpCongViec."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID = Field(..., description="ID danh mục")
    ma_danh_muc: str = Field(..., description="Mã danh mục")
    ten_cong_viec: str = Field(..., description="Tên công việc")
    ma_sp: Optional[str] = Field(default=None, description="Mã SP chuẩn")
    nhom_cong_viec: Optional[str] = Field(default=None, description="Nhóm công việc")


# =============================================================================
# FILTER SCHEMAS (cho Query Params)
# =============================================================================

class CongChucFilterParams(BaseModel):
    """Schema cho filter params khi query CongChuc."""
    don_vi_id: Optional[UUID] = Field(default=None, description="Filter theo đơn vị")
    vai_tro_id: Optional[UUID] = Field(default=None, description="Filter theo vai trò")
    is_lanh_dao: Optional[bool] = Field(default=None, description="Filter lãnh đạo")
    is_active: Optional[bool] = Field(default=True, description="Filter active (default: True)")
    search: Optional[str] = Field(
        default=None, 
        min_length=1,
        max_length=100,
        description="Tìm kiếm theo tên hoặc mã CC"
    )


class DanhMucSpFilterParams(BaseModel):
    """Schema cho filter params khi query DanhMucSpCongViec."""
    sp_chuan_id: Optional[UUID] = Field(default=None, description="Filter theo SP chuẩn")
    don_vi_ap_dung_id: Optional[UUID] = Field(default=None, description="Filter theo đơn vị áp dụng")
    nhom_cong_viec: Optional[str] = Field(default=None, description="Filter theo nhóm công việc")
    is_active: Optional[bool] = Field(default=True, description="Filter active (default: True)")
    search: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="Tìm kiếm theo tên hoặc mã"
    )


# =============================================================================
# UPDATE FORWARD REFS
# =============================================================================

# Cần update forward references cho nested schemas
DonViDetailResponse.model_rebuild()
