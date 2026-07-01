"""
app/schemas/phieu_danh_gia.py
==============================
Pydantic schemas cho phiếu theo dõi, đánh giá công chức theo QUÝ (Mẫu 01A/01B).

Phiên bản: 1.0.0 (17/04/2026)
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# =============================================================================
# REQUEST SCHEMAS
# =============================================================================

#: Mã mức xếp loại hợp lệ (Nghị định 335/2025/NĐ-CP)
XEP_LOAI_HOP_LE = {"HTXSNV", "HTTNV", "HTNV", "KHTNV"}


class UpsertPhieuQuyRequest(BaseModel):
    """Tạo mới hoặc cập nhật phiếu nháp của CC (mục 4.1/4.2 & mục 5)."""

    quy: int = Field(..., ge=1, le=4, description="Quý (1-4)")
    nam: int = Field(..., ge=2020, le=2100, description="Năm")
    uu_diem: Optional[str] = Field(None, description="Mục 4.1: Ưu điểm")
    han_che: Optional[str] = Field(None, description="Mục 4.2: Hạn chế, khuyết điểm")
    tu_de_xuat_xep_loai: Optional[str] = Field(
        None,
        description="Mục 5: Cá nhân tự đề xuất mức xếp loại "
        "(HTXSNV | HTTNV | HTNV | KHTNV)",
    )


class PheDuyetPhieuRequest(BaseModel):
    """
    TDV/CCT duyệt phiếu: chấp nhận + nhập nhận xét.

    - Phiếu THÁNG (mẫu 01): chỉ dùng `y_kien_lanh_dao` (mục 6).
    - Phiếu QUÝ (mẫu 02): `y_kien_lanh_dao` = mục III.1 (ý kiến người trực tiếp
      sử dụng); các trường xếp loại là mục III.2 và mục IV.
    """

    y_kien_lanh_dao: Optional[str] = Field(
        None,
        description="Mục 6 (tháng) / Mục III.1 (quý): Ý kiến nhận xét",
    )
    de_xuat_xep_loai: Optional[str] = Field(
        None,
        description="Mục III.2 (quý): Người trực tiếp sử dụng đề xuất mức xếp loại",
    )
    quyet_dinh_xep_loai: Optional[str] = Field(
        None,
        description="Mục IV.1 (quý): Quyết định mức xếp loại của cấp có thẩm quyền",
    )
    y_kien_cap_tham_quyen: Optional[str] = Field(
        None,
        description="Mục IV.2 (quý): Ý kiến nhận xét của cấp có thẩm quyền",
    )


class TuChoiPhieuRequest(BaseModel):
    """TDV/CCT từ chối phiếu: bắt buộc nhập lý do."""

    ly_do_tu_choi: str = Field(..., min_length=1, description="Lý do từ chối")


class TraLaiPhieuRequest(BaseModel):
    """
    TDV/CCT trả lại phiếu đã phê duyệt (xử lý trường hợp phê duyệt nhầm).
    Lý do là tuỳ chọn — sẽ hiển thị cho CC như ghi chú trả lại.
    """

    ly_do: Optional[str] = Field(
        None,
        description="Ghi chú cho CC khi trả lại (không bắt buộc)",
    )


# =============================================================================
# RESPONSE SCHEMAS
# =============================================================================

class NguoiKyResponse(BaseModel):
    """Tóm tắt CC (để hiển thị ô Công chức / Cấp có thẩm quyền)."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    ma_cc: str
    ho_ten: str
    chuc_vu: Optional[str] = None


class PhieuDanhGiaQuyResponse(BaseModel):
    """Chi tiết phiếu đánh giá quý."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    cong_chuc_id: UUID
    cong_chuc: Optional[NguoiKyResponse] = None

    quy: int
    nam: int

    uu_diem: Optional[str] = None
    han_che: Optional[str] = None
    y_kien_lanh_dao: Optional[str] = None

    # Xếp loại (mẫu 02A/02B theo quý)
    tu_de_xuat_xep_loai: Optional[str] = None
    de_xuat_xep_loai: Optional[str] = None
    quyet_dinh_xep_loai: Optional[str] = None
    y_kien_cap_tham_quyen: Optional[str] = None

    trang_thai: str = Field(..., description="NHAP | CHO_PHE_DUYET | DA_PHE_DUYET | BI_TU_CHOI")
    ngay_gui_duyet: Optional[datetime] = None

    nguoi_phe_duyet_id: Optional[UUID] = None
    nguoi_phe_duyet: Optional[NguoiKyResponse] = None
    ngay_phe_duyet: Optional[datetime] = None
    ly_do_tu_choi: Optional[str] = None

    created_at: datetime
    updated_at: datetime


class PhieuChoPheDuyetItem(BaseModel):
    """
    1 dòng trong bảng phiếu quý (TDV/CCT).

    `id` nullable vì bảng này có thể chứa placeholder NHAP khi CC chưa soạn
    phiếu (backend tự sinh dòng giả để TDV thấy toàn bộ CC trong phạm vi duyệt).
    """
    model_config = ConfigDict(from_attributes=True)

    id: Optional[UUID] = None
    cong_chuc_id: UUID
    ma_cc: str
    ho_ten: str
    chuc_vu: Optional[str] = None
    don_vi_ten: Optional[str] = None
    quy: int
    nam: int
    trang_thai: str
    ngay_gui_duyet: Optional[datetime] = None
    ngay_phe_duyet: Optional[datetime] = None
    uu_diem: Optional[str] = None
    han_che: Optional[str] = None
    y_kien_lanh_dao: Optional[str] = None
    tu_de_xuat_xep_loai: Optional[str] = None
    de_xuat_xep_loai: Optional[str] = None
    quyet_dinh_xep_loai: Optional[str] = None
    y_kien_cap_tham_quyen: Optional[str] = None


class ChiTietThangThieu(BaseModel):
    """Chi tiết số lượng còn chưa duyệt trong 1 tháng."""

    thang: int
    cv_chua_duyet: int = 0
    tc_chua_duyet: int = 0


class KiemTraDuDieuKienResponse(BaseModel):
    """
    Kết quả kiểm tra điều kiện gửi duyệt phiếu quý.

    CC chỉ nên gửi phiếu khi toàn bộ công việc + tiêu chí chung đã được phê
    duyệt. Nếu còn mục tạm tính, FE hiện cảnh báo trước khi gửi.
    """

    quy: int
    nam: int
    co_van_de: bool = Field(
        ..., description="True nếu còn công việc hoặc tiêu chí chưa duyệt"
    )
    so_cv_chua_duyet: int = 0
    so_tc_chua_duyet: int = 0
    chi_tiet_thang: list[ChiTietThangThieu] = Field(default_factory=list)


# =============================================================================
# SCHEMAS PHIẾU THÁNG (08/05/2026)
# =============================================================================

class UpsertPhieuThangRequest(BaseModel):
    """CC tạo / cập nhật phiếu nháp tháng (mục 4 & 5)."""

    thang: int = Field(..., ge=1, le=12, description="Tháng (1-12)")
    nam: int = Field(..., ge=2020, le=2100, description="Năm")
    uu_diem: Optional[str] = Field(None, description="Mục 4: Ưu điểm")
    han_che: Optional[str] = Field(None, description="Mục 5: Hạn chế, khuyết điểm")


class PhieuDanhGiaThangResponse(BaseModel):
    """Chi tiết phiếu đánh giá tháng."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    cong_chuc_id: UUID
    cong_chuc: Optional[NguoiKyResponse] = None

    thang: int
    nam: int

    uu_diem: Optional[str] = None
    han_che: Optional[str] = None
    y_kien_lanh_dao: Optional[str] = None

    trang_thai: str
    ngay_gui_duyet: Optional[datetime] = None

    nguoi_phe_duyet_id: Optional[UUID] = None
    nguoi_phe_duyet: Optional[NguoiKyResponse] = None
    ngay_phe_duyet: Optional[datetime] = None
    ly_do_tu_choi: Optional[str] = None

    created_at: datetime
    updated_at: datetime


class PhieuThangChoPheDuyetItem(BaseModel):
    """1 dòng trong bảng phiếu tháng (TDV/CCT)."""
    model_config = ConfigDict(from_attributes=True)

    id: Optional[UUID] = None
    cong_chuc_id: UUID
    ma_cc: str
    ho_ten: str
    chuc_vu: Optional[str] = None
    don_vi_ten: Optional[str] = None
    thang: int
    nam: int
    trang_thai: str
    ngay_gui_duyet: Optional[datetime] = None
    ngay_phe_duyet: Optional[datetime] = None
    uu_diem: Optional[str] = None
    han_che: Optional[str] = None
    y_kien_lanh_dao: Optional[str] = None


class KiemTraDuDieuKienThangResponse(BaseModel):
    """Kiểm tra điều kiện gửi phiếu tháng — đếm CV/TC chưa duyệt trong tháng."""

    thang: int
    nam: int
    co_van_de: bool
    so_cv_chua_duyet: int = 0
    so_tc_chua_duyet: int = 0
