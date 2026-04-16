"""
app/schemas/leave.py
====================
Pydantic schemas cho Quản lý Nghỉ phép (Leave Management).

Module này hỗ trợ đặc thù nghiệp vụ Hải quan:
- Công chức làm việc theo CA/KÍP, không nghỉ cố định T7/CN
- CC phải đăng ký NGHI_TUAN trên hệ thống cho ngày nghỉ tuần
- Công thức KPI: SP_được_giao = (Ngày_dương_lịch - Ngày_nghỉ_đã_duyệt) × 96

Bao gồm schemas cho:
- NghiPhepCreate: Tạo đơn nghỉ đơn lẻ
- NghiPhepBulkCreate: Đăng ký nghỉ nhiều ngày (đặc biệt cho NGHI_TUAN)
- NghiPhepResponse: Response chi tiết
- ThongKeNghiPhep: Thống kê nghỉ phép

Phiên bản: 1.1 (27/01/2026)
Fix: Sửa min_length=10 → min_length=1 trong TuChoiNghiPhepRequest
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator


# =============================================================================
# ENUMS (Mirror từ models để dùng trong schema validation)
# =============================================================================

class LoaiNghiEnum(str, Enum):
    """Loại nghỉ phép - 9 loại."""
    NGHI_TUAN = "NGHI_TUAN"         # ⭐ Nghỉ tuần (thay thế T7/CN - HQ làm ca/kíp)
    NGHI_TET = "NGHI_TET"
    PHEP_NAM = "PHEP_NAM"           # Phép năm (12-14 ngày/năm)
    NGHI_LE = "NGHI_LE"             # Nghỉ các ngày lễ
    NGHI_OM = "NGHI_OM"             # Ốm đau
    THAI_SAN = "THAI_SAN"           # Thai sản
    VIEC_RIENG = "VIEC_RIENG"       # Việc riêng có lương
    KHONG_LUONG = "KHONG_LUONG"     # Nghỉ không lương
    NGHI_BU = "NGHI_BU"             # Nghỉ bù
    KHAC = "KHAC"                   # Khác


class TrangThaiNghiEnum(str, Enum):
    """Trạng thái đơn nghỉ."""
    CHO_PHE_DUYET = "CHO_PHE_DUYET"
    DA_PHE_DUYET = "DA_PHE_DUYET"
    TU_CHOI = "TU_CHOI"
    HUY = "HUY"


# =============================================================================
# NESTED SCHEMAS (để response)
# =============================================================================

class CongChucNghiPhepBrief(BaseModel):
    """Thông tin tóm tắt CC trong nghỉ phép."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    ma_cc: str
    ho_ten: str
    chuc_vu: Optional[str] = None
    don_vi_ten: Optional[str] = None
    
    @classmethod
    def from_cong_chuc(cls, cc) -> "CongChucNghiPhepBrief":
        """Tạo brief từ CongChuc object."""
        return cls(
            id=cc.id,
            ma_cc=cc.ma_cc,
            ho_ten=cc.ho_ten,
            chuc_vu=cc.chuc_vu,
            don_vi_ten=cc.don_vi.ten_don_vi if cc.don_vi else None
        )


# =============================================================================
# CREATE / UPDATE SCHEMAS
# =============================================================================

class NghiPhepBase(BaseModel):
    """Base schema cho đăng ký nghỉ phép."""
    
    loai_nghi: LoaiNghiEnum = Field(
        ...,
        description="Loại nghỉ: NGHI_TUAN, PHEP_NAM, NGHI_LE, NGHI_OM, THAI_SAN, VIEC_RIENG, KHONG_LUONG, NGHI_BU, KHAC"
    )
    
    tu_ngay: date = Field(
        ...,
        description="Ngày bắt đầu nghỉ"
    )
    
    den_ngay: date = Field(
        ...,
        description="Ngày kết thúc nghỉ"
    )
    
    so_ngay: Decimal = Field(
        ...,
        gt=0,
        le=365,
        description="Số ngày nghỉ thực tế (cho phép 0.5 để nghỉ buổi)"
    )
    
    ly_do: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="Lý do xin nghỉ"
    )
    
    tai_lieu_dinh_kem: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Đường dẫn file đính kèm"
    )
    
    nguoi_phe_duyet_id: Optional[UUID] = Field(
        default=None,
        description="ID người phê duyệt (CC chọn Phó ĐV, Phó ĐV chọn Trưởng ĐV...)"
    )


class NghiPhepCreate(NghiPhepBase):
    """Schema để tạo mới đơn nghỉ đơn lẻ."""
    
    @field_validator("den_ngay")
    @classmethod
    def validate_den_ngay(cls, v: date, info) -> date:
        """Đảm bảo den_ngay >= tu_ngay."""
        tu_ngay = info.data.get("tu_ngay")
        if tu_ngay and v < tu_ngay:
            raise ValueError("Ngày kết thúc phải >= ngày bắt đầu (LEAVE_001)")
        return v
    
    @field_validator("so_ngay")
    @classmethod
    def validate_so_ngay(cls, v: Decimal) -> Decimal:
        """Kiểm tra số ngày hợp lệ."""
        if v <= 0:
            raise ValueError("Số ngày nghỉ phải > 0 (LEAVE_002)")
        # Cho phép nghỉ nửa ngày (0.5)
        if v % Decimal("0.5") != 0:
            raise ValueError("Số ngày nghỉ phải là bội số của 0.5")
        return v


class NghiPhepBulkCreate(BaseModel):
    """
    Schema để đăng ký nghỉ nhiều ngày cùng lúc.
    
    Đặc biệt hữu ích cho NGHI_TUAN - đăng ký nghỉ tuần hàng loạt.
    
    Ví dụ request:
    {
        "loai_nghi": "NGHI_TUAN",
        "danh_sach_ngay": ["2026-01-04", "2026-01-05", "2026-01-11", "2026-01-12"],
        "nguoi_phe_duyet_id": "uuid",
        "ly_do": "Đăng ký nghỉ tuần tháng 1/2026"
    }
    """
    
    loai_nghi: LoaiNghiEnum = Field(
        ...,
        description="Loại nghỉ (NGHI_TUAN, PHEP_NAM, NGHI_LE, ...)"
    )
    
    danh_sach_ngay: List[date] = Field(
        ...,
        min_length=1,
        max_length=31,
        description="Danh sách các ngày nghỉ (tối đa 31 ngày)"
    )
    
    nguoi_phe_duyet_id: Optional[UUID] = Field(
        default=None,
        description="ID người phê duyệt"
    )
    
    ly_do: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="Lý do chung cho tất cả ngày nghỉ"
    )
    
    @field_validator("danh_sach_ngay")
    @classmethod
    def validate_danh_sach_ngay(cls, v: List[date]) -> List[date]:
        """Kiểm tra danh sách ngày không trùng và sắp xếp."""
        if len(v) != len(set(v)):
            raise ValueError("Danh sách ngày không được trùng lặp")
        return sorted(v)  # Sắp xếp tăng dần


class NghiPhepUpdate(BaseModel):
    """Schema để cập nhật đơn nghỉ (partial update)."""
    
    loai_nghi: Optional[LoaiNghiEnum] = None
    tu_ngay: Optional[date] = None
    den_ngay: Optional[date] = None
    so_ngay: Optional[Decimal] = Field(default=None, gt=0, le=365)
    ly_do: Optional[str] = Field(default=None, max_length=2000)
    tai_lieu_dinh_kem: Optional[str] = Field(default=None, max_length=500)
    nguoi_phe_duyet_id: Optional[UUID] = None
    
    @model_validator(mode="after")
    def validate_dates(self) -> "NghiPhepUpdate":
        """Validate ngày nếu cả 2 đều được cung cấp."""
        if self.tu_ngay and self.den_ngay:
            if self.den_ngay < self.tu_ngay:
                raise ValueError("Ngày kết thúc phải >= ngày bắt đầu (LEAVE_001)")
        return self


class PheDuyetNghiPhepRequest(BaseModel):
    """Schema request phê duyệt đơn nghỉ."""
    ghi_chu: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Ghi chú của người phê duyệt"
    )


class TuChoiNghiPhepRequest(BaseModel):
    """Schema request từ chối đơn nghỉ."""
    ly_do_tu_choi: str = Field(
        ...,
        min_length=1,  # ✅ FIX: Đổi từ 10 → 1 (cho phép lý do ngắn như "Trùng lịch")
        max_length=1000,
        description="Lý do từ chối (bắt buộc)"
    )


# =============================================================================
# RESPONSE SCHEMAS
# =============================================================================

class NghiPhepResponse(BaseModel):
    """Schema response chi tiết cho đơn nghỉ."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    
    # Thông tin người đăng ký
    cong_chuc_id: UUID
    cong_chuc: Optional[CongChucNghiPhepBrief] = None
    
    # Thông tin nghỉ
    loai_nghi: LoaiNghiEnum
    loai_nghi_ten: str = Field(description="Tên tiếng Việt của loại nghỉ")
    tu_ngay: date
    den_ngay: date
    so_ngay: Decimal
    ly_do: Optional[str] = None
    tai_lieu_dinh_kem: Optional[str] = None
    
    # Thông tin phê duyệt
    nguoi_phe_duyet_id: Optional[UUID] = None
    nguoi_phe_duyet: Optional[CongChucNghiPhepBrief] = None
    trang_thai: TrangThaiNghiEnum
    trang_thai_ten: str = Field(description="Tên tiếng Việt của trạng thái")
    ly_do_tu_choi: Optional[str] = None
    ngay_phe_duyet: Optional[datetime] = None
    ghi_chu_phe_duyet: Optional[str] = None
    
    # Liên kết KPI
    thang_ap_dung: Optional[int] = None
    nam_ap_dung: Optional[int] = None
    da_tinh_kpi: bool = False
    
    # Timestamps
    created_at: datetime
    updated_at: Optional[datetime] = None


class NghiPhepListResponse(BaseModel):
    """Schema response danh sách đơn nghỉ (phân trang)."""
    items: List[NghiPhepResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class NghiPhepBulkResponse(BaseModel):
    """
    Schema response sau khi đăng ký bulk.
    
    ⚠️ QUAN TRỌNG: Frontend phụ thuộc vào cấu trúc này!
    Không thay đổi tên các field.
    
    Response example:
    {
        "success": true,
        "tong_don_tao": 4,
        "danh_sach_id": ["uuid1", "uuid2", "uuid3", "uuid4"],
        "ngay_da_ton_tai": ["2026-01-18"],
        "nguoi_phe_duyet_id": "uuid-approver",
        "message": "Đã tạo 4 đơn nghỉ phép"
    }
    """
    success: bool = Field(
        default=True,
        description="Trạng thái tạo đơn"
    )
    tong_don_tao: int = Field(
        ...,
        description="Số đơn đã tạo thành công"
    )
    danh_sach_id: List[UUID] = Field(
        default_factory=list,
        description="Danh sách ID các đơn đã tạo"
    )
    ngay_da_ton_tai: List[date] = Field(
        default_factory=list,
        description="Danh sách các ngày đã có đơn trước đó (bị skip)"
    )
    nguoi_phe_duyet_id: Optional[UUID] = Field(
        default=None,
        description="ID người phê duyệt đã được gán"
    )
    message: str = Field(
        ...,
        description="Thông báo kết quả"
    )


# =============================================================================
# THỐNG KÊ SCHEMAS
# =============================================================================

class ThongKeNghiPhepLoai(BaseModel):
    """Thống kê nghỉ phép theo loại."""
    nghi_tuan: Decimal = Field(default=Decimal("0"), description="Số ngày nghỉ tuần")
    phep_nam: Decimal = Field(default=Decimal("0"), description="Số ngày phép năm đã nghỉ")
    phep_nam_con_lai: Optional[Decimal] = Field(default=None, description="Số ngày phép năm còn lại")
    nghi_le: Decimal = Field(default=Decimal("0"), description="Số ngày nghỉ lễ")
    nghi_om: Decimal = Field(default=Decimal("0"), description="Số ngày nghỉ ốm")
    thai_san: Decimal = Field(default=Decimal("0"), description="Số ngày thai sản")
    viec_rieng: Decimal = Field(default=Decimal("0"), description="Số ngày việc riêng")
    khong_luong: Decimal = Field(default=Decimal("0"), description="Số ngày không lương")
    nghi_bu: Decimal = Field(default=Decimal("0"), description="Số ngày nghỉ bù")
    khac: Decimal = Field(default=Decimal("0"), description="Số ngày khác")


class ThongKeNghiPhepThang(BaseModel):
    """Thống kê nghỉ phép theo tháng."""
    thang: int
    nam: int
    nghi_tuan: Decimal = Field(default=Decimal("0"))
    nghi_khac: Decimal = Field(default=Decimal("0"))
    tong: Decimal = Field(default=Decimal("0"))


class ThongKeNghiPhepCaNhan(BaseModel):
    """Thống kê nghỉ phép cá nhân."""
    cong_chuc_id: UUID
    nam: int
    tong_ngay_nghi: Decimal
    chi_tiet: ThongKeNghiPhepLoai
    theo_thang: List[ThongKeNghiPhepThang]


class ThongKeNghiPhepCC(BaseModel):
    """Thống kê nghỉ phép của 1 CC trong đơn vị."""
    cong_chuc_id: UUID
    ho_ten: str
    nghi_tuan: Decimal = Field(default=Decimal("0"))
    nghi_khac: Decimal = Field(default=Decimal("0"))
    tong_ngay_nghi: Decimal = Field(default=Decimal("0"))
    con_phep_nam: Optional[Decimal] = None


class ThongKeNghiPhepTongHop(BaseModel):
    """Thống kê tổng hợp đơn nghỉ."""
    tong_don: int
    da_phe_duyet: int
    cho_phe_duyet: int
    tu_choi: int
    tong_ngay_nghi: Decimal


class ThongKeNghiPhepDonVi(BaseModel):
    """Thống kê nghỉ phép theo đơn vị."""
    don_vi_id: UUID
    don_vi_ten: str
    thang: int
    nam: int
    tong_hop: ThongKeNghiPhepTongHop
    theo_loai: ThongKeNghiPhepLoai
    danh_sach_cc: List[ThongKeNghiPhepCC]


# =============================================================================
# HELPER SCHEMAS cho tính KPI
# =============================================================================

class TongNgayNghiThangResponse(BaseModel):
    """
    Response tổng ngày nghỉ của 1 CC trong 1 tháng.
    Dùng để tính KPI: SP_được_giao = (Ngày_dương_lịch - Tổng_nghỉ) × 96
    """
    cong_chuc_id: UUID
    thang: int
    nam: int
    tong_ngay_nghi: Decimal = Field(
        default=Decimal("0"),
        description="Tổng ngày nghỉ đã duyệt (bao gồm NGHI_TUAN + PHEP_NAM + ...)"
    )
    chi_tiet: ThongKeNghiPhepLoai
    
    # Computed
    so_ngay_trong_thang: int = Field(description="Số ngày dương lịch trong tháng")
    so_ngay_lam_viec: Decimal = Field(description="Số ngày làm việc thực tế = Số ngày trong tháng - Tổng nghỉ")
    sp_duoc_giao: Decimal = Field(description="SP được giao = Số ngày làm việc × 96")