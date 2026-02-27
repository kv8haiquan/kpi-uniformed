"""
app/api/v1/endpoints/admin.py
=============================
API Endpoints cho Admin Module.

Phiên bản: 1.1.0 (06/02/2026)

CHANGELOG v1.1.0:
- FIX: Sử dụng hash_password() để generate hash động thay vì hardcoded hash
- Tạo user mới và reset password giờ sẽ tạo hash bcrypt đúng chuẩn

Chức năng:
- Quản lý User (CRUD, status, reset password, transfer)
- Quản lý SP Chuẩn (CRUD)
- Quản lý Cấp độ phức tạp (CRUD)
- Quản lý Danh mục công việc (CRUD)

Quyền truy cập: Chỉ ADMIN (is_system_admin = true)
"""

from datetime import date, datetime
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, HTTPException, status, Query
from sqlalchemy import select, func, and_, or_, exists, Integer, text
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import DatabaseDep, AdminUserDep
from app.core.security import hash_password
from app.models.user_org import CongChuc, DonVi, VaiTro, GioiTinh
from app.models.task_catalog import SpCongViecChuan, CapDoPhucTap, DanhMucSpCongViec
from app.models.kpi_submission import KeKhaiCongViec, TrangThaiKeKhai
from app.models.kpi_assessment import DanhGiaThang
from app.models.bao_cao_xep_loai import BaoCaoXepLoai, ChiTietXepLoai
from app.models.admin import LichSuDieuChuyen
from app.schemas.common import (
    DataResponse,
    DataListResponse,
    PaginatedResponse,
    Pagination,
    success_response,
    error_response,
)
from app.schemas.admin import (
    # User
    UserCreateRequest,
    UserUpdateRequest,
    UserStatusRequest,
    UserTransferRequest,
    UserResponse,
    LichSuDieuChuyenResponse,
    # SP Chuẩn
    SpChuanCreateRequest,
    SpChuanUpdateRequest,
    SpChuanResponse,
    # Cấp độ
    CapDoCreateRequest,
    CapDoUpdateRequest,
    CapDoResponse,
    # Danh mục CV
    DanhMucCvCreateRequest,
    DanhMucCvUpdateRequest,
    DanhMucCvResponse,
    # Common
    AdminActionResponse,
    AdminStatsResponse,
)


router = APIRouter()

# Mã công chức Admin gốc - không được phép thao tác
PROTECTED_ADMIN_MA_CC = "ADMIN-001"

# Mật khẩu mặc định cho user mới và reset password
DEFAULT_PASSWORD = "123456"


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def user_to_response(cc: CongChuc) -> dict:
    """Convert CongChuc model to response dict."""
    response = {
        "id": cc.id,
        "ma_cc": cc.ma_cc,
        "ho_ten": cc.ho_ten,
        "email": cc.email,
        "so_dien_thoai": cc.so_dien_thoai,
        "ngay_sinh": cc.ngay_sinh,
        "gioi_tinh": cc.gioi_tinh.value if cc.gioi_tinh else None,
        "chuc_vu": cc.chuc_vu,
        "is_lanh_dao": cc.is_lanh_dao,
        "is_active": cc.is_active,
        "ngay_vao_nganh": cc.ngay_vao_nganh,
        "ngay_vao_chi_cuc": cc.ngay_vao_chi_cuc,
        "last_login": cc.last_login,
        "created_at": cc.created_at,
        # Đơn vị
        "don_vi_id": None,
        "don_vi_ma": None,
        "don_vi_ten": None,
        # Vai trò
        "vai_tro_id": None,
        "vai_tro_ma": None,
        "vai_tro_ten": None,
    }
    
    if cc.don_vi:
        response["don_vi_id"] = cc.don_vi.id
        response["don_vi_ma"] = cc.don_vi.ma_don_vi
        response["don_vi_ten"] = cc.don_vi.ten_don_vi
    
    if cc.vai_tro:
        response["vai_tro_id"] = cc.vai_tro.id
        response["vai_tro_ma"] = cc.vai_tro.ma_vai_tro
        response["vai_tro_ten"] = cc.vai_tro.ten_vai_tro
    
    return response


def lich_su_to_response(ls: LichSuDieuChuyen) -> dict:
    """Convert LichSuDieuChuyen model to response dict."""
    return {
        "id": ls.id,
        "cong_chuc_id": ls.cong_chuc_id,
        "don_vi_cu_id": ls.don_vi_cu_id,
        "don_vi_cu_ten": ls.don_vi_cu.ten_don_vi if ls.don_vi_cu else None,
        "don_vi_moi_id": ls.don_vi_moi_id,
        "don_vi_moi_ten": ls.don_vi_moi.ten_don_vi if ls.don_vi_moi else None,
        "vai_tro_cu_id": ls.vai_tro_cu_id,
        "vai_tro_cu_ten": ls.vai_tro_cu.ten_vai_tro if ls.vai_tro_cu else None,
        "vai_tro_moi_id": ls.vai_tro_moi_id,
        "vai_tro_moi_ten": ls.vai_tro_moi.ten_vai_tro if ls.vai_tro_moi else None,
        "chuc_vu_cu": ls.chuc_vu_cu,
        "chuc_vu_moi": ls.chuc_vu_moi,
        "ly_do": ls.ly_do,
        "ngay_hieu_luc": ls.ngay_hieu_luc,
        "nguoi_thuc_hien_id": ls.nguoi_thuc_hien_id,
        "nguoi_thuc_hien_ten": ls.nguoi_thuc_hien.ho_ten if ls.nguoi_thuc_hien else None,
        "created_at": ls.created_at,
    }


def danh_muc_to_response(dm: DanhMucSpCongViec) -> dict:
    """Convert DanhMucSpCongViec to response dict."""
    return {
        "id": dm.id,
        "ma_danh_muc": dm.ma_danh_muc,
        "ten_cong_viec": dm.ten_cong_viec,
        "mo_ta": dm.mo_ta,
        "nhom_cong_viec": dm.nhom_cong_viec,
        "is_active": dm.is_active,
        "sp_chuan_id": dm.sp_chuan_id,
        "sp_chuan_ma": dm.sp_chuan.ma_sp if dm.sp_chuan else None,
        "sp_chuan_ten": dm.sp_chuan.ten_sp if dm.sp_chuan else None,
        "he_so_quy_doi": dm.sp_chuan.he_so_quy_doi_sp1 if dm.sp_chuan else None,
        "don_vi_ap_dung_id": dm.don_vi_ap_dung_id,
        "don_vi_ap_dung_ten": dm.don_vi_ap_dung.ten_don_vi if dm.don_vi_ap_dung else "Toàn Chi cục",
        "created_at": dm.created_at,
    }


# =============================================================================
# THỐNG KÊ ADMIN
# =============================================================================

@router.get(
    "/stats",
    summary="Thống kê tổng quan Admin",
    response_model=DataResponse[AdminStatsResponse],
)
async def get_admin_stats(
    db: DatabaseDep,
    admin: AdminUserDep,
) -> dict:
    """Lấy thống kê tổng quan cho Admin Dashboard."""
    
    # Đếm users
    user_stmt = select(
        func.count(CongChuc.id).label("total"),
        func.sum(func.cast(CongChuc.is_active, Integer)).label("active"),
    ).where(CongChuc.is_deleted == False)
    user_result = await db.execute(user_stmt)
    user_row = user_result.one()
    
    tong_user = user_row.total or 0
    user_active = user_row.active or 0
    
    # Đếm đơn vị
    dv_stmt = select(func.count(DonVi.id)).where(
        DonVi.is_deleted == False,
        DonVi.is_active == True
    )
    tong_don_vi = (await db.execute(dv_stmt)).scalar() or 0
    
    # Đếm SP chuẩn
    sp_stmt = select(func.count(SpCongViecChuan.id)).where(
        SpCongViecChuan.is_active == True
    )
    tong_sp_chuan = (await db.execute(sp_stmt)).scalar() or 0
    
    # Đếm cấp độ
    cd_stmt = select(func.count(CapDoPhucTap.id)).where(
        CapDoPhucTap.is_active == True
    )
    tong_cap_do = (await db.execute(cd_stmt)).scalar() or 0
    
    # Đếm danh mục CV
    dm_stmt = select(func.count(DanhMucSpCongViec.id)).where(
        DanhMucSpCongViec.is_deleted == False,
        DanhMucSpCongViec.is_active == True
    )
    tong_danh_muc_cv = (await db.execute(dm_stmt)).scalar() or 0
    
    data = {
        "tong_user": tong_user,
        "user_active": user_active,
        "user_inactive": tong_user - user_active,
        "tong_don_vi": tong_don_vi,
        "tong_sp_chuan": tong_sp_chuan,
        "tong_cap_do": tong_cap_do,
        "tong_danh_muc_cv": tong_danh_muc_cv,
    }
    
    return success_response(data=data, message="Thống kê Admin")


# =============================================================================
# VAI TRÒ - DANH SÁCH VAI TRÒ
# =============================================================================

@router.get(
    "/vai-tro",
    summary="Danh sách tất cả vai trò",
)
async def get_vai_tro_list(
    db: DatabaseDep,
    admin: AdminUserDep,
) -> dict:
    """Lấy danh sách tất cả vai trò từ bảng vai_tro (bao gồm QLDV)."""
    stmt = select(VaiTro).where(VaiTro.is_active == True).order_by(VaiTro.created_at)
    result = await db.execute(stmt)
    vai_tro_list = result.scalars().all()

    data = [
        {
            "id": str(vt.id),
            "ma_vai_tro": vt.ma_vai_tro,
            "ten_vai_tro": vt.ten_vai_tro,
            "cap_bac": vt.cap_bac.value if vt.cap_bac else None,
            "is_lanh_dao": vt.is_lanh_dao,
            "is_system_admin": vt.is_system_admin,
        }
        for vt in vai_tro_list
    ]

    return success_response(data=data, message="Danh sách vai trò")


# =============================================================================
# USER MANAGEMENT - LIST & DETAIL
# =============================================================================

@router.get(
    "/users",
    summary="Danh sách tất cả người dùng",
    response_model=PaginatedResponse[UserResponse],
)
async def get_users(
    db: DatabaseDep,
    admin: AdminUserDep,
    page: int = Query(default=1, ge=1, description="Trang hiện tại"),
    page_size: int = Query(default=20, ge=1, le=100, description="Số item/trang"),
    search: Optional[str] = Query(default=None, description="Tìm theo mã CC hoặc họ tên"),
    don_vi_id: Optional[UUID] = Query(default=None, description="Filter theo đơn vị"),
    vai_tro_id: Optional[UUID] = Query(default=None, description="Filter theo vai trò"),
    is_active: Optional[bool] = Query(default=None, description="Filter theo trạng thái"),
    is_lanh_dao: Optional[bool] = Query(default=None, description="Filter lãnh đạo"),
) -> dict:
    """Lấy danh sách toàn bộ người dùng với phân trang và filter."""
    
    # Base query
    stmt = (
        select(CongChuc)
        .options(
            selectinload(CongChuc.don_vi),
            selectinload(CongChuc.vai_tro),
        )
        .where(CongChuc.is_deleted == False)
    )
    
    # Filters
    if search:
        search_pattern = f"%{search}%"
        stmt = stmt.where(
            or_(
                CongChuc.ma_cc.ilike(search_pattern),
                CongChuc.ho_ten.ilike(search_pattern),
            )
        )
    
    if don_vi_id:
        stmt = stmt.where(CongChuc.don_vi_id == don_vi_id)
    
    if vai_tro_id:
        stmt = stmt.where(CongChuc.vai_tro_id == vai_tro_id)
    
    if is_active is not None:
        stmt = stmt.where(CongChuc.is_active == is_active)
    
    if is_lanh_dao is not None:
        stmt = stmt.where(CongChuc.is_lanh_dao == is_lanh_dao)
    
    # Count total
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0
    
    # Pagination
    offset = (page - 1) * page_size
    stmt = stmt.order_by(CongChuc.ma_cc).offset(offset).limit(page_size)
    
    result = await db.execute(stmt)
    users = result.scalars().all()
    
    data = [user_to_response(u) for u in users]
    
    return {
        "success": True,
        "data": data,
        "pagination": Pagination(
            page=page,
            page_size=page_size,
            total_items=total,
            total_pages=(total + page_size - 1) // page_size,
        ).model_dump(),
        "message": f"Có {total} người dùng",
    }


@router.get(
    "/users/{user_id}",
    summary="Chi tiết người dùng",
    response_model=DataResponse[UserResponse],
)
async def get_user_detail(
    user_id: UUID,
    db: DatabaseDep,
    admin: AdminUserDep,
) -> dict:
    """Lấy chi tiết một người dùng."""
    
    stmt = (
        select(CongChuc)
        .options(
            selectinload(CongChuc.don_vi),
            selectinload(CongChuc.vai_tro),
        )
        .where(CongChuc.id == user_id)
        .where(CongChuc.is_deleted == False)
    )
    
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response(code="ADMIN_007", message="User không tồn tại")
        )
    
    return success_response(data=user_to_response(user), message="Chi tiết user")


# =============================================================================
# USER MANAGEMENT - CREATE
# =============================================================================

@router.post(
    "/users",
    summary="Tạo mới tài khoản",
    response_model=DataResponse[UserResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_user(
    payload: UserCreateRequest,
    db: DatabaseDep,
    admin: AdminUserDep,
) -> dict:
    """
    Tạo mới tài khoản người dùng.
    
    - Password mặc định: 123456
    - Username tự động = ma_cc (lowercase)
    """
    
    # Kiểm tra mã CC đã tồn tại chưa
    existing_stmt = select(CongChuc).where(
        CongChuc.ma_cc == payload.ma_cc,
        CongChuc.is_deleted == False
    )
    existing = (await db.execute(existing_stmt)).scalar_one_or_none()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_response(code="ADMIN_005", message=f"Mã công chức '{payload.ma_cc}' đã tồn tại")
        )
    
    # Kiểm tra đơn vị tồn tại
    don_vi_stmt = select(DonVi).where(
        DonVi.id == payload.don_vi_id,
        DonVi.is_deleted == False
    )
    don_vi = (await db.execute(don_vi_stmt)).scalar_one_or_none()
    
    if not don_vi:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_response(code="ADMIN_004", message="Đơn vị không tồn tại")
        )
    
    # Kiểm tra vai trò tồn tại
    vai_tro_stmt = select(VaiTro).where(VaiTro.id == payload.vai_tro_id)
    vai_tro = (await db.execute(vai_tro_stmt)).scalar_one_or_none()
    
    if not vai_tro:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_response(code="ADMIN_004", message="Vai trò không tồn tại")
        )
    
    # Tạo user mới - v1.1.0: Dùng hash_password() để generate hash động
    new_user = CongChuc(
        ma_cc=payload.ma_cc,
        ho_ten=payload.ho_ten,
        don_vi_id=payload.don_vi_id,
        vai_tro_id=payload.vai_tro_id,
        email=payload.email,
        so_dien_thoai=payload.so_dien_thoai,
        ngay_sinh=payload.ngay_sinh,
        gioi_tinh=GioiTinh(payload.gioi_tinh) if payload.gioi_tinh else None,
        chuc_vu=payload.chuc_vu,
        is_lanh_dao=payload.is_lanh_dao or vai_tro.is_lanh_dao,
        is_active=True,
        username=payload.ma_cc.lower(),
        password_hash=hash_password(DEFAULT_PASSWORD),
    )
    
    db.add(new_user)
    
    try:
        await db.flush()
        await db.refresh(new_user, ["don_vi", "vai_tro"])
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(code="DB_ERROR", message=f"Lỗi tạo user: {str(e)}")
        )
    
    return success_response(
        data=user_to_response(new_user),
        message=f"Đã tạo tài khoản '{payload.ma_cc}' với mật khẩu mặc định 123456"
    )


# =============================================================================
# USER MANAGEMENT - UPDATE
# =============================================================================

@router.put(
    "/users/{user_id}",
    summary="Cập nhật thông tin người dùng",
    response_model=DataResponse[UserResponse],
)
async def update_user(
    user_id: UUID,
    payload: UserUpdateRequest,
    db: DatabaseDep,
    admin: AdminUserDep,
) -> dict:
    """Cập nhật thông tin cơ bản của người dùng."""
    
    # Lấy user
    stmt = (
        select(CongChuc)
        .options(selectinload(CongChuc.don_vi), selectinload(CongChuc.vai_tro))
        .where(CongChuc.id == user_id)
        .where(CongChuc.is_deleted == False)
    )
    user = (await db.execute(stmt)).scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response(code="ADMIN_007", message="User không tồn tại")
        )
    
    # Không cho phép sửa ADMIN-001
    if user.ma_cc == PROTECTED_ADMIN_MA_CC:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=error_response(code="ADMIN_002", message="Không thể thao tác với tài khoản ADMIN-001")
        )
    
    # Cập nhật các trường
    if payload.ho_ten is not None:
        user.ho_ten = payload.ho_ten
    if payload.email is not None:
        user.email = payload.email
    if payload.so_dien_thoai is not None:
        user.so_dien_thoai = payload.so_dien_thoai
    if payload.ngay_sinh is not None:
        user.ngay_sinh = payload.ngay_sinh
    if payload.gioi_tinh is not None:
        user.gioi_tinh = GioiTinh(payload.gioi_tinh)
    if payload.chuc_vu is not None:
        user.chuc_vu = payload.chuc_vu
    if payload.ngay_vao_nganh is not None:
        user.ngay_vao_nganh = payload.ngay_vao_nganh
    if payload.ngay_vao_chi_cuc is not None:
        user.ngay_vao_chi_cuc = payload.ngay_vao_chi_cuc
    
    try:
        await db.flush()
        await db.refresh(user, ["don_vi", "vai_tro"])
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(code="DB_ERROR", message=f"Lỗi cập nhật: {str(e)}")
        )
    
    return success_response(data=user_to_response(user), message="Cập nhật thành công")


# =============================================================================
# USER MANAGEMENT - STATUS (Kích hoạt/Vô hiệu hóa)
# =============================================================================

@router.put(
    "/users/{user_id}/status",
    summary="Kích hoạt/Vô hiệu hóa tài khoản",
    response_model=DataResponse[UserResponse],
)
async def update_user_status(
    user_id: UUID,
    payload: UserStatusRequest,
    db: DatabaseDep,
    admin: AdminUserDep,
) -> dict:
    """Kích hoạt hoặc vô hiệu hóa tài khoản."""
    
    stmt = (
        select(CongChuc)
        .options(selectinload(CongChuc.don_vi), selectinload(CongChuc.vai_tro))
        .where(CongChuc.id == user_id)
        .where(CongChuc.is_deleted == False)
    )
    user = (await db.execute(stmt)).scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response(code="ADMIN_007", message="User không tồn tại")
        )
    
    # Không cho phép vô hiệu hóa ADMIN-001
    if user.ma_cc == PROTECTED_ADMIN_MA_CC:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=error_response(code="ADMIN_002", message="Không thể thao tác với tài khoản ADMIN-001")
        )
    
    user.is_active = payload.is_active
    
    try:
        await db.flush()
        await db.refresh(user, ["don_vi", "vai_tro"])
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(code="DB_ERROR", message=f"Lỗi: {str(e)}")
        )
    
    action = "kích hoạt" if payload.is_active else "vô hiệu hóa"
    return success_response(data=user_to_response(user), message=f"Đã {action} tài khoản")


# =============================================================================
# USER MANAGEMENT - RESET PASSWORD
# =============================================================================

@router.put(
    "/users/{user_id}/reset-password",
    summary="Đặt lại mật khẩu về mặc định",
    response_model=DataResponse[dict],
)
async def reset_user_password(
    user_id: UUID,
    db: DatabaseDep,
    admin: AdminUserDep,
) -> dict:
    """Đặt lại mật khẩu về 123456."""
    
    stmt = select(CongChuc).where(
        CongChuc.id == user_id,
        CongChuc.is_deleted == False
    )
    user = (await db.execute(stmt)).scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response(code="ADMIN_007", message="User không tồn tại")
        )
    
    # Không cho phép reset password ADMIN-001
    if user.ma_cc == PROTECTED_ADMIN_MA_CC:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=error_response(code="ADMIN_002", message="Không thể thao tác với tài khoản ADMIN-001")
        )
    
    # v1.1.0: Dùng hash_password() để generate hash động
    user.password_hash = hash_password(DEFAULT_PASSWORD)
    
    try:
        await db.flush()
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(code="DB_ERROR", message=f"Lỗi: {str(e)}")
        )
    
    return success_response(
        data={"user_id": str(user_id), "ma_cc": user.ma_cc, "new_password": "123456"},
        message=f"Đã đặt lại mật khẩu cho '{user.ma_cc}' về 123456"
    )


# =============================================================================
# USER MANAGEMENT - DELETE (Xóa hoàn toàn)
# =============================================================================

@router.delete(
    "/users/{user_id}",
    summary="Xóa hoàn toàn người dùng",
    response_model=DataResponse[dict],
)
async def delete_user(
    user_id: UUID,
    db: DatabaseDep,
    admin: AdminUserDep,
) -> dict:
    """
    Xóa hoàn toàn người dùng khỏi hệ thống (hard delete).
    
    Điều kiện:
    - User phải đang bị vô hiệu hóa (is_active = False)
    - Không thể xóa tài khoản ADMIN-001
    
    Dữ liệu bị xóa:
    - Phê duyệt SP (phe_duyet_sp)
    - Kê khai công việc (ke_khai_cong_viec)
    - Kê khai lãnh đạo (ke_khai_lanh_dao)
    - Tiêu chí chung đánh giá (tieu_chi_chung_danh_gia)
    - Lãnh đạo chỉ số (lanh_dao_chi_so)
    - Đánh giá D,Đ,E (danh_gia_dde)
    - Chi tiết xếp loại (chi_tiet_xep_loai)
    - Đăng ký nghỉ (dang_ky_nghi)
    - Đánh giá tháng (danh_gia_thang)
    - Lịch sử điều chuyển (lich_su_dieu_chuyen)
    
    Lưu ý: Thao tác này KHÔNG THỂ HOÀN TÁC!
    """
    
    stmt = select(CongChuc).where(
        CongChuc.id == user_id,
        CongChuc.is_deleted == False
    )
    user = (await db.execute(stmt)).scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response(code="ADMIN_007", message="User không tồn tại")
        )
    
    # Không cho phép xóa ADMIN-001
    if user.ma_cc == PROTECTED_ADMIN_MA_CC:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=error_response(code="ADMIN_002", message="Không thể xóa tài khoản ADMIN-001")
        )
    
    # Chỉ cho phép xóa user đã bị vô hiệu hóa
    if user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_response(
                code="ADMIN_008", 
                message="Chỉ có thể xóa user đã bị vô hiệu hóa. Vui lòng vô hiệu hóa trước khi xóa."
            )
        )
    
    # Lưu thông tin để trả về
    deleted_info = {
        "user_id": str(user_id),
        "ma_cc": user.ma_cc,
        "ho_ten": user.ho_ten,
    }
    
    try:
        # Xóa các dữ liệu liên quan theo thứ tự FK (con trước, cha sau)
        # Tham khảo: clear_user_month.sh
        
        # 1. Xóa phê duyệt SP (FK → ke_khai_cong_viec)
        await db.execute(
            text("""
                DELETE FROM phe_duyet_sp 
                WHERE ke_khai_id IN (
                    SELECT id FROM ke_khai_cong_viec WHERE cong_chuc_id = :user_id
                )
            """),
            {"user_id": user_id}
        )
        
        # 2. Xóa kê khai công việc
        await db.execute(
            text("DELETE FROM ke_khai_cong_viec WHERE cong_chuc_id = :user_id"),
            {"user_id": user_id}
        )
        
        # 3. Xóa kê khai lãnh đạo
        await db.execute(
            text("DELETE FROM ke_khai_lanh_dao WHERE cong_chuc_id = :user_id"),
            {"user_id": user_id}
        )
        
        # 4. Xóa tiêu chí chung đánh giá (FK → danh_gia_thang)
        await db.execute(
            text("""
                DELETE FROM tieu_chi_chung_danh_gia 
                WHERE danh_gia_thang_id IN (
                    SELECT id FROM danh_gia_thang WHERE cong_chuc_id = :user_id
                )
            """),
            {"user_id": user_id}
        )
        
        # 5. Xóa lãnh đạo chỉ số (FK → danh_gia_thang)
        await db.execute(
            text("""
                DELETE FROM lanh_dao_chi_so 
                WHERE danh_gia_thang_id IN (
                    SELECT id FROM danh_gia_thang WHERE cong_chuc_id = :user_id
                )
            """),
            {"user_id": user_id}
        )
        
        # 6. Xóa đánh giá D,Đ,E
        await db.execute(
            text("DELETE FROM danh_gia_dde WHERE cong_chuc_id = :user_id"),
            {"user_id": user_id}
        )
        
        # 7. Xóa chi tiết xếp loại
        await db.execute(
            text("DELETE FROM chi_tiet_xep_loai WHERE cong_chuc_id = :user_id"),
            {"user_id": user_id}
        )
        
        # 8. Xóa đăng ký nghỉ
        await db.execute(
            text("DELETE FROM dang_ky_nghi WHERE cong_chuc_id = :user_id"),
            {"user_id": user_id}
        )
        
        # 9. Xóa đánh giá tháng (bảng cha - xóa sau các bảng con)
        await db.execute(
            text("DELETE FROM danh_gia_thang WHERE cong_chuc_id = :user_id"),
            {"user_id": user_id}
        )
        
        # 10. Xóa lịch sử điều chuyển
        await db.execute(
            text("DELETE FROM lich_su_dieu_chuyen WHERE cong_chuc_id = :user_id"),
            {"user_id": user_id}
        )
        
        # 11. Cuối cùng: Xóa user
        await db.delete(user)
        
        await db.flush()
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(code="DB_ERROR", message=f"Lỗi xóa user: {str(e)}")
        )
    
    return success_response(
        data=deleted_info,
        message=f"Đã xóa hoàn toàn tài khoản '{deleted_info['ma_cc']}' ({deleted_info['ho_ten']})"
    )


# =============================================================================
# USER MANAGEMENT - TRANSFER (Điều chuyển)
# =============================================================================

@router.put(
    "/users/{user_id}/transfer",
    summary="Điều chuyển nhân sự",
    response_model=DataResponse[UserResponse],
)
async def transfer_user(
    user_id: UUID,
    payload: UserTransferRequest,
    db: DatabaseDep,
    admin: AdminUserDep,
) -> dict:
    """
    Điều chuyển nhân sự sang đơn vị/vai trò khác.
    Tự động lưu lịch sử điều chuyển.
    """
    
    # Lấy user hiện tại
    stmt = (
        select(CongChuc)
        .options(selectinload(CongChuc.don_vi), selectinload(CongChuc.vai_tro))
        .where(CongChuc.id == user_id)
        .where(CongChuc.is_deleted == False)
    )
    user = (await db.execute(stmt)).scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response(code="ADMIN_007", message="User không tồn tại")
        )
    
    # Không cho phép điều chuyển ADMIN-001
    if user.ma_cc == PROTECTED_ADMIN_MA_CC:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=error_response(code="ADMIN_002", message="Không thể thao tác với tài khoản ADMIN-001")
        )
    
    # Lưu thông tin cũ để ghi lịch sử
    don_vi_cu_id = user.don_vi_id
    vai_tro_cu_id = user.vai_tro_id
    chuc_vu_cu = user.chuc_vu
    
    has_change = False
    
    # Cập nhật đơn vị mới
    if payload.don_vi_id_moi and payload.don_vi_id_moi != user.don_vi_id:
        don_vi_moi_stmt = select(DonVi).where(
            DonVi.id == payload.don_vi_id_moi,
            DonVi.is_deleted == False
        )
        don_vi_moi = (await db.execute(don_vi_moi_stmt)).scalar_one_or_none()
        
        if not don_vi_moi:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_response(code="ADMIN_004", message="Đơn vị mới không tồn tại")
            )
        
        user.don_vi_id = payload.don_vi_id_moi
        has_change = True
    
    # Cập nhật vai trò mới
    if payload.vai_tro_id_moi and payload.vai_tro_id_moi != user.vai_tro_id:
        vai_tro_moi_stmt = select(VaiTro).where(VaiTro.id == payload.vai_tro_id_moi)
        vai_tro_moi = (await db.execute(vai_tro_moi_stmt)).scalar_one_or_none()
        
        if not vai_tro_moi:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_response(code="ADMIN_004", message="Vai trò mới không tồn tại")
            )
        
        user.vai_tro_id = payload.vai_tro_id_moi
        # Cập nhật is_lanh_dao theo vai trò mới
        user.is_lanh_dao = vai_tro_moi.is_lanh_dao
        has_change = True
    
    # Cập nhật chức vụ
    if payload.chuc_vu_moi is not None:
        user.chuc_vu = payload.chuc_vu_moi
        has_change = True
    
    # Cập nhật is_lanh_dao nếu được chỉ định
    if payload.is_lanh_dao is not None:
        user.is_lanh_dao = payload.is_lanh_dao
        has_change = True
    
    if not has_change:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_response(code="VAL_001", message="Không có thông tin thay đổi")
        )

    # =========================================================================
    # XỬ LÝ DỮ LIỆU LỊCH SỬ KHI CHUYỂN ĐƠN VỊ
    # =========================================================================
    if payload.don_vi_id_moi and payload.don_vi_id_moi != don_vi_cu_id:
        # 1. Lock all unlocked DanhGiaThang records for current month or older
        current_month = date.today().month
        current_year = date.today().year

        await db.execute(
            sa.update(DanhGiaThang)
            .where(DanhGiaThang.cong_chuc_id == user_id)
            .where(DanhGiaThang.is_khoa == False)
            .where(
                or_(
                    DanhGiaThang.nam < current_year,
                    and_(
                        DanhGiaThang.nam == current_year,
                        DanhGiaThang.thang <= current_month
                    )
                )
            )
            .values(is_khoa=True)
        )

        # 2. Soft-delete all NHAP status ke_khai_cong_viec records
        await db.execute(
            sa.update(KeKhaiCongViec)
            .where(KeKhaiCongViec.cong_chuc_id == user_id)
            .where(KeKhaiCongViec.trang_thai == TrangThaiKeKhai.NHAP)
            .where(KeKhaiCongViec.is_deleted == False)
            .values(is_deleted=True, is_khoa=True)
        )

        # 3. Remove CC from chi_tiet_xep_loai if BaoCaoXepLoai is NHAP, CHO_PHE_DUYET, or TU_CHOI
        # (Không xóa nếu đã DA_PHE_DUYET - báo cáo đã khóa)
        # First, get the chi_tiet_xep_loai records to delete
        chi_tiet_to_delete_stmt = (
            select(ChiTietXepLoai.id)
            .join(BaoCaoXepLoai)
            .where(ChiTietXepLoai.cong_chuc_id == user_id)
            .where(
                or_(
                    BaoCaoXepLoai.trang_thai == "NHAP",
                    BaoCaoXepLoai.trang_thai == "CHO_PHE_DUYET",
                    BaoCaoXepLoai.trang_thai == "TU_CHOI"
                )
            )
        )
        result = await db.execute(chi_tiet_to_delete_stmt)
        chi_tiet_ids = [row[0] for row in result.fetchall()]

        if chi_tiet_ids:
            await db.execute(
                sa.delete(ChiTietXepLoai)
                .where(ChiTietXepLoai.id.in_(chi_tiet_ids))
            )

        await db.flush()

    # Tạo bản ghi lịch sử điều chuyển
    lich_su = LichSuDieuChuyen(
        cong_chuc_id=user_id,
        don_vi_cu_id=don_vi_cu_id,
        don_vi_moi_id=user.don_vi_id,
        vai_tro_cu_id=vai_tro_cu_id,
        vai_tro_moi_id=user.vai_tro_id,
        chuc_vu_cu=chuc_vu_cu,
        chuc_vu_moi=user.chuc_vu,
        ly_do=payload.ly_do,
        ngay_hieu_luc=payload.ngay_hieu_luc or date.today(),
        nguoi_thuc_hien_id=admin.id,
    )
    db.add(lich_su)
    
    try:
        await db.flush()
        await db.refresh(user, ["don_vi", "vai_tro"])
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(code="DB_ERROR", message=f"Lỗi điều chuyển: {str(e)}")
        )
    
    return success_response(data=user_to_response(user), message="Điều chuyển thành công")


# =============================================================================
# USER MANAGEMENT - TRANSFER HISTORY
# =============================================================================

@router.get(
    "/users/{user_id}/transfer-history",
    summary="Lịch sử điều chuyển của nhân sự",
    response_model=DataResponse[List[LichSuDieuChuyenResponse]],
)
async def get_transfer_history(
    user_id: UUID,
    db: DatabaseDep,
    admin: AdminUserDep,
) -> dict:
    """Lấy lịch sử điều chuyển của một nhân sự."""
    
    # Kiểm tra user tồn tại
    user_stmt = select(CongChuc).where(
        CongChuc.id == user_id,
        CongChuc.is_deleted == False
    )
    user = (await db.execute(user_stmt)).scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response(code="ADMIN_007", message="User không tồn tại")
        )
    
    # Lấy lịch sử
    stmt = (
        select(LichSuDieuChuyen)
        .options(
            selectinload(LichSuDieuChuyen.don_vi_cu),
            selectinload(LichSuDieuChuyen.don_vi_moi),
            selectinload(LichSuDieuChuyen.vai_tro_cu),
            selectinload(LichSuDieuChuyen.vai_tro_moi),
            selectinload(LichSuDieuChuyen.nguoi_thuc_hien),
        )
        .where(LichSuDieuChuyen.cong_chuc_id == user_id)
        .order_by(LichSuDieuChuyen.created_at.desc())
    )
    
    result = await db.execute(stmt)
    histories = result.scalars().all()
    
    data = [lich_su_to_response(ls) for ls in histories]
    
    return success_response(
        data=data,
        message=f"Có {len(data)} lần điều chuyển"
    )


# =============================================================================
# SP CHUẨN MANAGEMENT
# =============================================================================

@router.get(
    "/sp-chuan",
    summary="Danh sách SP Chuẩn",
    response_model=DataResponse[List[SpChuanResponse]],
)
async def get_sp_chuan_list(
    db: DatabaseDep,
    admin: AdminUserDep,
    include_inactive: bool = Query(default=False, description="Bao gồm SP không active"),
) -> dict:
    """Lấy danh sách tất cả SP Chuẩn."""
    
    stmt = select(SpCongViecChuan)
    
    if not include_inactive:
        stmt = stmt.where(SpCongViecChuan.is_active == True)
    
    stmt = stmt.order_by(SpCongViecChuan.ma_sp)
    
    result = await db.execute(stmt)
    items = result.scalars().all()
    
    data = [
        {
            "id": sp.id,
            "ma_sp": sp.ma_sp,
            "ten_sp": sp.ten_sp,
            "mo_ta": sp.mo_ta,
            "thoi_gian_phut": sp.thoi_gian_phut,
            "he_so_quy_doi_sp1": sp.he_so_quy_doi_sp1,
            "is_sp_goc": sp.is_sp_goc,
            "is_active": sp.is_active,
            "created_at": sp.created_at,
        }
        for sp in items
    ]
    
    return success_response(data=data, message=f"Có {len(data)} SP chuẩn")


@router.get(
    "/sp-chuan/{sp_id}",
    summary="Chi tiết SP Chuẩn",
    response_model=DataResponse[SpChuanResponse],
)
async def get_sp_chuan_detail(
    sp_id: UUID,
    db: DatabaseDep,
    admin: AdminUserDep,
) -> dict:
    """Lấy chi tiết một SP Chuẩn."""
    
    stmt = select(SpCongViecChuan).where(SpCongViecChuan.id == sp_id)
    sp = (await db.execute(stmt)).scalar_one_or_none()
    
    if not sp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response(code="NOT_FOUND", message="SP Chuẩn không tồn tại")
        )
    
    data = {
        "id": sp.id,
        "ma_sp": sp.ma_sp,
        "ten_sp": sp.ten_sp,
        "mo_ta": sp.mo_ta,
        "thoi_gian_phut": sp.thoi_gian_phut,
        "he_so_quy_doi_sp1": sp.he_so_quy_doi_sp1,
        "is_sp_goc": sp.is_sp_goc,
        "is_active": sp.is_active,
        "created_at": sp.created_at,
    }
    
    return success_response(data=data, message="Chi tiết SP Chuẩn")


@router.post(
    "/sp-chuan",
    summary="Tạo mới SP Chuẩn",
    response_model=DataResponse[SpChuanResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_sp_chuan(
    payload: SpChuanCreateRequest,
    db: DatabaseDep,
    admin: AdminUserDep,
) -> dict:
    """Tạo mới SP Chuẩn."""
    
    # Kiểm tra mã đã tồn tại
    existing_stmt = select(SpCongViecChuan).where(SpCongViecChuan.ma_sp == payload.ma_sp)
    existing = (await db.execute(existing_stmt)).scalar_one_or_none()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_response(code="ADMIN_005", message=f"Mã SP '{payload.ma_sp}' đã tồn tại")
        )
    
    new_sp = SpCongViecChuan(
        ma_sp=payload.ma_sp,
        ten_sp=payload.ten_sp,
        mo_ta=payload.mo_ta,
        thoi_gian_phut=payload.thoi_gian_phut,
        he_so_quy_doi_sp1=payload.he_so_quy_doi_sp1,
        is_sp_goc=False,
        is_active=True,
    )
    
    db.add(new_sp)
    
    try:
        await db.flush()
        await db.refresh(new_sp)
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(code="DB_ERROR", message=f"Lỗi tạo SP Chuẩn: {str(e)}")
        )
    
    data = {
        "id": new_sp.id,
        "ma_sp": new_sp.ma_sp,
        "ten_sp": new_sp.ten_sp,
        "mo_ta": new_sp.mo_ta,
        "thoi_gian_phut": new_sp.thoi_gian_phut,
        "he_so_quy_doi_sp1": new_sp.he_so_quy_doi_sp1,
        "is_sp_goc": new_sp.is_sp_goc,
        "is_active": new_sp.is_active,
        "created_at": new_sp.created_at,
    }
    
    return success_response(data=data, message=f"Đã tạo SP Chuẩn '{payload.ma_sp}'")


@router.put(
    "/sp-chuan/{sp_id}",
    summary="Cập nhật SP Chuẩn",
    response_model=DataResponse[SpChuanResponse],
)
async def update_sp_chuan(
    sp_id: UUID,
    payload: SpChuanUpdateRequest,
    db: DatabaseDep,
    admin: AdminUserDep,
) -> dict:
    """Cập nhật SP Chuẩn."""
    
    stmt = select(SpCongViecChuan).where(SpCongViecChuan.id == sp_id)
    sp = (await db.execute(stmt)).scalar_one_or_none()
    
    if not sp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response(code="NOT_FOUND", message="SP Chuẩn không tồn tại")
        )
    
    # Nếu là SP gốc (SP1), không cho sửa hệ số
    if sp.is_sp_goc and payload.he_so_quy_doi_sp1 is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_response(code="ADMIN_002", message="Không thể sửa hệ số của SP gốc (SP1)")
        )
    
    # Cập nhật các trường
    if payload.ten_sp is not None:
        sp.ten_sp = payload.ten_sp
    if payload.mo_ta is not None:
        sp.mo_ta = payload.mo_ta
    if payload.thoi_gian_phut is not None:
        sp.thoi_gian_phut = payload.thoi_gian_phut
    if payload.he_so_quy_doi_sp1 is not None:
        sp.he_so_quy_doi_sp1 = payload.he_so_quy_doi_sp1
    
    try:
        await db.flush()
        await db.refresh(sp)
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(code="DB_ERROR", message=f"Lỗi cập nhật: {str(e)}")
        )
    
    data = {
        "id": sp.id,
        "ma_sp": sp.ma_sp,
        "ten_sp": sp.ten_sp,
        "mo_ta": sp.mo_ta,
        "thoi_gian_phut": sp.thoi_gian_phut,
        "he_so_quy_doi_sp1": sp.he_so_quy_doi_sp1,
        "is_sp_goc": sp.is_sp_goc,
        "is_active": sp.is_active,
        "created_at": sp.created_at,
    }
    
    return success_response(data=data, message="Cập nhật thành công")


@router.delete(
    "/sp-chuan/{sp_id}",
    summary="Vô hiệu hóa SP Chuẩn",
    response_model=DataResponse[dict],
)
async def deactivate_sp_chuan(
    sp_id: UUID,
    db: DatabaseDep,
    admin: AdminUserDep,
) -> dict:
    """Vô hiệu hóa SP Chuẩn (soft delete - đánh dấu is_active=False)."""
    
    stmt = select(SpCongViecChuan).where(SpCongViecChuan.id == sp_id)
    sp = (await db.execute(stmt)).scalar_one_or_none()
    
    if not sp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response(code="NOT_FOUND", message="SP Chuẩn không tồn tại")
        )
    
    # Không cho vô hiệu hóa SP gốc
    if sp.is_sp_goc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_response(code="ADMIN_002", message="Không thể vô hiệu hóa SP gốc (SP1)")
        )
    
    # Kiểm tra có danh mục CV đang sử dụng không
    dm_stmt = select(exists().where(
        DanhMucSpCongViec.sp_chuan_id == sp_id,
        DanhMucSpCongViec.is_deleted == False,
        DanhMucSpCongViec.is_active == True
    ))
    has_dm = (await db.execute(dm_stmt)).scalar()
    
    if has_dm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_response(
                code="ADMIN_003",
                message="Không thể vô hiệu hóa SP đang được sử dụng trong danh mục công việc"
            )
        )
    
    sp.is_active = False
    
    try:
        await db.flush()
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(code="DB_ERROR", message=f"Lỗi: {str(e)}")
        )
    
    return success_response(
        data={"id": str(sp_id), "ma_sp": sp.ma_sp, "is_active": False},
        message=f"Đã vô hiệu hóa SP '{sp.ma_sp}'"
    )


# =============================================================================
# CẤP ĐỘ PHỨC TẠP MANAGEMENT
# =============================================================================

@router.get(
    "/cap-do",
    summary="Danh sách Cấp độ phức tạp",
    response_model=DataResponse[List[CapDoResponse]],
)
async def get_cap_do_list(
    db: DatabaseDep,
    admin: AdminUserDep,
    include_inactive: bool = Query(default=False, description="Bao gồm cấp độ không active"),
) -> dict:
    """Lấy danh sách tất cả Cấp độ phức tạp."""
    
    stmt = select(CapDoPhucTap)
    
    if not include_inactive:
        stmt = stmt.where(CapDoPhucTap.is_active == True)
    
    stmt = stmt.order_by(CapDoPhucTap.thu_tu)
    
    result = await db.execute(stmt)
    items = result.scalars().all()
    
    data = [
        {
            "id": cd.id,
            "ma_cap_do": cd.ma_cap_do,
            "ten_cap_do": cd.ten_cap_do,
            "mo_ta": cd.mo_ta,
            "he_so_sp1": cd.he_so_sp1,
            "he_so_sp2": cd.he_so_sp2,
            "is_theo_thuc_te": cd.is_theo_thuc_te,
            "thu_tu": cd.thu_tu,
            "is_active": cd.is_active,
            "created_at": cd.created_at,
        }
        for cd in items
    ]
    
    return success_response(data=data, message=f"Có {len(data)} cấp độ")


@router.get(
    "/cap-do/{cap_do_id}",
    summary="Chi tiết Cấp độ",
    response_model=DataResponse[CapDoResponse],
)
async def get_cap_do_detail(
    cap_do_id: UUID,
    db: DatabaseDep,
    admin: AdminUserDep,
) -> dict:
    """Lấy chi tiết một Cấp độ."""
    
    stmt = select(CapDoPhucTap).where(CapDoPhucTap.id == cap_do_id)
    cd = (await db.execute(stmt)).scalar_one_or_none()
    
    if not cd:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response(code="NOT_FOUND", message="Cấp độ không tồn tại")
        )
    
    data = {
        "id": cd.id,
        "ma_cap_do": cd.ma_cap_do,
        "ten_cap_do": cd.ten_cap_do,
        "mo_ta": cd.mo_ta,
        "he_so_sp1": cd.he_so_sp1,
        "he_so_sp2": cd.he_so_sp2,
        "is_theo_thuc_te": cd.is_theo_thuc_te,
        "thu_tu": cd.thu_tu,
        "is_active": cd.is_active,
        "created_at": cd.created_at,
    }
    
    return success_response(data=data, message="Chi tiết cấp độ")


@router.post(
    "/cap-do",
    summary="Tạo mới Cấp độ",
    response_model=DataResponse[CapDoResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_cap_do(
    payload: CapDoCreateRequest,
    db: DatabaseDep,
    admin: AdminUserDep,
) -> dict:
    """Tạo mới Cấp độ phức tạp."""
    
    # Kiểm tra mã đã tồn tại
    existing_stmt = select(CapDoPhucTap).where(CapDoPhucTap.ma_cap_do == payload.ma_cap_do)
    existing = (await db.execute(existing_stmt)).scalar_one_or_none()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_response(code="ADMIN_005", message=f"Mã cấp độ '{payload.ma_cap_do}' đã tồn tại")
        )
    
    new_cd = CapDoPhucTap(
        ma_cap_do=payload.ma_cap_do,
        ten_cap_do=payload.ten_cap_do,
        mo_ta=payload.mo_ta,
        he_so_sp1=payload.he_so_sp1,
        he_so_sp2=payload.he_so_sp2,
        is_theo_thuc_te=payload.is_theo_thuc_te,
        thu_tu=payload.thu_tu,
        is_active=True,
    )
    
    db.add(new_cd)
    
    try:
        await db.flush()
        await db.refresh(new_cd)
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(code="DB_ERROR", message=f"Lỗi tạo cấp độ: {str(e)}")
        )
    
    data = {
        "id": new_cd.id,
        "ma_cap_do": new_cd.ma_cap_do,
        "ten_cap_do": new_cd.ten_cap_do,
        "mo_ta": new_cd.mo_ta,
        "he_so_sp1": new_cd.he_so_sp1,
        "he_so_sp2": new_cd.he_so_sp2,
        "is_theo_thuc_te": new_cd.is_theo_thuc_te,
        "thu_tu": new_cd.thu_tu,
        "is_active": new_cd.is_active,
        "created_at": new_cd.created_at,
    }
    
    return success_response(data=data, message=f"Đã tạo cấp độ '{payload.ma_cap_do}'")


@router.put(
    "/cap-do/{cap_do_id}",
    summary="Cập nhật Cấp độ",
    response_model=DataResponse[CapDoResponse],
)
async def update_cap_do(
    cap_do_id: UUID,
    payload: CapDoUpdateRequest,
    db: DatabaseDep,
    admin: AdminUserDep,
) -> dict:
    """Cập nhật Cấp độ phức tạp."""
    
    stmt = select(CapDoPhucTap).where(CapDoPhucTap.id == cap_do_id)
    cd = (await db.execute(stmt)).scalar_one_or_none()
    
    if not cd:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response(code="NOT_FOUND", message="Cấp độ không tồn tại")
        )
    
    # Cập nhật các trường
    if payload.ten_cap_do is not None:
        cd.ten_cap_do = payload.ten_cap_do
    if payload.mo_ta is not None:
        cd.mo_ta = payload.mo_ta
    if payload.he_so_sp1 is not None:
        cd.he_so_sp1 = payload.he_so_sp1
    if payload.he_so_sp2 is not None:
        cd.he_so_sp2 = payload.he_so_sp2
    if payload.is_theo_thuc_te is not None:
        cd.is_theo_thuc_te = payload.is_theo_thuc_te
    if payload.thu_tu is not None:
        cd.thu_tu = payload.thu_tu
    
    try:
        await db.flush()
        await db.refresh(cd)
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(code="DB_ERROR", message=f"Lỗi cập nhật: {str(e)}")
        )
    
    data = {
        "id": cd.id,
        "ma_cap_do": cd.ma_cap_do,
        "ten_cap_do": cd.ten_cap_do,
        "mo_ta": cd.mo_ta,
        "he_so_sp1": cd.he_so_sp1,
        "he_so_sp2": cd.he_so_sp2,
        "is_theo_thuc_te": cd.is_theo_thuc_te,
        "thu_tu": cd.thu_tu,
        "is_active": cd.is_active,
        "created_at": cd.created_at,
    }
    
    return success_response(data=data, message="Cập nhật thành công")


@router.delete(
    "/cap-do/{cap_do_id}",
    summary="Vô hiệu hóa Cấp độ",
    response_model=DataResponse[dict],
)
async def deactivate_cap_do(
    cap_do_id: UUID,
    db: DatabaseDep,
    admin: AdminUserDep,
) -> dict:
    """Vô hiệu hóa Cấp độ (soft delete)."""
    
    stmt = select(CapDoPhucTap).where(CapDoPhucTap.id == cap_do_id)
    cd = (await db.execute(stmt)).scalar_one_or_none()
    
    if not cd:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response(code="NOT_FOUND", message="Cấp độ không tồn tại")
        )
    
    # Kiểm tra có kê khai đang sử dụng không
    kk_stmt = select(exists().where(
        KeKhaiCongViec.cap_do_id == cap_do_id,
        KeKhaiCongViec.is_deleted == False
    ))
    has_kk = (await db.execute(kk_stmt)).scalar()
    
    if has_kk:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_response(
                code="ADMIN_003",
                message="Không thể vô hiệu hóa cấp độ đang được sử dụng trong kê khai"
            )
        )
    
    cd.is_active = False
    
    try:
        await db.flush()
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(code="DB_ERROR", message=f"Lỗi: {str(e)}")
        )
    
    return success_response(
        data={"id": str(cap_do_id), "ma_cap_do": cd.ma_cap_do, "is_active": False},
        message=f"Đã vô hiệu hóa cấp độ '{cd.ma_cap_do}'"
    )


# =============================================================================
# DANH MỤC CÔNG VIỆC MANAGEMENT
# =============================================================================

@router.get(
    "/danh-muc-cv",
    summary="Danh sách Danh mục công việc",
    response_model=PaginatedResponse[DanhMucCvResponse],
)
async def get_danh_muc_cv_list(
    db: DatabaseDep,
    admin: AdminUserDep,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    search: Optional[str] = Query(default=None, description="Tìm theo mã hoặc tên"),
    sp_chuan_id: Optional[UUID] = Query(default=None, description="Filter theo SP chuẩn"),
    don_vi_id: Optional[UUID] = Query(default=None, description="Filter theo đơn vị áp dụng"),
    include_inactive: bool = Query(default=False, description="Bao gồm danh mục không active"),
) -> dict:
    """Lấy danh sách Danh mục công việc với phân trang và filter."""
    
    stmt = (
        select(DanhMucSpCongViec)
        .options(
            selectinload(DanhMucSpCongViec.sp_chuan),
            selectinload(DanhMucSpCongViec.don_vi_ap_dung),
        )
        .where(DanhMucSpCongViec.is_deleted == False)
    )
    
    if not include_inactive:
        stmt = stmt.where(DanhMucSpCongViec.is_active == True)
    
    if search:
        search_pattern = f"%{search}%"
        stmt = stmt.where(
            or_(
                DanhMucSpCongViec.ma_danh_muc.ilike(search_pattern),
                DanhMucSpCongViec.ten_cong_viec.ilike(search_pattern),
            )
        )
    
    if sp_chuan_id:
        stmt = stmt.where(DanhMucSpCongViec.sp_chuan_id == sp_chuan_id)
    
    if don_vi_id:
        stmt = stmt.where(
            or_(
                DanhMucSpCongViec.don_vi_ap_dung_id == don_vi_id,
                DanhMucSpCongViec.don_vi_ap_dung_id.is_(None),
            )
        )
    
    # Count total
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0
    
    # Pagination
    offset = (page - 1) * page_size
    stmt = stmt.order_by(DanhMucSpCongViec.ma_danh_muc).offset(offset).limit(page_size)
    
    result = await db.execute(stmt)
    items = result.scalars().all()
    
    data = [danh_muc_to_response(dm) for dm in items]
    
    return {
        "success": True,
        "data": data,
        "pagination": Pagination(
            page=page,
            page_size=page_size,
            total_items=total,
            total_pages=(total + page_size - 1) // page_size,
        ).model_dump(),
        "message": f"Có {total} danh mục công việc",
    }


@router.get(
    "/danh-muc-cv/{dm_id}",
    summary="Chi tiết Danh mục công việc",
    response_model=DataResponse[DanhMucCvResponse],
)
async def get_danh_muc_cv_detail(
    dm_id: UUID,
    db: DatabaseDep,
    admin: AdminUserDep,
) -> dict:
    """Lấy chi tiết một Danh mục công việc."""
    
    stmt = (
        select(DanhMucSpCongViec)
        .options(
            selectinload(DanhMucSpCongViec.sp_chuan),
            selectinload(DanhMucSpCongViec.don_vi_ap_dung),
        )
        .where(DanhMucSpCongViec.id == dm_id)
        .where(DanhMucSpCongViec.is_deleted == False)
    )
    dm = (await db.execute(stmt)).scalar_one_or_none()
    
    if not dm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response(code="NOT_FOUND", message="Danh mục không tồn tại")
        )
    
    return success_response(data=danh_muc_to_response(dm), message="Chi tiết danh mục")


@router.post(
    "/danh-muc-cv",
    summary="Tạo mới Danh mục công việc",
    response_model=DataResponse[DanhMucCvResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_danh_muc_cv(
    payload: DanhMucCvCreateRequest,
    db: DatabaseDep,
    admin: AdminUserDep,
) -> dict:
    """Tạo mới Danh mục công việc."""
    
    # Kiểm tra mã đã tồn tại
    existing_stmt = select(DanhMucSpCongViec).where(
        DanhMucSpCongViec.ma_danh_muc == payload.ma_danh_muc,
        DanhMucSpCongViec.is_deleted == False
    )
    existing = (await db.execute(existing_stmt)).scalar_one_or_none()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_response(code="ADMIN_005", message=f"Mã danh mục '{payload.ma_danh_muc}' đã tồn tại")
        )
    
    # Kiểm tra SP chuẩn tồn tại
    sp_stmt = select(SpCongViecChuan).where(
        SpCongViecChuan.id == payload.sp_chuan_id,
        SpCongViecChuan.is_active == True
    )
    sp = (await db.execute(sp_stmt)).scalar_one_or_none()
    
    if not sp:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_response(code="ADMIN_004", message="SP Chuẩn không tồn tại hoặc không active")
        )
    
    # Kiểm tra đơn vị áp dụng (nếu có)
    if payload.don_vi_ap_dung_id:
        dv_stmt = select(DonVi).where(
            DonVi.id == payload.don_vi_ap_dung_id,
            DonVi.is_deleted == False
        )
        dv = (await db.execute(dv_stmt)).scalar_one_or_none()
        
        if not dv:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_response(code="ADMIN_004", message="Đơn vị áp dụng không tồn tại")
            )
    
    new_dm = DanhMucSpCongViec(
        ma_danh_muc=payload.ma_danh_muc,
        ten_cong_viec=payload.ten_cong_viec,
        mo_ta=payload.mo_ta,
        sp_chuan_id=payload.sp_chuan_id,
        don_vi_ap_dung_id=payload.don_vi_ap_dung_id,
        nhom_cong_viec=payload.nhom_cong_viec,
        is_active=True,
    )
    
    db.add(new_dm)
    
    try:
        await db.flush()
        await db.refresh(new_dm, ["sp_chuan", "don_vi_ap_dung"])
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(code="DB_ERROR", message=f"Lỗi tạo danh mục: {str(e)}")
        )
    
    return success_response(
        data=danh_muc_to_response(new_dm),
        message=f"Đã tạo danh mục '{payload.ma_danh_muc}'"
    )


@router.put(
    "/danh-muc-cv/{dm_id}",
    summary="Cập nhật Danh mục công việc",
    response_model=DataResponse[DanhMucCvResponse],
)
async def update_danh_muc_cv(
    dm_id: UUID,
    payload: DanhMucCvUpdateRequest,
    db: DatabaseDep,
    admin: AdminUserDep,
) -> dict:
    """Cập nhật Danh mục công việc."""
    
    stmt = (
        select(DanhMucSpCongViec)
        .options(
            selectinload(DanhMucSpCongViec.sp_chuan),
            selectinload(DanhMucSpCongViec.don_vi_ap_dung),
        )
        .where(DanhMucSpCongViec.id == dm_id)
        .where(DanhMucSpCongViec.is_deleted == False)
    )
    dm = (await db.execute(stmt)).scalar_one_or_none()
    
    if not dm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response(code="NOT_FOUND", message="Danh mục không tồn tại")
        )
    
    # Kiểm tra SP chuẩn mới (nếu có)
    if payload.sp_chuan_id:
        sp_stmt = select(SpCongViecChuan).where(
            SpCongViecChuan.id == payload.sp_chuan_id,
            SpCongViecChuan.is_active == True
        )
        sp = (await db.execute(sp_stmt)).scalar_one_or_none()
        
        if not sp:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_response(code="ADMIN_004", message="SP Chuẩn không tồn tại")
            )
    
    # Cập nhật các trường
    if payload.ten_cong_viec is not None:
        dm.ten_cong_viec = payload.ten_cong_viec
    if payload.mo_ta is not None:
        dm.mo_ta = payload.mo_ta
    if payload.sp_chuan_id is not None:
        dm.sp_chuan_id = payload.sp_chuan_id
    if payload.don_vi_ap_dung_id is not None:
        dm.don_vi_ap_dung_id = payload.don_vi_ap_dung_id
    if payload.nhom_cong_viec is not None:
        dm.nhom_cong_viec = payload.nhom_cong_viec
    
    try:
        await db.flush()
        await db.refresh(dm, ["sp_chuan", "don_vi_ap_dung"])
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(code="DB_ERROR", message=f"Lỗi cập nhật: {str(e)}")
        )
    
    return success_response(data=danh_muc_to_response(dm), message="Cập nhật thành công")


@router.delete(
    "/danh-muc-cv/{dm_id}",
    summary="Vô hiệu hóa Danh mục công việc",
    response_model=DataResponse[dict],
)
async def deactivate_danh_muc_cv(
    dm_id: UUID,
    db: DatabaseDep,
    admin: AdminUserDep,
) -> dict:
    """Vô hiệu hóa Danh mục công việc (soft delete)."""
    
    stmt = select(DanhMucSpCongViec).where(
        DanhMucSpCongViec.id == dm_id,
        DanhMucSpCongViec.is_deleted == False
    )
    dm = (await db.execute(stmt)).scalar_one_or_none()
    
    if not dm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response(code="NOT_FOUND", message="Danh mục không tồn tại")
        )
    
    # Kiểm tra có kê khai đang sử dụng không
    kk_stmt = select(exists().where(
        KeKhaiCongViec.danh_muc_sp_id == dm_id,
        KeKhaiCongViec.is_deleted == False
    ))
    has_kk = (await db.execute(kk_stmt)).scalar()
    
    if has_kk:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_response(
                code="ADMIN_003",
                message="Không thể vô hiệu hóa danh mục đang được sử dụng trong kê khai"
            )
        )
    
    dm.is_active = False
    
    try:
        await db.flush()
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(code="DB_ERROR", message=f"Lỗi: {str(e)}")
        )
    
    return success_response(
        data={"id": str(dm_id), "ma_danh_muc": dm.ma_danh_muc, "is_active": False},
        message=f"Đã vô hiệu hóa danh mục '{dm.ma_danh_muc}'"
    )