"""
app/schemas/bao_cao_xep_loai_quy.py
====================================
Pydantic schemas cho Báo cáo Xếp loại Chất lượng Công chức theo Quý.

Bao gồm schemas cho:
- BaoCaoXepLoaiQuyResponse: Response chi tiết báo cáo quý
- ChiTietXepLoaiQuyResponse: Response chi tiết từng CC
- DeXuatXepLoaiQuyRequest: Request điều chỉnh xếp loại (Đội trưởng)
- QuyetDinhXepLoaiQuyRequest: Request điều chỉnh xếp loại (CCT)
- PheDuyetQuyRequest: Request phê duyệt/từ chối báo cáo quý

Phiên bản: 1.0 (16/04/2026)
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict, field_validator

# Import từ schemas bao_cao_xep_loai
from app.schemas.bao_cao_xep_loai import (
    TrangThaiBaoCaoEnum,
    XepLoaiEnum,
    DonViBrief,
    CongChucBrief,
)


# =============================================================================
# CHI TIẾT XẾP LOẠI QUÝ
# =============================================================================

class ChiTietXepLoaiQuyResponse(BaseModel):
    """Response chi tiết xếp loại quý của 1 công chức."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    cong_chuc_id: UUID
    cong_chuc: Optional[CongChucBrief] = None

    # Phân loại
    is_lanh_dao: bool = False

    # Điểm từ hệ thống (trung bình 3 tháng)
    diem_tieu_chi_chung: Decimal = Field(default=Decimal("0"), description="Điểm tiêu chí chung (0-30) - TB 3 tháng")
    diem_kpi: Decimal = Field(default=Decimal("0"), description="Điểm KPI (0-70) - TB 3 tháng")
    diem_tong: Decimal = Field(default=Decimal("0"), description="Điểm tổng (0-100) - TB 3 tháng")
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


class DeXuatXepLoaiQuyRequest(BaseModel):
    """
    Request điều chỉnh xếp loại đề xuất quý (Đội trưởng).

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


class QuyetDinhXepLoaiQuyRequest(BaseModel):
    """
    Request điều chỉnh xếp loại quyết định quý (CCT).

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
# BÁO CÁO XẾP LOẠI QUÝ
# =============================================================================

class BaoCaoXepLoaiQuyResponse(BaseModel):
    """Response chi tiết báo cáo xếp loại quý."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID

    # Thông tin báo cáo
    don_vi_id: UUID
    don_vi: Optional[DonViBrief] = None
    quy: int
    nam: int

    # Người lập
    nguoi_lap_id: UUID
    nguoi_lap: Optional[CongChucBrief] = None
    ngay_lap: Optional[datetime] = None

    # Gửi duyệt
    ngay_gui_duyet: Optional[datetime] = None

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
    chi_tiets: List[ChiTietXepLoaiQuyResponse] = []

    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class BaoCaoXepLoaiQuyBriefResponse(BaseModel):
    """Response tóm tắt báo cáo quý (cho danh sách)."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID

    # Thông tin báo cáo
    don_vi: Optional[DonViBrief] = None
    quy: int
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

class ThongKeBaoCaoQuy(BaseModel):
    """Thống kê xếp loại trong báo cáo quý."""
    tong_cong_chuc: int = 0
    so_loai_a: int = 0
    so_loai_b: int = 0
    so_loai_c: int = 0
    so_loai_d: int = 0
    so_loai_e: int = 0


class GuiDuyetBaoCaoQuyResponse(BaseModel):
    """Response sau khi gửi duyệt báo cáo quý."""
    id: UUID
    trang_thai: str
    ngay_lap: datetime
    canh_bao_ty_le_a: bool = False
    thong_ke: ThongKeBaoCaoQuy


class ChiTietTuChoiQuyItem(BaseModel):
    """Chi tiết từ chối 1 CC cụ thể trong báo cáo quý."""
    chi_tiet_id: UUID = Field(..., description="ID chi tiết xếp loại quý")
    ly_do: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Lý do từ chối"
    )


class PheDuyetQuyRequest(BaseModel):
    """
    Request phê duyệt/từ chối báo cáo quý (CCT).

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
    chi_tiet_tu_choi: Optional[List[ChiTietTuChoiQuyItem]] = Field(
        default=None,
        description="Danh sách CC bị từ chối (chỉ khi REJECT)"
    )

    @field_validator("action")
    @classmethod
    def validate_action(cls, v: str) -> str:
        if v not in ["APPROVE", "REJECT"]:
            raise ValueError("action phải là APPROVE hoặc REJECT")
        return v


class PheDuyetBaoCaoQuyResponse(BaseModel):
    """Response sau khi phê duyệt/từ chối báo cáo quý."""
    id: UUID
    trang_thai: str
    ngay_phe_duyet: Optional[datetime] = None
    so_cc_bi_tu_choi: int = 0


# =============================================================================
# THỐNG KÊ
# =============================================================================

class ThongKeXepLoaiDonViQuy(BaseModel):
    """Thống kê xếp loại quý của 1 đơn vị."""
    don_vi: DonViBrief
    tong: int = 0
    A: int = 0
    B: int = 0
    C: int = 0
    D: int = 0
    E: int = 0
    trang_thai: str = "CHUA_CO"  # Trạng thái báo cáo


class ThongKeXepLoaiChiCucQuy(BaseModel):
    """Thống kê xếp loại quý toàn Chi cục."""
    quy: int
    nam: int
    tong_cong_chuc: int = 0
    theo_xep_loai: dict = Field(
        default_factory=lambda: {"A": 0, "B": 0, "C": 0, "D": 0, "E": 0}
    )
    theo_don_vi: List[ThongKeXepLoaiDonViQuy] = []


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

TRANG_THAI_TEN_QUY = {
    "NHAP": "Đang soạn",
    "CHO_PHE_DUYET": "Chờ phê duyệt",
    "DA_PHE_DUYET": "Đã phê duyệt",
    "TU_CHOI": "Bị từ chối",
}


def get_trang_thai_ten_quy(trang_thai: str) -> str:
    """Lấy tên tiếng Việt của trạng thái báo cáo quý."""
    return TRANG_THAI_TEN_QUY.get(trang_thai, trang_thai)
