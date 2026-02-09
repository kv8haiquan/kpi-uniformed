"""
app/schemas/kpi_submission.py
=============================
Pydantic schemas cho Kê khai công việc (KPI Submission).

Cập nhật v2.7.4 (2026-02-02):
- Thêm 4 fields mô tả lỗi:
  + ghi_chu_tu_dg_chat_luong, ghi_chu_tu_dg_tien_do (CC tự nhập)
  + ghi_chu_loi_chat_luong, ghi_chu_loi_tien_do (LĐ chốt)

Cập nhật v2.7.0 (2026-01-31):
- Thêm fields tạm tính vào ThongKeKeKhaiResponse:
  + tam_tinh_sp_quy_doi
  + tam_tinh_sp_chat_luong
  + tam_tinh_sp_tien_do

Bao gồm schemas cho:
- KeKhaiCongViec: Kê khai công việc
- ThongKeKeKhai: Thống kê kê khai theo tháng
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict, field_validator

from app.schemas.master_data import (
    CongChucBriefResponse,
    DanhMucSpBriefResponse,
    CapDoResponse,
)


# =============================================================================
# KE KHAI - CREATE / UPDATE SCHEMAS
# =============================================================================

class KeKhaiBase(BaseModel):
    """Base schema cho KeKhaiCongViec."""
    danh_muc_sp_id: UUID = Field(..., description="ID công việc trong danh mục")
    cap_do_id: UUID = Field(..., description="ID cấp độ phức tạp")
    so_luong: int = Field(
        ..., 
        ge=1,
        description="Số lượng công việc (kê khai gộp)"
    )
    ngay_thuc_hien: Optional[date] = Field(
        default=None,
        description="Ngày thực hiện công việc"
    )
    mo_ta_cong_viec: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="Mô tả chi tiết công việc"
    )
    nguoi_phe_duyet_id: Optional[UUID] = Field(
        default=None,
        description="ID người phê duyệt (CC chọn Phó ĐV)"
    )
    he_so_thuc_te: Optional[Decimal] = Field(
        default=None,
        ge=0,
        description="Hệ số thực tế (chỉ dùng cho C5)"
    )
    is_doi_moi_sang_tao: bool = Field(
        default=False,
        description="Có tính đổi mới sáng tạo không"
    )
    ngay_deadline: Optional[date] = Field(
        default=None,
        description="Hạn hoàn thành"
    )
    ngay_hoan_thanh: Optional[date] = Field(
        default=None,
        description="Ngày hoàn thành thực tế"
    )
    
    # -------------------------------------------------------------------------
    # TỰ ĐÁNH GIÁ CỦA CÔNG CHỨC (CC tự nhập khi kê khai)
    # -------------------------------------------------------------------------
    tu_danh_gia_chat_luong: int = Field(
        default=0,
        ge=0,
        description="Số lỗi chất lượng do CC tự đánh giá"
    )
    tu_danh_gia_tien_do: int = Field(
        default=0,
        ge=0,
        description="Số lần chậm tiến độ do CC tự đánh giá"
    )
    ghi_chu_tu_danh_gia: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="Giải trình của CC về lỗi tự đánh giá"
    )
    
    # v2.7.4: Mô tả lỗi tự đánh giá - tách riêng CL và TĐ
    ghi_chu_tu_dg_chat_luong: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Mô tả lỗi chất lượng do CC tự đánh giá"
    )
    ghi_chu_tu_dg_tien_do: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Mô tả lỗi tiến độ do CC tự đánh giá"
    )


class KeKhaiCreate(KeKhaiBase):
    """Schema để tạo mới Kê khai."""
    
    @field_validator("ngay_thuc_hien")
    @classmethod
    def validate_ngay_thuc_hien(cls, v: Optional[date]) -> Optional[date]:
        """Không cho phép ngày thực hiện trong tương lai."""
        if v and v > date.today():
            raise ValueError("Ngày thực hiện không được là ngày trong tương lai")
        return v
    
    @field_validator("ngay_hoan_thanh")
    @classmethod
    def validate_ngay_hoan_thanh(cls, v: Optional[date]) -> Optional[date]:
        """Không cho phép ngày hoàn thành trong tương lai."""
        if v and v > date.today():
            raise ValueError("Ngày hoàn thành không được là ngày trong tương lai")
        return v


class KeKhaiUpdate(BaseModel):
    """Schema để cập nhật Kê khai (partial update)."""
    danh_muc_sp_id: Optional[UUID] = Field(default=None, description="ID công việc")
    cap_do_id: Optional[UUID] = Field(default=None, description="ID cấp độ")
    so_luong: Optional[int] = Field(default=None, ge=1, description="Số lượng")
    ngay_thuc_hien: Optional[date] = Field(default=None, description="Ngày thực hiện")
    mo_ta_cong_viec: Optional[str] = Field(default=None, max_length=2000)
    nguoi_phe_duyet_id: Optional[UUID] = Field(default=None, description="ID người phê duyệt")
    he_so_thuc_te: Optional[Decimal] = Field(default=None, ge=0)
    is_doi_moi_sang_tao: Optional[bool] = Field(default=None)
    ngay_deadline: Optional[date] = Field(default=None)
    ngay_hoan_thanh: Optional[date] = Field(default=None)
    
    # -------------------------------------------------------------------------
    # TỰ ĐÁNH GIÁ CỦA CÔNG CHỨC (CC tự nhập khi kê khai)
    # -------------------------------------------------------------------------
    tu_danh_gia_chat_luong: Optional[int] = Field(
        default=None,
        ge=0,
        description="Số lỗi chất lượng do CC tự đánh giá"
    )
    tu_danh_gia_tien_do: Optional[int] = Field(
        default=None,
        ge=0,
        description="Số lần chậm tiến độ do CC tự đánh giá"
    )
    ghi_chu_tu_danh_gia: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="Giải trình của CC về lỗi tự đánh giá"
    )
    
    # v2.7.4: Mô tả lỗi tự đánh giá - tách riêng CL và TĐ
    ghi_chu_tu_dg_chat_luong: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Mô tả lỗi chất lượng do CC tự đánh giá"
    )
    ghi_chu_tu_dg_tien_do: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Mô tả lỗi tiến độ do CC tự đánh giá"
    )
    
    @field_validator("ngay_thuc_hien")
    @classmethod
    def validate_ngay_thuc_hien(cls, v: Optional[date]) -> Optional[date]:
        """Không cho phép ngày thực hiện trong tương lai."""
        if v and v > date.today():
            raise ValueError("Ngày thực hiện không được là ngày trong tương lai")
        return v


# =============================================================================
# KE KHAI - RESPONSE SCHEMAS
# =============================================================================

class DanhMucSpNestedResponse(BaseModel):
    """Schema response nested cho DanhMuc trong KeKhai."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    ma_danh_muc: str
    ten_cong_viec: str
    ma_sp: Optional[str] = None  # Mã SP chuẩn (SP1, SP2, ...)
    he_so_quy_doi: Optional[float] = None  # Hệ số quy đổi


class CapDoNestedResponse(BaseModel):
    """Schema response nested cho CapDo trong KeKhai."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    ma_cap_do: str
    ten_cap_do: str
    he_so_sp1: float
    he_so_sp2: float
    is_theo_thuc_te: bool


class NguoiPheDuyetNestedResponse(BaseModel):
    """Schema response nested cho người phê duyệt."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    ma_cc: str
    ho_ten: str
    chuc_vu: Optional[str] = None


class KeKhaiResponse(BaseModel):
    """
    Schema response đầy đủ cho KeKhaiCongViec.
    
    Bao gồm:
    - Thông tin kê khai cơ bản
    - Tự đánh giá của CC (+ mô tả lỗi v2.7.4)
    - Phản hồi của Lãnh đạo (sau khi phê duyệt) (+ mô tả lỗi v2.7.4)
    - Kết quả quy đổi điểm
    """
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID = Field(..., description="ID kê khai")
    
    # -------------------------------------------------------------------------
    # NGƯỜI KÊ KHAI
    # -------------------------------------------------------------------------
    cong_chuc_id: UUID
    cong_chuc: Optional[CongChucBriefResponse] = None
    
    # -------------------------------------------------------------------------
    # THỜI GIAN
    # -------------------------------------------------------------------------
    thang: int = Field(..., ge=1, le=12, description="Tháng kê khai")
    nam: int = Field(..., ge=2025, description="Năm kê khai")
    ngay_thuc_hien: Optional[date] = None
    
    # -------------------------------------------------------------------------
    # CÔNG VIỆC
    # -------------------------------------------------------------------------
    danh_muc_sp: Optional[DanhMucSpNestedResponse] = None
    cap_do: Optional[CapDoNestedResponse] = None
    so_luong: int
    he_so_thuc_te: Optional[float] = None
    
    # -------------------------------------------------------------------------
    # NGƯỜI PHÊ DUYỆT
    # -------------------------------------------------------------------------
    nguoi_phe_duyet_id: Optional[UUID] = None
    nguoi_phe_duyet: Optional[NguoiPheDuyetNestedResponse] = None
    
    # -------------------------------------------------------------------------
    # THÔNG TIN BỔ SUNG
    # -------------------------------------------------------------------------
    mo_ta_cong_viec: Optional[str] = None
    is_doi_moi_sang_tao: bool = False
    ngay_deadline: Optional[date] = None
    ngay_hoan_thanh: Optional[date] = None
    
    # -------------------------------------------------------------------------
    # TRẠNG THÁI
    # -------------------------------------------------------------------------
    trang_thai: str = Field(..., description="Trạng thái: NHAP, CHO_PHE_DUYET, DA_PHE_DUYET, TU_CHOI, HUY")
    
    # -------------------------------------------------------------------------
    # TỰ ĐÁNH GIÁ CỦA CÔNG CHỨC (CC tự nhập khi kê khai)
    # -------------------------------------------------------------------------
    tu_danh_gia_chat_luong: int = Field(
        default=0,
        description="Số lỗi chất lượng do CC tự đánh giá"
    )
    tu_danh_gia_tien_do: int = Field(
        default=0,
        description="Số lần chậm tiến độ do CC tự đánh giá"
    )
    ghi_chu_tu_danh_gia: Optional[str] = Field(
        default=None,
        description="Giải trình của CC về lỗi tự đánh giá"
    )
    # v2.7.4: Mô tả lỗi tự đánh giá
    ghi_chu_tu_dg_chat_luong: Optional[str] = Field(
        default=None,
        description="Mô tả lỗi chất lượng do CC tự đánh giá"
    )
    ghi_chu_tu_dg_tien_do: Optional[str] = Field(
        default=None,
        description="Mô tả lỗi tiến độ do CC tự đánh giá"
    )
    
    # -------------------------------------------------------------------------
    # PHẢN HỒI CỦA LÃNH ĐẠO (Lãnh đạo xác nhận khi phê duyệt)
    # -------------------------------------------------------------------------
    so_loi_chat_luong: int = Field(
        default=0,
        description="Số lỗi CL chốt cuối (do lãnh đạo xác nhận)"
    )
    so_loi_tien_do: int = Field(
        default=0,
        description="Số lỗi TĐ chốt cuối (do lãnh đạo xác nhận)"
    )
    y_kien_lanh_dao: Optional[str] = Field(
        default=None,
        description="Ý kiến phản hồi của lãnh đạo khi duyệt"
    )
    # v2.7.4: Mô tả lỗi lãnh đạo chốt
    ghi_chu_loi_chat_luong: Optional[str] = Field(
        default=None,
        description="Mô tả lỗi chất lượng do lãnh đạo chốt"
    )
    ghi_chu_loi_tien_do: Optional[str] = Field(
        default=None,
        description="Mô tả lỗi tiến độ do lãnh đạo chốt"
    )
    
    # -------------------------------------------------------------------------
    # KẾT QUẢ QUY ĐỔI
    # -------------------------------------------------------------------------
    so_sp_goc_quy_doi: Optional[float] = Field(
        default=None,
        description="Số SP gốc sau quy đổi = so_luong × he_so_sp × he_so_cap_do"
    )
    so_sp_chat_luong: Optional[float] = Field(
        default=None,
        description="SP sau khi trừ lỗi chất lượng"
    )
    so_sp_tien_do: Optional[float] = Field(
        default=None,
        description="SP sau khi trừ lỗi tiến độ"
    )
    
    # -------------------------------------------------------------------------
    # METADATA
    # -------------------------------------------------------------------------
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class KeKhaiBriefResponse(BaseModel):
    """Schema response tóm tắt cho KeKhaiCongViec."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    thang: int
    nam: int
    ten_cong_viec: Optional[str] = None
    so_luong: int
    trang_thai: str
    so_sp_goc_quy_doi: Optional[float] = None
    # Tự đánh giá
    tu_danh_gia_chat_luong: int = 0
    tu_danh_gia_tien_do: int = 0
    # Lãnh đạo chốt
    so_loi_chat_luong: int = 0
    so_loi_tien_do: int = 0
    created_at: Optional[datetime] = None


# =============================================================================
# THONG KE SCHEMAS
# =============================================================================

class ThongKeKeKhaiResponse(BaseModel):
    """
    Schema thống kê kê khai theo tháng.
    
    v2.7.0 UPDATE: Thêm fields tạm tính (tam_tinh_*) để hỗ trợ 2-tab UI
    
    Keys đã được đổi tên để khớp với Frontend IKeKhaiMonthSummary:
    - nhap -> tong_nhap
    - cho_phe_duyet -> tong_cho_duyet
    - da_phe_duyet -> tong_da_duyet
    - tu_choi -> tong_tu_choi
    """
    thang: int
    nam: int
    so_sp_duoc_giao: Optional[float] = Field(
        default=None,
        description="Số SP được giao trong tháng"
    )
    tong_ke_khai: int = Field(default=0, description="Tổng số bản kê khai")
    
    # =========================================================================
    # PHÂN LOẠI THEO TRẠNG THÁI
    # =========================================================================
    tong_da_duyet: int = Field(default=0, description="Số bản đã phê duyệt")
    tong_cho_duyet: int = Field(default=0, description="Số bản chờ phê duyệt")
    tong_tu_choi: int = Field(default=0, description="Số bản bị từ chối")
    tong_nhap: int = Field(default=0, description="Số bản đang nháp")
    
    # =========================================================================
    # CHÍNH THỨC (chỉ DA_PHE_DUYET)
    # =========================================================================
    tong_sp_quy_doi: Optional[float] = Field(
        default=None,
        description="Tổng SP quy đổi (chỉ đã phê duyệt)"
    )
    tong_sp_chat_luong: Optional[float] = Field(
        default=None,
        description="Tổng SP sau trừ lỗi chất lượng (chỉ đã phê duyệt)"
    )
    tong_sp_tien_do: Optional[float] = Field(
        default=None,
        description="Tổng SP sau trừ lỗi tiến độ (chỉ đã phê duyệt)"
    )
    ty_le_hoan_thanh: Optional[float] = Field(
        default=None,
        description="Tỷ lệ hoàn thành (%)"
    )
    
    # =========================================================================
    # TẠM TÍNH (NHAP + CHO_PHE_DUYET + DA_PHE_DUYET) - v2.7.0 NEW
    # =========================================================================
    tam_tinh_sp_quy_doi: Optional[float] = Field(
        default=0,
        description="Tổng SP tạm tính (bao gồm cả chưa duyệt)"
    )
    tam_tinh_sp_chat_luong: Optional[float] = Field(
        default=0,
        description="SP đạt CL tạm tính (dùng tu_danh_gia cho kê khai chưa duyệt)"
    )
    tam_tinh_sp_tien_do: Optional[float] = Field(
        default=0,
        description="SP đạt TĐ tạm tính (dùng tu_danh_gia cho kê khai chưa duyệt)"
    )
    
    # =========================================================================
    # THỐNG KÊ LỖI
    # =========================================================================
    # Tự đánh giá của CC
    tong_loi_cl_tu_danh_gia: int = Field(
        default=0,
        description="Tổng lỗi CL do CC tự đánh giá"
    )
    tong_loi_td_tu_danh_gia: int = Field(
        default=0,
        description="Tổng lỗi TĐ do CC tự đánh giá"
    )
    # Chốt cuối của lãnh đạo
    tong_loi_cl_chot: int = Field(
        default=0,
        description="Tổng lỗi CL chốt cuối (lãnh đạo)"
    )
    tong_loi_td_chot: int = Field(
        default=0,
        description="Tổng lỗi TĐ chốt cuối (lãnh đạo)"
    )


# =============================================================================
# GUI DUYET SCHEMAS
# =============================================================================

class GuiDuyetRequest(BaseModel):
    """Schema request khi gửi phê duyệt."""
    nguoi_phe_duyet_id: UUID = Field(
        ...,
        description="ID người phê duyệt (bắt buộc khi gửi duyệt)"
    )


class GuiDuyetResponse(BaseModel):
    """Schema response sau khi gửi phê duyệt."""
    success: bool = True
    message: str = "Đã gửi phê duyệt thành công"
    ke_khai_id: UUID
    nguoi_phe_duyet_id: UUID
    trang_thai_moi: str = "CHO_PHE_DUYET"


# =============================================================================
# FILTER PARAMS
# =============================================================================

class KeKhaiFilterParams(BaseModel):
    """Schema cho filter params khi query KeKhai."""
    thang: Optional[int] = Field(default=None, ge=1, le=12, description="Filter theo tháng")
    nam: Optional[int] = Field(default=None, ge=2025, description="Filter theo năm")
    trang_thai: Optional[str] = Field(
        default=None,
        pattern="^(NHAP|CHO_PHE_DUYET|DA_PHE_DUYET|TU_CHOI|HUY)$",
        description="Filter theo trạng thái"
    )
    danh_muc_sp_id: Optional[UUID] = Field(default=None, description="Filter theo công việc")
    co_loi: Optional[bool] = Field(
        default=None,
        description="Filter các bản kê khai có lỗi (tự đánh giá hoặc lãnh đạo chốt)"
    )