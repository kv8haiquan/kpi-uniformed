"""
app/schemas/assessment.py
=========================
Pydantic schemas cho Module Đánh giá Tiêu chí chung (v3.5.0).

THAY ĐỔI CHÍNH v3.5.0 (02/02/2026):
1. Thêm CHO_CAP2, TU_CHOI vào TrangThaiTieuChiEnum
2. Thêm TuChoiTieuChiRequest schema cho endpoint từ chối
3. DanhSachChoPheDuyetItem thêm: diem_tc_cap1/2, ly_do_tu_choi_tc, cap_phe_duyet_hien_tai

THAY ĐỔI CHÍNH v2.7.0 (31/01/2026):
1. FIX BUG: Thêm fields cho 2 cấp phê duyệt vào DanhSachChoPheDuyetItem
   - nguoi_phe_duyet_tc_cap1_id, ngay_phe_duyet_tc_cap1
   - nguoi_phe_duyet_tc_cap2_id, ngay_phe_duyet_tc_cap2
   - trang_thai_tieu_chi
2. Frontend cần các fields này để hiển thị đúng trạng thái cấp 1/2

THAY ĐỔI CHÍNH (v2.5.0 - 26/01/2026):
1. AUDIT TRAIL: Request Input đổi từ `is_achieved` → `is_achieved_cc`, `ghi_chu` → `ghi_chu_cc`
2. VIRTUAL RECORD: Thêm `is_new_record` và `CHUA_DANH_GIA` cho trường hợp chưa có dữ liệu
3. FINAL RESULT: Response trả về thêm `is_achieved` = kết quả cuối cùng để tính điểm
4. TRACKING: Thêm `danh_gia_thang_id` vào TieuChiItemResponse

LOGIC CHẤM ĐIỂM NHỊ PHÂN (Binary Scoring):
- Frontend GỬI: is_achieved_cc (True/False) - đây là bản tích của CC
- Backend TỰ ĐỘNG TÍNH: điểm = diem_toi_da if is_achieved else 0
- Điểm KPI dùng is_achieved (= is_achieved_ld nếu đã duyệt, else is_achieved_cc)

ĐIỂM TỐI ĐA THEO NHÓM:
- Nhóm 1 (1.1, 1.2): 5.0 điểm/tiêu chí
- Nhóm 2 (2.1-2.4): 2.5 điểm/tiêu chí  
- Nhóm 3 (3.1-3.4): 2.5 điểm/tiêu chí

LUỒNG PHÊ DUYỆT 2 CẤP:
1. CC tick/bỏ tick → is_achieved_cc → Gửi phê duyệt (chọn Phó ĐT)
2. Phó ĐT (cấp 1) xem → Có thể điều chỉnh → Duyệt cấp 1
3. ĐT (cấp 2) xem → Có thể điều chỉnh → Duyệt cấp 2 → HOÀN TẤT
4. Điểm KPI dùng is_achieved_ld (final) để tính

Phiên bản: 2.7.0 (31/01/2026)
"""

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Optional, List, Any
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator, computed_field


# =============================================================================
# ENUMS
# =============================================================================

class TrangThaiTieuChiEnum(str, Enum):
    """Trạng thái chấm tiêu chí chung."""
    CHUA_DANH_GIA = "CHUA_DANH_GIA"  # Mới - Virtual Record
    NHAP = "NHAP"
    CHO_PHE_DUYET = "CHO_PHE_DUYET"
    CHO_CAP2 = "CHO_CAP2"            # ⭐ v3.5: Chờ ĐT duyệt cấp 2
    DA_PHE_DUYET = "DA_PHE_DUYET"
    TU_CHOI = "TU_CHOI"              # ⭐ v3.5: Bị từ chối


class TrangThaiDanhGiaThangEnum(str, Enum):
    """Trạng thái tổng hợp đánh giá tháng."""
    CHUA_DANH_GIA = "CHUA_DANH_GIA"  # Virtual Record - chưa có bản ghi trong DB
    DANG_DANH_GIA = "DANG_DANH_GIA"
    CHO_TONG_HOP = "CHO_TONG_HOP"
    DA_TONG_HOP = "DA_TONG_HOP"
    CHO_PHE_DUYET = "CHO_PHE_DUYET"
    HOAN_THANH = "HOAN_THANH"


class MucXepLoaiEnum(str, Enum):
    """Mức xếp loại."""
    A = "A"
    B = "B"
    C = "C"
    D = "D"


# =============================================================================
# TIÊU CHÍ CHUNG - REQUEST SCHEMAS
# =============================================================================

class TieuChiItemInput(BaseModel):
    """
    Input cho MỘT tiêu chí khi CC tự đánh giá.
    
    ⚠️ QUAN TRỌNG (v2.5.0):
    - Field đổi từ `is_achieved` → `is_achieved_cc` để khẳng định đây là bản tích của CC
    - Field đổi từ `ghi_chu` → `ghi_chu_cc`
    - Backend tự động tính điểm theo công thức nhị phân
    """
    ma_tieu_chi: str = Field(
        ...,
        description="Mã tiêu chí: 1.1, 1.2, 2.1, 2.2, ..., 3.4"
    )
    is_achieved_cc: bool = Field(
        ...,
        description="Bản tích của CC: True = Đạt, False = Không đạt"
    )
    ghi_chu_cc: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Ghi chú của CC khi tự đánh giá (nếu có)"
    )


class TuDanhGiaTieuChiRequest(BaseModel):
    """
    Schema request để CC TỰ ĐÁNH GIÁ tiêu chí chung.
    
    Endpoint: POST /danh-gia/tu-danh-gia
    
    Request body example (v2.5.0):
    {
        "thang": 1,
        "nam": 2026,
        "tieu_chi": [
            {"ma_tieu_chi": "1.1", "is_achieved_cc": true},
            {"ma_tieu_chi": "1.2", "is_achieved_cc": true},
            {"ma_tieu_chi": "2.1", "is_achieved_cc": true},
            {"ma_tieu_chi": "2.2", "is_achieved_cc": true},
            {"ma_tieu_chi": "2.3", "is_achieved_cc": true},
            {"ma_tieu_chi": "2.4", "is_achieved_cc": true},
            {"ma_tieu_chi": "3.1", "is_achieved_cc": false},
            {"ma_tieu_chi": "3.2", "is_achieved_cc": true, "ghi_chu_cc": "Có sáng kiến XYZ"},
            {"ma_tieu_chi": "3.3", "is_achieved_cc": false},
            {"ma_tieu_chi": "3.4", "is_achieved_cc": false}
        ],
        "gui_phe_duyet": true,
        "nguoi_phe_duyet_id": "uuid"
    }
    """
    thang: int = Field(
        ...,
        ge=1,
        le=12,
        description="Tháng đánh giá (1-12)"
    )
    nam: int = Field(
        ...,
        ge=2025,
        description="Năm đánh giá (>= 2025)"
    )
    tieu_chi: List[TieuChiItemInput] = Field(
        ...,
        min_length=1,
        max_length=10,
        description="Danh sách 10 tiêu chí chính (1.1, 1.2, 2.1-2.4, 3.1-3.4)"
    )
    gui_phe_duyet: bool = Field(
        default=False,
        description="True = Gửi phê duyệt ngay, False = Lưu nháp"
    )
    nguoi_phe_duyet_id: Optional[UUID] = Field(
        default=None,
        description="ID người phê duyệt (bắt buộc nếu gui_phe_duyet=True)"
    )
    
    @field_validator("tieu_chi")
    @classmethod
    def validate_tieu_chi_unique(cls, v):
        """Đảm bảo không có tiêu chí trùng mã."""
        ma_list = [tc.ma_tieu_chi for tc in v]
        if len(ma_list) != len(set(ma_list)):
            raise ValueError("Có tiêu chí bị trùng mã")
        return v
    
    @model_validator(mode="after")
    def validate_nguoi_phe_duyet(self) -> "TuDanhGiaTieuChiRequest":
        """Nếu gửi phê duyệt, phải chọn người duyệt."""
        if self.gui_phe_duyet and not self.nguoi_phe_duyet_id:
            raise ValueError("Phải chọn người phê duyệt khi gửi")
        return self


class DieuChinhTieuChiItem(BaseModel):
    """
    Input cho MỘT tiêu chí khi LĐ điều chỉnh.
    
    LĐ có thể thay đổi is_achieved khác với CC.
    """
    ma_tieu_chi: str = Field(
        ...,
        description="Mã tiêu chí cần điều chỉnh"
    )
    is_achieved_ld: bool = Field(
        ...,
        description="Giá trị LĐ điều chỉnh"
    )
    ly_do_dieu_chinh: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Lý do điều chỉnh (bắt buộc nếu khác CC)"
    )


class PheDuyetTieuChiRequest(BaseModel):
    """
    Schema request để LĐ PHÊ DUYỆT tiêu chí chung.
    
    Endpoint: POST /danh-gia/{danh_gia_thang_id}/phe-duyet-tieu-chi
    
    Có 2 trường hợp:
    1. Đồng ý 100%: dieu_chinh = [] hoặc không có
    2. Có điều chỉnh: dieu_chinh = [...] với các tiêu chí cần sửa
    
    Request body example (có điều chỉnh):
    {
        "ghi_chu": "Đã điều chỉnh tiêu chí 3.2",
        "dieu_chinh": [
            {
                "ma_tieu_chi": "3.2",
                "is_achieved_ld": false,
                "ly_do_dieu_chinh": "Chưa có minh chứng cụ thể"
            }
        ]
    }
    """
    ghi_chu: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Ghi chú của LĐ khi phê duyệt"
    )
    dieu_chinh: Optional[List[DieuChinhTieuChiItem]] = Field(
        default=None,
        description="Danh sách các tiêu chí LĐ điều chỉnh (nếu có)"
    )
    
    @field_validator("dieu_chinh")
    @classmethod
    def validate_dieu_chinh_unique(cls, v):
        """Đảm bảo không có tiêu chí trùng trong điều chỉnh."""
        if v:
            ma_list = [tc.ma_tieu_chi for tc in v]
            if len(ma_list) != len(set(ma_list)):
                raise ValueError("Có tiêu chí bị trùng trong danh sách điều chỉnh")
        return v


class PheDuyetTieuChiBulkRequest(BaseModel):
    """
    Schema request phê duyệt hàng loạt (không điều chỉnh).
    
    Endpoint: POST /danh-gia/phe-duyet-tieu-chi-bulk
    
    ⚠️ Chỉ dùng khi LĐ đồng ý 100% với bản tự đánh giá của CC.
    """
    danh_gia_thang_ids: List[UUID] = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Danh sách ID đánh giá tháng cần phê duyệt"
    )
    ghi_chu: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Ghi chú chung cho tất cả"
    )


class TuChoiTieuChiRequest(BaseModel):
    """
    ⭐ v3.5.0: Request từ chối tiêu chí chung.
    
    Endpoint: POST /danh-gia/{danh_gia_thang_id}/tu-choi-tieu-chi
    
    Phó ĐT/ĐT từ chối → reset tất cả tiêu chí về NHAP → CC tự chấm lại.
    
    Request body example:
    {
        "ly_do_tu_choi": "Tiêu chí 2.3 chưa có minh chứng, cần bổ sung"
    }
    """
    ly_do_tu_choi: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Lý do từ chối (BẮT BUỘC)"
    )


# =============================================================================
# TIÊU CHÍ CHUNG - RESPONSE SCHEMAS
# =============================================================================

class TieuChiItemResponse(BaseModel):
    """
    Response cho một tiêu chí chung.
    
    THAY ĐỔI v2.5.0:
    - Thêm `danh_gia_thang_id` để Frontend định danh
    - Thêm `is_achieved` = kết quả cuối cùng dùng để tính điểm
    - Thêm `diem` = điểm cuối cùng (dựa trên is_achieved)
    """
    model_config = ConfigDict(from_attributes=True)
    
    id: Optional[UUID] = Field(default=None, description="ID của bản ghi đánh giá tiêu chí")
    danh_gia_thang_id: Optional[UUID] = Field(
        default=None,
        description="ID đánh giá tháng (để Frontend định danh)"
    )
    tieu_chi_id: Optional[UUID] = Field(default=None, description="ID tiêu chí master data")
    ma_tieu_chi: str
    ten_tieu_chi: str
    nhom_tieu_chi: int = Field(..., ge=1, le=3)
    diem_toi_da: float
    gia_tri_mac_dinh: bool = Field(
        default=True,
        description="Giá trị mặc định: True cho Nhóm 1&2, False cho Nhóm 3"
    )
    
    # =========================================================================
    # AUDIT TRAIL - 3 trường is_achieved
    # =========================================================================
    is_achieved_cc: bool = Field(
        ...,
        description="BẢN TÍCH CC: Công chức tự đánh giá"
    )
    is_achieved_ld: Optional[bool] = Field(
        default=None,
        description="BẢN TÍCH LĐ: Lãnh đạo điều chỉnh (NULL = chưa duyệt)"
    )
    is_achieved: bool = Field(
        ...,
        description="KẾT QUẢ CUỐI CÙNG: = is_achieved_ld nếu đã duyệt, else is_achieved_cc"
    )
    
    # =========================================================================
    # ĐIỂM TỰ ĐỘNG TÍNH
    # =========================================================================
    diem_tu_cham: float = Field(
        ...,
        description="Điểm CC = diem_toi_da if is_achieved_cc else 0"
    )
    diem_phe_duyet: Optional[float] = Field(
        default=None,
        description="Điểm LĐ = diem_toi_da if is_achieved_ld else 0"
    )
    diem: float = Field(
        ...,
        description="ĐIỂM CUỐI CÙNG: = diem_phe_duyet nếu đã duyệt, else diem_tu_cham"
    )
    
    # Trạng thái
    trang_thai: TrangThaiTieuChiEnum
    
    # Ghi chú
    ghi_chu_cc: Optional[str] = None
    ghi_chu_ld: Optional[str] = None
    ly_do_dieu_chinh: Optional[str] = None
    
    # Metadata
    ngay_gui: Optional[datetime] = None
    ngay_phe_duyet: Optional[datetime] = None
    
    @computed_field
    @property
    def has_difference(self) -> bool:
        """LĐ có điều chỉnh khác CC không."""
        if self.is_achieved_ld is None:
            return False
        return self.is_achieved_cc != self.is_achieved_ld


class TieuChiChungTongHop(BaseModel):
    """Tổng hợp điểm tiêu chí chung theo nhóm."""
    nhom_1_diem: float = Field(default=0, description="Điểm nhóm 1 (max 10)")
    nhom_2_diem: float = Field(default=0, description="Điểm nhóm 2 (max 10)")
    nhom_3_diem: float = Field(default=0, description="Điểm nhóm 3 (max 10)")
    tong_diem: float = Field(default=0, description="Tổng điểm (max 30)")
    
    # Chi tiết (optional)
    nhom_1_chi_tiet: Optional[List[TieuChiItemResponse]] = None
    nhom_2_chi_tiet: Optional[List[TieuChiItemResponse]] = None
    nhom_3_chi_tiet: Optional[List[TieuChiItemResponse]] = None


class TuDanhGiaResponse(BaseModel):
    """
    Response sau khi CC tự đánh giá tiêu chí chung.
    
    THAY ĐỔI v2.5.0:
    - Thêm `is_new_record`: True nếu tạo mới, False nếu cập nhật
    """
    model_config = ConfigDict(from_attributes=True)
    
    success: bool = True
    message: str
    
    danh_gia_thang_id: UUID
    cong_chuc_id: UUID
    thang: int
    nam: int
    
    # Flag Virtual Record
    is_new_record: bool = Field(
        default=False,
        description="True = Tạo mới bản ghi, False = Cập nhật bản ghi có sẵn"
    )
    
    trang_thai: TrangThaiTieuChiEnum
    
    # Tổng hợp điểm
    tong_hop: TieuChiChungTongHop
    
    # Chi tiết từng tiêu chí
    tieu_chi: List[TieuChiItemResponse]
    
    # Thời gian
    ngay_gui: Optional[datetime] = None
    nguoi_phe_duyet_id: Optional[UUID] = None


class DanhGiaThangTieuChiResponse(BaseModel):
    """
    Response cho GET /danh-gia/tieu-chi/thang/{t}/nam/{n}.
    
    HỖ TRỢ VIRTUAL RECORD:
    - Nếu chưa có bản ghi trong DB → Trả về `is_new_record=True`, `trang_thai=CHUA_DANH_GIA`
    - Nếu đã có bản ghi → Trả về dữ liệu thực với `is_new_record=False`
    
    Điều này giúp Frontend không bị lỗi 404 và có thể render form với giá trị mặc định.
    """
    model_config = ConfigDict(from_attributes=True)
    
    # Core info
    danh_gia_thang_id: Optional[UUID] = Field(
        default=None,
        description="ID đánh giá tháng (NULL nếu is_new_record=True)"
    )
    cong_chuc_id: UUID
    thang: int
    nam: int
    
    # =========================================================================
    # VIRTUAL RECORD FLAG
    # =========================================================================
    is_new_record: bool = Field(
        default=False,
        description="True = Chưa có bản ghi trong DB (Virtual Record)"
    )
    
    # =========================================================================
    # TARGET KPI (Tính từ nghỉ phép)
    # =========================================================================
    so_ngay_trong_thang: int = Field(
        ...,
        description="Tổng số ngày trong tháng (28-31)"
    )
    so_ngay_nghi_phep: int = Field(
        default=0,
        description="Số ngày nghỉ phép đã được duyệt"
    )
    so_ngay_lam_viec: int = Field(
        ...,
        description="Số ngày làm việc = so_ngay_trong_thang - so_ngay_nghi_phep"
    )
    target_kpi: float = Field(
        ...,
        description="Target KPI = so_ngay_lam_viec × 96 (8h × 12 SP/h)"
    )
    
    # =========================================================================
    # TRẠNG THÁI
    # =========================================================================
    trang_thai: TrangThaiTieuChiEnum = Field(
        default=TrangThaiTieuChiEnum.CHUA_DANH_GIA,
        description="CHUA_DANH_GIA nếu is_new_record=True"
    )
    trang_thai_danh_gia_thang: TrangThaiDanhGiaThangEnum = Field(
        default=TrangThaiDanhGiaThangEnum.CHUA_DANH_GIA,
        description="Trạng thái tổng hợp của đánh giá tháng"
    )
    
    # =========================================================================
    # TỔNG HỢP ĐIỂM
    # =========================================================================
    tong_hop: TieuChiChungTongHop
    
    # =========================================================================
    # CHI TIẾT TỪNG TIÊU CHÍ
    # =========================================================================
    tieu_chi: List[TieuChiItemResponse] = Field(
        ...,
        description="10 tiêu chí với giá trị mặc định hoặc giá trị đã lưu"
    )
    
    # =========================================================================
    # METADATA PHÊ DUYỆT
    # =========================================================================
    nguoi_phe_duyet_id: Optional[UUID] = None
    nguoi_phe_duyet_ten: Optional[str] = None
    ngay_gui: Optional[datetime] = None
    ngay_phe_duyet: Optional[datetime] = None


class DanhSachChoPheDuyetItem(BaseModel):
    """
    Một item trong danh sách chờ phê duyệt.
    
    v2.7.0 FIX: Thêm các fields cho 2 cấp phê duyệt để Frontend hiển thị đúng.
    """
    model_config = ConfigDict(from_attributes=True)
    
    danh_gia_thang_id: UUID
    
    # Thông tin CC
    cong_chuc_id: UUID
    ma_cc: str
    ho_ten: str
    don_vi_ten: Optional[str] = None
    
    thang: int
    nam: int
    
    # Điểm tự chấm
    diem_tu_cham: float = Field(..., description="Tổng điểm CC tự chấm (0-30)")
    
    # Trạng thái & thời gian
    trang_thai: TrangThaiTieuChiEnum
    ngay_gui: datetime
    
    # =========================================================================
    # v2.7.0 FIX: THÊM FIELDS CHO 2 CẤP PHÊ DUYỆT
    # =========================================================================
    # Cấp 1 - Phó Đội trưởng
    nguoi_phe_duyet_tc_cap1_id: Optional[UUID] = Field(
        default=None,
        description="ID người phê duyệt cấp 1 (Phó ĐT)"
    )
    ngay_phe_duyet_tc_cap1: Optional[datetime] = Field(
        default=None,
        description="Ngày phê duyệt cấp 1"
    )
    
    # Cấp 2 - Đội trưởng  
    nguoi_phe_duyet_tc_cap2_id: Optional[UUID] = Field(
        default=None,
        description="ID người phê duyệt cấp 2 (ĐT)"
    )
    ngay_phe_duyet_tc_cap2: Optional[datetime] = Field(
        default=None,
        description="Ngày phê duyệt cấp 2"
    )
    
    # Trạng thái tiêu chí (để FE xác định đã hoàn tất chưa)
    trang_thai_tieu_chi: Optional[str] = Field(
        default=None,
        description="Trạng thái tiêu chí từ DanhGiaThang.trang_thai_tc"
    )
    
    # =========================================================================
    # v3.5.0: THÊM FIELDS CHO TỪ CHỐI + CẤP PHÊ DUYỆT
    # =========================================================================
    diem_tc_cap1: Optional[float] = Field(
        default=None,
        description="Điểm tiêu chí sau khi Phó ĐT duyệt cấp 1"
    )
    diem_tc_cap2: Optional[float] = Field(
        default=None,
        description="Điểm tiêu chí sau khi ĐT duyệt cấp 2"
    )
    diem_tieu_chi_chung: Optional[float] = Field(
        default=None,
        description="Điểm tiêu chí chung cuối cùng (0-30)"
    )
    ly_do_tu_choi_tc: Optional[str] = Field(
        default=None,
        description="Lý do từ chối tiêu chí (nếu có)"
    )
    cap_phe_duyet_hien_tai: Optional[str] = Field(
        default=None,
        description="'cap1' hoặc 'cap2' - cấp đang chờ duyệt"
    )


class DanhSachChoPheDuyetResponse(BaseModel):
    """Response danh sách tiêu chí chung chờ phê duyệt."""
    tong_so: int
    danh_sach: List[DanhSachChoPheDuyetItem]
    
    # Phân trang
    page: int = 1
    page_size: int = 20
    total_pages: int = 1


class ChiTietPheDuyetResponse(BaseModel):
    """Response chi tiết khi LĐ xem một bản tự đánh giá."""
    model_config = ConfigDict(from_attributes=True)
    
    danh_gia_thang_id: UUID
    
    # Thông tin CC
    cong_chuc: dict  # CongChucBrief
    
    thang: int
    nam: int
    
    # Tổng hợp
    tong_hop_cc: TieuChiChungTongHop  # Điểm CC tự chấm
    
    # Chi tiết từng tiêu chí
    tieu_chi: List[TieuChiItemResponse]
    
    # Danh sách tiêu chí có sự khác biệt (sau khi duyệt)
    danh_sach_khac_biet: Optional[List[TieuChiItemResponse]] = None
    
    # Thời gian
    ngay_gui: datetime
    trang_thai: TrangThaiTieuChiEnum


class PheDuyetTieuChiResponse(BaseModel):
    """Response sau khi LĐ phê duyệt tiêu chí chung."""
    success: bool = True
    message: str
    
    danh_gia_thang_id: UUID
    
    # Điểm sau phê duyệt
    diem_tieu_chi_chung: float = Field(
        ...,
        description="Tổng điểm tiêu chí chung sau phê duyệt (0-30)"
    )
    
    # Số tiêu chí LĐ điều chỉnh
    so_dieu_chinh: int = Field(
        default=0,
        description="Số tiêu chí LĐ điều chỉnh khác CC"
    )
    
    trang_thai: TrangThaiTieuChiEnum = TrangThaiTieuChiEnum.DA_PHE_DUYET
    ngay_phe_duyet: datetime


class PheDuyetBulkResponse(BaseModel):
    """Response phê duyệt hàng loạt."""
    success: bool = True
    message: str
    
    tong_phe_duyet: int
    danh_sach_id: List[UUID]


# =============================================================================
# TIÊU CHÍ CHUNG MASTER DATA - RESPONSE
# =============================================================================

class TieuChiChungMasterResponse(BaseModel):
    """Response cho master data tiêu chí chung."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    ma_tieu_chi: str
    ma_tieu_chi_con: Optional[str] = None
    nhom_tieu_chi: int
    ten_tieu_chi: str
    mo_ta: Optional[str] = None
    diem_toi_da: float
    gia_tri_mac_dinh: bool
    loai_logic: str
    parent_ma_tieu_chi: Optional[str] = None
    thu_tu: int


class DanhMucTieuChiResponse(BaseModel):
    """Response danh mục tiêu chí chung (để hiển thị form)."""
    nhom_1: List[TieuChiChungMasterResponse] = Field(
        ...,
        description="Nhóm 1: Phẩm chất chính trị, đạo đức (10 điểm)"
    )
    nhom_2: List[TieuChiChungMasterResponse] = Field(
        ...,
        description="Nhóm 2: Năng lực chuyên môn (10 điểm)"
    )
    nhom_3: List[TieuChiChungMasterResponse] = Field(
        ...,
        description="Nhóm 3: Năng lực đổi mới (10 điểm)"
    )
    tong_diem_toi_da: float = 30.0


# =============================================================================
# HELPER SCHEMAS
# =============================================================================

class CongChucBriefForAssessment(BaseModel):
    """Thông tin tóm tắt CC trong đánh giá."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    ma_cc: str
    ho_ten: str
    chuc_vu: Optional[str] = None
    don_vi_id: Optional[UUID] = None
    don_vi_ten: Optional[str] = None
    is_lanh_dao: bool = False


class NguoiPheDuyetOption(BaseModel):
    """Option người phê duyệt cho dropdown."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    ma_cc: str
    ho_ten: str
    chuc_vu: Optional[str] = None


class DanhSachNguoiPheDuyetResponse(BaseModel):
    """Response danh sách người phê duyệt tiêu chí chung."""
    danh_sach: List[NguoiPheDuyetOption]
    ghi_chu: Optional[str] = None


# =============================================================================
# THỐNG KÊ SCHEMAS
# =============================================================================

class ThongKeTieuChiChungDonVi(BaseModel):
    """Thống kê tiêu chí chung theo đơn vị."""
    don_vi_id: UUID
    don_vi_ten: str
    thang: int
    nam: int
    
    tong_cc: int = Field(..., description="Tổng số CC trong đơn vị")
    da_tu_danh_gia: int = Field(..., description="Số CC đã tự đánh giá")
    cho_phe_duyet: int = Field(..., description="Số CC chờ phê duyệt")
    da_phe_duyet: int = Field(..., description="Số CC đã được phê duyệt")
    
    # Điểm trung bình
    diem_tb_tu_cham: Optional[float] = None
    diem_tb_phe_duyet: Optional[float] = None
    
    # Số tiêu chí bị điều chỉnh
    tong_dieu_chinh: int = Field(
        default=0,
        description="Tổng số tiêu chí LĐ điều chỉnh khác CC"
    )


class SoSanhCCvsLD(BaseModel):
    """So sánh điểm CC tự chấm vs LĐ phê duyệt."""
    cong_chuc_id: UUID
    ho_ten: str
    thang: int
    nam: int
    
    diem_cc: float
    diem_ld: float
    chenh_lech: float
    
    # Chi tiết các tiêu chí khác nhau
    tieu_chi_khac_biet: List[TieuChiItemResponse]


# =============================================================================
# CONSTANTS - ĐIỂM TỐI ĐA VÀ GIÁ TRỊ MẶC ĐỊNH
# =============================================================================

TIEU_CHI_DIEM_TOI_DA = {
    "1.1": 5.0,
    "1.2": 5.0,
    "2.1": 2.5,
    "2.2": 2.5,
    "2.3": 2.5,
    "2.4": 2.5,
    "3.1": 2.5,
    "3.2": 2.5,
    "3.3": 2.5,
    "3.4": 2.5,
}

TIEU_CHI_GIA_TRI_MAC_DINH = {
    # Nhóm 1 & 2: Mặc định ĐẠT (True)
    "1.1": True,
    "1.2": True,
    "2.1": True,
    "2.2": True,
    "2.3": True,
    "2.4": True,
    # Nhóm 3: Mặc định KHÔNG ĐẠT (False)
    "3.1": False,
    "3.2": False,
    "3.3": False,
    "3.4": False,
}

TIEU_CHI_NHOM = {
    "1.1": 1, "1.2": 1,
    "2.1": 2, "2.2": 2, "2.3": 2, "2.4": 2,
    "3.1": 3, "3.2": 3, "3.3": 3, "3.4": 3,
}

TIEU_CHI_TEN = {
    "1.1": "Phẩm chất chính trị, đạo đức",
    "1.2": "Văn hóa công vụ, trách nhiệm kỷ luật",
    "2.1": "Kiến thức chuyên môn, nghiệp vụ",
    "2.2": "Kỹ năng nghiệp vụ",
    "2.3": "Sử dụng công nghệ thông tin",
    "2.4": "Sử dụng ngoại ngữ",
    "3.1": "Có sáng kiến, cải tiến trong công tác",
    "3.2": "Sẵn sàng tham gia nhiệm vụ chính trị đột xuất",
    "3.3": "Tích cực nghiên cứu, học tập nâng cao trình độ",
    "3.4": "Đóng góp ý kiến cải tiến quy trình, quy định",
}


def tinh_diem_binary(ma_tieu_chi: str, is_achieved: bool) -> float:
    """
    Tính điểm theo logic nhị phân.
    
    Args:
        ma_tieu_chi: Mã tiêu chí (1.1, 1.2, ...)
        is_achieved: True = Đạt, False = Không đạt
    
    Returns:
        Điểm số (0 hoặc diem_toi_da)
    """
    if is_achieved:
        return TIEU_CHI_DIEM_TOI_DA.get(ma_tieu_chi, 0)
    return 0.0


def build_virtual_tieu_chi_response(
    ma_tieu_chi: str,
    danh_gia_thang_id: Optional[UUID] = None
) -> TieuChiItemResponse:
    """
    Build virtual TieuChiItemResponse với giá trị mặc định.
    
    Dùng khi chưa có bản ghi trong DB.
    """
    gia_tri_mac_dinh = TIEU_CHI_GIA_TRI_MAC_DINH.get(ma_tieu_chi, True)
    diem_toi_da = TIEU_CHI_DIEM_TOI_DA.get(ma_tieu_chi, 0)
    diem = diem_toi_da if gia_tri_mac_dinh else 0
    
    return TieuChiItemResponse(
        id=None,
        danh_gia_thang_id=danh_gia_thang_id,
        tieu_chi_id=None,
        ma_tieu_chi=ma_tieu_chi,
        ten_tieu_chi=TIEU_CHI_TEN.get(ma_tieu_chi, ma_tieu_chi),
        nhom_tieu_chi=TIEU_CHI_NHOM.get(ma_tieu_chi, 1),
        diem_toi_da=diem_toi_da,
        gia_tri_mac_dinh=gia_tri_mac_dinh,
        is_achieved_cc=gia_tri_mac_dinh,
        is_achieved_ld=None,
        is_achieved=gia_tri_mac_dinh,
        diem_tu_cham=diem,
        diem_phe_duyet=None,
        diem=diem,
        trang_thai=TrangThaiTieuChiEnum.CHUA_DANH_GIA,
        ghi_chu_cc=None,
        ghi_chu_ld=None,
        ly_do_dieu_chinh=None,
        ngay_gui=None,
        ngay_phe_duyet=None,
    )


def build_virtual_tong_hop() -> TieuChiChungTongHop:
    """
    Build TieuChiChungTongHop với giá trị mặc định (Virtual Record).
    
    Mặc định:
    - Nhóm 1: 10 điểm (1.1=5, 1.2=5)
    - Nhóm 2: 10 điểm (2.1-2.4 = 2.5 mỗi tiêu chí)
    - Nhóm 3: 0 điểm (mặc định không đạt)
    """
    return TieuChiChungTongHop(
        nhom_1_diem=10.0,
        nhom_2_diem=10.0,
        nhom_3_diem=0.0,
        tong_diem=20.0,
    )