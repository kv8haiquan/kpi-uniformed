"""
app/api/v1/endpoints/nghi_phep.py
=================================
API Endpoints cho Quản lý Nghỉ phép (Leave Management).

Đặc thù nghiệp vụ Hải quan:
- Công chức làm việc theo CA/KÍP, KHÔNG nghỉ cố định T7/CN
- CC phải đăng ký NGHI_TUAN trên hệ thống cho ngày nghỉ tuần
- Công thức KPI: SP_được_giao = (Ngày_dương_lịch - Ngày_nghỉ_đã_duyệt) × 96

Endpoints:
- GET /nghi-phep/nguoi-phe-duyet: Lấy DS người phê duyệt phù hợp
- GET /nghi-phep: DS đơn nghỉ của bản thân
- GET /nghi-phep/{id}: Chi tiết đơn nghỉ
- POST /nghi-phep: Tạo đơn nghỉ đơn lẻ
- POST /nghi-phep/bulk: Đăng ký nghỉ tuần hàng loạt
- PUT /nghi-phep/{id}: Cập nhật đơn
- DELETE /nghi-phep/{id}: Xóa/Hủy đơn
- GET /nghi-phep/cho-phe-duyet: DS chờ tôi phê duyệt
- POST /nghi-phep/{id}/phe-duyet: Phê duyệt (1 CẤP)
- POST /nghi-phep/{id}/tu-choi: Từ chối (1 CẤP)
- GET /nghi-phep/thong-ke: Thống kê cá nhân
- GET /nghi-phep/thong-ke/don-vi/{don_vi_id}: Thống kê đơn vị

Phiên bản: 3.1.0 (01/02/2026) - FIX cho phép đăng ký nghỉ trùng ngày (LEAVE_005)
  - v3.1: Thêm check_overlap_nghi_phep() + find_existing_dates_for_bulk()
    + create_nghi_phep: Raise LEAVE_005 nếu trùng ngày với đơn active
    + create_nghi_phep_bulk: Skip ngày trùng, trả ngay_da_ton_tai trong response
    + update_nghi_phep: Check trùng ngày khi sửa (exclude chính đơn đang sửa)
  - v3.0.1: FIX route order conflict
  - v3.0: PHÊ DUYỆT 1 CẤP (ĐT duyệt là xong)
"""

import calendar
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, func, and_, or_, case
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import DatabaseDep, ActiveUserDep
from app.models.leave import DangKyNghi, LoaiNghi, TrangThaiNghi
from app.models.user_org import CongChuc, VaiTro, CapBacVaiTro, DonVi
from app.schemas.common import (
    success_response,
    error_response,
)
from app.schemas.leave import (
    LoaiNghiEnum,
    TrangThaiNghiEnum,
    NghiPhepCreate,
    NghiPhepBulkCreate,
    NghiPhepUpdate,
    PheDuyetNghiPhepRequest,
    TuChoiNghiPhepRequest,
    NghiPhepResponse,
    NghiPhepBulkResponse,
    CongChucNghiPhepBrief,
    ThongKeNghiPhepLoai,
    ThongKeNghiPhepThang,
    ThongKeNghiPhepCaNhan,
    ThongKeNghiPhepDonVi,
    ThongKeNghiPhepTongHop,
    ThongKeNghiPhepCC,
    TongNgayNghiThangResponse,
)


router = APIRouter()


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def build_nghi_phep_response(nghi: DangKyNghi) -> dict:
    """
    Chuyển đổi DangKyNghi model thành response dict.
    v3.0: Đơn giản hóa - chỉ 1 cấp phê duyệt
    """
    # Thông tin người đăng ký
    cong_chuc_data = None
    if nghi.cong_chuc:
        cc = nghi.cong_chuc
        cong_chuc_data = {
            "id": cc.id,
            "ma_cc": cc.ma_cc,
            "ho_ten": cc.ho_ten,
            "chuc_vu": cc.chuc_vu,
            "don_vi_ten": cc.don_vi.ten_don_vi if cc.don_vi else None,
        }
    
    # Thông tin người phê duyệt (chỉ 1 cấp)
    nguoi_phe_duyet_data = None
    if nghi.nguoi_phe_duyet:
        npd = nghi.nguoi_phe_duyet
        nguoi_phe_duyet_data = {
            "id": npd.id,
            "ma_cc": npd.ma_cc,
            "ho_ten": npd.ho_ten,
            "chuc_vu": npd.chuc_vu,
            "don_vi_ten": npd.don_vi.ten_don_vi if npd.don_vi else None,
        }
    
    return {
        "id": nghi.id,
        "cong_chuc_id": nghi.cong_chuc_id,
        "cong_chuc": cong_chuc_data,
        "loai_nghi": nghi.loai_nghi.value,
        "loai_nghi_ten": nghi.loai_nghi_ten,
        "tu_ngay": nghi.tu_ngay,
        "den_ngay": nghi.den_ngay,
        "so_ngay": float(nghi.so_ngay),
        "ly_do": nghi.ly_do,
        "tai_lieu_dinh_kem": nghi.tai_lieu_dinh_kem,
        
        # Phê duyệt (1 cấp)
        "nguoi_phe_duyet_id": nghi.nguoi_phe_duyet_id,
        "nguoi_phe_duyet": nguoi_phe_duyet_data,
        
        # Trạng thái
        "trang_thai": nghi.trang_thai.value,
        "trang_thai_ten": nghi.trang_thai_ten,
        "ly_do_tu_choi": nghi.ly_do_tu_choi,
        "ngay_phe_duyet": nghi.ngay_phe_duyet.isoformat() if nghi.ngay_phe_duyet else None,
        "ghi_chu_phe_duyet": nghi.ghi_chu_phe_duyet,
        
        # Liên kết KPI
        "thang_ap_dung": nghi.thang_ap_dung,
        "nam_ap_dung": nghi.nam_ap_dung,
        "da_tinh_kpi": nghi.da_tinh_kpi,
        
        # Khóa dữ liệu
        "is_khoa": nghi.is_khoa,
        
        # Timestamps
        "created_at": nghi.created_at.isoformat() if nghi.created_at else None,
        "updated_at": nghi.updated_at.isoformat() if nghi.updated_at else None,
    }


async def auto_assign_thang_ap_dung(nghi: DangKyNghi) -> None:
    """
    Tự động gán thang_ap_dung và nam_ap_dung dựa trên tu_ngay.
    Nếu nghỉ qua nhiều tháng, lấy tháng của tu_ngay.
    """
    if nghi.tu_ngay:
        nghi.thang_ap_dung = nghi.tu_ngay.month
        nghi.nam_ap_dung = nghi.tu_ngay.year


# =============================================================================
# KIỂM TRA TRÙNG NGÀY NGHỈ (LEAVE_005) - v3.1
# =============================================================================

async def check_overlap_nghi_phep(
    db: AsyncSession,
    cong_chuc_id: UUID,
    tu_ngay: date,
    den_ngay: date,
    exclude_id: Optional[UUID] = None,
) -> Optional[DangKyNghi]:
    """
    Kiểm tra khoảng ngày [tu_ngay, den_ngay] có trùng với đơn nghỉ
    đang active (CHO_PHE_DUYET, DA_PHE_DUYET) của cùng công chức không.

    Logic overlap: existing.tu_ngay <= den_ngay AND existing.den_ngay >= tu_ngay

    Args:
        db: Database session
        cong_chuc_id: ID công chức cần check
        tu_ngay: Ngày bắt đầu nghỉ mới
        den_ngay: Ngày kết thúc nghỉ mới
        exclude_id: Bỏ qua đơn này (dùng khi update)

    Returns:
        DangKyNghi đầu tiên bị trùng, hoặc None nếu không trùng
    """
    active_statuses = [
        TrangThaiNghi.CHO_PHE_DUYET,
        TrangThaiNghi.DA_PHE_DUYET,
    ]

    stmt = (
        select(DangKyNghi)
        .where(DangKyNghi.is_deleted == False)
        .where(DangKyNghi.cong_chuc_id == cong_chuc_id)
        .where(DangKyNghi.trang_thai.in_(active_statuses))
        .where(DangKyNghi.tu_ngay <= den_ngay)
        .where(DangKyNghi.den_ngay >= tu_ngay)
    )

    if exclude_id:
        stmt = stmt.where(DangKyNghi.id != exclude_id)

    result = await db.execute(stmt.limit(1))
    return result.scalar_one_or_none()


async def find_existing_dates_for_bulk(
    db: AsyncSession,
    cong_chuc_id: UUID,
    danh_sach_ngay: List[date],
) -> List[date]:
    """
    Tìm các ngày trong danh_sach_ngay đã có đơn nghỉ active.
    Dùng cho bulk create để skip ngày trùng thay vì tạo duplicate.

    Returns:
        List các ngày đã tồn tại đơn nghỉ (CHO_PHE_DUYET hoặc DA_PHE_DUYET)
    """
    if not danh_sach_ngay:
        return []

    min_ngay = min(danh_sach_ngay)
    max_ngay = max(danh_sach_ngay)

    active_statuses = [
        TrangThaiNghi.CHO_PHE_DUYET,
        TrangThaiNghi.DA_PHE_DUYET,
    ]

    # Query tất cả đơn active trong khoảng ngày
    stmt = (
        select(DangKyNghi.tu_ngay, DangKyNghi.den_ngay)
        .where(DangKyNghi.is_deleted == False)
        .where(DangKyNghi.cong_chuc_id == cong_chuc_id)
        .where(DangKyNghi.trang_thai.in_(active_statuses))
        .where(DangKyNghi.tu_ngay <= max_ngay)
        .where(DangKyNghi.den_ngay >= min_ngay)
    )

    result = await db.execute(stmt)
    existing_ranges = result.all()

    # Build set các ngày đã có đơn
    existing_dates = set()
    for row in existing_ranges:
        current = row.tu_ngay
        while current <= row.den_ngay:
            existing_dates.add(current)
            current += timedelta(days=1)

    # Trả về các ngày trong request mà đã tồn tại
    return [ngay for ngay in danh_sach_ngay if ngay in existing_dates]


# =============================================================================
# SMART AUTO-ASSIGN APPROVER - v3.0: CHỈ 1 CẤP
# =============================================================================

async def find_approver(
    db: AsyncSession,
    user: CongChuc,
) -> Optional[CongChuc]:
    """
    🔄 TÌM NGƯỜI PHÊ DUYỆT TỰ ĐỘNG - v3.0: CHỈ 1 CẤP
    
    Quy tắc nghiệp vụ (đơn giản hóa):
    ┌─────────────────────────────────────────────────────────────────┐
    │  User là ai?       │  Người duyệt là?                          │
    ├────────────────────┼────────────────────────────────────────────┤
    │  CCT               │  Tự phê duyệt (trả về chính mình)         │
    │  PCCT              │  CCT                                       │
    │  TDV (Đội trưởng)  │  CCT                                       │
    │  PDV (Phó ĐT)      │  TDV cùng đơn vị → fallback CCT           │
    │  CC                │  TDV cùng đơn vị → fallback CCT           │
    └─────────────────────────────────────────────────────────────────┘
    
    Returns:
        CongChuc: Người phê duyệt phù hợp
        None: Nếu không tìm được ai (trường hợp hiếm)
    """
    # Lấy cấp bậc của user
    user_cap_bac = None
    if user.vai_tro:
        user_cap_bac = user.vai_tro.cap_bac
    
    # -------------------------------------------------------------------------
    # CASE 1: CCT → Tự phê duyệt
    # -------------------------------------------------------------------------
    if user_cap_bac == CapBacVaiTro.CHI_CUC_TRUONG:
        return user  # Trả về chính user
    
    # -------------------------------------------------------------------------
    # CASE 2: PCCT hoặc TDV → Tìm CCT
    # -------------------------------------------------------------------------
    if user_cap_bac in [CapBacVaiTro.PHO_CHI_CUC_TRUONG, CapBacVaiTro.TRUONG_DON_VI]:
        stmt = (
            select(CongChuc)
            .join(VaiTro, CongChuc.vai_tro_id == VaiTro.id)
            .where(CongChuc.is_deleted == False)
            .where(CongChuc.is_active == True)
            .where(VaiTro.cap_bac == CapBacVaiTro.CHI_CUC_TRUONG)
            .limit(1)
        )
        result = await db.execute(stmt)
        cct = result.scalar_one_or_none()
        return cct  # Có thể None nếu không có CCT (hiếm)
    
    # -------------------------------------------------------------------------
    # CASE 3: PDV, CC, hoặc role khác → Tìm TDV (Đội trưởng) cùng đơn vị
    # -------------------------------------------------------------------------
    
    # Bước 3.1: Tìm Trưởng đơn vị (TDV) cùng don_vi_id
    stmt_tdv = (
        select(CongChuc)
        .join(VaiTro, CongChuc.vai_tro_id == VaiTro.id)
        .where(CongChuc.is_deleted == False)
        .where(CongChuc.is_active == True)
        .where(CongChuc.don_vi_id == user.don_vi_id)  # Cùng đơn vị
        .where(VaiTro.cap_bac == CapBacVaiTro.TRUONG_DON_VI)
        .limit(1)
    )
    result_tdv = await db.execute(stmt_tdv)
    truong_don_vi = result_tdv.scalar_one_or_none()
    
    if truong_don_vi:
        # Tìm thấy TDV cùng đơn vị
        return truong_don_vi
    
    # Bước 3.2: Không có TDV → Fallback tìm CCT
    stmt_cct = (
        select(CongChuc)
        .join(VaiTro, CongChuc.vai_tro_id == VaiTro.id)
        .where(CongChuc.is_deleted == False)
        .where(CongChuc.is_active == True)
        .where(VaiTro.cap_bac == CapBacVaiTro.CHI_CUC_TRUONG)
        .limit(1)
    )
    result_cct = await db.execute(stmt_cct)
    cct = result_cct.scalar_one_or_none()
    
    return cct  # Có thể None nếu không có CCT


async def get_approver_list_for_user(
    db: AsyncSession,
    current_user: CongChuc,
) -> List[CongChuc]:
    """
    Lấy DANH SÁCH người phê duyệt để hiển thị cho user chọn (dropdown).
    v3.0: Đơn giản hóa - chỉ 1 cấp
    
    Logic:
    - Admin → Tất cả Lãnh đạo
    - CCT → Danh sách rỗng (tự phê duyệt)
    - PCCT/TDV → Các CCT
    - PDV/CC → Các TDV cùng đơn vị (fallback CCT)
    """
    user_cap_bac = None
    is_admin = False
    
    if current_user.vai_tro:
        user_cap_bac = current_user.vai_tro.cap_bac
        is_admin = getattr(current_user.vai_tro, 'is_system_admin', False) or False
    
    # Admin → Tất cả Lãnh đạo
    if is_admin:
        stmt = (
            select(CongChuc)
            .join(VaiTro, CongChuc.vai_tro_id == VaiTro.id)
            .where(CongChuc.is_deleted == False)
            .where(CongChuc.is_active == True)
            .where(VaiTro.is_lanh_dao == True)
            .order_by(VaiTro.cap_bac, CongChuc.ho_ten)
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())
    
    # CCT → Tự phê duyệt (không cần chọn)
    if user_cap_bac == CapBacVaiTro.CHI_CUC_TRUONG:
        return []
    
    # Phó CCT / Trưởng ĐV → Danh sách CCT
    if user_cap_bac in [CapBacVaiTro.PHO_CHI_CUC_TRUONG, CapBacVaiTro.TRUONG_DON_VI]:
        stmt = (
            select(CongChuc)
            .join(VaiTro, CongChuc.vai_tro_id == VaiTro.id)
            .where(CongChuc.is_deleted == False)
            .where(CongChuc.is_active == True)
            .where(VaiTro.cap_bac == CapBacVaiTro.CHI_CUC_TRUONG)
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())
    
    # Phó ĐV / CC / Khác → Danh sách TDV cùng đơn vị
    stmt = (
        select(CongChuc)
        .join(VaiTro, CongChuc.vai_tro_id == VaiTro.id)
        .where(CongChuc.is_deleted == False)
        .where(CongChuc.is_active == True)
        .where(CongChuc.don_vi_id == current_user.don_vi_id)
        .where(VaiTro.cap_bac == CapBacVaiTro.TRUONG_DON_VI)
    )
    result = await db.execute(stmt)
    tdv_list = list(result.scalars().all())
    
    # Nếu đơn vị không có TDV → fallback CCT
    if not tdv_list:
        stmt_cct = (
            select(CongChuc)
            .join(VaiTro, CongChuc.vai_tro_id == VaiTro.id)
            .where(CongChuc.is_deleted == False)
            .where(CongChuc.is_active == True)
            .where(VaiTro.cap_bac == CapBacVaiTro.CHI_CUC_TRUONG)
        )
        result_cct = await db.execute(stmt_cct)
        return list(result_cct.scalars().all())
    
    return tdv_list


# =============================================================================
# GET NGUOI PHE DUYET (Đặt trước các route có path variable)
# =============================================================================

@router.get("/nguoi-phe-duyet")
async def get_nguoi_phe_duyet(
    db: DatabaseDep,
    current_user: ActiveUserDep,
) -> dict:
    """
    Lấy danh sách người phê duyệt phù hợp với cấp bậc của user.
    
    Luồng phê duyệt nghỉ phép (v3.0 - 1 CẤP):
    - CC/PDV → Trưởng ĐV cùng đơn vị (Đội trưởng duyệt là xong)
    - PCCT/TDV → Chi cục trưởng
    - CCT → Tự phê duyệt
    """
    approvers = await get_approver_list_for_user(db, current_user)
    
    data = [
        {
            "id": a.id,
            "ma_cc": a.ma_cc,
            "ho_ten": a.ho_ten,
            "chuc_vu": a.chuc_vu,
            "don_vi_ten": a.don_vi.ten_don_vi if a.don_vi else None,
        }
        for a in approvers
    ]
    
    return success_response(data=data)


# =============================================================================
# GET DANH SÁCH CHỜ PHÊ DUYỆT
# =============================================================================

@router.get("/cho-phe-duyet")
async def get_cho_phe_duyet(
    db: DatabaseDep,
    current_user: ActiveUserDep,
) -> dict:
    """
    Lấy danh sách đơn nghỉ phép chờ tôi phê duyệt.
    v3.0: Chỉ 1 cấp - ai được assign làm nguoi_phe_duyet thì duyệt
    """
    # Query đơn chờ duyệt mà current_user là người phê duyệt
    stmt = (
        select(DangKyNghi)
        .options(
            selectinload(DangKyNghi.cong_chuc).selectinload(CongChuc.don_vi),
            selectinload(DangKyNghi.cong_chuc).selectinload(CongChuc.vai_tro),
            selectinload(DangKyNghi.nguoi_phe_duyet),
        )
        .where(DangKyNghi.is_deleted == False)
        .where(DangKyNghi.trang_thai == TrangThaiNghi.CHO_PHE_DUYET)
        .where(DangKyNghi.nguoi_phe_duyet_id == current_user.id)
        .order_by(DangKyNghi.created_at.desc())
    )
    
    result = await db.execute(stmt)
    items = result.scalars().all()
    
    data = [build_nghi_phep_response(item) for item in items]
    
    return success_response(data={"items": data})


# =============================================================================
# GET LỊCH SỬ PHÊ DUYỆT
# =============================================================================

@router.get("/lich-su")
async def get_lich_su_phe_duyet(
    db: DatabaseDep,
    current_user: ActiveUserDep,
    trang_thai: Optional[str] = Query(None, description="Filter: DA_PHE_DUYET, TU_CHOI"),
) -> dict:
    """
    Lấy lịch sử các đơn nghỉ phép đã duyệt/từ chối bởi current_user.
    """
    stmt = (
        select(DangKyNghi)
        .options(
            selectinload(DangKyNghi.cong_chuc).selectinload(CongChuc.don_vi),
            selectinload(DangKyNghi.cong_chuc).selectinload(CongChuc.vai_tro),
            selectinload(DangKyNghi.nguoi_phe_duyet),
        )
        .where(DangKyNghi.is_deleted == False)
        .where(DangKyNghi.nguoi_phe_duyet_id == current_user.id)
        .where(DangKyNghi.trang_thai.in_([TrangThaiNghi.DA_PHE_DUYET, TrangThaiNghi.TU_CHOI]))
    )
    
    # Filter theo trang_thai nếu có
    if trang_thai:
        if trang_thai == "DA_PHE_DUYET":
            stmt = stmt.where(DangKyNghi.trang_thai == TrangThaiNghi.DA_PHE_DUYET)
        elif trang_thai == "TU_CHOI":
            stmt = stmt.where(DangKyNghi.trang_thai == TrangThaiNghi.TU_CHOI)
    
    stmt = stmt.order_by(DangKyNghi.ngay_phe_duyet.desc())
    
    result = await db.execute(stmt)
    items = result.scalars().all()
    
    data = [build_nghi_phep_response(item) for item in items]
    
    return success_response(data={"items": data})


# =============================================================================

# =============================================================================
# ⚠️ QUAN TRỌNG: THỨ TỰ ROUTE TRONG FASTAPI
# =============================================================================
# FastAPI match route THEO THỨ TỰ ĐĂNG KÝ. Nếu /{nghi_phep_id} đứng trước
# /tong-ngay-nghi, thì request GET /tong-ngay-nghi sẽ bị match vào
# /{nghi_phep_id} → parse "tong-ngay-nghi" thành UUID → lỗi 422.
#
# QUY TẮC: TẤT CẢ static routes PHẢI đặt TRƯỚC dynamic /{nghi_phep_id}
# =============================================================================

# THỐNG KÊ CÁ NHÂN
# =============================================================================

@router.get("/thong-ke")
async def get_thong_ke_ca_nhan(
    db: DatabaseDep,
    current_user: ActiveUserDep,
    nam: int = Query(..., ge=2020, le=2100),
) -> dict:
    """
    Thống kê nghỉ phép cá nhân trong năm.
    """
    # Query tổng theo loại nghỉ
    stmt = (
        select(
            DangKyNghi.loai_nghi,
            func.sum(DangKyNghi.so_ngay).label("tong_ngay"),
            func.count(DangKyNghi.id).label("so_don"),
        )
        .where(DangKyNghi.is_deleted == False)
        .where(DangKyNghi.cong_chuc_id == current_user.id)
        .where(DangKyNghi.nam_ap_dung == nam)
        .where(DangKyNghi.trang_thai == TrangThaiNghi.DA_PHE_DUYET)
        .group_by(DangKyNghi.loai_nghi)
    )
    result = await db.execute(stmt)
    rows = result.all()
    
    # Build response
    chi_tiet_loai = []
    tong_ngay = Decimal("0")
    tong_don = 0
    
    for row in rows:
        chi_tiet_loai.append({
            "loai_nghi": row.loai_nghi.value,
            "loai_nghi_ten": row.loai_nghi.label if hasattr(row.loai_nghi, 'label') else row.loai_nghi.value,
            "tong_ngay": float(row.tong_ngay or 0),
            "so_don": row.so_don or 0,
        })
        tong_ngay += row.tong_ngay or Decimal("0")
        tong_don += row.so_don or 0
    
    return success_response(data={
        "nam": nam,
        "tong_ngay_nghi": float(tong_ngay),
        "tong_so_don": tong_don,
        "chi_tiet_loai": chi_tiet_loai,
    })


# =============================================================================
# THỐNG KÊ ĐƠN VỊ
# =============================================================================

@router.get("/thong-ke/don-vi/{don_vi_id}")
async def get_thong_ke_don_vi(
    db: DatabaseDep,
    current_user: ActiveUserDep,
    don_vi_id: UUID,
    thang: int = Query(..., ge=1, le=12),
    nam: int = Query(..., ge=2020, le=2100),
) -> dict:
    """
    Thống kê nghỉ phép của đơn vị theo tháng.
    Chỉ Lãnh đạo đơn vị hoặc CCT mới được xem.
    """
    # Kiểm tra quyền
    cap_bac = current_user.vai_tro.cap_bac if current_user.vai_tro else None
    is_lanh_dao = cap_bac in [
        CapBacVaiTro.CHI_CUC_TRUONG,
        CapBacVaiTro.PHO_CHI_CUC_TRUONG,
        CapBacVaiTro.TRUONG_DON_VI,
        CapBacVaiTro.PHO_DON_VI,
    ]
    
    if not is_lanh_dao and current_user.don_vi_id != don_vi_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=error_response(code="PERM_001", message="Bạn không có quyền xem thống kê đơn vị này")
        )
    
    # Query thống kê theo CC trong đơn vị
    stmt = (
        select(
            CongChuc.id,
            CongChuc.ma_cc,
            CongChuc.ho_ten,
            func.sum(DangKyNghi.so_ngay).label("tong_ngay"),
            func.count(DangKyNghi.id).label("so_don"),
        )
        .join(DangKyNghi, DangKyNghi.cong_chuc_id == CongChuc.id)
        .where(CongChuc.don_vi_id == don_vi_id)
        .where(CongChuc.is_deleted == False)
        .where(DangKyNghi.is_deleted == False)
        .where(DangKyNghi.thang_ap_dung == thang)
        .where(DangKyNghi.nam_ap_dung == nam)
        .where(DangKyNghi.trang_thai == TrangThaiNghi.DA_PHE_DUYET)
        .group_by(CongChuc.id, CongChuc.ma_cc, CongChuc.ho_ten)
        .order_by(CongChuc.ho_ten)
    )
    result = await db.execute(stmt)
    rows = result.all()
    
    chi_tiet_cc = []
    tong_ngay = Decimal("0")
    
    for row in rows:
        chi_tiet_cc.append({
            "cong_chuc_id": row.id,
            "ma_cc": row.ma_cc,
            "ho_ten": row.ho_ten,
            "tong_ngay": float(row.tong_ngay or 0),
            "so_don": row.so_don or 0,
        })
        tong_ngay += row.tong_ngay or Decimal("0")
    
    return success_response(data={
        "don_vi_id": don_vi_id,
        "thang": thang,
        "nam": nam,
        "tong_ngay_nghi": float(tong_ngay),
        "so_cong_chuc": len(chi_tiet_cc),
        "chi_tiet_cong_chuc": chi_tiet_cc,
    })


# =============================================================================
# TỔNG NGÀY NGHỈ THÁNG (cho tính KPI)
# =============================================================================

@router.get("/tong-ngay-nghi")
async def get_tong_ngay_nghi_thang(
    db: DatabaseDep,
    current_user: ActiveUserDep,
    thang: int = Query(..., ge=1, le=12),
    nam: int = Query(..., ge=2020, le=2100),
    cong_chuc_id: Optional[UUID] = Query(None),
) -> dict:
    """
    Lấy tổng ngày nghỉ đã duyệt trong tháng của 1 CC.
    Dùng cho tính KPI.
    """
    target_cc_id = cong_chuc_id or current_user.id
    
    result = await tinh_tong_ngay_nghi_thang(db, target_cc_id, thang, nam)
    
    return success_response(data=result)


# =============================================================================
# GET NGHỈ PHÉP CỦA CÔNG CHỨC (Lãnh đạo/Admin xem nghỉ phép CC khác)
# =============================================================================

@router.get("/cong-chuc/{cong_chuc_id}")
async def get_nghi_phep_cong_chuc(
    cong_chuc_id: UUID,
    db: DatabaseDep,
    current_user: ActiveUserDep,
    thang: Optional[int] = Query(None, ge=1, le=12, description="Filter theo tháng áp dụng"),
    nam: Optional[int] = Query(None, ge=2020, le=2100, description="Filter theo năm áp dụng"),
    trang_thai: Optional[str] = Query(None, description="Filter: CHO_PHE_DUYET, DA_PHE_DUYET, TU_CHOI"),
    loai_nghi: Optional[str] = Query(None, description="Filter theo loại nghỉ"),
) -> dict:
    """
    Lấy danh sách đơn nghỉ phép của một công chức cụ thể.
    
    **Mục đích:** Dùng trong modal "Chi tiết công chức" của Báo cáo xếp loại,
    cho phép Đội trưởng/CCT xem chi tiết nghỉ phép của CC.
    
    **Quyền truy cập:**
    - Lãnh đạo đơn vị (TDV, PDV): Chỉ xem CC cùng đơn vị
    - Chi cục trưởng (CCT), Phó CCT: Xem tất cả CC
    - Admin: Xem tất cả CC
    """
    # =========================================================================
    # 1. Kiểm tra quyền
    # =========================================================================
    is_admin = getattr(current_user.vai_tro, 'is_system_admin', False) if current_user.vai_tro else False
    cap_bac = current_user.vai_tro.cap_bac if current_user.vai_tro else None
    
    is_cct_or_pcct = cap_bac in [CapBacVaiTro.CHI_CUC_TRUONG, CapBacVaiTro.PHO_CHI_CUC_TRUONG]
    is_lanh_dao_don_vi = cap_bac in [CapBacVaiTro.TRUONG_DON_VI, CapBacVaiTro.PHO_DON_VI]
    
    if not (is_admin or is_cct_or_pcct or is_lanh_dao_don_vi):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=error_response(
                code="PERM_001",
                message="Chỉ Lãnh đạo hoặc Admin mới được xem nghỉ phép của công chức khác"
            )
        )
    
    # =========================================================================
    # 2. Kiểm tra công chức tồn tại
    # =========================================================================
    cc_stmt = (
        select(CongChuc)
        .where(CongChuc.id == cong_chuc_id)
        .where(CongChuc.is_deleted == False)
    )
    cc_result = await db.execute(cc_stmt)
    cong_chuc = cc_result.scalar_one_or_none()
    
    if not cong_chuc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response(code="NOT_FOUND", message="Không tìm thấy công chức")
        )
    
    # =========================================================================
    # 3. Kiểm tra cùng đơn vị (nếu là lãnh đạo đơn vị)
    # =========================================================================
    if is_lanh_dao_don_vi and not is_admin and not is_cct_or_pcct:
        if cong_chuc.don_vi_id != current_user.don_vi_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=error_response(
                    code="PERM_002",
                    message="Lãnh đạo đơn vị chỉ được xem nghỉ phép của CC cùng đơn vị"
                )
            )
    
    # =========================================================================
    # 4. Query đơn nghỉ phép
    # =========================================================================
    stmt = (
        select(DangKyNghi)
        .options(
            selectinload(DangKyNghi.cong_chuc).selectinload(CongChuc.don_vi),
            selectinload(DangKyNghi.nguoi_phe_duyet),
        )
        .where(DangKyNghi.is_deleted == False)
        .where(DangKyNghi.cong_chuc_id == cong_chuc_id)
    )
    
    if thang:
        stmt = stmt.where(DangKyNghi.thang_ap_dung == thang)
    if nam:
        stmt = stmt.where(DangKyNghi.nam_ap_dung == nam)
    if trang_thai:
        stmt = stmt.where(DangKyNghi.trang_thai == TrangThaiNghi(trang_thai))
    if loai_nghi:
        stmt = stmt.where(DangKyNghi.loai_nghi == LoaiNghi(loai_nghi))
    
    stmt = stmt.order_by(DangKyNghi.tu_ngay.desc())
    
    result = await db.execute(stmt)
    items = result.scalars().all()
    
    data = [build_nghi_phep_response(item) for item in items]
    
    return success_response(data=data)


# GET DANH SÁCH NGHỈ PHÉP CỦA BẢN THÂN
# =============================================================================

@router.get("")
async def get_nghi_phep_list(
    db: DatabaseDep,
    current_user: ActiveUserDep,
    thang: Optional[int] = Query(None, ge=1, le=12),
    nam: Optional[int] = Query(None, ge=2020, le=2100),
    trang_thai: Optional[str] = Query(None),
    loai_nghi: Optional[str] = Query(None),
) -> dict:
    """
    Lấy danh sách đơn nghỉ phép của bản thân.
    """
    stmt = (
        select(DangKyNghi)
        .options(
            selectinload(DangKyNghi.cong_chuc).selectinload(CongChuc.don_vi),
            selectinload(DangKyNghi.nguoi_phe_duyet),
        )
        .where(DangKyNghi.is_deleted == False)
        .where(DangKyNghi.cong_chuc_id == current_user.id)
    )
    
    if thang:
        stmt = stmt.where(DangKyNghi.thang_ap_dung == thang)
    if nam:
        stmt = stmt.where(DangKyNghi.nam_ap_dung == nam)
    if trang_thai:
        stmt = stmt.where(DangKyNghi.trang_thai == TrangThaiNghi(trang_thai))
    if loai_nghi:
        stmt = stmt.where(DangKyNghi.loai_nghi == LoaiNghi(loai_nghi))
    
    stmt = stmt.order_by(DangKyNghi.tu_ngay.desc())
    
    result = await db.execute(stmt)
    items = result.scalars().all()
    
    data = [build_nghi_phep_response(item) for item in items]
    
    return success_response(data=data)


# =============================================================================
# GET CHI TIẾT NGHỈ PHÉP
# =============================================================================

@router.get("/{nghi_phep_id}")
async def get_nghi_phep_detail(
    db: DatabaseDep,
    current_user: ActiveUserDep,
    nghi_phep_id: UUID,
) -> dict:
    """
    Lấy chi tiết đơn nghỉ phép.
    """
    stmt = (
        select(DangKyNghi)
        .options(
            selectinload(DangKyNghi.cong_chuc).selectinload(CongChuc.don_vi),
            selectinload(DangKyNghi.nguoi_phe_duyet).selectinload(CongChuc.don_vi),
        )
        .where(DangKyNghi.id == nghi_phep_id)
        .where(DangKyNghi.is_deleted == False)
    )
    result = await db.execute(stmt)
    nghi_phep = result.scalar_one_or_none()
    
    if not nghi_phep:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response(code="NOT_FOUND", message="Đơn nghỉ phép không tồn tại")
        )
    
    return success_response(data=build_nghi_phep_response(nghi_phep))


# =============================================================================
# TẠO ĐƠN NGHỈ PHÉP
# =============================================================================

@router.post("")
async def create_nghi_phep(
    db: DatabaseDep,
    current_user: ActiveUserDep,
    payload: NghiPhepCreate,
) -> dict:
    """
    Tạo đơn nghỉ phép mới.
    v3.0: Chỉ cần chọn 1 người phê duyệt (Đội trưởng)
    v3.1: Thêm kiểm tra trùng ngày (LEAVE_005)
    """
    # Validate ngày
    if payload.den_ngay < payload.tu_ngay:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_response(code="VALID_001", message="Ngày kết thúc phải >= ngày bắt đầu")
        )
    
    # ✅ FIX v3.1: Kiểm tra trùng ngày với đơn đã tồn tại (LEAVE_005)
    existing = await check_overlap_nghi_phep(
        db=db,
        cong_chuc_id=current_user.id,
        tu_ngay=payload.tu_ngay,
        den_ngay=payload.den_ngay,
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_response(
                code="LEAVE_005",
                message=(
                    f"Trùng ngày nghỉ với đơn đã đăng ký "
                    f"({existing.tu_ngay.strftime('%d/%m/%Y')} - "
                    f"{existing.den_ngay.strftime('%d/%m/%Y')}, "
                    f"trạng thái: {existing.trang_thai.value})"
                )
            )
        )
    
    # Tính số ngày
    so_ngay = (payload.den_ngay - payload.tu_ngay).days + 1
    if payload.so_ngay:
        so_ngay = payload.so_ngay  # Override nếu user nhập
    
    # Tìm người phê duyệt
    nguoi_phe_duyet_id = payload.nguoi_phe_duyet_id
    if not nguoi_phe_duyet_id:
        # Auto-assign
        approver = await find_approver(db, current_user)
        if approver:
            nguoi_phe_duyet_id = approver.id
    
    # Tạo đơn
    nghi_phep = DangKyNghi(
        cong_chuc_id=current_user.id,
        loai_nghi=LoaiNghi(payload.loai_nghi),
        tu_ngay=payload.tu_ngay,
        den_ngay=payload.den_ngay,
        so_ngay=Decimal(str(so_ngay)),
        ly_do=payload.ly_do,
        nguoi_phe_duyet_id=nguoi_phe_duyet_id,
        trang_thai=TrangThaiNghi.CHO_PHE_DUYET,
    )
    
    # Auto-assign tháng áp dụng
    await auto_assign_thang_ap_dung(nghi_phep)
    
    db.add(nghi_phep)
    await db.flush()
    
    # Reload với relationships
    stmt = (
        select(DangKyNghi)
        .options(
            selectinload(DangKyNghi.cong_chuc).selectinload(CongChuc.don_vi),
            selectinload(DangKyNghi.nguoi_phe_duyet),
        )
        .where(DangKyNghi.id == nghi_phep.id)
    )
    result = await db.execute(stmt)
    nghi_phep = result.scalar_one()
    
    return success_response(
        data=build_nghi_phep_response(nghi_phep),
        message="Tạo đơn nghỉ phép thành công"
    )


# =============================================================================
# TẠO BULK NGHỈ TUẦN
# =============================================================================

@router.post("/bulk")
async def create_nghi_phep_bulk(
    db: DatabaseDep,
    current_user: ActiveUserDep,
    payload: NghiPhepBulkCreate,
) -> dict:
    """
    Đăng ký nghỉ tuần hàng loạt (nhiều ngày cùng lúc).
    v3.1: Kiểm tra trùng ngày, skip ngày đã tồn tại, dùng NghiPhepBulkResponse.
    """
    if not payload.danh_sach_ngay or len(payload.danh_sach_ngay) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_response(code="VALID_001", message="Danh sách ngày không được rỗng")
        )
    
    # ✅ FIX v3.1: Kiểm tra ngày đã tồn tại đơn nghỉ active
    ngay_da_ton_tai = await find_existing_dates_for_bulk(
        db=db,
        cong_chuc_id=current_user.id,
        danh_sach_ngay=payload.danh_sach_ngay,
    )
    
    # Lọc ra các ngày mới (chưa có đơn)
    existing_set = set(ngay_da_ton_tai)
    ngay_moi = [ngay for ngay in payload.danh_sach_ngay if ngay not in existing_set]
    
    # Nếu tất cả đều trùng → trả kết quả (0 đơn tạo), không raise error
    if not ngay_moi:
        return success_response(
            data={
                "tong_don_tao": 0,
                "danh_sach_id": [],
                "ngay_da_ton_tai": [d.isoformat() for d in ngay_da_ton_tai],
            },
            message="Tất cả ngày đã được đăng ký trước đó"
        )
    
    # Tìm người phê duyệt
    nguoi_phe_duyet_id = payload.nguoi_phe_duyet_id
    if not nguoi_phe_duyet_id:
        approver = await find_approver(db, current_user)
        if approver:
            nguoi_phe_duyet_id = approver.id
    
    # Chỉ tạo đơn cho ngày MỚI (skip ngày trùng)
    created_ids = []
    for ngay in ngay_moi:
        nghi = DangKyNghi(
            cong_chuc_id=current_user.id,
            loai_nghi=LoaiNghi.NGHI_TUAN,
            tu_ngay=ngay,
            den_ngay=ngay,
            so_ngay=Decimal("1"),
            ly_do=payload.ly_do or "Nghỉ tuần",
            nguoi_phe_duyet_id=nguoi_phe_duyet_id,
            trang_thai=TrangThaiNghi.CHO_PHE_DUYET,
        )
        await auto_assign_thang_ap_dung(nghi)
        db.add(nghi)
        await db.flush()
        created_ids.append(str(nghi.id))
    
    # ✅ FIX v3.1: Dùng đúng schema NghiPhepBulkResponse
    tong_don_tao = len(created_ids)
    message_parts = [f"Đã tạo {tong_don_tao} đơn nghỉ tuần"]
    if ngay_da_ton_tai:
        message_parts.append(f"bỏ qua {len(ngay_da_ton_tai)} ngày đã tồn tại")
    
    return success_response(
        data={
            "tong_don_tao": tong_don_tao,
            "danh_sach_id": created_ids,
            "ngay_da_ton_tai": [d.isoformat() for d in ngay_da_ton_tai],
        },
        message=", ".join(message_parts)
    )


# =============================================================================
# CẬP NHẬT ĐƠN NGHỈ PHÉP
# =============================================================================

@router.put("/{nghi_phep_id}")
async def update_nghi_phep(
    db: DatabaseDep,
    current_user: ActiveUserDep,
    nghi_phep_id: UUID,
    payload: NghiPhepUpdate,
) -> dict:
    """
    Cập nhật đơn nghỉ phép (chỉ khi còn NHAP hoặc CHO_PHE_DUYET).
    """
    stmt = (
        select(DangKyNghi)
        .options(
            selectinload(DangKyNghi.cong_chuc).selectinload(CongChuc.don_vi),
            selectinload(DangKyNghi.nguoi_phe_duyet),
        )
        .where(DangKyNghi.id == nghi_phep_id)
        .where(DangKyNghi.is_deleted == False)
    )
    result = await db.execute(stmt)
    nghi_phep = result.scalar_one_or_none()
    
    if not nghi_phep:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response(code="NOT_FOUND", message="Đơn nghỉ phép không tồn tại")
        )
    
    # Chỉ chủ sở hữu mới được sửa
    if nghi_phep.cong_chuc_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=error_response(code="PERM_001", message="Bạn không có quyền sửa đơn này")
        )
    
    # Chỉ sửa khi chưa duyệt
    if nghi_phep.trang_thai not in [TrangThaiNghi.NHAP, TrangThaiNghi.CHO_PHE_DUYET]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_response(code="BIZ_001", message="Không thể sửa đơn đã được xử lý")
        )
    
    # ✅ FIX v3.1: Kiểm tra trùng ngày nếu user thay đổi ngày (LEAVE_005)
    check_tu_ngay = payload.tu_ngay if payload.tu_ngay is not None else nghi_phep.tu_ngay
    check_den_ngay = payload.den_ngay if payload.den_ngay is not None else nghi_phep.den_ngay
    
    existing = await check_overlap_nghi_phep(
        db=db,
        cong_chuc_id=current_user.id,
        tu_ngay=check_tu_ngay,
        den_ngay=check_den_ngay,
        exclude_id=nghi_phep_id,  # Bỏ qua chính đơn đang sửa
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_response(
                code="LEAVE_005",
                message=(
                    f"Trùng ngày nghỉ với đơn đã đăng ký "
                    f"({existing.tu_ngay.strftime('%d/%m/%Y')} - "
                    f"{existing.den_ngay.strftime('%d/%m/%Y')}, "
                    f"trạng thái: {existing.trang_thai.value})"
                )
            )
        )
    
    # Cập nhật các trường
    if payload.loai_nghi is not None:
        nghi_phep.loai_nghi = LoaiNghi(payload.loai_nghi)
    if payload.tu_ngay is not None:
        nghi_phep.tu_ngay = payload.tu_ngay
    if payload.den_ngay is not None:
        nghi_phep.den_ngay = payload.den_ngay
    if payload.so_ngay is not None:
        nghi_phep.so_ngay = Decimal(str(payload.so_ngay))
    if payload.ly_do is not None:
        nghi_phep.ly_do = payload.ly_do
    if payload.nguoi_phe_duyet_id is not None:
        nghi_phep.nguoi_phe_duyet_id = payload.nguoi_phe_duyet_id
    
    # Re-calculate so_ngay nếu thay đổi ngày
    if payload.tu_ngay or payload.den_ngay:
        if nghi_phep.den_ngay and nghi_phep.tu_ngay:
            nghi_phep.so_ngay = Decimal(str((nghi_phep.den_ngay - nghi_phep.tu_ngay).days + 1))
    
    await auto_assign_thang_ap_dung(nghi_phep)
    
    await db.flush()
    await db.refresh(nghi_phep)
    
    return success_response(
        data=build_nghi_phep_response(nghi_phep),
        message="Cập nhật đơn nghỉ phép thành công"
    )


# =============================================================================
# XÓA ĐƠN NGHỈ PHÉP
# =============================================================================

@router.delete("/{nghi_phep_id}")
async def delete_nghi_phep(
    db: DatabaseDep,
    current_user: ActiveUserDep,
    nghi_phep_id: UUID,
) -> dict:
    """
    Xóa/Hủy đơn nghỉ phép.
    """
    stmt = (
        select(DangKyNghi)
        .where(DangKyNghi.id == nghi_phep_id)
        .where(DangKyNghi.is_deleted == False)
    )
    result = await db.execute(stmt)
    nghi_phep = result.scalar_one_or_none()
    
    if not nghi_phep:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response(code="NOT_FOUND", message="Đơn nghỉ phép không tồn tại")
        )
    
    # Chỉ chủ sở hữu mới được xóa
    if nghi_phep.cong_chuc_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=error_response(code="PERM_001", message="Bạn không có quyền xóa đơn này")
        )
    
    # Không xóa đơn đã duyệt
    if nghi_phep.trang_thai == TrangThaiNghi.DA_PHE_DUYET:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_response(
                code="BIZ_002",
                message="Không thể xóa đơn đã phê duyệt. Vui lòng liên hệ Lãnh đạo."
            )
        )
    
    # Soft delete
    nghi_phep.is_deleted = True
    nghi_phep.trang_thai = TrangThaiNghi.HUY
    
    return success_response(
        data={"id": nghi_phep_id},
        message="Đã hủy đơn nghỉ phép"
    )


# =============================================================================
# PHÊ DUYỆT - v3.0: CHỈ 1 CẤP
# =============================================================================

@router.post("/{nghi_phep_id}/phe-duyet")
async def phe_duyet_nghi_phep(
    db: DatabaseDep,
    current_user: ActiveUserDep,
    nghi_phep_id: UUID,
    payload: PheDuyetNghiPhepRequest,
) -> dict:
    """
    Phê duyệt đơn nghỉ phép - v3.0: CHỈ 1 CẤP.
    
    Luồng đơn giản:
    - Ai được assign làm nguoi_phe_duyet thì duyệt → XONG
    - CCT tự duyệt đơn của mình
    """
    stmt = (
        select(DangKyNghi)
        .options(
            selectinload(DangKyNghi.cong_chuc).selectinload(CongChuc.don_vi),
            selectinload(DangKyNghi.cong_chuc).selectinload(CongChuc.vai_tro),
            selectinload(DangKyNghi.nguoi_phe_duyet),
        )
        .where(DangKyNghi.id == nghi_phep_id)
        .where(DangKyNghi.is_deleted == False)
    )
    result = await db.execute(stmt)
    nghi_phep = result.scalar_one_or_none()
    
    if not nghi_phep:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response(code="NOT_FOUND", message="Đơn nghỉ phép không tồn tại")
        )
    
    # Kiểm tra đã bị khóa chưa
    if nghi_phep.is_khoa:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_response(code="BIZ_002", message="Dữ liệu đã bị khóa, không thể chỉnh sửa")
        )
    
    # Kiểm tra trạng thái
    if nghi_phep.trang_thai != TrangThaiNghi.CHO_PHE_DUYET:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_response(code="BIZ_001", message="Đơn không ở trạng thái chờ phê duyệt")
        )
    
    # Lấy cấp bậc người đang login
    cap_bac_current = None
    if current_user.vai_tro:
        cap_bac_current = current_user.vai_tro.cap_bac
    
    # ==========================================================================
    # CASE 1: CCT tự phê duyệt đơn của mình
    # ==========================================================================
    if (nghi_phep.cong_chuc_id == current_user.id and 
        cap_bac_current == CapBacVaiTro.CHI_CUC_TRUONG):
        
        nghi_phep.trang_thai = TrangThaiNghi.DA_PHE_DUYET
        nghi_phep.ngay_phe_duyet = datetime.now()
        nghi_phep.ghi_chu_phe_duyet = payload.ghi_chu
        
        await db.flush()
        await db.refresh(nghi_phep)
        
        return success_response(
            data=build_nghi_phep_response(nghi_phep),
            message="Chi cục trưởng đã tự phê duyệt đơn nghỉ phép"
        )
    
    # ==========================================================================
    # CASE 2: Người được assign (nguoi_phe_duyet) duyệt → XONG
    # ==========================================================================
    if nghi_phep.nguoi_phe_duyet_id == current_user.id:
        nghi_phep.trang_thai = TrangThaiNghi.DA_PHE_DUYET
        nghi_phep.ngay_phe_duyet = datetime.now()
        nghi_phep.ghi_chu_phe_duyet = payload.ghi_chu
        
        await db.flush()
        await db.refresh(nghi_phep)
        
        return success_response(
            data=build_nghi_phep_response(nghi_phep),
            message="Đã phê duyệt đơn nghỉ phép thành công"
        )
    
    # ==========================================================================
    # CASE 3: CCT có thể duyệt thay nếu cần (quyền cao hơn)
    # ==========================================================================
    if cap_bac_current == CapBacVaiTro.CHI_CUC_TRUONG:
        nghi_phep.trang_thai = TrangThaiNghi.DA_PHE_DUYET
        nghi_phep.ngay_phe_duyet = datetime.now()
        nghi_phep.ghi_chu_phe_duyet = payload.ghi_chu
        # Ghi nhận CCT là người duyệt thực tế
        nghi_phep.nguoi_phe_duyet_id = current_user.id
        
        await db.flush()
        await db.refresh(nghi_phep)
        
        return success_response(
            data=build_nghi_phep_response(nghi_phep),
            message="Chi cục trưởng đã phê duyệt đơn nghỉ phép"
        )
    
    # Không có quyền
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=error_response(code="PERM_002", message="Bạn không có quyền phê duyệt đơn này")
    )


# =============================================================================
# TỪ CHỐI - v3.0: CHỈ 1 CẤP
# =============================================================================

@router.post("/{nghi_phep_id}/tu-choi")
async def tu_choi_nghi_phep(
    db: DatabaseDep,
    current_user: ActiveUserDep,
    nghi_phep_id: UUID,
    payload: TuChoiNghiPhepRequest,
) -> dict:
    """
    Từ chối đơn nghỉ phép - v3.0: CHỈ 1 CẤP.
    
    Bắt buộc phải có lý do từ chối.
    """
    stmt = (
        select(DangKyNghi)
        .options(
            selectinload(DangKyNghi.cong_chuc).selectinload(CongChuc.don_vi),
            selectinload(DangKyNghi.cong_chuc).selectinload(CongChuc.vai_tro),
            selectinload(DangKyNghi.nguoi_phe_duyet),
        )
        .where(DangKyNghi.id == nghi_phep_id)
        .where(DangKyNghi.is_deleted == False)
    )
    result = await db.execute(stmt)
    nghi_phep = result.scalar_one_or_none()
    
    if not nghi_phep:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response(code="NOT_FOUND", message="Đơn nghỉ phép không tồn tại")
        )
    
    # Kiểm tra đã bị khóa chưa
    if nghi_phep.is_khoa:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_response(code="BIZ_002", message="Dữ liệu đã bị khóa, không thể chỉnh sửa")
        )
    
    # Kiểm tra trạng thái
    if nghi_phep.trang_thai != TrangThaiNghi.CHO_PHE_DUYET:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_response(code="BIZ_001", message="Đơn không ở trạng thái chờ phê duyệt")
        )
    
    # Lấy cấp bậc người đang login
    cap_bac_current = None
    if current_user.vai_tro:
        cap_bac_current = current_user.vai_tro.cap_bac
    
    # Kiểm tra quyền từ chối
    can_reject = False
    
    # Người được assign có quyền từ chối
    if nghi_phep.nguoi_phe_duyet_id == current_user.id:
        can_reject = True
    
    # CCT có quyền từ chối tất cả
    if cap_bac_current == CapBacVaiTro.CHI_CUC_TRUONG:
        can_reject = True
    
    if not can_reject:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=error_response(code="PERM_002", message="Bạn không có quyền từ chối đơn này")
        )
    
    # Từ chối
    nghi_phep.trang_thai = TrangThaiNghi.TU_CHOI
    nghi_phep.ly_do_tu_choi = payload.ly_do_tu_choi
    nghi_phep.ngay_phe_duyet = datetime.now()
    
    await db.flush()
    await db.refresh(nghi_phep)
    
    return success_response(
        data=build_nghi_phep_response(nghi_phep),
        message="Đã từ chối đơn nghỉ phép"
    )


# =============================================================================
# TRẢ LẠI ĐƠN NGHỈ ĐÃ DUYỆT - v3.2
# =============================================================================

class TraLaiNghiPhepRequest(BaseModel):
    """Schema request trả lại đơn nghỉ đã duyệt."""
    ly_do: str = Field(..., min_length=1, max_length=500, description="Lý do trả lại")


@router.post("/{nghi_phep_id}/tra-lai")
async def tra_lai_nghi_phep(
    db: DatabaseDep,
    current_user: ActiveUserDep,
    nghi_phep_id: UUID,
    payload: TraLaiNghiPhepRequest,
) -> dict:
    """
    Trả lại đơn nghỉ phép đã duyệt - v3.2.
    
    Dùng khi lãnh đạo duyệt nhầm, cần hoàn tác.
    Đơn sẽ quay về trạng thái CHO_PHE_DUYET để CC chỉnh sửa hoặc gửi lại.
    
    Quyền:
    - Người đã phê duyệt (nguoi_phe_duyet)
    - Chi cục trưởng (CCT)
    
    Ràng buộc:
    - Chỉ trả lại đơn có trạng thái DA_PHE_DUYET
    - Không trả lại đơn đã bị khóa
    - Không trả lại đơn đã tính KPI
    """
    stmt = (
        select(DangKyNghi)
        .options(
            selectinload(DangKyNghi.cong_chuc).selectinload(CongChuc.don_vi),
            selectinload(DangKyNghi.cong_chuc).selectinload(CongChuc.vai_tro),
            selectinload(DangKyNghi.nguoi_phe_duyet),
        )
        .where(DangKyNghi.id == nghi_phep_id)
        .where(DangKyNghi.is_deleted == False)
    )
    result = await db.execute(stmt)
    nghi_phep = result.scalar_one_or_none()
    
    if not nghi_phep:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response(code="NOT_FOUND", message="Đơn nghỉ phép không tồn tại")
        )
    
    # Kiểm tra đã bị khóa chưa
    if nghi_phep.is_khoa:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_response(
                code="BIZ_002",
                message="Dữ liệu đã bị khóa, không thể trả lại"
            )
        )
    
    # Kiểm tra trạng thái - chỉ trả lại đơn DA_PHE_DUYET
    if nghi_phep.trang_thai != TrangThaiNghi.DA_PHE_DUYET:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_response(
                code="BIZ_001",
                message=f"Chỉ có thể trả lại đơn đã phê duyệt. Trạng thái hiện tại: {nghi_phep.trang_thai.value}"
            )
        )
    
    # Kiểm tra đã tính KPI chưa
    if nghi_phep.da_tinh_kpi:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_response(
                code="BIZ_003",
                message="Đơn nghỉ đã được tính vào KPI, không thể trả lại. Vui lòng liên hệ quản trị viên."
            )
        )
    
    # Kiểm tra quyền trả lại
    cap_bac_current = None
    if current_user.vai_tro:
        cap_bac_current = current_user.vai_tro.cap_bac
    
    can_tra_lai = False
    
    # Người đã phê duyệt có quyền trả lại
    if nghi_phep.nguoi_phe_duyet_id == current_user.id:
        can_tra_lai = True
    
    # CCT có quyền trả lại tất cả
    if cap_bac_current == CapBacVaiTro.CHI_CUC_TRUONG:
        can_tra_lai = True
    
    if not can_tra_lai:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=error_response(
                code="PERM_002",
                message="Bạn không có quyền trả lại đơn này"
            )
        )
    
    # ===== Thực hiện trả lại =====
    nghi_phep.trang_thai = TrangThaiNghi.CHO_PHE_DUYET
    nghi_phep.ngay_phe_duyet = None
    nghi_phep.ghi_chu_phe_duyet = f"[TRẢ LẠI] {payload.ly_do}"
    
    await db.flush()
    await db.refresh(nghi_phep)
    
    return success_response(
        data=build_nghi_phep_response(nghi_phep),
        message="Đã trả lại đơn nghỉ phép về trạng thái chờ phê duyệt"
    )


# =============================================================================
# HELPER FUNCTION cho tính KPI (Export để dùng trong danh_gia.py)
# =============================================================================

async def tinh_tong_ngay_nghi_thang(
    db: AsyncSession,
    cong_chuc_id: UUID,
    thang: int,
    nam: int,
) -> dict:
    """
    Tính tổng ngày nghỉ trong tháng của 1 CC.
    
    Dùng cho công thức KPI:
    SP_được_giao = (Ngày_dương_lịch - Tổng_nghỉ) × 96
    
    ⚠️ QUAN TRỌNG: KHÔNG tự động trừ T7/CN!
    Chỉ trừ các ngày nghỉ CC đã đăng ký.
    
    v3.1: Trả thêm tam_tinh_ngay_nghi (CHO_PHE_DUYET + DA_PHE_DUYET)
    để trang đánh giá tab tạm tính có target SP chính xác.
    
    Returns:
        dict: {
            # Chính thức (chỉ DA_PHE_DUYET)
            "tong_ngay_nghi": Decimal,
            "so_ngay_lam_viec": Decimal,
            "sp_duoc_giao": Decimal,
            # Tạm tính (CHO_PHE_DUYET + DA_PHE_DUYET)
            "tam_tinh_ngay_nghi": Decimal,
            "tam_tinh_ngay_lam_viec": Decimal,
            "tam_tinh_sp_duoc_giao": Decimal,
            ...
        }
    """
    # -----------------------------------------------------------------------
    # CHÍNH THỨC: Chỉ đếm DA_PHE_DUYET
    # -----------------------------------------------------------------------
    stmt_chinh_thuc = (
        select(
            DangKyNghi.loai_nghi,
            func.sum(DangKyNghi.so_ngay).label("tong_ngay")
        )
        .where(DangKyNghi.is_deleted == False)
        .where(DangKyNghi.cong_chuc_id == cong_chuc_id)
        .where(DangKyNghi.thang_ap_dung == thang)
        .where(DangKyNghi.nam_ap_dung == nam)
        .where(DangKyNghi.trang_thai == TrangThaiNghi.DA_PHE_DUYET)
        .group_by(DangKyNghi.loai_nghi)
    )
    result = await db.execute(stmt_chinh_thuc)
    rows = result.all()
    
    # Build chi tiết (chính thức)
    chi_tiet = {
        "nghi_tuan": Decimal("0"),
        "phep_nam": Decimal("0"),
        "nghi_le": Decimal("0"),
        "nghi_tet": Decimal("0"),
        "nghi_om": Decimal("0"),
        "thai_san": Decimal("0"),
        "viec_rieng": Decimal("0"),
        "khong_luong": Decimal("0"),
        "nghi_bu": Decimal("0"),
        "khac": Decimal("0"),
    }
    
    loai_mapping = {
        LoaiNghi.NGHI_TUAN: "nghi_tuan",
        LoaiNghi.PHEP_NAM: "phep_nam",
        LoaiNghi.NGHI_LE: "nghi_le",
        LoaiNghi.NGHI_TET: "nghi_tet",
        LoaiNghi.NGHI_OM: "nghi_om",
        LoaiNghi.THAI_SAN: "thai_san",
        LoaiNghi.VIEC_RIENG: "viec_rieng",
        LoaiNghi.KHONG_LUONG: "khong_luong",
        LoaiNghi.NGHI_BU: "nghi_bu",
        LoaiNghi.KHAC: "khac",
    }
    
    tong_ngay_nghi = Decimal("0")
    for row in rows:
        key = loai_mapping.get(row.loai_nghi)
        if key and row.tong_ngay:
            chi_tiet[key] = Decimal(str(row.tong_ngay))
            tong_ngay_nghi += Decimal(str(row.tong_ngay))
    
    # Tính số ngày trong tháng (dương lịch)
    so_ngay_trong_thang = calendar.monthrange(nam, thang)[1]
    
    # Tính số ngày làm việc (chính thức)
    # ⚠️ KHÔNG tự động trừ T7/CN!
    so_ngay_lam_viec = Decimal(str(so_ngay_trong_thang)) - tong_ngay_nghi
    if so_ngay_lam_viec < 0:
        so_ngay_lam_viec = Decimal("0")
    
    sp_per_ngay = Decimal("96")
    sp_duoc_giao = so_ngay_lam_viec * sp_per_ngay
    
    # -----------------------------------------------------------------------
    # TẠM TÍNH: CHO_PHE_DUYET + DA_PHE_DUYET (v3.1)
    # -----------------------------------------------------------------------
    stmt_tam_tinh = (
        select(
            func.sum(DangKyNghi.so_ngay).label("tong_ngay")
        )
        .where(DangKyNghi.is_deleted == False)
        .where(DangKyNghi.cong_chuc_id == cong_chuc_id)
        .where(DangKyNghi.thang_ap_dung == thang)
        .where(DangKyNghi.nam_ap_dung == nam)
        .where(DangKyNghi.trang_thai.in_([
            TrangThaiNghi.CHO_PHE_DUYET,
            TrangThaiNghi.DA_PHE_DUYET,
        ]))
    )
    result_tam_tinh = await db.execute(stmt_tam_tinh)
    row_tam_tinh = result_tam_tinh.scalar_one_or_none()
    
    tam_tinh_ngay_nghi = Decimal(str(row_tam_tinh)) if row_tam_tinh else Decimal("0")
    tam_tinh_ngay_lam_viec = Decimal(str(so_ngay_trong_thang)) - tam_tinh_ngay_nghi
    if tam_tinh_ngay_lam_viec < 0:
        tam_tinh_ngay_lam_viec = Decimal("0")
    tam_tinh_sp_duoc_giao = tam_tinh_ngay_lam_viec * sp_per_ngay
    
    # Tính riêng số ngày CHỜ PHÊ DUYỆT (để frontend hiển thị)
    cho_duyet_ngay_nghi = tam_tinh_ngay_nghi - tong_ngay_nghi
    
    return {
        "cong_chuc_id": cong_chuc_id,
        "thang": thang,
        "nam": nam,
        # Chính thức (chỉ DA_PHE_DUYET)
        "tong_ngay_nghi": tong_ngay_nghi,
        "chi_tiet": chi_tiet,
        "so_ngay_trong_thang": so_ngay_trong_thang,
        "so_ngay_lam_viec": so_ngay_lam_viec,
        "sp_duoc_giao": sp_duoc_giao,
        # Tạm tính (CHO_PHE_DUYET + DA_PHE_DUYET) - v3.1
        "tam_tinh_ngay_nghi": tam_tinh_ngay_nghi,
        "tam_tinh_ngay_lam_viec": tam_tinh_ngay_lam_viec,
        "tam_tinh_sp_duoc_giao": tam_tinh_sp_duoc_giao,
        "cho_duyet_ngay_nghi": cho_duyet_ngay_nghi,
    }