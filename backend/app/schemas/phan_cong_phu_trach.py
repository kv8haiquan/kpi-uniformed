"""
app/schemas/phan_cong_phu_trach.py
==================================
Pydantic schemas cho phân công CCT/PCCT phụ trách đơn vị.
"""

from datetime import date
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


# =============================================================================
# BRIEF SCHEMAS (cho relationship)
# =============================================================================

class CongChucBrief(BaseModel):
    """Thông tin tóm tắt CongChuc dùng trong response."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    ma_cc: str
    ho_ten: str
    chuc_vu: Optional[str] = None


class DonViBrief(BaseModel):
    """Thông tin tóm tắt DonVi dùng trong response."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    ma_don_vi: str
    ten_don_vi: str


# =============================================================================
# REQUEST SCHEMAS
# =============================================================================

class PhanCongCreate(BaseModel):
    """Tạo phân công mới."""
    lanh_dao_id: UUID = Field(..., description="ID LĐ phụ trách (CCT hoặc PCCT)")
    don_vi_id: UUID = Field(..., description="ID đơn vị được phụ trách")
    hieu_luc_tu: date = Field(..., description="Ngày bắt đầu hiệu lực")
    hieu_luc_den: Optional[date] = Field(
        default=None, description="Ngày kết thúc (NULL = vẫn còn hiệu lực)"
    )
    ghi_chu: Optional[str] = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def _check_dates(self) -> "PhanCongCreate":
        if self.hieu_luc_den is not None and self.hieu_luc_den < self.hieu_luc_tu:
            raise ValueError("hieu_luc_den phải >= hieu_luc_tu")
        return self


class PhanCongUpdate(BaseModel):
    """Cập nhật phân công (chỉ cho phép sửa hiệu lực + ghi chú)."""
    hieu_luc_den: Optional[date] = Field(default=None)
    ghi_chu: Optional[str] = Field(default=None, max_length=2000)


class PhanCongKetThucRequest(BaseModel):
    """Kết thúc phân công tại 1 ngày cụ thể."""
    hieu_luc_den: date = Field(..., description="Ngày kết thúc hiệu lực")


# =============================================================================
# RESPONSE SCHEMAS
# =============================================================================

class PhanCongResponse(BaseModel):
    """Response 1 phân công."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    lanh_dao_id: UUID
    don_vi_id: UUID
    hieu_luc_tu: date
    hieu_luc_den: Optional[date] = None
    ghi_chu: Optional[str] = None
    is_deleted: bool

    # Eager-loaded
    lanh_dao: Optional[CongChucBrief] = None
    don_vi: Optional[DonViBrief] = None
