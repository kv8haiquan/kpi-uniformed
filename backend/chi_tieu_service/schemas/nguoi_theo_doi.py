"""
chi_tieu_service/schemas/nguoi_theo_doi.py
==========================================
Schemas quan ly nguoi theo doi chi tieu (gan platform_role THEO_DOI_CHI_TIEU).
"""

from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field

# Chi cho phep gan 2 role cua module chi tieu
RoleChiTieu = Literal["THEO_DOI_CHI_TIEU", "QT_CHI_TIEU"]


class GanNguoiTheoDoiRequest(BaseModel):
    cong_chuc_id: UUID
    don_vi_ids: list[UUID] = Field(default_factory=list)
    role: RoleChiTieu = "THEO_DOI_CHI_TIEU"


class CapNhatPhamViRequest(BaseModel):
    don_vi_ids: list[UUID] = Field(default_factory=list)
    role: RoleChiTieu = "THEO_DOI_CHI_TIEU"


class NguoiTheoDoiItem(BaseModel):
    cong_chuc_id: UUID
    ma_cc: Optional[str] = None
    ho_ten: Optional[str] = None
    chuc_vu: Optional[str] = None
    don_vi_cong_chuc: Optional[str] = None
    role: str
    don_vi_ids: list[str] = Field(default_factory=list)
    is_active: bool = True


class CongChucSearchItem(BaseModel):
    id: UUID
    ma_cc: Optional[str] = None
    ho_ten: Optional[str] = None
    chuc_vu: Optional[str] = None
    don_vi_id: Optional[UUID] = None
    ten_don_vi: Optional[str] = None
