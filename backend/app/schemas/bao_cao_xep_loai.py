"""
app/schemas/bao_cao_xep_loai.py
===============================
Pydantic schemas cho Báo cáo Xếp loại Chất lượng Công chức.

Bao gồm schemas cho:
- BaoCaoXepLoaiResponse: Response chi tiết báo cáo
- ChiTietXepLoaiResponse: Response chi tiết từng CC
- DeXuatXepLoaiRequest: Request điều chỉnh xếp loại (Đội trưởng)
- QuyetDinhXepLoaiRequest: Request điều chỉnh xếp loại (CCT)
- PheDuyetBaoCaoRequest: Request phê duyệt/từ chối báo cáo

Phiên bản: 1.0 (28/01/2026)
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict, field_validator


# =============================================================================
# ENUMS
# =============================================================================

class TrangThaiBaoCaoEnum(str, Enum):
    """Trạng thái báo cáo."""
    NHAP = "NHAP"
    CHO_PHE_DUYET = "CHO_PHE_DUYET"
    DA_PHE_DUYET = "DA_PHE_DUYET"
    TU_CHOI = "TU_CHOI"


class XepLoaiEnum(str, Enum):
    """Mức xếp loại chất lượng."""
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    E = "E"


# =============================================================================
# NESTED SCHEMAS
# =============================================================================

class DonViBrief(BaseModel):
    """Thông tin tóm tắt đơn vị."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    ma_don_vi: str
    ten_don_vi: str


class CongChucBrief(BaseModel):
    """Thông tin tóm tắt công chức."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    ma_cc: str
    ho_ten: str
    chuc_vu: Optional[str] = None


class ThongKeBaoCao(BaseModel):
    """Thống kê xếp loại trong báo cáo."""
    tong_cong_chuc: int = 0
    so_loai_a: int = 0
    so_loai_b: int = 0
    so_loai_c: int = 0
    so_loai_d: int = 0
    so_loai_e: int = 0


# =============================================================================
# CHI TIẾT XẾP LOẠI
# =============================================================================

class ChiTietXepLoaiResponse(BaseModel):
    """Response chi tiết xếp loại của 1 công chức."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    cong_chuc_id: UUID
    cong_chuc: Optional[CongChucBrief] = None
    
    # Phân loại
    is_lanh_dao: bool = False
    
    # Điểm từ hệ thống
    diem_tieu_chi_chung: Decimal = Field(default=Decimal("0"), description="Điểm tiêu chí chung (0-30)")
    diem_kpi: Decimal = Field(default=Decimal("0"), description="Điểm KPI (0-70)")
    diem_tong: Decimal = Field(default=Decimal("0"), description="Điểm tổng (0-100)")
    xep_loai_he_thong: str = Field(description="Xếp loại hệ thống tự tính")
    
    # Đề xuất của Đội trưởng
    xep_loai_de_xuat: Optional[str] = None
    ly_do_dieu_chinh_dt: Optional[str] = None
    
    # Quyết định của CCT
    xep_loai_quyet_dinh: Optional[str] = None
    ly_do_dieu_chinh_cct: Optional[str] = None
    
    # Trạng thái từ chối
    bi_tu_choi: bool = False
    ly_do_tu_choi: Optional[str] = None
    
    # Ghi chú
    ghi_chu: Optional[str] = None


class DeXuatXepLoaiRequest(BaseModel):
    """
    Request điều chỉnh xếp loại đề xuất (Đội trưởng).
    
    Validation:
    - Nếu xep_loai_de_xuat != xep_loai_he_thong → ly_do_dieu_chinh BẮT BUỘC
    """
    xep_loai_de_xuat: XepLoaiEnum = Field(
        ...,
        description="Mức xếp loại đề xuất (A/B/C/D/E)"
    )
    ly_do_dieu_chinh: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="Lý do điều chỉnh (bắt buộc nếu khác hệ thống)"
    )
    ghi_chu: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Ghi chú bổ sung"
    )


class QuyetDinhXepLoaiRequest(BaseModel):
    """
    Request điều chỉnh xếp loại quyết định (CCT).
    
    Validation:
    - Nếu xep_loai_quyet_dinh != xep_loai_de_xuat → ly_do_dieu_chinh BẮT BUỘC
    """
    xep_loai_quyet_dinh: XepLoaiEnum = Field(
        ...,
        description="Mức xếp loại quyết định (A/B/C/D/E)"
    )
    ly_do_dieu_chinh: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="Lý do điều chỉnh (bắt buộc nếu khác đề xuất)"
    )


# =============================================================================
# BÁO CÁO XẾP LOẠI
# =============================================================================

class BaoCaoXepLoaiResponse(BaseModel):
    """Response chi tiết báo cáo xếp loại."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    
    # Thông tin báo cáo
    don_vi_id: UUID
    don_vi: Optional[DonViBrief] = None
    thang: int
    nam: int
    
    # Người lập
    nguoi_lap_id: UUID
    nguoi_lap: Optional[CongChucBrief] = None
    ngay_lap: Optional[datetime] = None
    
    # Trạng thái
    trang_thai: str
    trang_thai_ten: str = Field(default="", description="Tên tiếng Việt của trạng thái")
    
    # Phê duyệt
    nguoi_phe_duyet_id: Optional[UUID] = None
    nguoi_phe_duyet: Optional[CongChucBrief] = None
    ngay_phe_duyet: Optional[datetime] = None
    y_kien_phe_duyet: Optional[str] = None
    
    # Thống kê
    tong_cong_chuc: int = 0
    so_loai_a: int = 0
    so_loai_b: int = 0
    so_loai_c: int = 0
    so_loai_d: int = 0
    so_loai_e: int = 0
    canh_bao_ty_le_a: bool = False
    
    # Chi tiết
    chi_tiet: List[ChiTietXepLoaiResponse] = []
    
    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class BaoCaoXepLoaiBriefResponse(BaseModel):
    """Response tóm tắt báo cáo (cho danh sách)."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    
    # Thông tin báo cáo
    don_vi: Optional[DonViBrief] = None
    thang: int
    nam: int
    
    # Người lập
    nguoi_lap: Optional[CongChucBrief] = None
    ngay_lap: Optional[datetime] = None
    
    # Trạng thái
    trang_thai: str
    
    # Thống kê
    tong_cong_chuc: int = 0
    so_loai_a: int = 0
    so_loai_b: int = 0
    so_loai_c: int = 0
    so_loai_d: int = 0
    so_loai_e: int = 0
    canh_bao_ty_le_a: bool = False


# =============================================================================
# GỬI DUYỆT & PHÊ DUYỆT
# =============================================================================

class GuiDuyetBaoCaoResponse(BaseModel):
    """Response sau khi gửi duyệt báo cáo."""
    id: UUID
    trang_thai: str
    ngay_lap: datetime
    canh_bao_ty_le_a: bool = False
    thong_ke: ThongKeBaoCao


class ChiTietTuChoiItem(BaseModel):
    """Chi tiết từ chối 1 CC cụ thể."""
    chi_tiet_id: UUID = Field(..., description="ID chi tiết xếp loại")
    ly_do: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Lý do từ chối"
    )


class PheDuyetBaoCaoRequest(BaseModel):
    """
    Request phê duyệt/từ chối báo cáo (CCT).
    
    Logic:
    - APPROVE: Phê duyệt toàn bộ báo cáo
    - REJECT: Từ chối, có thể chỉ định danh sách CC bị từ chối
    """
    action: str = Field(
        ...,
        description="APPROVE hoặc REJECT"
    )
    y_kien: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="Ý kiến của CCT"
    )
    chi_tiet_tu_choi: Optional[List[ChiTietTuChoiItem]] = Field(
        default=None,
        description="Danh sách CC bị từ chối (chỉ khi REJECT)"
    )
    
    @field_validator("action")
    @classmethod
    def validate_action(cls, v: str) -> str:
        if v not in ["APPROVE", "REJECT"]:
            raise ValueError("action phải là APPROVE hoặc REJECT")
        return v


class PheDuyetBaoCaoResponse(BaseModel):
    """Response sau khi phê duyệt/từ chối báo cáo."""
    id: UUID
    trang_thai: str
    ngay_phe_duyet: Optional[datetime] = None
    so_cc_bi_tu_choi: int = 0


# =============================================================================
# THỐNG KÊ
# =============================================================================

class ThongKeXepLoaiDonVi(BaseModel):
    """Thống kê xếp loại của 1 đơn vị."""
    don_vi: DonViBrief
    tong: int = 0
    A: int = 0
    B: int = 0
    C: int = 0
    D: int = 0
    E: int = 0
    trang_thai: str = "CHUA_CO"  # Trạng thái báo cáo


class ThongKeXepLoaiChiCuc(BaseModel):
    """Thống kê xếp loại toàn Chi cục."""
    thang: int
    nam: int
    tong_cong_chuc: int = 0
    theo_xep_loai: dict = Field(
        default_factory=lambda: {"A": 0, "B": 0, "C": 0, "D": 0, "E": 0}
    )
    theo_don_vi: List[ThongKeXepLoaiDonVi] = []


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

TRANG_THAI_TEN = {
    "NHAP": "Đang soạn",
    "CHO_PHE_DUYET": "Chờ phê duyệt",
    "DA_PHE_DUYET": "Đã phê duyệt",
    "TU_CHOI": "Bị từ chối",
}


def get_trang_thai_ten(trang_thai: str) -> str:
    """Lấy tên tiếng Việt của trạng thái."""
    return TRANG_THAI_TEN.get(trang_thai, trang_thai)
