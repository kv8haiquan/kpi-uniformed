"""
app/schemas/admin_pl3.py
========================
Pydantic schemas cho Admin CRUD danh mục PL3 (Phase C — 28/04/2026).

Form admin chỉ nhập 5 trường nghiệp vụ chính:
  - ten_cong_viec, linh_vuc, nhom_pl3, diem_cham, (nhiem_vu/cong_viec_chi_tiet/san_pham_dau_ra optional)

Backend tự compute:
  - he_so_quy_doi = diem_cham / 25
  - khung_diem_toi_da = {1:100, 2:200, 3:300, 4:400, 5:500}[nhom_pl3]
  - ten_linh_vuc = lookup từ data đã có (DanhMucSpCongViec với linh_vuc=X)

Quyết định nghiệp vụ Phase A: 4 cột chấm chi tiết đã DROP, không lưu nữa.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


VALID_LINH_VUC = {
    "I", "II", "III", "IV", "V", "VI", "VII", "VIII",
    "IX", "X", "XI", "XII", "XIII", "XIV", "XV",
}

NHOM_KHUNG_MAP = {1: 100, 2: 200, 3: 300, 4: 400, 5: 500}


class DanhMucPL3CreateRequest(BaseModel):
    """Tạo mới mục PL3 (admin form)."""

    model_config = ConfigDict(extra="forbid")

    # Mã unique do admin gửi (vd: PL3-I-CUSTOM-001). Phải ≤ 30 chars.
    ma_danh_muc: str = Field(..., min_length=4, max_length=30, pattern=r"^PL3-[A-Z]+-.+$")

    ten_cong_viec: str = Field(..., min_length=3, max_length=500)
    linh_vuc: str = Field(..., min_length=1, max_length=10)
    nhom_pl3: int = Field(..., ge=1, le=5)
    diem_cham: int = Field(..., gt=0, le=500)

    nhiem_vu: Optional[str] = Field(default=None, max_length=500)
    cong_viec_chi_tiet: Optional[str] = Field(default=None)
    san_pham_dau_ra: Optional[str] = Field(default=None)
    mo_ta: Optional[str] = Field(default=None)

    is_active: bool = Field(default=True)

    @field_validator("linh_vuc")
    @classmethod
    def validate_linh_vuc(cls, v: str) -> str:
        v = v.upper().strip()
        if v not in VALID_LINH_VUC:
            raise ValueError(f"linh_vuc phải thuộc {sorted(VALID_LINH_VUC)}")
        return v

    @field_validator("diem_cham")
    @classmethod
    def validate_diem_cham_in_range(cls, v: int, info) -> int:
        # Cross-field: diem_cham phải ≤ khung của nhóm
        nhom = info.data.get("nhom_pl3")
        if nhom is not None:
            khung = NHOM_KHUNG_MAP.get(nhom)
            if khung and v > khung:
                raise ValueError(
                    f"diem_cham={v} vượt khung của Nhóm {nhom} (max {khung})"
                )
        return v


class DanhMucPL3UpdateRequest(BaseModel):
    """Sửa mục PL3 (tất cả optional)."""

    model_config = ConfigDict(extra="forbid")

    ten_cong_viec: Optional[str] = Field(default=None, min_length=3, max_length=500)
    linh_vuc: Optional[str] = Field(default=None, min_length=1, max_length=10)
    nhom_pl3: Optional[int] = Field(default=None, ge=1, le=5)
    diem_cham: Optional[int] = Field(default=None, gt=0, le=500)

    nhiem_vu: Optional[str] = Field(default=None, max_length=500)
    cong_viec_chi_tiet: Optional[str] = Field(default=None)
    san_pham_dau_ra: Optional[str] = Field(default=None)
    mo_ta: Optional[str] = Field(default=None)

    is_active: Optional[bool] = None

    @field_validator("linh_vuc")
    @classmethod
    def validate_linh_vuc(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        v = v.upper().strip()
        if v not in VALID_LINH_VUC:
            raise ValueError(f"linh_vuc phải thuộc {sorted(VALID_LINH_VUC)}")
        return v


class DanhMucPL3Response(BaseModel):
    """Response 1 mục PL3."""

    id: UUID
    ma_danh_muc: str
    ten_cong_viec: str
    mo_ta: Optional[str] = None
    nguon_du_lieu: str

    linh_vuc: Optional[str] = None
    ten_linh_vuc: Optional[str] = None
    nhiem_vu: Optional[str] = None
    cong_viec_chi_tiet: Optional[str] = None
    san_pham_dau_ra: Optional[str] = None
    nhom_pl3: Optional[int] = None
    khung_diem_toi_da: Optional[int] = None
    diem_cham: Optional[int] = None
    he_so_quy_doi: Optional[float] = None
    is_active: bool

    created_at: datetime
    updated_at: datetime


# =============================================================================
# kpi_version_pinned (Task C.4)
# =============================================================================

class KpiVersionPinRequest(BaseModel):
    """Set kpi_version_pinned cho 1 CC hoặc bulk cho 1 đơn vị."""

    model_config = ConfigDict(extra="forbid")

    # None = unpin (dùng platform_config default).
    # 'V1' hoặc 'V2_PL3' = pin cụ thể.
    kpi_version_pinned: Optional[str] = Field(default=None)

    @field_validator("kpi_version_pinned")
    @classmethod
    def validate_version(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        if v not in ("V1", "V2_PL3"):
            raise ValueError("kpi_version_pinned phải là 'V1', 'V2_PL3' hoặc null")
        return v


# =============================================================================
# Excel import (Task C.2)
# =============================================================================

class ExcelImportError(BaseModel):
    """1 lỗi parse/validate trong import Excel."""

    row: int
    ma_danh_muc: Optional[str] = None
    error: str


class ExcelImportSummary(BaseModel):
    """Tổng kết import Excel (dry-run hoặc commit)."""

    total_rows_in_file: int
    valid: int
    invalid: int
    will_insert: int
    will_update: int
    skipped: int


class ExcelImportPreviewRow(BaseModel):
    """Preview 1 row sẽ insert/update."""

    ma_danh_muc: str
    ten_cong_viec: str
    linh_vuc: str
    nhom_pl3: int
    diem_cham: int
    he_so_quy_doi: float
    action: str  # 'insert' hoặc 'update'


class ExcelImportResponse(BaseModel):
    """Response cho dry-run hoặc commit."""

    summary: ExcelImportSummary
    errors: list[ExcelImportError]
    preview: list[ExcelImportPreviewRow]
    is_dry_run: bool
    file_hash: Optional[str] = None
