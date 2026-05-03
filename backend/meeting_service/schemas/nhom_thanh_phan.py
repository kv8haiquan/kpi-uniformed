"""Schemas cho nhóm thành phần dùng chung (meeting.nhom_thanh_phan).

3 nhóm schema:
- Nhóm: Create / Update / Response (CRUD bảng nhom_thanh_phan)
- Chi tiết: Add / Update / Response (CRUD bảng nhom_thanh_phan_chi_tiet)
- Merge: ThemTuNhomRequest / ThemTuNhomResponse (gộp nhóm vào cuộc họp)
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


VAI_TRO_VALUES = ["CHU_TRI", "THU_KY", "THANH_VIEN"]
LOAI_THAM_DU_VALUES = ["BAT_BUOC", "THAM_KHAO"]


# ───────────────────────────────────────────────────────────────────
# CHI TIẾT (thành viên trong nhóm)
# ───────────────────────────────────────────────────────────────────

class ChiTietCreate(BaseModel):
    """Dùng cho cả tạo nhóm (kèm danh sách) và POST /thanh-vien."""
    cong_chuc_id: UUID
    vai_tro: str = Field(default="THANH_VIEN")
    loai_tham_du: str = Field(default="BAT_BUOC")

    @field_validator("vai_tro")
    @classmethod
    def _check_vai_tro(cls, v: str) -> str:
        if v not in VAI_TRO_VALUES:
            raise ValueError(f"vai_tro must be one of {VAI_TRO_VALUES}")
        return v

    @field_validator("loai_tham_du")
    @classmethod
    def _check_loai(cls, v: str) -> str:
        if v not in LOAI_THAM_DU_VALUES:
            raise ValueError(f"loai_tham_du must be one of {LOAI_THAM_DU_VALUES}")
        return v


class ChiTietUpdate(BaseModel):
    """PUT /nhom-thanh-phan/{id}/thanh-vien/{cc_id} — sửa vai_tro/loai_tham_du."""
    vai_tro: Optional[str] = None
    loai_tham_du: Optional[str] = None

    @field_validator("vai_tro")
    @classmethod
    def _check_vai_tro(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in VAI_TRO_VALUES:
            raise ValueError(f"vai_tro must be one of {VAI_TRO_VALUES}")
        return v

    @field_validator("loai_tham_du")
    @classmethod
    def _check_loai(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in LOAI_THAM_DU_VALUES:
            raise ValueError(f"loai_tham_du must be one of {LOAI_THAM_DU_VALUES}")
        return v


class ChiTietResponse(BaseModel):
    """Item chi tiết — kèm thông tin CBCC để FE hiển thị tên/mã/đơn vị."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    nhom_id: UUID
    cong_chuc_id: UUID
    vai_tro: str
    loai_tham_du: str
    created_at: datetime

    # JOIN từ public.cong_chuc — service tự bind
    ho_ten: Optional[str] = None
    ma_cc: Optional[str] = None
    don_vi_id: Optional[UUID] = None
    ten_don_vi: Optional[str] = None
    chuc_vu: Optional[str] = None


# ───────────────────────────────────────────────────────────────────
# NHÓM
# ───────────────────────────────────────────────────────────────────

class NhomCreate(BaseModel):
    ten_nhom: str = Field(..., min_length=1, max_length=200)
    mo_ta: Optional[str] = None
    loai_nhom: Optional[str] = Field(None, max_length=100)
    chi_tiet: list[ChiTietCreate] = Field(default_factory=list)


class NhomUpdate(BaseModel):
    ten_nhom: Optional[str] = Field(None, min_length=1, max_length=200)
    mo_ta: Optional[str] = None
    loai_nhom: Optional[str] = Field(None, max_length=100)


class NhomListItem(BaseModel):
    """1 row trong list view — kèm so_thanh_vien để FE hiển thị nhanh."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    ten_nhom: str
    mo_ta: Optional[str] = None
    loai_nhom: Optional[str] = None
    nguoi_tao_id: UUID
    created_at: datetime
    updated_at: datetime
    so_thanh_vien: int = 0
    # Hỗ trợ FE hiển thị tên người tạo
    nguoi_tao_ho_ten: Optional[str] = None


class NhomResponse(BaseModel):
    """Chi tiết 1 nhóm — kèm full danh sách thành viên."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    ten_nhom: str
    mo_ta: Optional[str] = None
    loai_nhom: Optional[str] = None
    nguoi_tao_id: UUID
    created_at: datetime
    updated_at: datetime
    chi_tiet: list[ChiTietResponse] = Field(default_factory=list)


# ───────────────────────────────────────────────────────────────────
# MERGE — them thành phần từ nhóm vào cuộc họp
# ───────────────────────────────────────────────────────────────────

class ThemTuNhomRequest(BaseModel):
    """POST /cuoc-hop/{id}/thanh-phan/them-tu-nhom — body."""
    nhom_ids: list[UUID] = Field(..., min_length=1)


class ThemTuNhomResponse(BaseModel):
    """Kết quả gộp — báo về số thành viên đã thêm / bỏ qua / auto-fill."""
    so_them: int
    so_bo_qua_trung: int
    tong_thanh_phan: int
    chu_toa_auto_filled: bool = False
    thu_ky_auto_filled: bool = False


# ───────────────────────────────────────────────────────────────────
# BATCH — thêm nhiều thành viên 1 lần
# ───────────────────────────────────────────────────────────────────

class ChiTietBatchRequest(BaseModel):
    """POST /nhom-thanh-phan/{id}/thanh-vien/batch — body.

    Skip cong_chuc đã có sẵn (không 409) — trả số đã thêm + bỏ qua.
    Trùng cong_chuc_id giữa các item trong cùng request → cũng skip.
    """
    chi_tiet: list[ChiTietCreate] = Field(..., min_length=1)


class ChiTietBatchResponse(BaseModel):
    so_them: int
    so_bo_qua_trung: int
    tong_thanh_vien: int
