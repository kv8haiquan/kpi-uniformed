"""
app/api/v1/endpoints/don_vi.py
==============================
API Endpoints cho Quản lý Đơn vị.

Endpoints:
- GET /don-vi: Lấy danh sách đơn vị
- GET /don-vi/{id}: Lấy chi tiết đơn vị
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import DatabaseDep, ActiveUserDep
from app.models.user_org import DonVi, CongChuc, VaiTro, CapBacVaiTro
from app.schemas.common import DataListResponse, DataResponse, success_response
from app.schemas.master_data import (
    DonViResponse, 
    DonViDetailResponse,
    CongChucBriefResponse,
)


router = APIRouter()


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def don_vi_to_response(don_vi: DonVi) -> dict:
    """
    Convert DonVi model to response dict.
    Xử lý enum values để serialize đúng.
    """
    return {
        "id": don_vi.id,
        "ma_don_vi": don_vi.ma_don_vi,
        "ten_don_vi": don_vi.ten_don_vi,
        "ten_viet_tat": don_vi.ten_viet_tat,
        "loai_don_vi": don_vi.loai_don_vi.value if don_vi.loai_don_vi else None,
        "parent_id": don_vi.parent_id,
        "thu_tu_hien_thi": don_vi.thu_tu_hien_thi,
        "is_active": don_vi.is_active,
    }


# =============================================================================
# GET ALL DON VI
# =============================================================================

@router.get(
    "",
    summary="Lấy danh sách đơn vị",
    description="""
    Lấy toàn bộ danh sách đơn vị trong Chi cục.
    
    **Sắp xếp:** Theo `thu_tu_hien_thi` tăng dần.
    
    **Quyền truy cập:** Tất cả user đã đăng nhập.
    """,
    response_model=DataListResponse[DonViResponse],
)
async def get_don_vi_list(
    db: DatabaseDep,
    current_user: ActiveUserDep,
    is_active: Optional[bool] = Query(
        default=None,
        description="Filter theo trạng thái active (None = tất cả)"
    ),
) -> dict:
    """
    Lấy danh sách tất cả đơn vị.
    
    - Sắp xếp theo thứ tự hiển thị
    - Chỉ lấy đơn vị chưa bị xóa (is_deleted = False)
    - Optional: Filter theo is_active
    """
    # Build query
    stmt = (
        select(DonVi)
        .where(DonVi.is_deleted == False)
        .order_by(DonVi.thu_tu_hien_thi.asc(), DonVi.ten_don_vi.asc())
    )
    
    # Filter theo is_active nếu có
    if is_active is not None:
        stmt = stmt.where(DonVi.is_active == is_active)
    
    # Execute query
    result = await db.execute(stmt)
    don_vi_list = result.scalars().all()
    
    # Convert to response format
    data = [don_vi_to_response(dv) for dv in don_vi_list]
    
    return success_response(data=data)


# =============================================================================
# GET DON VI BY ID
# =============================================================================

@router.get(
    "/{don_vi_id}",
    summary="Lấy chi tiết đơn vị",
    description="""
    Lấy thông tin chi tiết của một đơn vị theo ID.
    
    **Bao gồm:**
    - Thông tin cơ bản của đơn vị
    - Số lượng công chức
    - Thông tin Trưởng đơn vị
    - Danh sách Phó đơn vị
    
    **Quyền truy cập:** Tất cả user đã đăng nhập.
    """,
    response_model=DataResponse[DonViDetailResponse],
    responses={
        404: {
            "description": "Không tìm thấy đơn vị",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "error": {
                            "code": "NOT_FOUND",
                            "message": "Không tìm thấy đơn vị"
                        }
                    }
                }
            }
        }
    }
)
async def get_don_vi_detail(
    don_vi_id: UUID,
    db: DatabaseDep,
    current_user: ActiveUserDep,
) -> dict:
    """
    Lấy chi tiết một đơn vị theo ID.
    
    Bao gồm:
    - Thông tin cơ bản
    - Đếm số công chức
    - Tìm Trưởng đơn vị (vai trò TDV)
    - Tìm các Phó đơn vị (vai trò PDV)
    """
    # Query đơn vị
    stmt = (
        select(DonVi)
        .where(DonVi.id == don_vi_id)
        .where(DonVi.is_deleted == False)
    )
    result = await db.execute(stmt)
    don_vi = result.scalar_one_or_none()
    
    if not don_vi:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": {
                    "code": "NOT_FOUND",
                    "message": "Không tìm thấy đơn vị"
                }
            }
        )
    
    # Đếm số công chức
    count_stmt = (
        select(func.count(CongChuc.id))
        .where(CongChuc.don_vi_id == don_vi_id)
        .where(CongChuc.is_deleted == False)
        .where(CongChuc.is_active == True)
    )
    count_result = await db.execute(count_stmt)
    so_cong_chuc = count_result.scalar() or 0
    
    # Tìm Trưởng đơn vị (vai trò TDV hoặc CCT nếu là Lãnh đạo Chi cục)
    truong_dv = None
    truong_stmt = (
        select(CongChuc)
        .join(VaiTro, CongChuc.vai_tro_id == VaiTro.id)
        .where(CongChuc.don_vi_id == don_vi_id)
        .where(CongChuc.is_deleted == False)
        .where(CongChuc.is_active == True)
        .where(
            (VaiTro.cap_bac == CapBacVaiTro.TRUONG_DON_VI) |
            (VaiTro.cap_bac == CapBacVaiTro.CHI_CUC_TRUONG)
        )
        .limit(1)
    )
    truong_result = await db.execute(truong_stmt)
    truong_cc = truong_result.scalar_one_or_none()
    if truong_cc:
        truong_dv = {
            "id": truong_cc.id,
            "ma_cc": truong_cc.ma_cc,
            "ho_ten": truong_cc.ho_ten,
        }
    
    # Tìm các Phó đơn vị (vai trò PDV hoặc PCCT)
    pho_dv_list = []
    pho_stmt = (
        select(CongChuc)
        .join(VaiTro, CongChuc.vai_tro_id == VaiTro.id)
        .where(CongChuc.don_vi_id == don_vi_id)
        .where(CongChuc.is_deleted == False)
        .where(CongChuc.is_active == True)
        .where(
            (VaiTro.cap_bac == CapBacVaiTro.PHO_DON_VI) |
            (VaiTro.cap_bac == CapBacVaiTro.PHO_CHI_CUC_TRUONG)
        )
    )
    pho_result = await db.execute(pho_stmt)
    pho_ccs = pho_result.scalars().all()
    for pho_cc in pho_ccs:
        pho_dv_list.append({
            "id": pho_cc.id,
            "ma_cc": pho_cc.ma_cc,
            "ho_ten": pho_cc.ho_ten,
        })
    
    # Build response
    data = don_vi_to_response(don_vi)
    data["so_cong_chuc"] = so_cong_chuc
    data["truong_don_vi"] = truong_dv
    data["pho_don_vi"] = pho_dv_list if pho_dv_list else None
    
    return success_response(data=data)


# =============================================================================
# GET DON VI TREE (Optional - lấy cây đơn vị)
# =============================================================================

@router.get(
    "/tree/all",
    summary="Lấy cây đơn vị",
    description="Lấy danh sách đơn vị dạng cây (parent-children)",
    response_model=DataListResponse[DonViResponse],
)
async def get_don_vi_tree(
    db: DatabaseDep,
    current_user: ActiveUserDep,
) -> dict:
    """
    Lấy danh sách đơn vị sắp xếp theo cây.
    Đơn vị cha trước, đơn vị con sau.
    """
    # Lấy tất cả đơn vị, sắp xếp theo parent_id và thu_tu
    stmt = (
        select(DonVi)
        .where(DonVi.is_deleted == False)
        .where(DonVi.is_active == True)
        .order_by(
            DonVi.parent_id.asc().nulls_first(),
            DonVi.thu_tu_hien_thi.asc(),
            DonVi.ten_don_vi.asc()
        )
    )
    
    result = await db.execute(stmt)
    don_vi_list = result.scalars().all()
    
    data = [don_vi_to_response(dv) for dv in don_vi_list]
    
    return success_response(data=data)
