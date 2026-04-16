"""
lms_service/schemas/bai_kiem_tra.py
===================================
Pydantic schemas cho bai kiem tra CRUD + luong thi.
"""

from datetime import datetime
from decimal import Decimal
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from lms_service.schemas.cau_hoi import CauHoiForExam


class CauHoiInline(BaseModel):
    """Schema tao cau hoi truc tiep trong BKT (inline, khong qua ngan hang)."""
    noi_dung: str = Field(..., min_length=1)
    loai: str = Field(default="TRAC_NGHIEM_1")
    do_kho: str = Field(default="TRUNG_BINH")
    diem: Decimal = Field(default=Decimal("1.0"), ge=0)
    dap_an: dict
    giai_thich: Optional[str] = None


class BaiKiemTraCreate(BaseModel):
    """Schema tao bai kiem tra."""
    # Optional vi khoa_hoc_id duoc lay tu URL path parameter, backend se override
    khoa_hoc_id: Optional[UUID] = None
    tieu_de: str = Field(..., min_length=1, max_length=300)
    mo_ta: Optional[str] = None
    thoi_gian_lam_bai_phut: Optional[int] = Field(None, ge=1)
    so_lan_lam_toi_da: int = Field(default=3, ge=1)
    diem_dat: Decimal = Field(default=Decimal("70.00"), ge=0, le=100)
    tron_de: bool = True
    tron_dap_an: bool = True
    # Cau hinh hien thi ket qua sau khi nop bai
    che_do_xem_ket_qua: str = "XEM_DIEM_VA_DAP_AN"
    hien_giai_thich: bool = True
    # Khung gio thi hang ngay
    gio_mo: Optional[str] = None
    gio_dong: Optional[str] = None
    # cau_hoi_ids: chon tu ngan hang (co the rong neu dung cau_hoi_moi)
    cau_hoi_ids: Optional[list[UUID]] = None
    # cau_hoi_moi: tao moi inline ngay khi tao BKT
    cau_hoi_moi: Optional[list[CauHoiInline]] = None


class BaiKiemTraUpdate(BaseModel):
    """Schema cap nhat bai kiem tra."""
    tieu_de: Optional[str] = Field(None, min_length=1, max_length=300)
    mo_ta: Optional[str] = None
    thoi_gian_lam_bai_phut: Optional[int] = Field(None, ge=1)
    so_lan_lam_toi_da: Optional[int] = Field(None, ge=1)
    diem_dat: Optional[Decimal] = Field(None, ge=0, le=100)
    tron_de: Optional[bool] = None
    tron_dap_an: Optional[bool] = None
    # Cau hinh hien thi ket qua
    che_do_xem_ket_qua: Optional[str] = None
    hien_giai_thich: Optional[bool] = None
    # Khung gio thi hang ngay
    gio_mo: Optional[str] = None
    gio_dong: Optional[str] = None
    cau_hoi_ids: Optional[list[UUID]] = None
    cau_hoi_moi: Optional[list[CauHoiInline]] = None


class BaiKiemTraResponse(BaseModel):
    """Schema response bai kiem tra."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    khoa_hoc_id: Optional[UUID] = None
    tieu_de: str
    mo_ta: Optional[str] = None
    so_cau_hoi: int
    thoi_gian_lam_bai_phut: Optional[int] = None
    so_lan_lam_toi_da: Optional[int] = 3
    diem_dat: Optional[Decimal] = Decimal("70.00")
    tron_de: Optional[bool] = True
    tron_dap_an: Optional[bool] = True
    # Cau hinh hien thi ket qua
    che_do_xem_ket_qua: str = "XEM_DIEM_VA_DAP_AN"
    hien_giai_thich: bool = True
    ngay_mo: Optional[str] = None
    ngay_dong: Optional[str] = None
    gio_mo: Optional[str] = None
    gio_dong: Optional[str] = None
    nguoi_tao_id: Optional[UUID] = None
    is_active: Optional[bool] = True
    created_at: Optional[datetime] = None
    # Thong ke ca nhan (chi co khi query voi user_id)
    so_lan_da_lam: Optional[int] = None
    diem_cao_nhat: Optional[Decimal] = None
    da_dat: Optional[bool] = None
    so_lan_con_lai: Optional[int] = None


class LichSuThiItem(BaseModel):
    """1 lan lam bai kiem tra."""
    id: UUID
    lan_thu: int
    diem: Optional[Decimal] = None
    so_cau_dung: Optional[int] = None
    so_cau_sai: Optional[int] = None
    thoi_gian_lam_giay: Optional[int] = None
    dat_yeu_cau: Optional[bool] = None
    ngay_lam: Optional[datetime] = None


class LichSuThiResponse(BaseModel):
    """Lich su lam bai kiem tra cua user hien tai."""
    bai_kiem_tra_id: UUID
    tieu_de: str
    so_lan_lam_toi_da: Optional[int] = 3
    diem_dat: Optional[Decimal] = None
    so_lan_da_lam: int = 0
    diem_cao_nhat: Optional[Decimal] = None
    da_dat: bool = False
    lich_su: list[LichSuThiItem] = []


class BatDauResponse(BaseModel):
    """Response khi bat dau lam bai kiem tra."""
    ket_qua_id: UUID
    lan_thu: int
    thoi_gian_phut: Optional[int] = None
    so_cau: int
    cau_hoi: list[CauHoiForExam]
    so_lan_con_lai: Optional[int] = None
    dang_tiep_tuc: bool = False
    chi_tiet_nhap: Optional[list] = None
    thoi_gian_da_lam_giay: Optional[int] = None
    so_lan_vi_pham: int = 0


class TraLoiItem(BaseModel):
    """1 cau tra loi."""
    cau_hoi_id: UUID
    dap_an: Any  # str, list[str], bool tuy loai


class NopBaiRequest(BaseModel):
    """Request nop bai kiem tra."""
    ket_qua_id: UUID
    tra_loi: list[TraLoiItem]


class LuuNhapRequest(BaseModel):
    """Request luu bai lam nhap."""
    ket_qua_id: UUID
    tra_loi: list[TraLoiItem]
    so_lan_vi_pham: int = 0


class KetQuaChiTietItem(BaseModel):
    """Chi tiet 1 cau trong ket qua."""
    cau_hoi_id: UUID
    noi_dung: Optional[str] = None
    loai: Optional[str] = None
    tra_loi: Any = None
    dap_an_dung: Any = None
    dung: Optional[bool] = None
    diem_dat: Optional[Decimal] = None
    diem_toi_da: Optional[Decimal] = None


class KetQuaResponse(BaseModel):
    """Response ket qua bai kiem tra."""
    id: UUID
    lan_thu: int
    diem: Optional[Decimal] = None
    so_cau_dung: Optional[int] = None
    so_cau_sai: Optional[int] = None
    thoi_gian_lam_giay: Optional[int] = None
    dat_yeu_cau: Optional[bool] = None
    ngay_lam: Optional[datetime] = None
    chi_tiet: Optional[list[KetQuaChiTietItem]] = None
