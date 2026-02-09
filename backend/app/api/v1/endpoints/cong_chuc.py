"""
app/api/v1/endpoints/cong_chuc.py
=================================
API Endpoints cho Quản lý Công chức.

Endpoints:
- GET /cong-chuc: Lấy danh sách công chức (có phân trang)
- GET /cong-chuc/{id}: Lấy chi tiết công chức
- GET /cong-chuc/pho-don-vi/{don_vi_id}: Lấy danh sách Phó ĐV (để chọn người phê duyệt)
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import DatabaseDep, ActiveUserDep
from app.models.user_org import CongChuc, DonVi, VaiTro, CapBacVaiTro
from app.schemas.common import (
    PaginatedResponse, 
    DataResponse, 
    Pagination,
    success_response,
)
from app.schemas.master_data import (
    CongChucResponse,
    CongChucDetailResponse,
    CongChucBriefResponse,
)


router = APIRouter()


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def cong_chuc_to_response(cc: CongChuc) -> dict:
    """
    Convert CongChuc model to response dict.
    Flatten relationships (don_vi, vai_tro) vào response.
    """
    response = {
        "id": cc.id,
        "ma_cc": cc.ma_cc,
        "ho_ten": cc.ho_ten,
        "ngay_sinh": cc.ngay_sinh,
        "gioi_tinh": cc.gioi_tinh.value if cc.gioi_tinh else None,
        "so_dien_thoai": cc.so_dien_thoai,
        "email": cc.email,
        "chuc_vu": cc.chuc_vu,
        "is_lanh_dao": cc.is_lanh_dao,
        "is_active": cc.is_active,
        "ngay_vao_nganh": cc.ngay_vao_nganh,
        "ngay_vao_chi_cuc": cc.ngay_vao_chi_cuc,
        # Đơn vị (flattened)
        "don_vi_id": None,
        "don_vi_ten": None,
        "don_vi_ma": None,
        # Vai trò (flattened)
        "vai_tro_id": None,
        "vai_tro_ma": None,
        "vai_tro_ten": None,
    }
    
    # Flatten đơn vị
    if cc.don_vi:
        response["don_vi_id"] = cc.don_vi.id
        response["don_vi_ten"] = cc.don_vi.ten_don_vi
        response["don_vi_ma"] = cc.don_vi.ma_don_vi
    
    # Flatten vai trò
    if cc.vai_tro:
        response["vai_tro_id"] = cc.vai_tro.id
        response["vai_tro_ma"] = cc.vai_tro.ma_vai_tro
        response["vai_tro_ten"] = cc.vai_tro.ten_vai_tro
    
    return response


def cong_chuc_to_detail_response(cc: CongChuc) -> dict:
    """
    Convert CongChuc model to detailed response dict.
    Bao gồm nested objects và last_login.
    """
    response = cong_chuc_to_response(cc)
    response["last_login"] = cc.last_login
    
    # Nested đơn vị
    if cc.don_vi:
        response["don_vi"] = {
            "id": cc.don_vi.id,
            "ma_don_vi": cc.don_vi.ma_don_vi,
            "ten_don_vi": cc.don_vi.ten_don_vi,
            "ten_viet_tat": cc.don_vi.ten_viet_tat,
            "loai_don_vi": cc.don_vi.loai_don_vi.value if cc.don_vi.loai_don_vi else None,
            "thu_tu_hien_thi": cc.don_vi.thu_tu_hien_thi,
            "is_active": cc.don_vi.is_active,
        }
    else:
        response["don_vi"] = None
    
    # Nested vai trò
    if cc.vai_tro:
        response["vai_tro"] = {
            "id": cc.vai_tro.id,
            "ma_vai_tro": cc.vai_tro.ma_vai_tro,
            "ten_vai_tro": cc.vai_tro.ten_vai_tro,
            "cap_bac": cc.vai_tro.cap_bac.value if cc.vai_tro.cap_bac else None,
            "is_lanh_dao": cc.vai_tro.is_lanh_dao,
        }
    else:
        response["vai_tro"] = None
    
    return response


# =============================================================================
# GET ALL CONG CHUC (PAGINATED)
# =============================================================================

@router.get(
    "",
    summary="Lấy danh sách công chức",
    description="""
    Lấy danh sách công chức với phân trang và filter.
    
    **Filter options:**
    - `don_vi_id`: Lọc theo đơn vị
    - `search`: Tìm kiếm theo tên hoặc mã công chức
    - `is_active`: Lọc theo trạng thái (mặc định: True)
    - `is_lanh_dao`: Lọc lãnh đạo
    
    **Phân trang:**
    - `page`: Trang hiện tại (mặc định: 1)
    - `page_size`: Số item mỗi trang (mặc định: 20, tối đa: 100)
    
    **Quyền truy cập:** 
    - CC: Chỉ xem bản thân
    - Phó ĐV, Trưởng ĐV: Xem CC thuộc đơn vị
    - CCT, PCCT, TCCB, Admin: Xem tất cả
    """,
    response_model=PaginatedResponse[CongChucResponse],
)
async def get_cong_chuc_list(
    db: DatabaseDep,
    current_user: ActiveUserDep,
    # Pagination
    page: int = Query(default=1, ge=1, description="Trang hiện tại"),
    page_size: int = Query(default=20, ge=1, le=100, description="Số item mỗi trang"),
    # Filters
    don_vi_id: Optional[UUID] = Query(default=None, description="Filter theo đơn vị"),
    search: Optional[str] = Query(
        default=None, 
        min_length=1, 
        max_length=100,
        description="Tìm kiếm theo tên hoặc mã CC"
    ),
    is_active: Optional[bool] = Query(default=True, description="Filter active"),
    is_lanh_dao: Optional[bool] = Query(default=None, description="Filter lãnh đạo"),
) -> dict:
    """
    Lấy danh sách công chức với phân trang.
    
    Query với eager loading cho don_vi và vai_tro.
    """
    # Base query với eager loading
    base_query = (
        select(CongChuc)
        .options(
            selectinload(CongChuc.don_vi),
            selectinload(CongChuc.vai_tro),
        )
        .where(CongChuc.is_deleted == False)
    )
    
    # Count query (không cần eager loading)
    count_query = (
        select(func.count(CongChuc.id))
        .where(CongChuc.is_deleted == False)
    )
    
    # Apply filters
    if don_vi_id:
        base_query = base_query.where(CongChuc.don_vi_id == don_vi_id)
        count_query = count_query.where(CongChuc.don_vi_id == don_vi_id)
    
    if is_active is not None:
        base_query = base_query.where(CongChuc.is_active == is_active)
        count_query = count_query.where(CongChuc.is_active == is_active)
    
    if is_lanh_dao is not None:
        base_query = base_query.where(CongChuc.is_lanh_dao == is_lanh_dao)
        count_query = count_query.where(CongChuc.is_lanh_dao == is_lanh_dao)
    
    if search:
        # Tìm kiếm theo tên hoặc mã CC (case-insensitive)
        search_pattern = f"%{search}%"
        search_filter = or_(
            CongChuc.ho_ten.ilike(search_pattern),
            CongChuc.ma_cc.ilike(search_pattern),
        )
        base_query = base_query.where(search_filter)
        count_query = count_query.where(search_filter)
    
    # Loại bỏ Super Admin khỏi danh sách (trừ khi user là Admin)
    is_admin = getattr(current_user, 'is_system_admin', False)
    if current_user.vai_tro and getattr(current_user.vai_tro, 'is_system_admin', False):
        is_admin = True
    
    if not is_admin:
        # Không hiển thị Super Admin trong danh sách
        base_query = base_query.where(
            ~CongChuc.vai_tro.has(VaiTro.is_system_admin == True)
        )
        count_query = count_query.where(
            ~CongChuc.vai_tro_id.in_(
                select(VaiTro.id).where(VaiTro.is_system_admin == True)
            )
        )
    
    # Get total count
    count_result = await db.execute(count_query)
    total_items = count_result.scalar() or 0
    
    # Apply pagination
    offset = (page - 1) * page_size
    base_query = (
        base_query
        .order_by(CongChuc.ho_ten.asc())
        .offset(offset)
        .limit(page_size)
    )
    
    # Execute query
    result = await db.execute(base_query)
    cong_chuc_list = result.scalars().all()
    
    # Convert to response format
    data = [cong_chuc_to_response(cc) for cc in cong_chuc_list]
    
    # Build pagination info
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
# GET CONG CHUC BY ID
# =============================================================================

@router.get(
    "/{cong_chuc_id}",
    summary="Lấy chi tiết công chức",
    description="""
    Lấy thông tin chi tiết của một công chức theo ID.
    
    **Bao gồm:**
    - Thông tin cá nhân
    - Thông tin đơn vị (nested)
    - Thông tin vai trò (nested)
    - Thời gian đăng nhập cuối
    
    **Quyền truy cập:** Theo phân quyền.
    """,
    response_model=DataResponse[CongChucDetailResponse],
    responses={
        404: {
            "description": "Không tìm thấy công chức",
        }
    }
)
async def get_cong_chuc_detail(
    cong_chuc_id: UUID,
    db: DatabaseDep,
    current_user: ActiveUserDep,
) -> dict:
    """
    Lấy chi tiết một công chức theo ID.
    """
    # Query với eager loading
    stmt = (
        select(CongChuc)
        .options(
            selectinload(CongChuc.don_vi),
            selectinload(CongChuc.vai_tro),
        )
        .where(CongChuc.id == cong_chuc_id)
        .where(CongChuc.is_deleted == False)
    )
    
    result = await db.execute(stmt)
    cong_chuc = result.scalar_one_or_none()
    
    if not cong_chuc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": {
                    "code": "NOT_FOUND",
                    "message": "Không tìm thấy công chức"
                }
            }
        )
    
    # Convert to response
    data = cong_chuc_to_detail_response(cong_chuc)
    
    return success_response(data=data)


# =============================================================================
# GET PHO DON VI BY DON VI ID
# =============================================================================

@router.get(
    "/pho-don-vi/{don_vi_id}",
    summary="Lấy danh sách Phó đơn vị",
    description="""
    Lấy danh sách Phó đơn vị của một đơn vị cụ thể.
    
    **Mục đích:** Để công chức chọn người phê duyệt khi kê khai công việc.
    
    **Quyền truy cập:** Tất cả user đã đăng nhập.
    """,
    response_model=DataResponse[list],
)
async def get_pho_don_vi_list(
    don_vi_id: UUID,
    db: DatabaseDep,
    current_user: ActiveUserDep,
) -> dict:
    """
    Lấy danh sách Phó đơn vị của đơn vị để CC chọn người phê duyệt.
    """
    # Query Phó đơn vị (vai trò PDV hoặc PCCT)
    stmt = (
        select(CongChuc)
        .join(VaiTro, CongChuc.vai_tro_id == VaiTro.id)
        .where(CongChuc.don_vi_id == don_vi_id)
        .where(CongChuc.is_deleted == False)
        .where(CongChuc.is_active == True)
        .where(
            (VaiTro.cap_bac == CapBacVaiTro.PHO_DON_VI) |
            (VaiTro.cap_bac == CapBacVaiTro.PHO_CHI_CUC_TRUONG)
        )
        .order_by(CongChuc.ho_ten.asc())
    )
    
    result = await db.execute(stmt)
    pho_dv_list = result.scalars().all()
    
    # Convert to brief response
    data = [
        {
            "id": cc.id,
            "ma_cc": cc.ma_cc,
            "ho_ten": cc.ho_ten,
        }
        for cc in pho_dv_list
    ]
    
    return success_response(data=data)


# =============================================================================
# GET CONG CHUC CURRENT USER'S DON VI
# =============================================================================

@router.get(
    "/don-vi/current",
    summary="Lấy danh sách CC cùng đơn vị",
    description="""
    Lấy danh sách công chức thuộc cùng đơn vị với user hiện tại.
    
    **Quyền truy cập:** Tất cả user đã đăng nhập.
    """,
    response_model=DataResponse[list],
)
async def get_cong_chuc_same_don_vi(
    db: DatabaseDep,
    current_user: ActiveUserDep,
) -> dict:
    """
    Lấy danh sách công chức cùng đơn vị với user hiện tại.
    """
    if not current_user.don_vi_id:
        return success_response(data=[])
    
    # Query công chức cùng đơn vị
    stmt = (
        select(CongChuc)
        .options(selectinload(CongChuc.vai_tro))
        .where(CongChuc.don_vi_id == current_user.don_vi_id)
        .where(CongChuc.is_deleted == False)
        .where(CongChuc.is_active == True)
        .order_by(CongChuc.ho_ten.asc())
    )
    
    result = await db.execute(stmt)
    cc_list = result.scalars().all()
    
    # Convert to response
    data = [cong_chuc_to_response(cc) for cc in cc_list]
    
    return success_response(data=data)
