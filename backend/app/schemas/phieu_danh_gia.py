"""
app/schemas/phieu_danh_gia.py
==============================
Pydantic schemas cho phiếu theo dõi, đánh giá công chức theo QUÝ (Mẫu 01A/01B).

Phiên bản: 1.0.0 (17/04/2026)
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# =============================================================================
# REQUEST SCHEMAS
# =============================================================================

class UpsertPhieuQuyRequest(BaseModel):
    """Tạo mới hoặc cập nhật phiếu nháp của CC (mục 4 & 5)."""

    quy: int = Field(..., ge=1, le=4, description="Quý (1-4)")
    nam: int = Field(..., ge=2020, le=2100, description="Năm")
    uu_diem: Optional[str] = Field(None, description="Mục 4: Ưu điểm")
    han_che: Optional[str] = Field(None, description="Mục 5: Hạn chế, khuyết điểm")


class PheDuyetPhieuRequest(BaseModel):
    """TDV/CCT duyệt phiếu: chấp nhận + nhập ý kiến mục 6."""

    y_kien_lanh_dao: Optional[str] = Field(
        None,
        description="Mục 6: Ý kiến nhận xét của cấp có thẩm quyền",
    )


class TuChoiPhieuRequest(BaseModel):
    """TDV/CCT từ chối phiếu: bắt buộc nhập lý do."""

    ly_do_tu_choi: str = Field(..., min_length=1, description="Lý do từ chối")


# =============================================================================
# RESPONSE SCHEMAS
# =============================================================================

class NguoiKyResponse(BaseModel):
    """Tóm tắt CC (để hiển thị ô Công chức / Cấp có thẩm quyền)."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    ma_cc: str
    ho_ten: str
    chuc_vu: Optional[str] = None


class PhieuDanhGiaQuyResponse(BaseModel):
    """Chi tiết phiếu đánh giá quý."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    cong_chuc_id: UUID
    cong_chuc: Optional[NguoiKyResponse] = None

    quy: int
    nam: int

    uu_diem: Optional[str] = None
    han_che: Optional[str] = None
    y_kien_lanh_dao: Optional[str] = None

    trang_thai: str = Field(..., description="NHAP | CHO_PHE_DUYET | DA_PHE_DUYET | BI_TU_CHOI")
    ngay_gui_duyet: Optional[datetime] = None

    nguoi_phe_duyet_id: Optional[UUID] = None
    nguoi_phe_duyet: Optional[NguoiKyResponse] = None
    ngay_phe_duyet: Optional[datetime] = None
    ly_do_tu_choi: Optional[str] = None

    created_at: datetime
    updated_at: datetime


class PhieuChoPheDuyetItem(BaseModel):
    """1 dòng trong danh sách phiếu chờ duyệt (TDV/CCT)."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    cong_chuc_id: UUID
    ma_cc: str
    ho_ten: str
    chuc_vu: Optional[str] = None
    don_vi_ten: Optional[str] = None
    quy: int
    nam: int
    trang_thai: str
    ngay_gui_duyet: Optional[datetime] = None
    uu_diem: Optional[str] = None
    han_che: Optional[str] = None
