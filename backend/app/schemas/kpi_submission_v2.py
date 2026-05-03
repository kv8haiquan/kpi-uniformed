"""
app/schemas/kpi_submission_v2.py
================================
Pydantic schemas cho V2_PL3 (28/04/2026).

Khác với V1:
- KHÔNG có cap_do_id (V2 bỏ C1-C5).
- KHÔNG có he_so_thuc_te (LOCKED 14: lãnh đạo KHÔNG override).
- Bắt buộc thang + nam ở request body.
- Response trả thêm snapshot fields: he_so_quy_doi_snapshot, nhom_pl3_snapshot,
  linh_vuc_snapshot, ten_linh_vuc, version_kekhai.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


# =============================================================================
# REQUEST SCHEMAS
# =============================================================================

class KeKhaiV2Base(BaseModel):
    """Common fields cho create/update V2."""

    # LOCKED 14: KHÔNG cho V2 nhận extra fields (vd: he_so_thuc_te, cap_do_id từ V1).
    # Pydantic sẽ trả 422 nếu client gửi field không có trong schema.
    model_config = ConfigDict(extra="forbid")

    # Bắt buộc gắn với 1 mục PL3 cụ thể (validate ở endpoint)
    danh_muc_sp_id: UUID = Field(..., description="ID mục PL3")

    # LOCKED 17: số nguyên dương
    so_luong: int = Field(..., gt=0, description="Số lượng (>0, nguyên)")

    thang: int = Field(..., ge=1, le=12, description="Tháng kê khai")
    nam: int = Field(..., ge=2025, description="Năm kê khai")

    ngay_thuc_hien: Optional[date] = Field(default=None)
    mo_ta_cong_viec: Optional[str] = Field(default=None, max_length=2000)
    is_doi_moi_sang_tao: bool = Field(default=False)
    ngay_deadline: Optional[date] = Field(default=None)
    ngay_hoan_thanh: Optional[date] = Field(default=None)

    nguoi_phe_duyet_id: UUID = Field(..., description="ID Phó ĐV phê duyệt")

    # Tự đánh giá (optional)
    tu_danh_gia_chat_luong: int = Field(default=0, ge=0)
    tu_danh_gia_tien_do: int = Field(default=0, ge=0)
    ghi_chu_tu_danh_gia: Optional[str] = Field(default=None, max_length=2000)
    ghi_chu_tu_dg_chat_luong: Optional[str] = Field(default=None, max_length=1000)
    ghi_chu_tu_dg_tien_do: Optional[str] = Field(default=None, max_length=1000)


class KeKhaiV2Create(KeKhaiV2Base):
    """Schema tạo mới kê khai V2."""

    @field_validator("ngay_thuc_hien")
    @classmethod
    def validate_ngay_thuc_hien(cls, v: Optional[date]) -> Optional[date]:
        if v and v > date.today():
            raise ValueError("Ngày thực hiện không được là ngày trong tương lai")
        return v


class KeKhaiV2Update(BaseModel):
    """Schema sửa kê khai V2 (chỉ NHAP/TU_CHOI). Tất cả fields optional."""

    model_config = ConfigDict(extra="forbid")

    danh_muc_sp_id: Optional[UUID] = None
    so_luong: Optional[int] = Field(default=None, gt=0)
    ngay_thuc_hien: Optional[date] = None
    mo_ta_cong_viec: Optional[str] = Field(default=None, max_length=2000)
    nguoi_phe_duyet_id: Optional[UUID] = None
    is_doi_moi_sang_tao: Optional[bool] = None
    ngay_deadline: Optional[date] = None
    ngay_hoan_thanh: Optional[date] = None
    tu_danh_gia_chat_luong: Optional[int] = Field(default=None, ge=0)
    tu_danh_gia_tien_do: Optional[int] = Field(default=None, ge=0)
    ghi_chu_tu_danh_gia: Optional[str] = Field(default=None, max_length=2000)
    ghi_chu_tu_dg_chat_luong: Optional[str] = Field(default=None, max_length=1000)
    ghi_chu_tu_dg_tien_do: Optional[str] = Field(default=None, max_length=1000)


class KeKhaiV2NhieuNgayCreate(BaseModel):
    """Tạo nhiều bản kê khai V2 cùng công việc cho nhiều ngày."""

    model_config = ConfigDict(extra="forbid")

    danh_muc_sp_id: UUID = Field(...)
    so_luong: int = Field(..., gt=0)
    ngay_thuc_hien_list: List[date] = Field(..., min_length=1, max_length=31)
    nguoi_phe_duyet_id: UUID = Field(...)
    mo_ta_cong_viec: Optional[str] = Field(default=None, max_length=2000)
    is_doi_moi_sang_tao: bool = Field(default=False)
    tu_danh_gia_chat_luong: int = Field(default=0, ge=0)
    tu_danh_gia_tien_do: int = Field(default=0, ge=0)
    ghi_chu_tu_danh_gia: Optional[str] = Field(default=None, max_length=2000)
    ghi_chu_tu_dg_chat_luong: Optional[str] = Field(default=None, max_length=1000)
    ghi_chu_tu_dg_tien_do: Optional[str] = Field(default=None, max_length=1000)

    @field_validator("ngay_thuc_hien_list")
    @classmethod
    def validate_ngay_list(cls, v: List[date]) -> List[date]:
        # Không trùng ngày
        if len(set(v)) != len(v):
            raise ValueError("Có ngày bị trùng trong danh sách")
        # Không tương lai
        for d in v:
            if d > date.today():
                raise ValueError(f"Ngày {d} là ngày tương lai")
        # Cùng tháng/năm
        first = v[0]
        for d in v[1:]:
            if d.month != first.month or d.year != first.year:
                raise ValueError("Tất cả ngày phải cùng tháng/năm")
        return v


# =============================================================================
# RESPONSE SCHEMAS
# =============================================================================

class DanhMucPL3BriefResponse(BaseModel):
    """Brief info của 1 mục PL3, kèm vào response kê khai."""

    id: UUID
    ma_danh_muc: str
    ten_cong_viec: str
    cong_viec_chi_tiet: Optional[str] = None
    san_pham_dau_ra: Optional[str] = None
    linh_vuc: Optional[str] = None
    ten_linh_vuc: Optional[str] = None
    nhom_pl3: Optional[int] = None
    khung_diem_toi_da: Optional[int] = None
    diem_cham: Optional[int] = None
    he_so_quy_doi: Optional[float] = None


class NguoiPheDuyetMini(BaseModel):
    """Brief info người phê duyệt — gắn vào response kê khai V2."""

    id: UUID
    ho_ten: str
    chuc_vu: Optional[str] = None


class KeKhaiV2Response(BaseModel):
    """Response cho 1 bản kê khai V2."""

    id: UUID
    cong_chuc_id: UUID
    thang: int
    nam: int
    ngay_thuc_hien: Optional[date] = None

    # Snapshot tại lúc tạo (immutable — LOCKED 13)
    version_kekhai: str  # luôn 'V2_PL3'
    he_so_quy_doi_snapshot: Optional[float] = None
    nhom_pl3_snapshot: Optional[int] = None
    linh_vuc_snapshot: Optional[str] = None

    # Mục PL3 (nested)
    danh_muc_sp: Optional[DanhMucPL3BriefResponse] = None

    so_luong: int
    nguoi_phe_duyet_id: Optional[UUID] = None
    nguoi_phe_duyet: Optional[NguoiPheDuyetMini] = None
    mo_ta_cong_viec: Optional[str] = None
    is_doi_moi_sang_tao: bool
    ngay_deadline: Optional[date] = None
    ngay_hoan_thanh: Optional[date] = None
    trang_thai: str

    # Tự đánh giá
    tu_danh_gia_chat_luong: int
    tu_danh_gia_tien_do: int
    ghi_chu_tu_danh_gia: Optional[str] = None
    ghi_chu_tu_dg_chat_luong: Optional[str] = None
    ghi_chu_tu_dg_tien_do: Optional[str] = None

    # Phản hồi LĐ (sau phê duyệt)
    so_loi_chat_luong: int
    so_loi_tien_do: int
    y_kien_lanh_dao: Optional[str] = None
    ghi_chu_loi_chat_luong: Optional[str] = None
    ghi_chu_loi_tien_do: Optional[str] = None

    # Quy đổi
    so_sp_goc_quy_doi: Optional[float] = None
    so_sp_chat_luong: Optional[float] = None
    so_sp_tien_do: Optional[float] = None

    is_khoa: bool
    created_at: datetime
    updated_at: datetime


class ThongKeKeKhaiV2Response(BaseModel):
    """Thống kê kê khai V2 theo tháng (cho banner UI + trang /danh-gia-v2)."""

    thang: int
    nam: int
    version_kekhai: str  # 'V2_PL3' hoặc 'V1' (nếu tháng đó là V1)
    # Tổng SP gốc quy đổi
    tong_sp_da_duyet: float
    tong_sp_cho_duyet: float
    tong_sp_du_kien: float  # da_duyet + cho_duyet + nhap
    # Tổng SP đạt CL/TĐ chính thức (chỉ DA_PHE_DUYET)
    tong_sp_chat_luong_da_duyet: float = 0.0
    tong_sp_tien_do_da_duyet: float = 0.0
    # Tổng SP tạm tính (NHAP + CHO + DA) — dùng cho tab Tạm tính trang đánh giá
    tong_sp_chat_luong_tam_tinh: float = 0.0
    tong_sp_tien_do_tam_tinh: float = 0.0
    # Số lượng kê khai
    so_kekhai_da_duyet: int
    so_kekhai_cho_duyet: int
    so_kekhai_nhap: int


class KeKhaiV2NhieuNgayResponse(BaseModel):
    """Response sau khi tạo nhiều ngày V2."""

    total_created: int
    ke_khai_ids: List[UUID]
    thang: int
    nam: int


# =============================================================================
# FAVORITES + RECENT (30/04/2026) — chỉ V2_PL3
# =============================================================================

class CongViecYeuThichCreate(BaseModel):
    """Body POST /favorites — mark 1 danh mục PL3 thành yêu thích."""

    model_config = ConfigDict(extra="forbid")

    danh_muc_sp_id: UUID = Field(..., description="ID mục PL3 cần đánh dấu")


class CongViecYeuThichResponse(BaseModel):
    """1 entry favorite, kèm danh mục nested để FE render trực tiếp."""

    id: UUID
    danh_muc_sp_id: UUID
    danh_muc_sp: DanhMucPL3BriefResponse
    created_at: datetime


class RecentDanhMucResponse(BaseModel):
    """1 mục đã dùng gần đây (look-back 3 tháng)."""

    danh_muc_sp_id: UUID
    danh_muc_sp: DanhMucPL3BriefResponse
    last_used_thang: int
    last_used_nam: int
    used_count_3m: int = Field(..., description="Số lần dùng trong 3 tháng look-back")
