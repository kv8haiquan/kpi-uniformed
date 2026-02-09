"""
app/schemas/leader_kpi.py
=========================
Pydantic Schemas cho Module Kê khai KPI Lãnh đạo.

Bao gồm:
1. Schemas cho Kê khai công việc Lãnh đạo
2. Schemas cho Đánh giá d, đ, e
3. Schemas cho Thống kê

Phiên bản: 2.7.4 (02/02/2026)
Cập nhật:
- v2.7.4: Thêm ghi_chu_loi_chat_luong, ghi_chu_loi_tien_do vào Create, Update, Response
- v2.7.0: Thêm fields tạm tính vào ThongKeKeKhaiLDResponse
- v2.7.3: FIX - Thêm so_loi_chat_luong, so_loi_tien_do vào KeKhaiLanhDaoCreate & Update
         Nếu thiếu 2 field này, Pydantic sẽ filter mất data từ Frontend → backend không nhận được
"""

from datetime import date, datetime
from enum import Enum
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator


# =============================================================================
# ENUMS
# =============================================================================

class TrangThaiHoanThanhEnum(str, Enum):
    """Trạng thái hoàn thành công việc."""
    DA_HOAN_THANH = "DA_HOAN_THANH"
    CHUA_HOAN_THANH = "CHUA_HOAN_THANH"


class TrangThaiKeKhaiLDEnum(str, Enum):
    """Trạng thái kê khai của Lãnh đạo."""
    NHAP = "NHAP"
    CHO_PHE_DUYET = "CHO_PHE_DUYET"
    DA_PHE_DUYET = "DA_PHE_DUYET"
    TU_CHOI = "TU_CHOI"


class TrangThaiDDEEnum(str, Enum):
    """Trạng thái đánh giá d, đ, e."""
    NHAP = "NHAP"
    CHO_PHE_DUYET = "CHO_PHE_DUYET"
    DA_PHE_DUYET = "DA_PHE_DUYET"


# =============================================================================
# NESTED SCHEMAS
# =============================================================================

class CongChucBriefResponse(BaseModel):
    """Thông tin tóm tắt công chức."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    ma_cc: str
    ho_ten: str
    chuc_vu: Optional[str] = None


class CongChucDetailResponse(CongChucBriefResponse):
    """Thông tin chi tiết công chức (có vai trò, đơn vị)."""
    vai_tro: Optional[dict] = None
    don_vi: Optional[dict] = None


# =============================================================================
# KÊ KHAI LÃNH ĐẠO - REQUEST SCHEMAS
# =============================================================================

class KeKhaiLanhDaoCreate(BaseModel):
    """Schema tạo kê khai công việc mới cho Lãnh đạo.
    
    v2.7.3: Thêm so_loi_chat_luong, so_loi_tien_do để lưu tự đánh giá lỗi.
    QUAN TRỌNG: Nếu thiếu 2 field này, Pydantic sẽ bỏ qua data từ Frontend
    dù Frontend có gửi lên, dẫn đến backend luôn nhận = 0.
    """
    
    thang: int = Field(..., ge=1, le=12, description="Tháng kê khai (1-12)")
    nam: int = Field(..., ge=2025, description="Năm kê khai")
    
    ten_cong_viec: str = Field(
        ..., 
        min_length=1, 
        max_length=500,
        description="Tên công việc"
    )
    mo_ta: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="Mô tả chi tiết công việc"
    )
    ngay_thuc_hien: date = Field(..., description="Ngày thực hiện công việc")
    
    trang_thai_hoan_thanh: TrangThaiHoanThanhEnum = Field(
        default=TrangThaiHoanThanhEnum.CHUA_HOAN_THANH,
        description="Trạng thái hoàn thành"
    )
    so_luong: int = Field(default=1, ge=1, description="Số lượng công việc")
    
    nguoi_phe_duyet_id: Optional[UUID] = Field(
        default=None,
        description="ID người phê duyệt"
    )
    
    # v2.7.3: Số lỗi tự đánh giá khi tạo kê khai
    so_loi_chat_luong: int = Field(default=0, ge=0, description="Số lỗi chất lượng tự đánh giá")
    so_loi_tien_do: int = Field(default=0, ge=0, description="Số lỗi tiến độ tự đánh giá")
    
    # v2.7.4: Mô tả lỗi
    ghi_chu_loi_chat_luong: Optional[str] = Field(default=None, max_length=1000, description="Mô tả / giải trình lỗi chất lượng")
    ghi_chu_loi_tien_do: Optional[str] = Field(default=None, max_length=1000, description="Mô tả / giải trình lỗi tiến độ")
    
    @field_validator("ngay_thuc_hien")
    @classmethod
    def validate_ngay_thuc_hien(cls, v, info):
        """Ngày thực hiện phải trong tháng/năm kê khai."""
        # Lưu ý: Validator này cần data context để check thang/nam
        # Sẽ validate ở service layer
        return v


class KeKhaiLanhDaoUpdate(BaseModel):
    """Schema cập nhật kê khai công việc.
    
    v2.7.3: Thêm so_loi_chat_luong, so_loi_tien_do.
    """
    
    ten_cong_viec: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=500,
        description="Tên công việc"
    )
    mo_ta: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="Mô tả chi tiết công việc"
    )
    ngay_thuc_hien: Optional[date] = Field(
        default=None,
        description="Ngày thực hiện công việc"
    )
    trang_thai_hoan_thanh: Optional[TrangThaiHoanThanhEnum] = Field(
        default=None,
        description="Trạng thái hoàn thành"
    )
    so_luong: Optional[int] = Field(
        default=None,
        ge=1,
        description="Số lượng công việc"
    )
    nguoi_phe_duyet_id: Optional[UUID] = Field(
        default=None,
        description="ID người phê duyệt"
    )
    
    # v2.7.3: Số lỗi tự đánh giá khi cập nhật
    so_loi_chat_luong: Optional[int] = Field(default=None, ge=0, description="Số lỗi chất lượng tự đánh giá")
    so_loi_tien_do: Optional[int] = Field(default=None, ge=0, description="Số lỗi tiến độ tự đánh giá")
    
    # v2.7.4: Mô tả lỗi
    ghi_chu_loi_chat_luong: Optional[str] = Field(default=None, max_length=1000, description="Mô tả / giải trình lỗi chất lượng")
    ghi_chu_loi_tien_do: Optional[str] = Field(default=None, max_length=1000, description="Mô tả / giải trình lỗi tiến độ")


class GuiDuyetRequest(BaseModel):
    """Schema gửi phê duyệt kê khai."""
    nguoi_phe_duyet_id: UUID = Field(..., description="ID người phê duyệt")


class PheDuyetKeKhaiLDRequest(BaseModel):
    """Schema phê duyệt kê khai Lãnh đạo."""
    
    action: str = Field(
        ..., 
        description="Hành động: APPROVE hoặc REJECT"
    )
    so_loi_chat_luong: int = Field(
        default=0,
        ge=0,
        description="Số lỗi chất lượng"
    )
    so_loi_tien_do: int = Field(
        default=0,
        ge=0,
        description="Số lỗi tiến độ"
    )
    y_kien: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Ý kiến của người phê duyệt"
    )
    
    @field_validator("action")
    @classmethod
    def validate_action(cls, v):
        if v.upper() not in ["APPROVE", "REJECT"]:
            raise ValueError("action phải là APPROVE hoặc REJECT")
        return v.upper()


# =============================================================================
# KÊ KHAI LÃNH ĐẠO - RESPONSE SCHEMAS
# =============================================================================

class KeKhaiLanhDaoResponse(BaseModel):
    """Schema response cho kê khai công việc Lãnh đạo."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    cong_chuc_id: UUID
    thang: int
    nam: int
    
    # Thông tin công việc
    ten_cong_viec: str
    mo_ta: Optional[str] = None
    ngay_thuc_hien: date
    trang_thai_hoan_thanh: str
    so_luong: int
    
    # Phê duyệt
    nguoi_phe_duyet_id: Optional[UUID] = None
    nguoi_phe_duyet: Optional[CongChucBriefResponse] = None
    trang_thai: str
    
    # Đánh giá
    so_loi_chat_luong: int = 0
    so_loi_tien_do: int = 0
    # v2.7.4: Mô tả lỗi
    ghi_chu_loi_chat_luong: Optional[str] = None
    ghi_chu_loi_tien_do: Optional[str] = None
    y_kien_lanh_dao: Optional[str] = None
    
    # Timestamps
    created_at: datetime
    updated_at: datetime


class KeKhaiLanhDaoListResponse(BaseModel):
    """Response danh sách kê khai."""
    data: List[KeKhaiLanhDaoResponse]
    total: int = 0


# =============================================================================
# ĐÁNH GIÁ d, đ, e - REQUEST SCHEMAS
# =============================================================================

class DanhGiaDDECreate(BaseModel):
    """Schema tạo/cập nhật đánh giá d, đ, e."""
    
    thang: int = Field(..., ge=1, le=12, description="Tháng đánh giá")
    nam: int = Field(..., ge=2025, description="Năm đánh giá")
    
    # d: Kết quả đơn vị (boolean → 100 hoặc 50)
    d_ket_qua_don_vi: bool = Field(
        default=True,
        description="Kết quả đơn vị: True=100%, False=50%"
    )
    d_ghi_chu: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Ghi chú cho chỉ số d"
    )
    
    # đ: Tổ chức triển khai
    dd_to_chuc_trien_khai: bool = Field(
        default=True,
        description="Tổ chức triển khai: True=100%, False=50%"
    )
    dd_ghi_chu: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Ghi chú cho chỉ số đ"
    )
    
    # e: Đoàn kết nội bộ
    e_doan_ket_noi_bo: bool = Field(
        default=True,
        description="Đoàn kết nội bộ: True=100%, False=50%"
    )
    e_ghi_chu: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Ghi chú cho chỉ số e"
    )
    
    def to_db_values(self) -> dict:
        """Convert boolean to int (100 hoặc 50) cho DB."""
        return {
            "d_ket_qua_don_vi": 100 if self.d_ket_qua_don_vi else 50,
            "d_ghi_chu": self.d_ghi_chu,
            "dd_to_chuc_trien_khai": 100 if self.dd_to_chuc_trien_khai else 50,
            "dd_ghi_chu": self.dd_ghi_chu,
            "e_doan_ket_noi_bo": 100 if self.e_doan_ket_noi_bo else 50,
            "e_ghi_chu": self.e_ghi_chu,
        }


class GuiDuyetDDERequest(BaseModel):
    """Schema gửi phê duyệt đánh giá d, đ, e."""
    nguoi_phe_duyet_id: UUID = Field(..., description="ID người phê duyệt")


class PheDuyetDDERequest(BaseModel):
    """Schema phê duyệt đánh giá d, đ, e."""
    
    action: str = Field(..., description="Hành động: APPROVE hoặc REJECT")
    
    # Giá trị điều chỉnh (optional)
    d_phe_duyet: Optional[int] = Field(
        default=None,
        description="Giá trị d sau điều chỉnh (50 hoặc 100)"
    )
    dd_phe_duyet: Optional[int] = Field(
        default=None,
        description="Giá trị đ sau điều chỉnh (50 hoặc 100)"
    )
    e_phe_duyet: Optional[int] = Field(
        default=None,
        description="Giá trị e sau điều chỉnh (50 hoặc 100)"
    )
    
    y_kien: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Ý kiến của người phê duyệt"
    )
    
    @field_validator("action")
    @classmethod
    def validate_action(cls, v):
        if v.upper() not in ["APPROVE", "REJECT"]:
            raise ValueError("action phải là APPROVE hoặc REJECT")
        return v.upper()
    
    @field_validator("d_phe_duyet", "dd_phe_duyet", "e_phe_duyet")
    @classmethod
    def validate_dde_values(cls, v):
        if v is not None and v not in [50, 100]:
            raise ValueError("Giá trị phải là 50 hoặc 100")
        return v


# =============================================================================
# ĐÁNH GIÁ d, đ, e - RESPONSE SCHEMAS
# =============================================================================

class DanhGiaDDEResponse(BaseModel):
    """Schema response cho đánh giá d, đ, e."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    cong_chuc_id: UUID
    thang: int
    nam: int
    
    # Giá trị tự đánh giá
    d_ket_qua_don_vi: int
    d_ghi_chu: Optional[str] = None
    dd_to_chuc_trien_khai: int
    dd_ghi_chu: Optional[str] = None
    e_doan_ket_noi_bo: int
    e_ghi_chu: Optional[str] = None
    
    # Phê duyệt
    trang_thai: str
    nguoi_phe_duyet_id: Optional[UUID] = None
    y_kien_phe_duyet: Optional[str] = None
    ngay_phe_duyet: Optional[datetime] = None
    
    # Giá trị sau phê duyệt
    d_phe_duyet: Optional[int] = None
    dd_phe_duyet: Optional[int] = None
    e_phe_duyet: Optional[int] = None
    
    # Giá trị cuối cùng (computed)
    d_final: int = 100
    dd_final: int = 100
    e_final: int = 100
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    
    @model_validator(mode="after")
    def compute_finals(self):
        """Tính giá trị cuối cùng."""
        self.d_final = self.d_phe_duyet if self.d_phe_duyet is not None else self.d_ket_qua_don_vi
        self.dd_final = self.dd_phe_duyet if self.dd_phe_duyet is not None else self.dd_to_chuc_trien_khai
        self.e_final = self.e_phe_duyet if self.e_phe_duyet is not None else self.e_doan_ket_noi_bo
        return self


# =============================================================================
# THỐNG KÊ
# =============================================================================

class ThongKeKeKhaiLDResponse(BaseModel):
    """
    Thống kê kê khai công việc Lãnh đạo theo tháng.
    
    v2.7.0 UPDATE: Thêm fields tạm tính (tam_tinh_*) để hỗ trợ 2-tab UI
    """
    
    thang: int
    nam: int
    
    # Tổng số công việc
    tong_cong_viec: int = 0
    
    # Theo trạng thái phê duyệt
    tong_da_duyet: int = 0
    tong_cho_duyet: int = 0
    tong_tu_choi: int = 0
    tong_nhap: int = 0
    
    # =========================================================================
    # CHÍNH THỨC (chỉ DA_PHE_DUYET)
    # =========================================================================
    tong_hoan_thanh: int = 0
    tong_chua_hoan_thanh: int = 0
    tong_dat_chat_luong: int = 0
    tong_dung_tien_do: int = 0
    
    # v2.6.4: Tổng số lỗi (để hiển thị)
    tong_loi_chat_luong: int = 0
    tong_loi_tien_do: int = 0
    
    # v2.6.5: Tổng điểm (để tính b, c chính xác)
    tong_diem_chat_luong: float = 0.0
    tong_diem_tien_do: float = 0.0
    
    # =========================================================================
    # TẠM TÍNH (NHAP + CHO_PHE_DUYET + DA_PHE_DUYET) - v2.7.0 NEW
    # =========================================================================
    tam_tinh_tong_cong_viec: int = Field(
        default=0,
        description="Tổng CV tạm tính (bao gồm cả chưa duyệt)"
    )
    tam_tinh_hoan_thanh: int = Field(
        default=0,
        description="CV hoàn thành tạm tính"
    )
    tam_tinh_chua_hoan_thanh: int = Field(
        default=0,
        description="CV chưa hoàn thành tạm tính"
    )
    tam_tinh_dat_chat_luong: int = Field(
        default=0,
        description="CV đạt CL tạm tính (chưa duyệt coi như đạt)"
    )
    tam_tinh_dung_tien_do: int = Field(
        default=0,
        description="CV đúng TĐ tạm tính (chưa duyệt coi như đạt)"
    )
    
    # v2.6.4: Tổng số lỗi tạm tính
    tam_tinh_loi_chat_luong: int = 0
    tam_tinh_loi_tien_do: int = 0
    
    # v2.6.5: Tổng điểm tạm tính
    tam_tinh_diem_chat_luong: float = 0.0
    tam_tinh_diem_tien_do: float = 0.0


class NguoiPheDuyetLDResponse(BaseModel):
    """Response danh sách người phê duyệt cho Lãnh đạo."""
    
    danh_sach: List[CongChucDetailResponse]
    ghi_chu: Optional[str] = None


# =============================================================================
# TÍNH ĐIỂM KPI LÃNH ĐẠO
# =============================================================================

class DiemKPILanhDaoResponse(BaseModel):
    """Response điểm KPI của Lãnh đạo."""
    
    thang: int
    nam: int
    cong_chuc_id: UUID
    
    # Target
    target: int = Field(..., description="Tổng số công việc đã duyệt")
    
    # Các chỉ số a, b, c (từ kê khai công việc)
    a_hoan_thanh: int = 0
    a_percent: float = 0.0
    
    b_dat_chat_luong: int = 0
    b_percent: float = 0.0
    
    c_dung_tien_do: int = 0
    c_percent: float = 0.0
    
    # Các chỉ số d, đ, e (từ đánh giá DDE)
    d_percent: float = 1.0  # Mặc định 100%
    dd_percent: float = 1.0
    e_percent: float = 1.0
    
    # Điểm KPI (70 điểm)
    diem_kpi: float = Field(
        ...,
        description="Điểm KPI = (a+b+c+d+đ+e)/6 × 70"
    )
    
    # Điểm tiêu chí chung (30 điểm) - nếu có
    diem_tieu_chi_chung: Optional[float] = None
    
    # Tổng điểm
    diem_tong: Optional[float] = None