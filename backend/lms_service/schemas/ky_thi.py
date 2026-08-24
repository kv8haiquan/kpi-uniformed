"""
lms_service/schemas/ky_thi.py
=============================
Pydantic schemas cho ky thi DGNL + cau truc de.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from lms_service.core.timezone import localize_vn

TRANG_THAI_KY_THI = ["NHAP", "CHO_DUYET", "DANG_MO", "DA_DONG"]

# Chuyen trang thai hop le: trang_thai_cu -> [trang_thai_moi_hop_le]
TRANG_THAI_TRANSITIONS = {
    "NHAP": ["CHO_DUYET"],
    "CHO_DUYET": ["DANG_MO", "NHAP"],  # Duyet hoac tra lai
    "DANG_MO": ["DA_DONG"],
    "DA_DONG": ["DANG_MO", "NHAP"],  # Mo lai hoac reset ve nhap
}


# ============================================================
# Ky thi schemas
# ============================================================

class KyThiCreate(BaseModel):
    """Schema tao ky thi moi."""
    ma_ky_thi: str = Field(..., min_length=1, max_length=50)
    ten_ky_thi: str = Field(..., min_length=1, max_length=300)
    mo_ta: Optional[str] = None
    ngay_bat_dau: datetime
    ngay_ket_thuc: datetime
    thoi_gian_lam_bai_phut: int = Field(default=60, ge=1, le=480)
    diem_dat: Decimal = Field(default=Decimal("50.00"), ge=0, le=100)
    so_lan_thi_toi_da: int = Field(default=1, ge=1, le=10)
    tron_cau_hoi: bool = True
    tron_dap_an: bool = True
    hien_ket_qua: bool = True
    hien_dap_an: bool = False
    yeu_cau_toan_man_hinh: bool = True

    @field_validator("ngay_bat_dau", "ngay_ket_thuc")
    @classmethod
    def gan_mui_gio_vn(cls, v: datetime) -> datetime:
        # FE gui datetime-local khong co offset -> hieu la gio VN
        return localize_vn(v)

    @field_validator("ngay_ket_thuc")
    @classmethod
    def validate_ngay_ket_thuc(cls, v, info):
        if "ngay_bat_dau" in info.data and v <= info.data["ngay_bat_dau"]:
            raise ValueError("Ngày kết thúc phải sau ngày bắt đầu")
        return v


class KyThiUpdate(BaseModel):
    """Schema cap nhat ky thi — tat ca optional, chi khi NHAP."""
    ma_ky_thi: Optional[str] = Field(None, min_length=1, max_length=50)
    ten_ky_thi: Optional[str] = Field(None, min_length=1, max_length=300)
    mo_ta: Optional[str] = None
    ngay_bat_dau: Optional[datetime] = None
    ngay_ket_thuc: Optional[datetime] = None
    thoi_gian_lam_bai_phut: Optional[int] = Field(None, ge=1, le=480)
    diem_dat: Optional[Decimal] = Field(None, ge=0, le=100)
    so_lan_thi_toi_da: Optional[int] = Field(None, ge=1, le=10)
    tron_cau_hoi: Optional[bool] = None
    tron_dap_an: Optional[bool] = None
    hien_ket_qua: Optional[bool] = None
    hien_dap_an: Optional[bool] = None
    yeu_cau_toan_man_hinh: Optional[bool] = None

    @field_validator("ngay_bat_dau", "ngay_ket_thuc")
    @classmethod
    def gan_mui_gio_vn(cls, v: Optional[datetime]) -> Optional[datetime]:
        # FE gui datetime-local khong co offset -> hieu la gio VN
        return localize_vn(v) if v is not None else None


class KyThiTrangThaiUpdate(BaseModel):
    """Schema chuyen trang thai ky thi."""
    trang_thai: str

    @field_validator("trang_thai")
    @classmethod
    def validate_trang_thai(cls, v):
        if v not in TRANG_THAI_KY_THI:
            raise ValueError(f"Trạng thái phải thuộc: {TRANG_THAI_KY_THI}")
        return v


class KyThiResponse(BaseModel):
    """Schema response ky thi."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    ma_ky_thi: str
    ten_ky_thi: str
    mo_ta: Optional[str] = None
    ngay_bat_dau: datetime
    ngay_ket_thuc: datetime
    thoi_gian_lam_bai_phut: int
    diem_dat: Optional[Decimal] = Decimal("50.00")
    so_lan_thi_toi_da: Optional[int] = 1
    tron_cau_hoi: Optional[bool] = True
    tron_dap_an: Optional[bool] = True
    hien_ket_qua: Optional[bool] = True
    hien_dap_an: Optional[bool] = False
    yeu_cau_toan_man_hinh: Optional[bool] = True
    trang_thai: Optional[str] = "NHAP"
    nguoi_tao_id: UUID
    nguoi_duyet_id: Optional[UUID] = None
    ngay_duyet: Optional[datetime] = None
    is_active: Optional[bool] = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    # JOIN fields
    nguoi_tao_ho_ten: Optional[str] = None
    nguoi_duyet_ho_ten: Optional[str] = None
    # Thong ke nhanh
    tong_thi_sinh: Optional[int] = 0
    so_vi_tri: Optional[int] = 0
    # Trang thai thi sinh cua user hien tai — FE quyet dinh nut Vao thi/Tiep tuc/Thi lai
    trang_thai_thi_sinh: Optional[str] = None  # CHUA_THI | DANG_THI | DA_NOP | VANG
    lan_thi_hien_tai: Optional[int] = 0


# ============================================================
# Cau truc de schemas
# ============================================================

class CauTrucDeItem(BaseModel):
    """1 dong cau truc de: linh vuc + so cau theo do kho."""
    linh_vuc_id: UUID
    so_cau_de: int = Field(default=0, ge=0)
    so_cau_trung_binh: int = Field(default=0, ge=0)
    so_cau_kho: int = Field(default=0, ge=0)


class CauTrucDeCreate(BaseModel):
    """Schema tao/cap nhat cau truc de cho 1 vi tri (bulk upsert)."""
    vi_tri_id: UUID
    cau_truc: list[CauTrucDeItem] = Field(..., min_length=1)


class ApDungMauRequest(BaseModel):
    """Schema ap dung mau cau truc de vao ky thi (nguyen tu, 1 transaction)."""
    template_id: UUID
    # True: xoa sach cau truc cu cua ky thi roi ghi theo mau (ke ca vi tri khong
    # co trong mau). False (mac dinh): chi ghi de cac vi tri co trong mau.
    ghi_de_toan_bo: bool = False


class CauTrucDeResponse(BaseModel):
    """Schema response 1 dong cau truc de."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    ky_thi_id: UUID
    vi_tri_id: UUID
    linh_vuc_id: UUID
    so_cau_de: Optional[int] = 0
    so_cau_trung_binh: Optional[int] = 0
    so_cau_kho: Optional[int] = 0
    created_at: Optional[datetime] = None
    # JOIN fields
    vi_tri_ten: Optional[str] = None
    linh_vuc_ten: Optional[str] = None


class CauTrucDeByViTri(BaseModel):
    """Cau truc de nhom theo vi tri."""
    vi_tri_id: UUID
    vi_tri_ten: str
    tong_cau: int = 0
    chi_tiet: list[CauTrucDeResponse] = []


# ============================================================
# Validate response
# ============================================================

class ValidateItem(BaseModel):
    """Ket qua validate 1 slot (linh_vuc + do_kho)."""
    linh_vuc_ten: str
    do_kho: str
    yeu_cau: int
    co_san: int
    du: bool


class ValidateViTri(BaseModel):
    """Ket qua validate 1 vi tri."""
    vi_tri_ten: str
    du_cau_hoi: bool
    chi_tiet: list[ValidateItem]


class ValidateResponse(BaseModel):
    """Ket qua validate toan bo ky thi."""
    ky_thi_id: UUID
    tat_ca_du: bool
    theo_vi_tri: list[ValidateViTri]


# ============================================================
# Thong ke response
# ============================================================

class ThongKeKyThi(BaseModel):
    """Thong ke ket qua ky thi."""
    tong_quan: dict = {}
    theo_vi_tri: list[dict] = []
    theo_don_vi: list[dict] = []
    theo_linh_vuc: list[dict] = []
