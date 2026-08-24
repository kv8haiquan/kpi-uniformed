"""
lms_service/schemas/cau_truc_de_template.py
===========================================
Pydantic schemas cho mau cau truc de thi DGNL.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CauTrucDeTemplateItem(BaseModel):
    """1 dong cau truc trong template."""
    vi_tri_id: UUID
    linh_vuc_id: UUID
    so_cau_de: int = Field(default=0, ge=0)
    so_cau_trung_binh: int = Field(default=0, ge=0)
    so_cau_kho: int = Field(default=0, ge=0)


class CauTrucDeTemplateCreate(BaseModel):
    """Schema tao template moi."""
    ten_template: str = Field(..., min_length=1, max_length=200)
    mo_ta: Optional[str] = None
    cau_truc: list[CauTrucDeTemplateItem] = Field(..., min_length=1)


class CauTrucDeTemplateUpdate(BaseModel):
    """Schema sua mau truc tiep (tab Mau cau truc de).

    Moi field deu optional — chi gui field can doi. Rieng `cau_truc` neu gui thi
    THAY THE toan bo danh sach dong (client gui anh chup day du sau khi sua).
    """
    ten_template: Optional[str] = Field(default=None, min_length=1, max_length=200)
    mo_ta: Optional[str] = None
    cau_truc: Optional[list[CauTrucDeTemplateItem]] = Field(default=None, min_length=1)


class CauTrucDeTemplateNhanBan(BaseModel):
    """Schema nhan ban mau — chi can ten moi."""
    ten_template: str = Field(..., min_length=1, max_length=200)
    mo_ta: Optional[str] = None


class CauTrucDeTemplateResponse(BaseModel):
    """Response 1 template."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    ten_template: str
    mo_ta: Optional[str] = None
    nguoi_tao_id: UUID
    nguoi_tao_ho_ten: Optional[str] = None
    cau_truc: list = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
