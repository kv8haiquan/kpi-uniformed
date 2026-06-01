"""
app/schemas/hdld.py
===================
Pydantic schemas (DTO) cho Bộ tiêu chí đánh giá HĐLĐ 111 theo VB714.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


NHOM_HOP_LE = {'I', 'II', 'III', 'IV', 'V', 'VI'}


# ============================ DANH MỤC TIÊU CHÍ ============================ #

class HdldTieuChiResponse(BaseModel):
    id: UUID
    nhom: str
    ten_nhom: str
    so_tt: int
    ten_tieu_chi: str
    mo_ta_chi_tiet: str
    diem_toi_da: int

    class Config:
        from_attributes = True


# ============================ CHI TIẾT ĐIỂM ============================ #

class HdldChiTietTuDanhGia(BaseModel):
    """1 dòng tiêu chí khi HĐLĐ tự đánh giá."""
    so_tt: int = Field(..., ge=1, le=3)
    diem_tu: Decimal = Field(..., ge=0, le=100)
    ghi_chu_tu: Optional[str] = Field(default=None, max_length=2000)


class HdldChiTietDuyet(BaseModel):
    """1 dòng tiêu chí khi cấp quản lý chấm."""
    so_tt: int = Field(..., ge=1, le=3)
    diem_ql: Decimal = Field(..., ge=0, le=100)
    ghi_chu_ql: Optional[str] = Field(default=None, max_length=2000)
    ly_do_sua: Optional[str] = Field(default=None, max_length=2000)


class HdldChiTietResponse(BaseModel):
    so_tt: int
    diem_tu: Optional[Decimal] = None
    ghi_chu_tu: Optional[str] = None
    diem_ql: Optional[Decimal] = None
    ghi_chu_ql: Optional[str] = None
    ly_do_sua: Optional[str] = None
    # Kèm thông tin tiêu chí (join từ hdld_tieu_chi)
    ten_tieu_chi: Optional[str] = None
    mo_ta_chi_tiet: Optional[str] = None

    class Config:
        from_attributes = True


# ============================ REQUESTS ============================ #

class HdldTuDanhGiaRequest(BaseModel):
    """HĐLĐ lưu nháp: chọn nhóm nghề + 3 điểm tự chấm + ghi chú.

    Rule: tiêu chí nào diem_tu < 100 BẮT BUỘC có ghi_chu_tu.
    """
    nhom_nghe: str = Field(..., description="Nhóm nghề I..VI")
    chi_tiets: List[HdldChiTietTuDanhGia] = Field(..., min_length=3, max_length=3)
    ghi_chu: Optional[str] = Field(default=None, max_length=2000)

    @field_validator('nhom_nghe')
    @classmethod
    def _check_nhom(cls, v: str) -> str:
        if v not in NHOM_HOP_LE:
            raise ValueError("Nhóm nghề không hợp lệ (I..VI)")
        return v

    @field_validator('chi_tiets')
    @classmethod
    def _check_ghi_chu(cls, v: List[HdldChiTietTuDanhGia]) -> List[HdldChiTietTuDanhGia]:
        sotts = sorted(ct.so_tt for ct in v)
        if sotts != [1, 2, 3]:
            raise ValueError("Phải có đủ 3 tiêu chí (so_tt = 1, 2, 3)")
        for ct in v:
            if ct.diem_tu < 100 and not (ct.ghi_chu_tu and ct.ghi_chu_tu.strip()):
                raise ValueError(
                    f"Tiêu chí {ct.so_tt}: điểm < 100% bắt buộc ghi chú lý do"
                )
        return v


class HdldNopRequest(BaseModel):
    """HĐLĐ nộp: chọn người duyệt (TDV/PDV cùng đơn vị)."""
    nguoi_duyet_id: UUID


class HdldDuyetRequest(BaseModel):
    """Cấp quản lý duyệt: nhập 3 điểm cột cấp quản lý.

    Rule: nếu diem_ql khác diem_tu của tiêu chí đó → BẮT BUỘC ly_do_sua.
    """
    chi_tiets: List[HdldChiTietDuyet] = Field(..., min_length=3, max_length=3)
    ghi_chu: Optional[str] = Field(default=None, max_length=2000)

    @field_validator('chi_tiets')
    @classmethod
    def _check_sott(cls, v: List[HdldChiTietDuyet]) -> List[HdldChiTietDuyet]:
        if sorted(ct.so_tt for ct in v) != [1, 2, 3]:
            raise ValueError("Phải có đủ 3 tiêu chí (so_tt = 1, 2, 3)")
        return v


class HdldTraLaiRequest(BaseModel):
    """Cấp quản lý trả lại (duyệt nhầm / cần bổ sung)."""
    ly_do: str = Field(..., min_length=1, max_length=2000)


# ============================ RESPONSES ============================ #

class CongChucBrief(BaseModel):
    id: UUID
    ma_cc: Optional[str] = None
    ho_ten: Optional[str] = None
    chuc_vu: Optional[str] = None

    class Config:
        from_attributes = True


class HdldDanhGiaResponse(BaseModel):
    id: UUID
    cong_chuc_id: UUID
    thang: int
    nam: int
    nhom_nghe: Optional[str] = None
    ten_nhom: Optional[str] = None
    trang_thai: str
    nguoi_duyet_id: Optional[UUID] = None
    nguoi_duyet: Optional[CongChucBrief] = None
    cong_chuc: Optional[CongChucBrief] = None
    diem_tc_tb_tu: Optional[Decimal] = None
    diem_tc_tb_ql: Optional[Decimal] = None
    diem_kpi_70: Optional[Decimal] = None
    ghi_chu: Optional[str] = None
    ly_do_tra_lai: Optional[str] = None
    ngay_nop: Optional[datetime] = None
    ngay_duyet: Optional[datetime] = None
    chi_tiets: List[HdldChiTietResponse] = []

    class Config:
        from_attributes = True


class NguoiDuyetOption(BaseModel):
    """1 lựa chọn người duyệt cho HĐLĐ."""
    id: UUID
    ma_cc: Optional[str] = None
    ho_ten: Optional[str] = None
    chuc_vu: Optional[str] = None
    cap_bac: Optional[str] = None
