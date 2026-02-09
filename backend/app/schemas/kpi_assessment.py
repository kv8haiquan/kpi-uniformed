"""
app/schemas/kpi_assessment.py
=============================
Pydantic schemas cho Phê duyệt và Đánh giá tháng.

PHIÊN BẢN: 2.7.0 (01/02/2026)
THAY ĐỔI QUAN TRỌNG:
- FIX BUG: so_loi_chat_luong/so_loi_tien_do đổi từ int(default=0) sang Optional[int](default=None)
  để get_so_loi_chot() fallback đúng về tu_danh_gia khi LĐ không nhập số lỗi
- NEW: Thêm cap_do_ma (Optional) vào PheDuyetRequest và PheDuyetBulkRequest
  để LĐ có thể điều chỉnh mức độ khi phê duyệt
- Binary Scoring: is_achieved_cc/ld thay vì diem
- Virtual Record: is_new_record flag
- tieu_chi_id (UUID) thay vì ma_tieu_chi (string)
- Audit Trail: ghi_chu_cc, ghi_chu_ld, ly_do_dieu_chinh

Bao gồm:
- PheDuyetRequest: Request phê duyệt/từ chối kê khai
- KeKhaiPendingResponse: Response cho danh sách chờ duyệt
- DanhGiaThangResponse: Kết quả đánh giá tháng (với Virtual Record)
- TieuChiChungMasterResponse: Master Data tiêu chí
- TuDanhGiaRequest: CC tự đánh giá Binary Scoring
- PheDuyetTieuChiRequest: LĐ phê duyệt tiêu chí
"""

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Optional, List, Literal
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator

from app.schemas.master_data import CongChucBriefResponse, DonViResponse
from app.schemas.kpi_submission import KeKhaiResponse


# =============================================================================
# ENUMS
# =============================================================================

class PheDuyetAction(str, Enum):
    """Hành động phê duyệt."""
    APPROVE = "APPROVE"  # Phê duyệt
    REJECT = "REJECT"    # Từ chối / Yêu cầu sửa


class MucXepLoai(str, Enum):
    """Mức xếp loại công chức."""
    A = "A"  # Hoàn thành xuất sắc (>= 90 điểm)
    B = "B"  # Hoàn thành tốt (70-89 điểm)
    C = "C"  # Hoàn thành (50-69 điểm)
    D = "D"  # Không hoàn thành (< 50 điểm)


class TrangThaiTieuChi(str, Enum):
    """Trạng thái của việc chấm tiêu chí chung."""
    NHAP = "NHAP"
    CHO_PHE_DUYET = "CHO_PHE_DUYET"
    DA_PHE_DUYET = "DA_PHE_DUYET"


class TrangThaiDanhGia(str, Enum):
    """Trạng thái của đánh giá tháng."""
    CHUA_DANH_GIA = "CHUA_DANH_GIA"      # Virtual Record - chưa có trong DB
    DANG_DANH_GIA = "DANG_DANH_GIA"
    CHO_TONG_HOP = "CHO_TONG_HOP"
    DA_TONG_HOP = "DA_TONG_HOP"
    CHO_PHE_DUYET = "CHO_PHE_DUYET"
    HOAN_THANH = "HOAN_THANH"
    CO_KIEN_NGHI = "CO_KIEN_NGHI"


class LoaiLogicTieuChi(str, Enum):
    """Logic chấm điểm tiêu chí."""
    ALL_OR_NOTHING = "ALL_OR_NOTHING"  # Nhóm 1, 2: Vi phạm 1 con → 0 điểm
    BONUS = "BONUS"                     # Nhóm 3: Có thành tích mới được điểm


# =============================================================================
# PHE DUYET SCHEMAS
# =============================================================================

class PheDuyetRequest(BaseModel):
    """
    Schema request phê duyệt kê khai.
    
    Lãnh đạo dùng để:
    - APPROVE: Phê duyệt, chốt số lỗi cuối cùng
    - REJECT: Từ chối, yêu cầu CC sửa lại
    """
    action: PheDuyetAction = Field(
        ...,
        description="Hành động: APPROVE (Phê duyệt) hoặc REJECT (Từ chối)"
    )
    noi_dung_trao_doi: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="Nhận xét/Lý do từ chối của lãnh đạo"
    )
    so_loi_chat_luong: Optional[int] = Field(
        default=None,
        ge=0,
        description="Số lỗi CL do LĐ chốt. None = dùng tu_danh_gia của CC"
    )
    so_loi_tien_do: Optional[int] = Field(
        default=None,
        ge=0,
        description="Số lỗi TĐ do LĐ chốt. None = dùng tu_danh_gia của CC"
    )
    cap_do_ma: Optional[str] = Field(
        default=None,
        pattern="^(C1|C2|C3|C4|C5)$",
        description="Mức độ do LĐ điều chỉnh. None = giữ nguyên"
    )
    
    @field_validator("noi_dung_trao_doi")
    @classmethod
    def validate_noi_dung_reject(cls, v, info):
        """Nếu REJECT, bắt buộc phải có lý do."""
        action = info.data.get("action")
        if action == PheDuyetAction.REJECT and not v:
            raise ValueError("Phải nhập lý do khi từ chối")
        return v


class PheDuyetBulkRequest(BaseModel):
    """Schema request phê duyệt nhiều kê khai cùng lúc."""
    ke_khai_ids: List[UUID] = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Danh sách ID các bản kê khai cần xử lý"
    )
    action: PheDuyetAction = Field(
        ...,
        description="Hành động: APPROVE hoặc REJECT"
    )
    noi_dung_trao_doi: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="Nhận xét chung cho tất cả"
    )
    # Chỉ áp dụng khi APPROVE. None = dùng tu_danh_gia của CC
    so_loi_chat_luong: Optional[int] = Field(default=None, ge=0)
    so_loi_tien_do: Optional[int] = Field(default=None, ge=0)
    cap_do_ma: Optional[str] = Field(
        default=None,
        pattern="^(C1|C2|C3|C4|C5)$",
        description="Mức độ do LĐ điều chỉnh. None = giữ nguyên"
    )


class PheDuyetResponse(BaseModel):
    """Schema response sau khi phê duyệt."""
    success: bool = True
    message: str
    processed_count: int = Field(..., description="Số bản kê khai đã xử lý")
    ke_khai_ids: List[UUID] = Field(..., description="Danh sách ID đã xử lý")
    trang_thai_moi: str = Field(..., description="Trạng thái mới")


# =============================================================================
# KE KHAI PENDING RESPONSE (Kế thừa KeKhaiResponse)
# =============================================================================

class CongChucPendingInfo(BaseModel):
    """Thông tin CC cho danh sách chờ duyệt."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    ma_cc: str
    ho_ten: str
    chuc_vu: Optional[str] = None
    don_vi_id: Optional[UUID] = None
    don_vi_ten: Optional[str] = None


class KeKhaiPendingResponse(BaseModel):
    """
    Schema response cho danh sách kê khai chờ phê duyệt.
    
    Kế thừa từ KeKhaiResponse và thêm thông tin:
    - Tự đánh giá của CC (để Lãnh đạo xem xét)
    - Thông tin đơn vị của CC
    """
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    cong_chuc: Optional[CongChucPendingInfo] = None
    thang: int
    nam: int
    ngay_thuc_hien: Optional[date] = None
    
    # Công việc
    danh_muc_sp_id: UUID
    danh_muc_ten: Optional[str] = None
    cap_do_ma: Optional[str] = None
    so_luong: int
    he_so_thuc_te: Optional[float] = None
    
    # Thông tin bổ sung
    mo_ta_cong_viec: Optional[str] = None
    is_doi_moi_sang_tao: bool = False
    ngay_deadline: Optional[date] = None
    ngay_hoan_thanh: Optional[date] = None
    
    # =========================================================================
    # TỰ ĐÁNH GIÁ CỦA CC (Lãnh đạo cần xem để so sánh)
    # =========================================================================
    tu_danh_gia_chat_luong: int = Field(
        default=0,
        description="Số lỗi CL do CC tự đánh giá"
    )
    tu_danh_gia_tien_do: int = Field(
        default=0,
        description="Số lỗi TĐ do CC tự đánh giá"
    )
    ghi_chu_tu_danh_gia: Optional[str] = Field(
        default=None,
        description="Giải trình của CC"
    )
    
    # Kết quả quy đổi
    so_sp_goc_quy_doi: Optional[float] = None
    
    # Trạng thái & thời gian
    trang_thai: str
    created_at: Optional[datetime] = None


# =============================================================================
# DANH GIA THANG SCHEMAS
# =============================================================================

class DiemChiTiet(BaseModel):
    """Chi tiết điểm KPI."""
    a_so_luong: Optional[float] = Field(default=None, description="Điểm số lượng (a)")
    b_chat_luong: Optional[float] = Field(default=None, description="Điểm chất lượng (b)")
    c_tien_do: Optional[float] = Field(default=None, description="Điểm tiến độ (c)")


# =============================================================================
# TIÊU CHÍ CHUNG - BINARY SCORING v2.5.0
# =============================================================================

class TieuChiChungMasterResponse(BaseModel):
    """
    Response cho Master Data tiêu chí chung.
    Dùng để hiển thị form đánh giá.
    """
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID = Field(..., description="UUID - dùng làm tieu_chi_id")
    ma_tieu_chi: str = Field(..., description="Mã tiêu chí: 1.1, 1.1a1, 2.1, ...")
    ma_tieu_chi_con: Optional[str] = Field(
        default=None, 
        description="Mã con: a1, b1, ... (null nếu TC lớn)"
    )
    nhom_tieu_chi: int = Field(..., ge=1, le=3, description="Nhóm: 1, 2, 3")
    ten_tieu_chi: str
    mo_ta: Optional[str] = None
    diem_toi_da: float = Field(..., description="5.0, 2.5, hoặc 0 (TC con)")
    gia_tri_mac_dinh: bool = Field(
        ..., 
        description="Giá trị mặc định: TRUE (nhóm 1,2), FALSE (nhóm 3)"
    )
    loai_logic: str = Field(..., description="ALL_OR_NOTHING hoặc BONUS")
    parent_ma_tieu_chi: Optional[str] = Field(
        default=None, 
        description="Mã TC cha (VD: '1.1' nếu là TC con của 1.1)"
    )
    thu_tu: int = Field(..., description="Thứ tự hiển thị 1-31")
    is_active: bool = True


class TieuChiChungItemResponse(BaseModel):
    """
    Kết quả chấm tiêu chí chung của CC - Binary Scoring.
    
    QUAN TRỌNG v2.5.0:
    - is_achieved_cc: Bản tích của CC (TRUE/FALSE)
    - is_achieved_ld: Bản tích của LĐ (NULL = chưa duyệt)
    - is_achieved: Kết quả cuối cùng (is_achieved_ld ?? is_achieved_cc)
    - diem: Điểm cuối cùng (diem_toi_da nếu is_achieved else 0)
    """
    model_config = ConfigDict(from_attributes=True)
    
    # Định danh
    id: Optional[UUID] = Field(default=None, description="UUID bản ghi đánh giá")
    tieu_chi_id: UUID = Field(..., description="UUID của tiêu chí Master")
    danh_gia_thang_id: Optional[UUID] = None
    
    # Thông tin từ Master Data (JOIN)
    ma_tieu_chi: str = Field(..., description="Mã tiêu chí (1.1, 1.2, ...)")
    ten_tieu_chi: str
    nhom_tieu_chi: int = Field(..., ge=1, le=3)
    diem_toi_da: float
    loai_logic: str = Field(..., description="ALL_OR_NOTHING hoặc BONUS")
    
    # ⭐ BINARY SCORING - Core fields
    is_achieved_cc: bool = Field(..., description="Bản tích CC: TRUE=Đạt")
    is_achieved_ld: Optional[bool] = Field(
        default=None, 
        description="Bản tích LĐ: NULL=Chưa duyệt"
    )
    is_achieved: bool = Field(
        ..., 
        description="⭐ KẾT QUẢ CUỐI CÙNG (is_achieved_ld ?? is_achieved_cc)"
    )
    
    # Điểm số (tự động tính từ is_achieved)
    diem_tu_cham: float = Field(..., description="= diem_toi_da if is_achieved_cc else 0")
    diem_phe_duyet: Optional[float] = Field(
        default=None, 
        description="= diem_toi_da if is_achieved_ld else 0"
    )
    diem: float = Field(
        ..., 
        description="⭐ ĐIỂM CUỐI CÙNG (diem_phe_duyet ?? diem_tu_cham)"
    )
    
    # Trạng thái
    trang_thai: str = Field(
        default="NHAP", 
        description="NHAP, CHO_PHE_DUYET, DA_PHE_DUYET"
    )
    
    # Ghi chú (Audit Trail)
    ghi_chu_cc: Optional[str] = Field(default=None, description="Giải trình của CC")
    ghi_chu_ld: Optional[str] = Field(default=None, description="Ghi chú của LĐ")
    ly_do_dieu_chinh: Optional[str] = Field(
        default=None, 
        description="Lý do LĐ điều chỉnh (nếu khác CC)"
    )
    
    # Metadata
    ngay_gui: Optional[datetime] = None
    ngay_phe_duyet: Optional[datetime] = None


class TieuChiChungItem(BaseModel):
    """
    Schema tương thích ngược cho TieuChiChungItemResponse.
    DEPRECATED: Dùng TieuChiChungItemResponse cho code mới.
    """
    model_config = ConfigDict(from_attributes=True)
    
    id: Optional[UUID] = None
    tieu_chi_id: Optional[UUID] = None
    ma_tieu_chi: str = Field(..., description="Mã tiêu chí (1.1, 1.2, ...)")
    ten_tieu_chi: Optional[str] = None
    nhom_tieu_chi: int = Field(..., ge=1, le=3, description="Nhóm (1, 2, 3)")
    diem_toi_da: float = Field(..., description="Điểm tối đa")
    loai_logic: Optional[str] = None
    
    # Binary Scoring fields (v2.5.0)
    is_achieved_cc: Optional[bool] = None
    is_achieved_ld: Optional[bool] = None
    is_achieved: Optional[bool] = None
    
    # Điểm số
    diem_tu_cham: Optional[float] = Field(default=None, description="Điểm CC tự chấm")
    diem_phe_duyet: Optional[float] = Field(default=None, description="Điểm LĐ phê duyệt")
    diem: Optional[float] = None
    
    # Trạng thái
    trang_thai: Optional[str] = None
    da_phe_duyet: bool = Field(default=False, description="Đã được phê duyệt chưa")
    
    # Ghi chú
    ghi_chu: Optional[str] = None
    ghi_chu_cc: Optional[str] = None
    ghi_chu_ld: Optional[str] = None


class TongHopKeKhai(BaseModel):
    """Tổng hợp kê khai trong tháng."""
    tong_ke_khai: int = Field(default=0, description="Tổng số bản kê khai")
    da_phe_duyet: int = Field(default=0, description="Số bản đã phê duyệt")
    cho_phe_duyet: int = Field(default=0, description="Số bản chờ phê duyệt")
    tong_sp_goc_quy_doi: float = Field(default=0, description="Tổng SP gốc quy đổi")
    tong_loi_chat_luong: int = Field(default=0, description="Tổng lỗi CL")
    tong_loi_tien_do: int = Field(default=0, description="Tổng lỗi TĐ")


class DanhGiaThangResponse(BaseModel):
    """
    Schema response đầy đủ cho Đánh giá tháng.
    
    PHIÊN BẢN 2.5.0:
    - is_new_record: Flag cho Virtual Record (chưa có trong DB)
    - tieu_chi_chung: Luôn có data (từ Master hoặc DB)
    - Binary Scoring trong các tiêu chí
    
    Hiển thị:
    - Thông tin CC được đánh giá
    - Điểm tiêu chí chung (A)
    - Điểm KPI (B) và chi tiết (a, b, c)
    - Điểm tổng và xếp loại
    """
    model_config = ConfigDict(from_attributes=True)
    
    # ⭐ VIRTUAL RECORD FLAG - QUAN TRỌNG
    is_new_record: bool = Field(
        default=False,
        description="⭐ TRUE = Chưa có bản ghi DB, cần khởi tạo form"
    )
    
    id: Optional[UUID] = Field(
        default=None,
        description="NULL nếu is_new_record = true"
    )
    
    # -------------------------------------------------------------------------
    # CÔNG CHỨC ĐƯỢC ĐÁNH GIÁ
    # -------------------------------------------------------------------------
    cong_chuc_id: UUID
    cong_chuc: Optional[CongChucBriefResponse] = None
    don_vi_ten: Optional[str] = None
    is_lanh_dao: bool = False
    
    thang: int
    nam: int
    
    # -------------------------------------------------------------------------
    # SỐ LIỆU GIAO VIỆC
    # -------------------------------------------------------------------------
    so_sp_goc_duoc_giao: Optional[float] = Field(
        default=None,
        description="Số SP gốc được giao trong tháng"
    )
    so_ngay_lam_viec: Optional[int] = None
    so_ngay_nghi_phep: int = 0
    
    # -------------------------------------------------------------------------
    # TỔNG HỢP KÊ KHAI
    # -------------------------------------------------------------------------
    tong_hop_ke_khai: Optional[TongHopKeKhai] = None
    
    # -------------------------------------------------------------------------
    # ĐIỂM SỐ
    # -------------------------------------------------------------------------
    diem_tieu_chi_chung: Optional[float] = Field(
        default=None,
        description="Điểm tiêu chí chung A (0-30)"
    )
    diem_kpi: Optional[float] = Field(
        default=None,
        description="Điểm KPI (tỷ lệ 0-1)"
    )
    diem_chi_tiet: Optional[DiemChiTiet] = None
    diem_tong: Optional[float] = Field(
        default=None,
        description="Điểm tổng (0-100)"
    )
    
    # -------------------------------------------------------------------------
    # XẾP LOẠI
    # -------------------------------------------------------------------------
    muc_xep_loai_tu_dong: Optional[str] = Field(
        default=None,
        description="Xếp loại hệ thống tự tính"
    )
    muc_xep_loai_de_xuat: Optional[str] = Field(
        default=None,
        description="Xếp loại Trưởng ĐV đề xuất"
    )
    muc_xep_loai_chinh_thuc: Optional[str] = Field(
        default=None,
        description="Xếp loại CCT quyết định"
    )
    ly_do_dieu_chinh: Optional[str] = None
    
    # -------------------------------------------------------------------------
    # TRẠNG THÁI
    # -------------------------------------------------------------------------
    trang_thai: str = Field(
        default="CHUA_DANH_GIA",
        description="CHUA_DANH_GIA (virtual), DANG_DANH_GIA, CHO_TONG_HOP, DA_TONG_HOP, CHO_PHE_DUYET, HOAN_THANH"
    )
    ngay_tong_hop: Optional[datetime] = None
    ngay_de_xuat: Optional[datetime] = None
    ngay_phe_duyet: Optional[datetime] = None
    
    # -------------------------------------------------------------------------
    # TIÊU CHÍ CHUNG CHI TIẾT - Binary Scoring
    # -------------------------------------------------------------------------
    tieu_chi_chung: Optional[List[TieuChiChungItem]] = Field(
        default=None,
        description="Danh sách tiêu chí với Binary Scoring"
    )
    
    # -------------------------------------------------------------------------
    # GHI CHÚ
    # -------------------------------------------------------------------------
    uu_diem: Optional[str] = None
    han_che: Optional[str] = None
    ghi_chu: Optional[str] = None
    
    # Metadata
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class DanhGiaThangBriefResponse(BaseModel):
    """Schema response tóm tắt cho danh sách đánh giá."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    cong_chuc_id: UUID
    ho_ten: Optional[str] = None
    ma_cc: Optional[str] = None
    don_vi_ten: Optional[str] = None
    thang: int
    nam: int
    diem_tong: Optional[float] = None
    muc_xep_loai_chinh_thuc: Optional[str] = None
    trang_thai: str


# =============================================================================
# TIEU CHI CHUNG INPUT/UPDATE SCHEMAS - Binary Scoring v2.5.0
# =============================================================================

class TieuChiChungInputBinary(BaseModel):
    """
    Input cho một tiêu chí khi CC tự chấm - BINARY SCORING.
    
    v2.5.0: Sử dụng is_achieved_cc (boolean) thay vì diem (float)
    """
    tieu_chi_id: UUID = Field(..., description="UUID của tiêu chí từ Master Data")
    is_achieved_cc: bool = Field(..., description="TRUE = Đạt, FALSE = Không đạt")
    ghi_chu_cc: Optional[str] = Field(
        default=None, 
        max_length=500,
        description="Giải trình của CC"
    )


class TuDanhGiaRequest(BaseModel):
    """
    Request CC tự đánh giá tiêu chí chung - Binary Scoring.
    
    CÁCH DÙNG:
    1. Frontend lấy Master Data từ GET /tieu-chi-chung
    2. User tick/untick các tiêu chí
    3. Gửi POST /tu-danh-gia với payload này
    """
    thang: int = Field(..., ge=1, le=12)
    nam: int = Field(..., ge=2025)
    tieu_chi: List[TieuChiChungInputBinary] = Field(
        ...,
        min_length=1,
        max_length=31,
        description="Danh sách tiêu chí với giá trị is_achieved_cc"
    )
    
    @field_validator("tieu_chi")
    @classmethod
    def validate_tieu_chi_unique(cls, v):
        """Đảm bảo không có tiêu chí trùng."""
        id_list = [tc.tieu_chi_id for tc in v]
        if len(id_list) != len(set(id_list)):
            raise ValueError("Có tiêu chí bị trùng ID")
        return v


class TieuChiChungInputLD(BaseModel):
    """
    Input cho một tiêu chí khi LĐ phê duyệt - Binary Scoring.
    
    LĐ có thể điều chỉnh is_achieved khác với CC.
    Nếu điều chỉnh, BẮT BUỘC phải có ly_do_dieu_chinh.
    """
    tieu_chi_id: UUID = Field(..., description="UUID của tiêu chí")
    is_achieved_ld: bool = Field(..., description="TRUE = Đạt (theo LĐ)")
    ghi_chu_ld: Optional[str] = Field(
        default=None, 
        max_length=500,
        description="Ghi chú của LĐ"
    )
    ly_do_dieu_chinh: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Lý do điều chỉnh (BẮT BUỘC nếu khác CC)"
    )


class PheDuyetTieuChiRequest(BaseModel):
    """
    Request LĐ phê duyệt tiêu chí chung.
    
    LĐ có thể:
    1. Giữ nguyên kết quả của CC (không gửi tiêu chí đó)
    2. Điều chỉnh (gửi tiêu chí với is_achieved_ld khác)
    """
    danh_gia_thang_id: UUID = Field(..., description="ID đánh giá tháng cần phê duyệt")
    tieu_chi: Optional[List[TieuChiChungInputLD]] = Field(
        default=None,
        description="Chỉ gửi các tiêu chí cần điều chỉnh"
    )
    ghi_chu_chung: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="Nhận xét chung của LĐ"
    )


# =============================================================================
# BACKWARD COMPATIBLE - TieuChiChungInput (Legacy)
# =============================================================================

class TieuChiChungInput(BaseModel):
    """
    Input cho một tiêu chí - LEGACY (để tương thích ngược).
    
    DEPRECATED: Dùng TieuChiChungInputBinary cho code mới.
    """
    ma_tieu_chi: Optional[str] = Field(default=None, description="[DEPRECATED] Mã tiêu chí")
    tieu_chi_id: Optional[UUID] = Field(default=None, description="UUID tiêu chí (ưu tiên)")
    diem: Optional[float] = Field(default=None, ge=0, description="[DEPRECATED] Điểm chấm")
    is_achieved_cc: Optional[bool] = Field(default=None, description="Binary scoring value")
    ghi_chu: Optional[str] = Field(default=None, max_length=500)
    ghi_chu_cc: Optional[str] = Field(default=None, max_length=500)
    
    @model_validator(mode='after')
    def check_id_or_ma(self):
        """Phải có ít nhất tieu_chi_id hoặc ma_tieu_chi."""
        if not self.tieu_chi_id and not self.ma_tieu_chi:
            raise ValueError("Phải có tieu_chi_id hoặc ma_tieu_chi")
        return self


class TieuChiChungUpdate(BaseModel):
    """
    Schema để nhập điểm tiêu chí chung - LEGACY.
    
    DEPRECATED: Dùng TuDanhGiaRequest hoặc PheDuyetTieuChiRequest.
    """
    danh_gia_thang_id: Optional[UUID] = Field(
        default=None,
        description="ID đánh giá tháng (nếu đã có)"
    )
    thang: int = Field(..., ge=1, le=12)
    nam: int = Field(..., ge=2025)
    tieu_chi: List[TieuChiChungInput] = Field(
        ...,
        min_length=1,
        description="Danh sách điểm các tiêu chí"
    )
    
    @field_validator("tieu_chi")
    @classmethod
    def validate_tieu_chi_unique(cls, v):
        """Đảm bảo không có tiêu chí trùng."""
        # Ưu tiên tieu_chi_id, fallback ma_tieu_chi
        id_list = [tc.tieu_chi_id or tc.ma_tieu_chi for tc in v]
        if len(id_list) != len(set(id_list)):
            raise ValueError("Có tiêu chí bị trùng")
        return v


# =============================================================================
# TONG HOP REQUEST
# =============================================================================

class TongHopRequest(BaseModel):
    """Request trigger tổng hợp đánh giá tháng."""
    cong_chuc_id: UUID = Field(..., description="ID công chức cần tổng hợp")
    thang: int = Field(..., ge=1, le=12)
    nam: int = Field(..., ge=2025)


class TongHopBulkRequest(BaseModel):
    """Request tổng hợp nhiều CC (theo đơn vị)."""
    don_vi_id: Optional[UUID] = Field(
        default=None,
        description="ID đơn vị (để tổng hợp cả đơn vị)"
    )
    cong_chuc_ids: Optional[List[UUID]] = Field(
        default=None,
        description="Danh sách CC cụ thể"
    )
    thang: int = Field(..., ge=1, le=12)
    nam: int = Field(..., ge=2025)


# =============================================================================
# FILTER PARAMS
# =============================================================================

class DanhGiaFilterParams(BaseModel):
    """Filter params cho danh sách đánh giá."""
    thang: Optional[int] = Field(default=None, ge=1, le=12)
    nam: Optional[int] = Field(default=None, ge=2025)
    don_vi_id: Optional[UUID] = None
    trang_thai: Optional[str] = None
    muc_xep_loai: Optional[str] = Field(
        default=None,
        pattern="^(A|B|C|D)$"
    )