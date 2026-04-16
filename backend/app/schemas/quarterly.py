"""
app/schemas/quarterly.py
=========================
Pydantic schemas cho Đánh giá quý (Quarterly Assessment).

PHIÊN BẢN: 3.6.0 (14/04/2026)

Schemas:
- DanhGiaQuyResponse: Kết quả đánh giá quý của 1 công chức
- TongHopQuyResponse: Danh sách tổng hợp quý (cho ĐT/CCT)
- ChiTietQuyResponse: Chi tiết 3 tháng trong quý
- ThongKeQuyResponse: Thống kê phân bổ xếp loại

Công thức tính điểm quý:
- diem_kpi_quy = TB((diem_kpi × 70) của 3 tháng)
- diem_tc_quy = trung bình điểm TC 3 tháng (luôn chia 3, thiếu tính 0)
- diem_tong_quy = diem_kpi_quy + diem_tc_quy
- xep_loai_quy = xep_loai_kpi(diem_tong_quy)
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict

from app.schemas.master_data import CongChucBriefResponse, DonViResponse


# =============================================================================
# RESPONSE SCHEMAS
# =============================================================================

class DanhGiaThangTrongQuy(BaseModel):
    """Chi tiết đánh giá 1 tháng trong quý."""
    model_config = ConfigDict(from_attributes=True)

    thang: int
    diem_kpi: float = Field(0.0, description="Điểm KPI tháng (scale 0-70, đã nhân)")
    diem_tc: float = Field(0.0, description="Điểm tiêu chí chung tháng (0-30)")
    diem_tong: float = Field(0.0, description="Điểm tổng tháng (0-100)")
    xep_loai_thang: Optional[str] = Field(None, description="Xếp loại tháng (từ báo cáo)")
    co_du_lieu: bool = Field(False, description="Có báo cáo tháng đã gửi duyệt/đã duyệt")
    nguon: Optional[str] = Field(None, description="Nguồn dữ liệu: 'DA_PHE_DUYET' | 'CHO_PHE_DUYET' | 'real_time' | null")


class DiemTCThangItem(BaseModel):
    """Điểm tiêu chí chung của 1 tháng trong quý."""
    thang: int
    diem_tc: float = Field(0.0, description="Điểm tiêu chí chung tháng (0-30)")


class ChiTietQuyResponse(BaseModel):
    """Chi tiết đánh giá quý của 1 công chức (3 tháng + tiêu chí)."""
    model_config = ConfigDict(from_attributes=True)

    cong_chuc_id: UUID
    cong_chuc: Optional[CongChucBriefResponse] = None
    don_vi: Optional[DonViResponse] = None
    quy: int
    nam: int

    # Chi tiết 3 tháng
    cac_thang: List[DanhGiaThangTrongQuy] = Field(default_factory=list)

    # Tiêu chí chung quý (trung bình 3 tháng)
    tieu_chi_quy: List[DiemTCThangItem] = Field(default_factory=list)

    # Điểm tổng hợp quý
    diem_kpi_quy: Optional[float] = None
    diem_tc_quy: Optional[float] = None
    diem_tong_quy: Optional[float] = None
    xep_loai_quy: Optional[str] = None

    # Edge cases
    co_chuyen_don_vi: bool = False
    ghi_chu: Optional[str] = None


class DanhGiaQuyResponse(BaseModel):
    """Kết quả đánh giá quý của 1 công chức (tóm tắt)."""
    model_config = ConfigDict(from_attributes=True)

    id: Optional[UUID] = None
    cong_chuc_id: UUID
    cong_chuc: Optional[CongChucBriefResponse] = None
    don_vi: Optional[DonViResponse] = None

    quy: int
    nam: int

    diem_kpi_quy: Optional[float] = Field(None, description="Điểm KPI quý (0-70)")
    diem_tc_quy: Optional[float] = Field(None, description="Điểm TC quý (0-30)")
    diem_tong_quy: Optional[float] = Field(None, description="Điểm tổng quý (0-100)")
    xep_loai_quy: Optional[str] = Field(None, description="Xếp loại A/B/C/D")

    co_chuyen_don_vi: bool = False
    ghi_chu: Optional[str] = None

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class TongHopQuyItem(BaseModel):
    """1 dòng trong danh sách tổng hợp quý."""
    stt: int
    cong_chuc_id: UUID
    ma_cc: str
    ho_ten: str
    don_vi_ten: str
    is_lanh_dao: bool

    diem_kpi_quy: Optional[float] = None
    diem_tc_quy: Optional[float] = None
    diem_tong_quy: Optional[float] = None
    xep_loai_quy: Optional[str] = None

    co_chuyen_don_vi: bool = False
    ghi_chu: Optional[str] = None


class ThongKeQuyResponse(BaseModel):
    """Thống kê phân bổ xếp loại quý."""
    tong_so_cc: int = 0
    so_luong_A: int = 0
    so_luong_B: int = 0
    so_luong_C: int = 0
    so_luong_D: int = 0
    so_luong_chua_tinh: int = 0

    ty_le_A: float = 0.0
    ty_le_B: float = 0.0
    ty_le_C: float = 0.0
    ty_le_D: float = 0.0


class TongHopQuyResponse(BaseModel):
    """Response cho endpoint GET /tong-hop (danh sách)."""
    data: List[TongHopQuyItem]
    thong_ke: ThongKeQuyResponse
    pagination: dict


# =============================================================================
# REQUEST SCHEMAS
# =============================================================================

class TinhLaiQuyRequest(BaseModel):
    """Request tính lại điểm quý (admin)."""
    quy: int = Field(..., ge=1, le=4, description="Quý (1-4)")
    nam: int = Field(..., ge=2025, description="Năm")
    don_vi_id: Optional[UUID] = Field(None, description="Tính lại cho 1 đơn vị, NULL = tất cả")
    cong_chuc_id: Optional[UUID] = Field(None, description="Tính lại cho 1 CC, NULL = tất cả")
