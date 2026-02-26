"""
app/api/v1/endpoints/phe_duyet.py
=================================
API Endpoints cho Phê duyệt kê khai công việc.

Giai đoạn 4: Phê duyệt & Assessment Module

FIX v2.7.0 (01/02/2026):
- LĐ có thể điều chỉnh cap_do_ma (mức độ) khi phê duyệt
  → Khi đổi mức độ: tự động tính lại so_sp_goc_quy_doi, so_sp_chat_luong, so_sp_tien_do
- Cần kết hợp với kpi_assessment.py schema fix: so_loi default=None (không phải 0)

FIX v2.6.1 (31/01/2026):
- Số lỗi chốt = Số lỗi LĐ nhập (nếu có) HOẶC Số lỗi tự đánh giá CC (mặc định)
- Lãnh đạo có quyền sửa lại số lỗi hoặc giữ nguyên số CC tự đánh giá

FIX v2.6.0 (31/01/2026):
- SỬA LỖI công thức tính so_sp_chat_luong và so_sp_tien_do
- Công thức đúng: SP_đạt = SP_gốc × (1 - 0.25 × min(Lỗi, SL×4) / SL)
- Mỗi lỗi trừ 25% của 1 đơn vị SP, không phải trừ nguyên số lỗi

Endpoints:
- GET /phe-duyet/pending: Danh sách kê khai chờ phê duyệt
- POST /phe-duyet/xu-ly: Phê duyệt/Từ chối một hoặc nhiều kê khai

Quy tắc:
- Chỉ người được gán nguoi_phe_duyet_id mới thấy và xử lý được
- APPROVE: Cập nhật trạng thái → DA_PHE_DUYET, lưu số lỗi chốt cuối
- REJECT: Cập nhật trạng thái → TU_CHOI (CC có thể sửa và gửi lại)
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import DatabaseDep, ActiveUserDep, is_qldv
from app.models.kpi_submission import KeKhaiCongViec, TrangThaiKeKhai
from app.models.task_catalog import DanhMucSpCongViec, CapDoPhucTap
from app.models.user_org import CongChuc, DonVi
from app.schemas.common import (
    DataResponse,
    PaginatedResponse,
    Pagination,
    success_response,
    error_response,
)
from pydantic import BaseModel, Field

from app.schemas.kpi_assessment import (
    PheDuyetAction,
    PheDuyetRequest,
    PheDuyetBulkRequest,
    PheDuyetResponse,
    KeKhaiPendingResponse,
    CongChucPendingInfo,
)


# =============================================================================
# SCHEMAS MỚI - TRẢ LẠI KÊ KHAI ĐÃ PHÊ DUYỆT
# =============================================================================

class TraLaiRequest(BaseModel):
    """Yêu cầu trả lại kê khai đã phê duyệt."""
    ly_do: str = Field(..., min_length=1, max_length=500, description="Lý do trả lại (bắt buộc)")


class TraLaiBulkRequest(BaseModel):
    """Yêu cầu trả lại nhiều kê khai đã phê duyệt."""
    ke_khai_ids: List[UUID] = Field(..., min_length=1, description="Danh sách ID kê khai")
    ly_do: str = Field(..., min_length=1, max_length=500, description="Lý do trả lại")


router = APIRouter()


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def tinh_sp_chat_luong_tien_do(
    so_sp_goc: Optional[Decimal],
    so_luong: int,
    so_loi_chat_luong: int,
    so_loi_tien_do: int,
) -> tuple[Decimal, Decimal]:
    """
    Tính SP đạt chất lượng và đúng tiến độ.
    
    FIX v2.6.0 (31/01/2026): Sửa công thức theo đúng Quy chế KPI
    
    Công thức (theo BUSINESS_RULES_FINAL.md - Mục 5.1):
    - SP đạt CL = Hệ số × (SL - 0.25 × min(Lần_lỗi_CL, SL × 4))
    - SP đạt TĐ = Hệ số × (SL - 0.25 × min(Lần_lỗi_TĐ, SL × 4))
    
    Quy về SP gốc đã quy đổi (so_sp_goc = SL × Hệ số):
    - SP đạt = so_sp_goc × (1 - 0.25 × min(Lỗi, SL×4) / SL)
    - Hoặc: SP đạt = so_sp_goc - (0.25 × min(Lỗi, SL×4) × sp_per_unit)
    
    Giải thích:
    - Mỗi lần lỗi trừ 25% của 1 đơn vị SP (không phải trừ nguyên 1 SP)
    - Tối đa 4 lần lỗi/đơn vị công việc (= trừ hết 100% của đơn vị đó)
    - Giá trị tối thiểu = 0 (không âm)
    
    Args:
        so_sp_goc: Số SP gốc quy đổi (đã tính = SL × Hệ số)
        so_luong: Số lượng công việc kê khai
        so_loi_chat_luong: Số lần lỗi chất lượng (do Lãnh đạo chốt hoặc CC tự đánh giá)
        so_loi_tien_do: Số lần lỗi tiến độ (do Lãnh đạo chốt hoặc CC tự đánh giá)
    
    Returns:
        Tuple (so_sp_chat_luong, so_sp_tien_do)
    
    Example:
        - Kê khai: 5 Quyết định, hệ số 96 → so_sp_goc = 480
        - Lỗi CL: 8 lần, Lỗi TĐ: 2 lần
        - max_loi = 5 × 4 = 20
        - sp_per_unit = 480 / 5 = 96
        - sp_tru_cl = 0.25 × min(8, 20) × 96 = 0.25 × 8 × 96 = 192
        - sp_tru_td = 0.25 × min(2, 20) × 96 = 0.25 × 2 × 96 = 48
        - so_sp_chat_luong = 480 - 192 = 288 ✓
        - so_sp_tien_do = 480 - 48 = 432 ✓
    """
    sp_goc = so_sp_goc or Decimal("0")
    
    # Trường hợp đặc biệt: không có SP hoặc số lượng = 0
    if sp_goc <= 0 or so_luong <= 0:
        return Decimal("0"), Decimal("0")
    
    # Tính SP cho mỗi đơn vị công việc
    sp_per_unit = sp_goc / Decimal(str(so_luong))
    
    # Số lỗi tối đa được tính = số lượng × 4 (mỗi SP bị trừ tối đa 4 lần = 100%)
    max_loi_cho_phep = so_luong * 4
    
    # Số lỗi thực tế tính (cap tại max)
    loi_tinh_cl = min(so_loi_chat_luong, max_loi_cho_phep)
    loi_tinh_td = min(so_loi_tien_do, max_loi_cho_phep)
    
    # Tính SP bị trừ: mỗi lỗi trừ 25% của 1 đơn vị SP
    sp_tru_cl = Decimal("0.25") * Decimal(str(loi_tinh_cl)) * sp_per_unit
    sp_tru_td = Decimal("0.25") * Decimal(str(loi_tinh_td)) * sp_per_unit
    
    # Kết quả (không âm)
    sp_chat_luong = max(sp_goc - sp_tru_cl, Decimal("0"))
    sp_tien_do = max(sp_goc - sp_tru_td, Decimal("0"))
    
    return sp_chat_luong, sp_tien_do


def get_so_loi_chot(
    payload_value: Optional[int],
    tu_danh_gia_value: Optional[int],
) -> int:
    """
    Lấy số lỗi chốt cuối cùng.
    
    FIX v2.6.1 (31/01/2026):
    - Nếu LĐ nhập số lỗi (payload_value is not None) → dùng giá trị LĐ nhập
    - Nếu LĐ không nhập (payload_value is None) → dùng số lỗi tự đánh giá CC
    
    Args:
        payload_value: Số lỗi LĐ nhập (có thể None nếu không nhập)
        tu_danh_gia_value: Số lỗi CC tự đánh giá
    
    Returns:
        Số lỗi chốt cuối cùng
    """
    if payload_value is not None:
        return payload_value
    return tu_danh_gia_value or 0


async def apply_cap_do_change(
    kk: KeKhaiCongViec,
    new_cap_do_ma: str,
    db,
) -> None:
    """
    Áp dụng thay đổi cấp độ (mức độ) do Lãnh đạo điều chỉnh khi phê duyệt.
    
    FIX v2.7.0 (01/02/2026):
    - Khi LĐ đổi mức độ → cần tính lại so_sp_goc_quy_doi
    - Công thức: so_sp_goc_quy_doi = so_luong × he_so_quy_doi_sp1 × he_so_cap_do
    
    Hệ số cấp độ:
    - C1: SP1 ×1, SP2 ×1
    - C2: SP1 ×4, SP2 ×2
    - C3: SP1 ×12, SP2 ×4
    - C4: SP1 ×24, SP2 ×8
    - C5: Theo thực tế (dùng he_so_thuc_te đã có)
    
    Args:
        kk: KeKhaiCongViec cần cập nhật
        new_cap_do_ma: Mã cấp độ mới (C1-C5)
        db: Database session
    """
    # Lookup cấp độ mới từ bảng cap_do_phuc_tap
    cd_stmt = select(CapDoPhucTap).where(CapDoPhucTap.ma_cap_do == new_cap_do_ma)
    cd_result = await db.execute(cd_stmt)
    new_cap_do = cd_result.scalar_one_or_none()
    
    if not new_cap_do:
        return  # Mã không hợp lệ → giữ nguyên
    
    if kk.cap_do_id == new_cap_do.id:
        return  # Cấp độ không đổi
    
    # Cập nhật cap_do_id
    kk.cap_do_id = new_cap_do.id
    
    # Lookup danh mục + SP chuẩn (cần cho tính hệ số)
    dm_stmt = (
        select(DanhMucSpCongViec)
        .options(selectinload(DanhMucSpCongViec.sp_chuan))
        .where(DanhMucSpCongViec.id == kk.danh_muc_sp_id)
    )
    dm_result = await db.execute(dm_stmt)
    danh_muc = dm_result.scalar_one_or_none()
    
    if not danh_muc or not danh_muc.sp_chuan:
        return  # Không có danh mục → không tính lại
    
    # Xác định hệ số cấp độ
    if new_cap_do.is_theo_thuc_te:
        # C5: dùng he_so_thuc_te đã có
        if kk.he_so_thuc_te:
            he_so_cap_do = Decimal(str(kk.he_so_thuc_te))
        else:
            return  # Chưa có hệ số thực tế → không tính lại
    else:
        # C1-C4: dùng hệ số từ bảng
        ma_sp = danh_muc.sp_chuan.ma_sp
        if ma_sp == "SP1":
            he_so_cap_do = new_cap_do.he_so_sp1
        else:
            he_so_cap_do = new_cap_do.he_so_sp2
    
    # Tính lại so_sp_goc_quy_doi = so_luong × he_so_quy_doi_sp1 × he_so_cap_do
    he_so_quy_doi = danh_muc.sp_chuan.he_so_quy_doi_sp1
    kk.so_sp_goc_quy_doi = Decimal(str(kk.so_luong)) * he_so_quy_doi * Decimal(str(he_so_cap_do))


def ke_khai_to_pending_response(kk: KeKhaiCongViec) -> dict:
    """
    Convert KeKhaiCongViec model to pending response dict.
    Bao gồm thông tin tự đánh giá của CC để Lãnh đạo xem xét.
    """
    response = {
        "id": kk.id,
        "cong_chuc": None,
        "thang": kk.thang,
        "nam": kk.nam,
        "ngay_thuc_hien": kk.ngay_thuc_hien,
        "danh_muc_sp_id": kk.danh_muc_sp_id,
        "danh_muc_ten": None,
        "cap_do_ma": None,
        "so_luong": kk.so_luong,
        "he_so_thuc_te": float(kk.he_so_thuc_te) if kk.he_so_thuc_te else None,
        "mo_ta_cong_viec": kk.mo_ta_cong_viec,
        "is_doi_moi_sang_tao": kk.is_doi_moi_sang_tao,
        "ngay_deadline": kk.ngay_deadline,
        "ngay_hoan_thanh": kk.ngay_hoan_thanh,
        # Tự đánh giá của CC
        "tu_danh_gia_chat_luong": kk.tu_danh_gia_chat_luong or 0,
        "tu_danh_gia_tien_do": kk.tu_danh_gia_tien_do or 0,
        "ghi_chu_tu_danh_gia": kk.ghi_chu_tu_danh_gia,
        # Kết quả
        "so_sp_goc_quy_doi": float(kk.so_sp_goc_quy_doi) if kk.so_sp_goc_quy_doi else None,
        "trang_thai": kk.trang_thai.value if kk.trang_thai else "CHO_PHE_DUYET",
        "created_at": kk.created_at,
    }
    
    # Nested: Người kê khai
    if kk.cong_chuc:
        cc = kk.cong_chuc
        response["cong_chuc"] = {
            "id": cc.id,
            "ma_cc": cc.ma_cc,
            "ho_ten": cc.ho_ten,
            "chuc_vu": cc.chuc_vu,
            "don_vi_id": cc.don_vi_id,
            "don_vi_ten": cc.don_vi.ten_don_vi if cc.don_vi else None,
        }
    
    # Nested: Danh mục SP
    if kk.danh_muc_sp:
        response["danh_muc_ten"] = kk.danh_muc_sp.ten_cong_viec
    
    # Nested: Cấp độ
    if kk.cap_do:
        response["cap_do_ma"] = kk.cap_do.ma_cap_do
    
    return response


# =============================================================================
# GET PENDING LIST (Danh sách chờ phê duyệt)
# =============================================================================

@router.get(
    "/pending",
    summary="Lấy danh sách kê khai chờ phê duyệt",
    description="""
    Lấy danh sách các bản kê khai có trạng thái CHO_PHE_DUYET.
    
    **Logic phân quyền:**
    - Chỉ hiển thị các kê khai mà `nguoi_phe_duyet_id` = current_user.id
    - Hoặc nếu là Admin/CCT thì thấy hết
    
    **Response bao gồm:**
    - Thông tin kê khai
    - Tự đánh giá của CC (để Lãnh đạo xem xét trước khi chốt)
    
    **Quyền truy cập:** Lãnh đạo hoặc người được gán phê duyệt.
    """,
    response_model=PaginatedResponse[KeKhaiPendingResponse],
)
async def get_pending_list(
    db: DatabaseDep,
    current_user: ActiveUserDep,
    # Pagination
    page: int = Query(default=1, ge=1, description="Trang hiện tại"),
    page_size: int = Query(default=20, ge=1, le=100, description="Số item mỗi trang"),
    # Filters
    don_vi_id: Optional[UUID] = Query(
        default=None,
        description="Filter theo đơn vị (chỉ Admin/CCT)"
    ),
    thang: Optional[int] = Query(default=None, ge=1, le=12, description="Filter theo tháng"),
    nam: Optional[int] = Query(default=None, ge=2025, description="Filter theo năm"),
) -> dict:
    """
    Lấy danh sách kê khai chờ phê duyệt.
    """
    # Kiểm tra quyền: Phải là Lãnh đạo hoặc Admin hoặc QLDV
    is_admin = getattr(current_user.vai_tro, 'is_system_admin', False) if current_user.vai_tro else False
    is_lanh_dao = current_user.is_lanh_dao or False
    is_qldv_user = is_qldv(current_user)
    
    # Base query
    base_query = (
        select(KeKhaiCongViec)
        .options(
            selectinload(KeKhaiCongViec.cong_chuc).selectinload(CongChuc.don_vi),
            selectinload(KeKhaiCongViec.danh_muc_sp),
            selectinload(KeKhaiCongViec.cap_do),
        )
        .where(KeKhaiCongViec.trang_thai == TrangThaiKeKhai.CHO_PHE_DUYET)
        .where(KeKhaiCongViec.is_deleted == False)
    )
    
    # Count query
    count_query = (
        select(func.count(KeKhaiCongViec.id))
        .where(KeKhaiCongViec.trang_thai == TrangThaiKeKhai.CHO_PHE_DUYET)
        .where(KeKhaiCongViec.is_deleted == False)
    )
    
    # Phân quyền:
    # - Admin/CCT: Thấy tất cả hoặc filter theo đơn vị
    # - QLDV: Thấy tất cả kê khai chờ phê duyệt của đơn vị (không filter theo người phê duyệt)
    # - Lãnh đạo thường: Chỉ thấy những bài mình được gán làm người phê duyệt
    if is_qldv_user and not is_admin:
        # QLDV: Lấy tất cả kê khai chờ phê duyệt của đơn vị
        base_query = (
            base_query
            .join(CongChuc, KeKhaiCongViec.cong_chuc_id == CongChuc.id)
            .where(CongChuc.don_vi_id == current_user.don_vi_id)
        )
        count_query = (
            count_query
            .join(CongChuc, KeKhaiCongViec.cong_chuc_id == CongChuc.id)
            .where(CongChuc.don_vi_id == current_user.don_vi_id)
        )
    elif not is_admin:
        # Chỉ lấy những kê khai mà current_user được gán làm người phê duyệt
        base_query = base_query.where(KeKhaiCongViec.nguoi_phe_duyet_id == current_user.id)
        count_query = count_query.where(KeKhaiCongViec.nguoi_phe_duyet_id == current_user.id)
    
    # Filter theo đơn vị (join với CongChuc)
    if don_vi_id:
        base_query = (
            base_query
            .join(CongChuc, KeKhaiCongViec.cong_chuc_id == CongChuc.id)
            .where(CongChuc.don_vi_id == don_vi_id)
        )
        count_query = (
            count_query
            .join(CongChuc, KeKhaiCongViec.cong_chuc_id == CongChuc.id)
            .where(CongChuc.don_vi_id == don_vi_id)
        )
    
    # Filter theo tháng/năm
    if thang:
        base_query = base_query.where(KeKhaiCongViec.thang == thang)
        count_query = count_query.where(KeKhaiCongViec.thang == thang)
    
    if nam:
        base_query = base_query.where(KeKhaiCongViec.nam == nam)
        count_query = count_query.where(KeKhaiCongViec.nam == nam)
    
    # Get total count
    count_result = await db.execute(count_query)
    total_items = count_result.scalar() or 0
    
    # Apply pagination
    offset = (page - 1) * page_size
    base_query = (
        base_query
        .order_by(KeKhaiCongViec.created_at.asc())  # FIFO: Bài cũ lên trước
        .offset(offset)
        .limit(page_size)
    )
    
    # Execute query
    result = await db.execute(base_query)
    ke_khai_list = result.scalars().all()
    
    # Convert to response
    data = [ke_khai_to_pending_response(kk) for kk in ke_khai_list]
    
    # Build pagination
    pagination = Pagination.create(
        page=page,
        page_size=page_size,
        total_items=total_items,
    )
    
    return {
        "success": True,
        "data": data,
        "pagination": pagination.model_dump(),
    }


# =============================================================================
# XU LY PHE DUYET (Phê duyệt / Từ chối)
# =============================================================================

@router.post(
    "/xu-ly",
    summary="Phê duyệt hoặc từ chối kê khai",
    description="""
    Xử lý phê duyệt cho một hoặc nhiều bản kê khai.
    
    **APPROVE (Phê duyệt):**
    - Cập nhật `trang_thai` → DA_PHE_DUYET
    - Lưu `so_loi_chat_luong`, `so_loi_tien_do`:
      + Nếu LĐ nhập → dùng giá trị LĐ nhập
      + Nếu LĐ không nhập → dùng số lỗi tự đánh giá CC
    - **Tính** `so_sp_chat_luong`, `so_sp_tien_do` (FIX v2.6.0)
    - Lưu `noi_dung_trao_doi` vào `y_kien_lanh_dao`
    
    **REJECT (Từ chối):**
    - Cập nhật `trang_thai` → TU_CHOI
    - Lưu lý do vào `y_kien_lanh_dao`
    - CC có thể sửa và gửi lại
    
    **Quyền truy cập:** Người được gán nguoi_phe_duyet_id.
    """,
    response_model=DataResponse[PheDuyetResponse],
)
async def xu_ly_phe_duyet(
    payload: PheDuyetBulkRequest,
    db: DatabaseDep,
    current_user: ActiveUserDep,
) -> dict:
    """
    Phê duyệt hoặc từ chối một hoặc nhiều kê khai.
    """
    # Block QLDV: QLDV không có quyền phê duyệt
    if is_qldv(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "error": {
                    "code": "PERM_003",
                    "message": "QLDV không có quyền phê duyệt. Chức năng này chỉ dành cho Lãnh đạo có thẩm quyền."
                }
            }
        )

    # Kiểm tra quyền cơ bản: Phải là Lãnh đạo hoặc Admin
    is_admin = getattr(current_user.vai_tro, 'is_system_admin', False) if current_user.vai_tro else False
    is_lanh_dao = current_user.is_lanh_dao or False

    if not (is_admin or is_lanh_dao):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "error": {
                    "code": "PERM_003",
                    "message": "Bạn không có quyền phê duyệt. Chỉ Lãnh đạo mới được phép."
                }
            }
        )
    
    # Lấy danh sách kê khai cần xử lý
    stmt = (
        select(KeKhaiCongViec)
        .options(
            selectinload(KeKhaiCongViec.danh_muc_sp).selectinload(DanhMucSpCongViec.sp_chuan),
            selectinload(KeKhaiCongViec.cap_do),
        )
        .where(KeKhaiCongViec.id.in_(payload.ke_khai_ids))
        .where(KeKhaiCongViec.is_deleted == False)
    )
    result = await db.execute(stmt)
    ke_khai_list = result.scalars().all()
    
    if not ke_khai_list:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": {
                    "code": "NOT_FOUND",
                    "message": "Không tìm thấy bản kê khai nào"
                }
            }
        )
    
    # Validate: Kiểm tra quyền phê duyệt từng bài
    processed_ids = []
    errors = []
    
    for kk in ke_khai_list:
        # Kiểm tra trạng thái
        if kk.trang_thai != TrangThaiKeKhai.CHO_PHE_DUYET:
            errors.append(f"Kê khai {kk.id} không ở trạng thái chờ phê duyệt")
            continue
        
        # Kiểm tra quyền: Phải là người được gán hoặc Admin
        if not is_admin and kk.nguoi_phe_duyet_id != current_user.id:
            errors.append(f"Bạn không phải người phê duyệt kê khai {kk.id}")
            continue
        
        # Xử lý phê duyệt
        if payload.action == PheDuyetAction.APPROVE:
            # =====================================================================
            # APPROVE: Phê duyệt
            # =====================================================================
            kk.trang_thai = TrangThaiKeKhai.DA_PHE_DUYET
            
            # =====================================================================
            # FIX v2.7.0: Cập nhật mức độ nếu LĐ điều chỉnh
            # =====================================================================
            if payload.cap_do_ma is not None:
                await apply_cap_do_change(kk, payload.cap_do_ma, db)
            
            # =====================================================================
            # FIX v2.6.1: Số lỗi chốt = LĐ nhập (nếu có) HOẶC CC tự đánh giá
            # =====================================================================
            kk.so_loi_chat_luong = get_so_loi_chot(
                payload.so_loi_chat_luong,
                kk.tu_danh_gia_chat_luong
            )
            kk.so_loi_tien_do = get_so_loi_chot(
                payload.so_loi_tien_do,
                kk.tu_danh_gia_tien_do
            )
            
            # Lưu ý kiến lãnh đạo
            kk.y_kien_lanh_dao = payload.noi_dung_trao_doi
            
            # =====================================================================
            # FIX v2.6.0: Tính SP chất lượng và tiến độ với công thức ĐÚNG
            # Công thức: SP_đạt = SP_gốc × (1 - 0.25 × min(Lỗi, SL×4) / SL)
            # =====================================================================
            sp_chat_luong, sp_tien_do = tinh_sp_chat_luong_tien_do(
                so_sp_goc=kk.so_sp_goc_quy_doi,
                so_luong=kk.so_luong,
                so_loi_chat_luong=kk.so_loi_chat_luong,
                so_loi_tien_do=kk.so_loi_tien_do,
            )
            kk.so_sp_chat_luong = sp_chat_luong
            kk.so_sp_tien_do = sp_tien_do
            
        else:
            # =====================================================================
            # REJECT: Từ chối / Yêu cầu sửa
            # =====================================================================
            kk.trang_thai = TrangThaiKeKhai.TU_CHOI
            
            # Lưu lý do từ chối
            kk.y_kien_lanh_dao = payload.noi_dung_trao_doi
        
        processed_ids.append(kk.id)
    
    # Nếu có lỗi và không xử lý được bài nào
    if not processed_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "error": {
                    "code": "PROCESS_FAILED",
                    "message": "Không xử lý được bài nào",
                    "details": errors
                }
            }
        )
    
    # Commit changes
    try:
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "error": {
                    "code": "DB_ERROR",
                    "message": f"Lỗi khi lưu dữ liệu: {str(e)}"
                }
            }
        )
    
    # Tạo response
    trang_thai_moi = "DA_PHE_DUYET" if payload.action == PheDuyetAction.APPROVE else "TU_CHOI"
    action_text = "phê duyệt" if payload.action == PheDuyetAction.APPROVE else "từ chối"
    
    response_data = {
        "success": True,
        "message": f"Đã {action_text} {len(processed_ids)} bản kê khai",
        "processed_count": len(processed_ids),
        "ke_khai_ids": processed_ids,
        "trang_thai_moi": trang_thai_moi,
    }
    
    # Nếu có errors, thêm vào response
    if errors:
        response_data["warnings"] = errors
    
    return success_response(data=response_data)


# =============================================================================
# XU LY DON LE (Phê duyệt từng bài)
# =============================================================================

@router.post(
    "/{ke_khai_id}",
    summary="Phê duyệt/từ chối một kê khai",
    description="""
    Xử lý phê duyệt cho một bản kê khai cụ thể.
    
    **FIX v2.6.1:** Số lỗi chốt = LĐ nhập (nếu có) HOẶC CC tự đánh giá.
    **FIX v2.6.0:** Sửa công thức tính so_sp_chat_luong và so_sp_tien_do.
    
    **Quyền truy cập:** Người được gán nguoi_phe_duyet_id.
    """,
    response_model=DataResponse[dict],
)
async def xu_ly_phe_duyet_don_le(
    ke_khai_id: UUID,
    payload: PheDuyetRequest,
    db: DatabaseDep,
    current_user: ActiveUserDep,
) -> dict:
    """
    Phê duyệt hoặc từ chối một kê khai cụ thể.
    """
    # Block QLDV: QLDV không có quyền phê duyệt
    if is_qldv(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "error": {
                    "code": "PERM_003",
                    "message": "QLDV không có quyền phê duyệt. Chức năng này chỉ dành cho Lãnh đạo có thẩm quyền."
                }
            }
        )

    # Lấy kê khai
    stmt = (
        select(KeKhaiCongViec)
        .options(
            selectinload(KeKhaiCongViec.cong_chuc),
            selectinload(KeKhaiCongViec.danh_muc_sp).selectinload(DanhMucSpCongViec.sp_chuan),
            selectinload(KeKhaiCongViec.cap_do),
        )
        .where(KeKhaiCongViec.id == ke_khai_id)
        .where(KeKhaiCongViec.is_deleted == False)
    )
    result = await db.execute(stmt)
    ke_khai = result.scalar_one_or_none()
    
    if not ke_khai:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": {
                    "code": "NOT_FOUND",
                    "message": "Không tìm thấy bản kê khai"
                }
            }
        )
    
    # Kiểm tra trạng thái
    if ke_khai.trang_thai != TrangThaiKeKhai.CHO_PHE_DUYET:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "error": {
                    "code": "INVALID_STATE",
                    "message": f"Kê khai không ở trạng thái chờ phê duyệt (hiện tại: {ke_khai.trang_thai.value})"
                }
            }
        )
    
    # Kiểm tra quyền
    is_admin = getattr(current_user.vai_tro, 'is_system_admin', False) if current_user.vai_tro else False
    
    if not is_admin and ke_khai.nguoi_phe_duyet_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "error": {
                    "code": "PERM_003",
                    "message": "Bạn không phải người được gán phê duyệt kê khai này"
                }
            }
        )
    
    # Xử lý phê duyệt
    if payload.action == PheDuyetAction.APPROVE:
        ke_khai.trang_thai = TrangThaiKeKhai.DA_PHE_DUYET
        
        # =====================================================================
        # FIX v2.7.0: Cập nhật mức độ nếu LĐ điều chỉnh
        # =====================================================================
        if payload.cap_do_ma is not None:
            await apply_cap_do_change(ke_khai, payload.cap_do_ma, db)
        
        # =====================================================================
        # FIX v2.6.1: Số lỗi chốt = LĐ nhập (nếu có) HOẶC CC tự đánh giá
        # =====================================================================
        ke_khai.so_loi_chat_luong = get_so_loi_chot(
            payload.so_loi_chat_luong,
            ke_khai.tu_danh_gia_chat_luong
        )
        ke_khai.so_loi_tien_do = get_so_loi_chot(
            payload.so_loi_tien_do,
            ke_khai.tu_danh_gia_tien_do
        )
        
        ke_khai.y_kien_lanh_dao = payload.noi_dung_trao_doi
        
        # =====================================================================
        # FIX v2.6.0: Tính SP chất lượng và tiến độ với công thức ĐÚNG
        # =====================================================================
        sp_chat_luong, sp_tien_do = tinh_sp_chat_luong_tien_do(
            so_sp_goc=ke_khai.so_sp_goc_quy_doi,
            so_luong=ke_khai.so_luong,
            so_loi_chat_luong=ke_khai.so_loi_chat_luong,
            so_loi_tien_do=ke_khai.so_loi_tien_do,
        )
        ke_khai.so_sp_chat_luong = sp_chat_luong
        ke_khai.so_sp_tien_do = sp_tien_do
        
        action_text = "phê duyệt"
    else:
        ke_khai.trang_thai = TrangThaiKeKhai.TU_CHOI
        ke_khai.y_kien_lanh_dao = payload.noi_dung_trao_doi
        action_text = "từ chối"
    
    try:
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "error": {
                    "code": "DB_ERROR",
                    "message": f"Lỗi khi lưu dữ liệu: {str(e)}"
                }
            }
        )
    
    return success_response(
        data={
            "ke_khai_id": ke_khai_id,
            "action": payload.action.value,
            "trang_thai_moi": ke_khai.trang_thai.value,
            "so_loi_chat_luong": ke_khai.so_loi_chat_luong,
            "so_loi_tien_do": ke_khai.so_loi_tien_do,
            # FIX v2.6.0: Trả về SP đã tính đúng
            "so_sp_chat_luong": float(ke_khai.so_sp_chat_luong) if ke_khai.so_sp_chat_luong else 0,
            "so_sp_tien_do": float(ke_khai.so_sp_tien_do) if ke_khai.so_sp_tien_do else 0,
        },
        message=f"Đã {action_text} kê khai thành công"
    )


# =============================================================================
# TRẢ LẠI KÊ KHAI ĐÃ PHÊ DUYỆT (MỚI v3.0.0)
# =============================================================================

@router.post(
    "/{ke_khai_id}/tra-lai",
    summary="Trả lại kê khai đã phê duyệt",
    description="""
    Trả lại kê khai đã phê duyệt nhầm về trạng thái NHAP.
    
    **Logic:**
    - Chuyển trạng thái: DA_PHE_DUYET → NHAP
    - Reset các giá trị đã chốt: so_loi_chat_luong, so_loi_tien_do, so_sp_chat_luong, so_sp_tien_do
    - Lưu lý do trả lại vào y_kien_lanh_dao
    - Chỉ người đã phê duyệt (nguoi_phe_duyet_id) hoặc Admin mới được trả lại
    
    **Quyền truy cập:** Lãnh đạo đã phê duyệt hoặc Admin.
    """,
    response_model=DataResponse[dict],
)
async def tra_lai_ke_khai(
    ke_khai_id: UUID,
    payload: TraLaiRequest,
    db: DatabaseDep,
    current_user: ActiveUserDep,
) -> dict:
    """Trả lại kê khai đã phê duyệt."""
    # Kiểm tra quyền cơ bản: Admin, Lãnh đạo, hoặc QLDV
    is_admin = getattr(current_user.vai_tro, 'is_system_admin', False) if current_user.vai_tro else False
    is_lanh_dao = current_user.is_lanh_dao or False
    is_qldv_user = is_qldv(current_user)

    if not (is_admin or is_lanh_dao or is_qldv_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "error": {
                    "code": "PERM_003",
                    "message": "Chỉ Lãnh đạo hoặc QLDV mới có quyền trả lại kê khai."
                }
            }
        )
    
    # Lấy kê khai
    stmt = (
        select(KeKhaiCongViec)
        .options(selectinload(KeKhaiCongViec.cong_chuc))
        .where(KeKhaiCongViec.id == ke_khai_id)
        .where(KeKhaiCongViec.is_deleted == False)
    )
    result = await db.execute(stmt)
    ke_khai = result.scalar_one_or_none()

    if not ke_khai:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": {"code": "NOT_FOUND", "message": "Không tìm thấy bản kê khai"}
            }
        )

    # Kiểm tra trạng thái: chỉ trả lại được khi DA_PHE_DUYET
    if ke_khai.trang_thai != TrangThaiKeKhai.DA_PHE_DUYET:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "error": {
                    "code": "INVALID_STATE",
                    "message": f"Chỉ trả lại được kê khai ở trạng thái ĐÃ PHÊ DUYỆT (hiện tại: {ke_khai.trang_thai.value})"
                }
            }
        )

    # Kiểm tra quyền:
    # - Admin: luôn được phép
    # - Người đã phê duyệt: được phép
    # - QLDV: được phép nếu cùng đơn vị
    is_same_don_vi = (ke_khai.cong_chuc and ke_khai.cong_chuc.don_vi_id == current_user.don_vi_id)

    if not is_admin:
        if is_qldv_user:
            # QLDV: chỉ được trả lại kê khai của đơn vị mình
            if not is_same_don_vi:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "success": False,
                        "error": {
                            "code": "PERM_003",
                            "message": "QLDV chỉ được trả lại kê khai của đơn vị mình"
                        }
                    }
                )
        elif ke_khai.nguoi_phe_duyet_id != current_user.id:
            # Lãnh đạo thường: chỉ được trả lại kê khai mình đã phê duyệt
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "success": False,
                    "error": {
                        "code": "PERM_003",
                        "message": "Bạn không phải người đã phê duyệt kê khai này"
                    }
                }
            )
    
    # === TRẢ LẠI ===
    ke_khai.trang_thai = TrangThaiKeKhai.NHAP
    ke_khai.y_kien_lanh_dao = f"[TRẢ LẠI] {payload.ly_do}"
    
    # Reset các giá trị đã chốt
    ke_khai.so_loi_chat_luong = 0
    ke_khai.so_loi_tien_do = 0
    ke_khai.so_sp_chat_luong = None
    ke_khai.so_sp_tien_do = None
    
    try:
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"success": False, "error": {"code": "DB_ERROR", "message": f"Lỗi: {str(e)}"}}
        )
    
    return success_response(
        data={
            "ke_khai_id": str(ke_khai_id),
            "trang_thai_moi": "NHAP",
            "ly_do": payload.ly_do,
        },
        message="Đã trả lại kê khai thành công. Công chức có thể sửa và gửi lại."
    )


@router.post(
    "/tra-lai-bulk",
    summary="Trả lại nhiều kê khai đã phê duyệt",
    description="Trả lại hàng loạt kê khai đã phê duyệt nhầm về trạng thái NHAP.",
    response_model=DataResponse[dict],
)
async def tra_lai_ke_khai_bulk(
    payload: TraLaiBulkRequest,
    db: DatabaseDep,
    current_user: ActiveUserDep,
) -> dict:
    """Trả lại nhiều kê khai đã phê duyệt."""
    is_admin = getattr(current_user.vai_tro, 'is_system_admin', False) if current_user.vai_tro else False
    is_lanh_dao = current_user.is_lanh_dao or False
    is_qldv_user = is_qldv(current_user)

    if not (is_admin or is_lanh_dao or is_qldv_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"success": False, "error": {"code": "PERM_003", "message": "Chỉ Lãnh đạo hoặc QLDV"}}
        )
    
    stmt = (
        select(KeKhaiCongViec)
        .options(selectinload(KeKhaiCongViec.cong_chuc))
        .where(KeKhaiCongViec.id.in_(payload.ke_khai_ids))
        .where(KeKhaiCongViec.is_deleted == False)
    )
    result = await db.execute(stmt)
    ke_khai_list = result.scalars().all()

    processed_ids = []
    errors = []

    for kk in ke_khai_list:
        if kk.trang_thai != TrangThaiKeKhai.DA_PHE_DUYET:
            errors.append(f"KK {kk.id}: không ở trạng thái DA_PHE_DUYET")
            continue

        # Kiểm tra quyền
        if not is_admin:
            is_same_don_vi = (kk.cong_chuc and kk.cong_chuc.don_vi_id == current_user.don_vi_id)

            if is_qldv_user:
                # QLDV: chỉ được trả lại kê khai của đơn vị mình
                if not is_same_don_vi:
                    errors.append(f"KK {kk.id}: không thuộc đơn vị của QLDV")
                    continue
            elif kk.nguoi_phe_duyet_id != current_user.id:
                # Lãnh đạo thường: chỉ được trả lại kê khai mình đã phê duyệt
                errors.append(f"KK {kk.id}: không phải người phê duyệt")
                continue
        
        kk.trang_thai = TrangThaiKeKhai.NHAP
        kk.y_kien_lanh_dao = f"[TRẢ LẠI] {payload.ly_do}"
        kk.so_loi_chat_luong = 0
        kk.so_loi_tien_do = 0
        kk.so_sp_chat_luong = None
        kk.so_sp_tien_do = None
        processed_ids.append(kk.id)
    
    if not processed_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"success": False, "error": {"code": "PROCESS_FAILED", "message": "Không trả lại được bài nào", "details": errors}}
        )
    
    try:
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"success": False, "error": {"code": "DB_ERROR", "message": str(e)}}
        )
    
    response_data = {
        "processed_count": len(processed_ids),
        "ke_khai_ids": processed_ids,
        "trang_thai_moi": "NHAP",
    }
    if errors:
        response_data["warnings"] = errors
    
    return success_response(data=response_data, message=f"Đã trả lại {len(processed_ids)} kê khai")


# =============================================================================
# THONG KE PENDING
# =============================================================================

@router.get(
    "/thong-ke",
    summary="Thống kê kê khai chờ phê duyệt",
    description="""
    Lấy thống kê số lượng kê khai chờ phê duyệt.
    
    **Quyền truy cập:** Lãnh đạo hoặc Admin.
    """,
    response_model=DataResponse[dict],
)
async def get_pending_stats(
    db: DatabaseDep,
    current_user: ActiveUserDep,
) -> dict:
    """
    Thống kê kê khai chờ phê duyệt.
    """
    is_admin = getattr(current_user.vai_tro, 'is_system_admin', False) if current_user.vai_tro else False
    is_qldv_user = is_qldv(current_user)

    # Query thống kê
    stats_query = (
        select(
            func.count(KeKhaiCongViec.id).label("tong_cho_duyet"),
            func.sum(KeKhaiCongViec.so_sp_goc_quy_doi).label("tong_sp"),
        )
        .where(KeKhaiCongViec.trang_thai == TrangThaiKeKhai.CHO_PHE_DUYET)
        .where(KeKhaiCongViec.is_deleted == False)
    )

    # Phân quyền:
    # - Admin: thống kê tất cả
    # - QLDV: thống kê đơn vị
    # - Lãnh đạo: thống kê công việc được gán
    if is_qldv_user and not is_admin:
        stats_query = (
            stats_query
            .join(CongChuc, KeKhaiCongViec.cong_chuc_id == CongChuc.id)
            .where(CongChuc.don_vi_id == current_user.don_vi_id)
        )
    elif not is_admin:
        stats_query = stats_query.where(KeKhaiCongViec.nguoi_phe_duyet_id == current_user.id)
    
    result = await db.execute(stats_query)
    row = result.one()
    
    return success_response(
        data={
            "tong_cho_duyet": row.tong_cho_duyet or 0,
            "tong_sp_quy_doi": float(row.tong_sp) if row.tong_sp else 0,
        }
    )


@router.get(
    "/lich-su",
    summary="Lấy lịch sử phê duyệt kê khai",
    description="Lấy danh sách các bản kê khai đã được xử lý (DA_PHE_DUYET hoặc TU_CHOI).",
)
async def get_lich_su_phe_duyet(
    db: DatabaseDep,
    current_user: ActiveUserDep,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    trang_thai: Optional[str] = Query(default=None, description="DA_PHE_DUYET | TU_CHOI | null"),
    don_vi_id: Optional[UUID] = Query(default=None),
    thang: Optional[int] = Query(default=None, ge=1, le=12),
    nam: Optional[int] = Query(default=None, ge=2025),
) -> dict:
    is_admin = getattr(current_user.vai_tro, 'is_system_admin', False) if current_user.vai_tro else False
    is_qldv_user = is_qldv(current_user)

    base_query = (
        select(KeKhaiCongViec)
        .options(
            selectinload(KeKhaiCongViec.cong_chuc).selectinload(CongChuc.don_vi),
            selectinload(KeKhaiCongViec.danh_muc_sp),
            selectinload(KeKhaiCongViec.cap_do),
        )
        .where(KeKhaiCongViec.is_deleted == False)
    )

    # Filter trạng thái
    if trang_thai == "DA_PHE_DUYET":
        base_query = base_query.where(KeKhaiCongViec.trang_thai == TrangThaiKeKhai.DA_PHE_DUYET)
    elif trang_thai == "TU_CHOI":
        base_query = base_query.where(KeKhaiCongViec.trang_thai == TrangThaiKeKhai.TU_CHOI)
    else:
        base_query = base_query.where(
            KeKhaiCongViec.trang_thai.in_([TrangThaiKeKhai.DA_PHE_DUYET, TrangThaiKeKhai.TU_CHOI])
        )

    # Phân quyền:
    # - Admin: xem tất cả
    # - QLDV: xem tất cả kê khai đã xử lý của đơn vị
    # - Lãnh đạo: chỉ xem kê khai mà mình đã phê duyệt
    if is_qldv_user and not is_admin:
        base_query = (
            base_query
            .join(CongChuc, KeKhaiCongViec.cong_chuc_id == CongChuc.id)
            .where(CongChuc.don_vi_id == current_user.don_vi_id)
        )
    elif not is_admin:
        base_query = base_query.where(KeKhaiCongViec.nguoi_phe_duyet_id == current_user.id)
    
    # Filter đơn vị
    if don_vi_id:
        base_query = base_query.join(CongChuc, KeKhaiCongViec.cong_chuc_id == CongChuc.id).where(CongChuc.don_vi_id == don_vi_id)
    
    # Filter tháng/năm
    if thang:
        base_query = base_query.where(KeKhaiCongViec.thang == thang)
    if nam:
        base_query = base_query.where(KeKhaiCongViec.nam == nam)
    
    # Count
    count_query = select(func.count()).select_from(base_query.subquery())
    total_items = (await db.execute(count_query)).scalar() or 0
    
    # Pagination
    offset = (page - 1) * page_size
    base_query = base_query.order_by(KeKhaiCongViec.updated_at.desc()).offset(offset).limit(page_size)
    
    result = await db.execute(base_query)
    ke_khai_list = result.scalars().all()
    
    data = [ke_khai_to_pending_response(kk) for kk in ke_khai_list]
    
    return {
        "success": True,
        "data": data,
        "pagination": Pagination.create(page=page, page_size=page_size, total_items=total_items).model_dump(),
    }