"""Schemas cho Module 1 — Quản lý cuộc họp."""

from datetime import date, datetime, time
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


KHOI_VALUES = ["DANG", "CHUYEN_MON", "HANH_CHINH", "BAN_NHOM"]
HINH_THUC_VALUES = ["TRUC_TIEP", "TRUC_TUYEN", "HYBRID"]
TRANG_THAI_VALUES = ["LEN_KE_HOACH", "DA_THONG_BAO", "DANG_DIEN_RA", "HOAN_THANH", "HUY"]
LOAI_THAM_DU_VALUES = ["BAT_BUOC", "THAM_KHAO"]
XAC_NHAN_VALUES = ["CHUA_PHAN_HOI", "THAM_DU", "KHONG_THAM_DU", "UY_QUYEN"]


class ThanhPhanCreate(BaseModel):
    cong_chuc_id: UUID
    loai_tham_du: str = Field(default="BAT_BUOC")

    @field_validator("loai_tham_du")
    @classmethod
    def _check_loai(cls, v: str) -> str:
        if v not in LOAI_THAM_DU_VALUES:
            raise ValueError(f"loai_tham_du must be one of {LOAI_THAM_DU_VALUES}")
        return v


class CuocHopCreate(BaseModel):
    tieu_de: str = Field(..., min_length=1, max_length=500)
    mo_ta: Optional[str] = None
    khoi: str = Field(default="CHUYEN_MON")
    hinh_thuc: str = Field(default="TRUC_TIEP")
    ngay_hop: date
    gio_bat_dau: time
    gio_ket_thuc: Optional[time] = None
    dia_diem: Optional[str] = Field(None, max_length=300)
    don_vi_to_chuc_id: UUID
    chu_toa_id: UUID
    thu_ky_id: Optional[UUID] = None
    thanh_phan: list[ThanhPhanCreate] = Field(default_factory=list)

    @field_validator("khoi")
    @classmethod
    def _check_khoi(cls, v: str) -> str:
        if v not in KHOI_VALUES:
            raise ValueError(f"khoi must be one of {KHOI_VALUES}")
        return v

    @field_validator("hinh_thuc")
    @classmethod
    def _check_ht(cls, v: str) -> str:
        if v not in HINH_THUC_VALUES:
            raise ValueError(f"hinh_thuc must be one of {HINH_THUC_VALUES}")
        return v


class CuocHopUpdate(BaseModel):
    tieu_de: Optional[str] = Field(None, min_length=1, max_length=500)
    mo_ta: Optional[str] = None
    khoi: Optional[str] = None
    hinh_thuc: Optional[str] = None
    ngay_hop: Optional[date] = None
    gio_bat_dau: Optional[time] = None
    gio_ket_thuc: Optional[time] = None
    dia_diem: Optional[str] = Field(None, max_length=300)
    thu_ky_id: Optional[UUID] = None

    @field_validator("khoi")
    @classmethod
    def _check_khoi(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in KHOI_VALUES:
            raise ValueError(f"khoi must be one of {KHOI_VALUES}")
        return v

    @field_validator("hinh_thuc")
    @classmethod
    def _check_ht(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in HINH_THUC_VALUES:
            raise ValueError(f"hinh_thuc must be one of {HINH_THUC_VALUES}")
        return v


class CuocHopHuy(BaseModel):
    ly_do: str = Field(..., min_length=1)


class ThanhPhanReplaceList(BaseModel):
    """PUT /cuoc-hop/{id}/thanh-phan — thay thế toàn bộ list thành phần.

    Service tự diff để emit notifications cho người được thêm mới.
    KHÔNG cho remove chu_toa_id hoặc thu_ky_id (raise 409).
    """
    thanh_phan: list[ThanhPhanCreate] = Field(default_factory=list)


class ThanhPhanItemResponse(BaseModel):
    """Item trong list thành phần — kèm thông tin CBCC để UI hiển thị tên/mã/đơn vị."""
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    cuoc_hop_id: UUID
    cong_chuc_id: UUID
    loai_tham_du: str
    xac_nhan: Optional[str] = None
    # G4-fix-7 (2026-05-03): JOIN cong_chuc + don_vi để FE không phải fetch riêng
    ho_ten: Optional[str] = None
    ma_cc: Optional[str] = None
    don_vi_id: Optional[UUID] = None
    ten_don_vi: Optional[str] = None
    chuc_vu: Optional[str] = None


class XacNhanThamDu(BaseModel):
    xac_nhan: str
    nguoi_uy_quyen_id: Optional[UUID] = None
    ghi_chu: Optional[str] = None

    @field_validator("xac_nhan")
    @classmethod
    def _check_xn(cls, v: str) -> str:
        if v not in XAC_NHAN_VALUES:
            raise ValueError(f"xac_nhan must be one of {XAC_NHAN_VALUES}")
        return v


class CuocHopResponse(BaseModel):
    """Chi tiết 1 cuộc họp."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tieu_de: str
    mo_ta: Optional[str]
    khoi: str
    hinh_thuc: str
    ngay_hop: date
    gio_bat_dau: time
    gio_ket_thuc: Optional[time]
    dia_diem: Optional[str]
    don_vi_to_chuc_id: Optional[UUID] = None
    chu_toa_id: Optional[UUID] = None
    thu_ky_id: Optional[UUID]
    trang_thai: str
    # Bảng `cuoc_hop` chứa CẢ cuộc họp HKG lẫn sự kiện Lịch công tác, phân
    # biệt bằng `nguon`. Trước đây response không trả cột này nên màn hình
    # HKG không biết mình đang mở nhầm một sự kiện Lịch công tác: nó vẽ đủ
    # nút "Xác nhận tham dự" / "Huỷ", bấm vào là 403 vì sự kiện Lịch công tác
    # không có `thanh_phan` và thường không có đơn vị tổ chức / chủ tọa.
    nguon: str
    ma_lich: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    created_by: UUID
    is_deleted: bool


class CuocHopListItem(BaseModel):
    """1 row trong list view."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tieu_de: str
    khoi: str
    hinh_thuc: str
    ngay_hop: date
    gio_bat_dau: time
    trang_thai: str
    don_vi_to_chuc_id: Optional[UUID] = None
    chu_toa_id: Optional[UUID] = None
    # Cần cho FE quyết định hiển thị nút "Sửa" với thư ký ngay trên list view
    thu_ky_id: Optional[UUID] = None
    so_thanh_phan: int = 0
