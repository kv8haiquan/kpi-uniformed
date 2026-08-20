"""Schemas cho nghiệp vụ Lịch công tác."""

from __future__ import annotations

from datetime import date, time
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

# 6 loại đang chạy thật trên lichkv8. Khác trục với `khoi` của HKG.
LOAI_LICH_VALUES = ["HOP", "TRUC_BAN", "HOI_NGHI", "LAM_VIEC", "CONG_TAC",
                    "LICH_KHAC"]
NGUON_VALUES = ["HKG", "LICH_CONG_TAC"]

NHAN_LOAI_LICH = {
    "HOP": "Họp",
    "TRUC_BAN": "Trực ban",
    "HOI_NGHI": "Hội nghị",
    "LAM_VIEC": "Làm việc",
    "CONG_TAC": "Đi công tác",
    "LICH_KHAC": "Lịch khác",
}


class NguoiTomTat(BaseModel):
    """Thông tin người rút gọn, dùng trong danh sách."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    ho_ten: str
    chuc_vu: Optional[str] = None


class LichCongTacItem(BaseModel):
    """Một sự kiện trên lịch — dùng cho cả xem tháng, tuần và danh sách."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    nguon: str
    ma_lich: Optional[str] = None
    tieu_de: str
    loai_lich: Optional[str] = None
    loai_lich_nhan: Optional[str] = None

    ngay_hien_thi: Optional[date] = None
    ngay_hop: date
    ngay_ket_thuc: Optional[date] = None
    gio_bat_dau: time
    gio_ket_thuc: Optional[time] = None

    dia_diem: Optional[str] = None
    trang_thai: str

    # Chủ trì: khớp được công chức thì có chu_toa, không thì đọc chu_tri_text.
    chu_toa: Optional[NguoiTomTat] = None
    chu_tri_text: Optional[str] = None

    don_vi_chuan_bi: Optional[str] = None
    so_van_ban: Optional[str] = None
    lanh_dao_lien_quan: list[NguoiTomTat] = Field(default_factory=list)
    so_tai_lieu: int = 0

    # Giao diện dùng để quyết định có hiện nút Sửa ngay trên danh sách không:
    # người thường chỉ sửa được sự kiện mình tạo.
    created_by: Optional[UUID] = None

    # Điểm công tác chuẩn bị (G5.3) — None khi chưa ai chấm.
    diem_chuan_bi: Optional[float] = None
    so_luot_cham: int = 0

    # Sự kiện nguồn HKG mở được sang màn hình Họp Không Giấy (tiêu chí 8.3).
    co_the_mo_hkg: bool = False


class LichCongTacChiTiet(LichCongTacItem):
    mo_ta: Optional[str] = None
    thanh_phan_text: Optional[str] = None
    ly_do_huy: Optional[str] = None


class LichCongTacCreate(BaseModel):
    tieu_de: str = Field(..., min_length=1, max_length=500)
    loai_lich: str
    ngay_hop: date
    gio_bat_dau: time
    gio_ket_thuc: Optional[time] = None
    ngay_ket_thuc: Optional[date] = None
    ngay_hien_thi: Optional[date] = None
    dia_diem: Optional[str] = Field(default=None, max_length=300)
    mo_ta: Optional[str] = None
    chu_toa_id: Optional[UUID] = None
    chu_tri_text: Optional[str] = Field(default=None, max_length=300)
    thanh_phan_text: Optional[str] = None
    don_vi_chuan_bi: Optional[str] = Field(default=None, max_length=200)
    so_van_ban: Optional[str] = Field(default=None, max_length=100)
    lanh_dao_lien_quan_ids: list[UUID] = Field(default_factory=list)

    @field_validator("loai_lich")
    @classmethod
    def _check_loai(cls, v: str) -> str:
        if v not in LOAI_LICH_VALUES:
            raise ValueError(f"loai_lich phải thuộc {LOAI_LICH_VALUES}")
        return v

    @field_validator("ngay_ket_thuc")
    @classmethod
    def _check_ngay(cls, v: Optional[date], info) -> Optional[date]:
        bd = info.data.get("ngay_hop")
        if v and bd and v < bd:
            raise ValueError("ngay_ket_thuc không được trước ngay_hop")
        return v


class LichCongTacUpdate(BaseModel):
    tieu_de: Optional[str] = Field(default=None, min_length=1, max_length=500)
    loai_lich: Optional[str] = None
    ngay_hop: Optional[date] = None
    gio_bat_dau: Optional[time] = None
    gio_ket_thuc: Optional[time] = None
    ngay_ket_thuc: Optional[date] = None
    ngay_hien_thi: Optional[date] = None
    dia_diem: Optional[str] = Field(default=None, max_length=300)
    mo_ta: Optional[str] = None
    trang_thai: Optional[str] = None
    chu_toa_id: Optional[UUID] = None
    chu_tri_text: Optional[str] = Field(default=None, max_length=300)
    thanh_phan_text: Optional[str] = None
    don_vi_chuan_bi: Optional[str] = Field(default=None, max_length=200)
    so_van_ban: Optional[str] = Field(default=None, max_length=100)
    lanh_dao_lien_quan_ids: Optional[list[UUID]] = None

    @field_validator("loai_lich")
    @classmethod
    def _check_loai(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in LOAI_LICH_VALUES:
            raise ValueError(f"loai_lich phải thuộc {LOAI_LICH_VALUES}")
        return v


class LichCongTacHuy(BaseModel):
    ly_do_huy: str = Field(..., min_length=1)


# ── Lịch theo lãnh đạo ────────────────────────────────────────────────

class LichLanhDaoNgay(BaseModel):
    ngay: date
    su_kien: list[LichCongTacItem]


class LichLanhDaoCard(BaseModel):
    lanh_dao: NguoiTomTat
    tong_su_kien: int
    theo_ngay: list[LichLanhDaoNgay]


# ── Tóm tắt lịch ──────────────────────────────────────────────────────

class TomTatLichNgay(BaseModel):
    ngay: date
    thu: str
    su_kien: list[LichCongTacItem]
    truc_ban: list[str] = Field(default_factory=list)


class TomTatLich(BaseModel):
    tu_ngay: date
    den_ngay: date
    theo_ngay: list[TomTatLichNgay]
    van_ban_thuan: str = Field(
        default="", description="Bản text sẵn để dán sang Zalo hoặc email")
