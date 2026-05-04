"""
app/api/v1/endpoints/danh_muc.py
================================
API Endpoints cho Danh mục Sản phẩm/Công việc.

Endpoints:
- GET /sp-chuan: Lấy danh sách SP chuẩn (SP1-SP4)
- GET /cap-do-phuc-tap: Lấy danh sách cấp độ phức tạp (C1-C5)
- GET /danh-muc-sp: Lấy danh sách công việc (có filter)
- GET /danh-muc-sp/{id}: Lấy chi tiết công việc
"""

from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import DatabaseDep, ActiveUserDep
from app.models.task_catalog import SpCongViecChuan, CapDoPhucTap, DanhMucSpCongViec
from app.models.user_org import DonVi
from app.schemas.common import (
    DataListResponse,
    DataResponse,
    PaginatedResponse,
    Pagination,
    success_response,
)
from app.schemas.master_data import (
    SpChuanResponse,
    CapDoResponse,
    DanhMucSpResponse,
    DanhMucSpBriefResponse,
)


router = APIRouter()


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def sp_chuan_to_response(sp: SpCongViecChuan) -> dict:
    """Convert SpCongViecChuan model to response dict."""
    return {
        "id": sp.id,
        "ma_sp": sp.ma_sp,
        "ten_sp": sp.ten_sp,
        "mo_ta": sp.mo_ta,
        "thoi_gian_phut": sp.thoi_gian_phut,
        "he_so_quy_doi_sp1": float(sp.he_so_quy_doi_sp1),  # Decimal -> float cho JSON
        "is_sp_goc": sp.is_sp_goc,
        "is_active": sp.is_active,
    }


def cap_do_to_response(cd: CapDoPhucTap) -> dict:
    """Convert CapDoPhucTap model to response dict."""
    return {
        "id": cd.id,
        "ma_cap_do": cd.ma_cap_do,
        "ten_cap_do": cd.ten_cap_do,
        "mo_ta": cd.mo_ta,
        "he_so_sp1": float(cd.he_so_sp1),
        "he_so_sp2": float(cd.he_so_sp2),
        "is_theo_thuc_te": cd.is_theo_thuc_te,
        "thu_tu": cd.thu_tu,
        "is_active": cd.is_active,
    }


def danh_muc_to_response(dm: DanhMucSpCongViec) -> dict:
    """Convert DanhMucSpCongViec model to response dict."""
    response = {
        "id": dm.id,
        "ma_danh_muc": dm.ma_danh_muc,
        "ten_cong_viec": dm.ten_cong_viec,
        "mo_ta": dm.mo_ta,
        "nhom_cong_viec": dm.nhom_cong_viec,
        "is_active": dm.is_active,
        "sp_chuan_id": str(dm.sp_chuan_id) if dm.sp_chuan_id else None,  # v2.7.0: Thêm sp_chuan_id trực tiếp
        "don_vi_ap_dung_id": dm.don_vi_ap_dung_id,
        "don_vi_ap_dung_ten": None,
        "sp_chuan": None,
    }
    
    # Nested SP chuẩn
    if dm.sp_chuan:
        response["sp_chuan"] = sp_chuan_to_response(dm.sp_chuan)
    
    # Đơn vị áp dụng
    if dm.don_vi_ap_dung:
        response["don_vi_ap_dung_ten"] = dm.don_vi_ap_dung.ten_don_vi
    
    return response


def danh_muc_to_brief_response(dm: DanhMucSpCongViec) -> dict:
    """Convert DanhMucSpCongViec model to brief response dict."""
    return {
        "id": dm.id,
        "ma_danh_muc": dm.ma_danh_muc,
        "ten_cong_viec": dm.ten_cong_viec,
        "ma_sp": dm.sp_chuan.ma_sp if dm.sp_chuan else None,
        "nhom_cong_viec": dm.nhom_cong_viec,
    }


# =============================================================================
# SP CHUAN (SP1-SP4)
# =============================================================================

@router.get(
    "/sp-chuan",
    summary="Lấy danh sách SP chuẩn",
    description="""
    Lấy danh sách 4 loại Sản phẩm chuẩn theo Quy chế KPI:
    
    - **SP1**: Tờ khai HQ được kiểm tra chi tiết hồ sơ (5 phút = 1 SP gốc)
    - **SP2**: Văn bản hành chính (60 phút = 12 SP gốc)
    - **SP3**: Giờ trực làm việc (60 phút = 12 SP gốc)
    - **SP4**: Giờ tuần tra kiểm soát (60 phút = 12 SP gốc)
    
    **Quyền truy cập:** Tất cả user đã đăng nhập.
    """,
    response_model=DataListResponse[SpChuanResponse],
)
async def get_sp_chuan_list(
    db: DatabaseDep,
    current_user: ActiveUserDep,
    is_active: Optional[bool] = Query(default=True, description="Filter active"),
) -> dict:
    """
    Lấy danh sách SP chuẩn (SP1-SP4).
    Sắp xếp theo mã SP.
    """
    stmt = select(SpCongViecChuan).order_by(SpCongViecChuan.ma_sp.asc())
    
    if is_active is not None:
        stmt = stmt.where(SpCongViecChuan.is_active == is_active)
    
    result = await db.execute(stmt)
    sp_list = result.scalars().all()
    
    data = [sp_chuan_to_response(sp) for sp in sp_list]
    
    return success_response(data=data)


# =============================================================================
# CAP DO PHUC TAP (C1-C5)
# =============================================================================

@router.get(
    "/cap-do-phuc-tap",
    summary="Lấy danh sách cấp độ phức tạp",
    description="""
    Lấy danh sách 5 cấp độ phức tạp theo Quy chế KPI:
    
    - **C1** (Dễ): SP1 x1, SP2 x1
    - **C2** (Trung bình): SP1 x4, SP2 x2
    - **C3** (Khó): SP1 x12, SP2 x4
    - **C4** (Rất khó): SP1 x24, SP2 x8
    - **C5** (Theo thực tế): Hệ số do lãnh đạo xác định
    
    **Quyền truy cập:** Tất cả user đã đăng nhập.
    """,
    response_model=DataListResponse[CapDoResponse],
)
async def get_cap_do_list(
    db: DatabaseDep,
    current_user: ActiveUserDep,
    is_active: Optional[bool] = Query(default=True, description="Filter active"),
) -> dict:
    """
    Lấy danh sách cấp độ phức tạp (C1-C5).
    Sắp xếp theo thứ tự.
    """
    stmt = select(CapDoPhucTap).order_by(CapDoPhucTap.thu_tu.asc())
    
    if is_active is not None:
        stmt = stmt.where(CapDoPhucTap.is_active == is_active)
    
    result = await db.execute(stmt)
    cap_do_list = result.scalars().all()
    
    data = [cap_do_to_response(cd) for cd in cap_do_list]
    
    return success_response(data=data)


# =============================================================================
# DANH MUC SP/CONG VIEC
# =============================================================================

@router.get(
    "/danh-muc-sp",
    summary="Lấy danh sách công việc",
    description="""
    Lấy danh sách danh mục sản phẩm/công việc với filter.
    
    **Filter options:**
    - `nhom_cong_viec`: Lọc theo nhóm công việc
    - `sp_chuan_id`: Lọc theo loại SP chuẩn (SP1-SP4)
    - `don_vi_ap_dung_id`: Lọc theo đơn vị áp dụng
    - `search`: Tìm kiếm theo tên hoặc mã
    
    **Quyền truy cập:** Tất cả user đã đăng nhập.
    """,
    response_model=PaginatedResponse[DanhMucSpResponse],
)
async def get_danh_muc_sp_list(
    db: DatabaseDep,
    current_user: ActiveUserDep,
    # Pagination
    page: int = Query(default=1, ge=1, description="Trang hiện tại"),
    page_size: int = Query(default=50, ge=1, le=200, description="Số item mỗi trang"),
    # Filters
    nhom_cong_viec: Optional[str] = Query(default=None, description="Filter theo nhóm công việc"),
    sp_chuan_id: Optional[UUID] = Query(default=None, description="Filter theo SP chuẩn"),
    don_vi_ap_dung_id: Optional[UUID] = Query(default=None, description="Filter theo đơn vị áp dụng"),
    search: Optional[str] = Query(
        default=None,
        min_length=1,
        max_length=100,
        description="Tìm kiếm theo tên hoặc mã"
    ),
    is_active: Optional[bool] = Query(default=True, description="Filter active"),
) -> dict:
    """
    Lấy danh sách danh mục SP/CV với phân trang và filter.
    """
    # Base query với eager loading
    base_query = (
        select(DanhMucSpCongViec)
        .options(
            selectinload(DanhMucSpCongViec.sp_chuan),
            selectinload(DanhMucSpCongViec.don_vi_ap_dung),
        )
        .where(DanhMucSpCongViec.is_deleted == False)
    )
    
    # Count query
    count_query = (
        select(func.count(DanhMucSpCongViec.id))
        .where(DanhMucSpCongViec.is_deleted == False)
    )
    
    # Apply filters
    if is_active is not None:
        base_query = base_query.where(DanhMucSpCongViec.is_active == is_active)
        count_query = count_query.where(DanhMucSpCongViec.is_active == is_active)
    
    if nhom_cong_viec:
        base_query = base_query.where(DanhMucSpCongViec.nhom_cong_viec == nhom_cong_viec)
        count_query = count_query.where(DanhMucSpCongViec.nhom_cong_viec == nhom_cong_viec)
    
    if sp_chuan_id:
        base_query = base_query.where(DanhMucSpCongViec.sp_chuan_id == sp_chuan_id)
        count_query = count_query.where(DanhMucSpCongViec.sp_chuan_id == sp_chuan_id)
    
    if don_vi_ap_dung_id:
        # Lấy công việc của đơn vị cụ thể HOẶC toàn Chi cục (NULL)
        base_query = base_query.where(
            (DanhMucSpCongViec.don_vi_ap_dung_id == don_vi_ap_dung_id) |
            (DanhMucSpCongViec.don_vi_ap_dung_id.is_(None))
        )
        count_query = count_query.where(
            (DanhMucSpCongViec.don_vi_ap_dung_id == don_vi_ap_dung_id) |
            (DanhMucSpCongViec.don_vi_ap_dung_id.is_(None))
        )
    
    if search:
        search_pattern = f"%{search}%"
        search_filter = or_(
            DanhMucSpCongViec.ten_cong_viec.ilike(search_pattern),
            DanhMucSpCongViec.ma_danh_muc.ilike(search_pattern),
        )
        base_query = base_query.where(search_filter)
        count_query = count_query.where(search_filter)
    
    # Get total count
    count_result = await db.execute(count_query)
    total_items = count_result.scalar() or 0
    
    # Apply pagination
    offset = (page - 1) * page_size
    base_query = (
        base_query
        .order_by(
            DanhMucSpCongViec.nhom_cong_viec.asc().nulls_last(),
            DanhMucSpCongViec.ma_danh_muc.asc(),
        )
        .offset(offset)
        .limit(page_size)
    )
    
    # Execute query
    result = await db.execute(base_query)
    danh_muc_list = result.scalars().all()
    
    # Convert to response
    data = [danh_muc_to_response(dm) for dm in danh_muc_list]
    
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


@router.get(
    "/danh-muc-sp/{danh_muc_id}",
    summary="Lấy chi tiết công việc",
    description="""
    Lấy thông tin chi tiết của một danh mục sản phẩm/công việc theo ID.
    
    **Quyền truy cập:** Tất cả user đã đăng nhập.
    """,
    response_model=DataResponse[DanhMucSpResponse],
    responses={
        404: {"description": "Không tìm thấy danh mục"}
    }
)
async def get_danh_muc_sp_detail(
    danh_muc_id: UUID,
    db: DatabaseDep,
    current_user: ActiveUserDep,
) -> dict:
    """
    Lấy chi tiết một danh mục SP/CV theo ID.
    """
    stmt = (
        select(DanhMucSpCongViec)
        .options(
            selectinload(DanhMucSpCongViec.sp_chuan),
            selectinload(DanhMucSpCongViec.don_vi_ap_dung),
        )
        .where(DanhMucSpCongViec.id == danh_muc_id)
        .where(DanhMucSpCongViec.is_deleted == False)
    )
    
    result = await db.execute(stmt)
    danh_muc = result.scalar_one_or_none()
    
    if not danh_muc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": {
                    "code": "NOT_FOUND",
                    "message": "Không tìm thấy danh mục sản phẩm/công việc"
                }
            }
        )
    
    data = danh_muc_to_response(danh_muc)
    
    return success_response(data=data)


# =============================================================================
# GET NHOM CONG VIEC (Distinct)
# =============================================================================

@router.get(
    "/nhom-cong-viec",
    summary="Lấy danh sách nhóm công việc",
    description="""
    Lấy danh sách các nhóm công việc hiện có (distinct values).
    
    Dùng để hiển thị dropdown filter trên UI.
    
    **Quyền truy cập:** Tất cả user đã đăng nhập.
    """,
    response_model=DataResponse[List[str]],
)
async def get_nhom_cong_viec_list(
    db: DatabaseDep,
    current_user: ActiveUserDep,
) -> dict:
    """
    Lấy danh sách nhóm công việc (distinct).
    """
    stmt = (
        select(DanhMucSpCongViec.nhom_cong_viec)
        .where(DanhMucSpCongViec.is_deleted == False)
        .where(DanhMucSpCongViec.is_active == True)
        .where(DanhMucSpCongViec.nhom_cong_viec.isnot(None))
        .distinct()
        .order_by(DanhMucSpCongViec.nhom_cong_viec.asc())
    )
    
    result = await db.execute(stmt)
    nhom_list = result.scalars().all()

    # Filter out None values
    data = [nhom for nhom in nhom_list if nhom]

    return success_response(data=data)


# =============================================================================
# PL3 V2 ENDPOINTS (28/04/2026)
# =============================================================================

# La Mã 1-15 dùng cho sort lĩnh vực
_ROMAN_ORDER = {
    "I": 1, "II": 2, "III": 3, "IV": 4, "V": 5,
    "VI": 6, "VII": 7, "VIII": 8, "IX": 9, "X": 10,
    "XI": 11, "XII": 12, "XIII": 13, "XIV": 14, "XV": 15,
}


@router.get(
    "/linh-vuc",
    summary="Danh sách 15 lĩnh vực PL3 (V2)",
    description="""
    Trả về 15 lĩnh vực (I-XV) cho dropdown filter UI V2.

    Lấy distinct (linh_vuc, ten_linh_vuc) từ các mục PL3 đã seed.
    Sắp xếp theo thứ tự La Mã.

    **Quyền:** mọi user đăng nhập.
    """,
)
async def get_linh_vuc_list_pl3(
    db: DatabaseDep,
    current_user: ActiveUserDep,
) -> dict:
    """Trả về 15 lĩnh vực PL3."""
    stmt = (
        select(
            DanhMucSpCongViec.linh_vuc,
            DanhMucSpCongViec.ten_linh_vuc,
        )
        .where(DanhMucSpCongViec.nguon_du_lieu == "PL3")
        .where(DanhMucSpCongViec.linh_vuc.isnot(None))
        .where(DanhMucSpCongViec.is_deleted == False)
        .distinct()
    )
    rows = (await db.execute(stmt)).all()
    items = [{"ma": r[0], "ten": r[1]} for r in rows]
    items.sort(key=lambda x: _ROMAN_ORDER.get(x["ma"], 999))
    return success_response(data=items)


@router.get(
    "/nhiem-vu",
    summary="Danh sách nhiệm vụ PL3 (V2) — distinct theo lĩnh vực",
    description="""
    Trả về danh sách distinct nhiệm vụ (cột B Excel PL3) cho dropdown filter
    cấp 2 trong modal kê khai V2.

    Yêu cầu query param `linh_vuc` (I-XV). Nhiệm vụ giữa các lĩnh vực có
    thể trùng tên nên BẮT BUỘC truyền lĩnh vực để tránh nhập nhằng.

    **Quyền:** mọi user đăng nhập.
    """,
)
async def get_nhiem_vu_pl3(
    db: DatabaseDep,
    current_user: ActiveUserDep,
    linh_vuc: str = Query(..., description="Mã lĩnh vực La Mã (I-XV)"),
) -> dict:
    """Distinct nhiem_vu lọc theo linh_vuc."""
    stmt = (
        select(DanhMucSpCongViec.nhiem_vu)
        .where(DanhMucSpCongViec.nguon_du_lieu == "PL3")
        .where(DanhMucSpCongViec.is_active == True)
        .where(DanhMucSpCongViec.is_deleted == False)
        .where(DanhMucSpCongViec.linh_vuc == linh_vuc.upper())
        .where(DanhMucSpCongViec.nhiem_vu.isnot(None))
        .distinct()
        .order_by(DanhMucSpCongViec.nhiem_vu.asc())
    )
    rows = (await db.execute(stmt)).scalars().all()
    data = [{"nhiem_vu": nv} for nv in rows if nv]
    return success_response(data=data)


@router.get(
    "/sp-cong-viec/pl3",
    summary="Danh sách mục PL3 — search/filter/pagination cho UI V2",
    description="""
    Trả về danh sách mục PL3 (V2) với filter:
    - **linh_vuc**: I, II, ..., XV
    - **nhiem_vu**: tên nhiệm vụ (cột B Excel) — exact match
    - **nhom_pl3**: 1-5
    - **search**: tìm trong ten_cong_viec + cong_viec_chi_tiet (ILIKE)
    - **page** (≥ 1, mặc định 1)
    - **size** (1-100, mặc định 50)

    Chỉ trả mục `nguon_du_lieu='PL3'` và `is_active=true`.

    **Quyền:** mọi user đăng nhập.
    """,
)
async def get_sp_cong_viec_pl3(
    db: DatabaseDep,
    current_user: ActiveUserDep,
    linh_vuc: Optional[str] = Query(default=None, description="I-XV"),
    nhiem_vu: Optional[str] = Query(default=None, max_length=500, description="Tên nhiệm vụ — exact match"),
    nhom_pl3: Optional[int] = Query(default=None, ge=1, le=5),
    search: Optional[str] = Query(default=None, min_length=1, max_length=200),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=50, ge=1, le=100),
) -> dict:
    """List mục PL3 với search + pagination."""
    base_query = (
        select(DanhMucSpCongViec)
        .where(DanhMucSpCongViec.nguon_du_lieu == "PL3")
        .where(DanhMucSpCongViec.is_active == True)
        .where(DanhMucSpCongViec.is_deleted == False)
    )
    count_query = (
        select(func.count(DanhMucSpCongViec.id))
        .where(DanhMucSpCongViec.nguon_du_lieu == "PL3")
        .where(DanhMucSpCongViec.is_active == True)
        .where(DanhMucSpCongViec.is_deleted == False)
    )

    if linh_vuc:
        base_query = base_query.where(DanhMucSpCongViec.linh_vuc == linh_vuc.upper())
        count_query = count_query.where(DanhMucSpCongViec.linh_vuc == linh_vuc.upper())

    if nhiem_vu:
        base_query = base_query.where(DanhMucSpCongViec.nhiem_vu == nhiem_vu)
        count_query = count_query.where(DanhMucSpCongViec.nhiem_vu == nhiem_vu)

    if nhom_pl3 is not None:
        base_query = base_query.where(DanhMucSpCongViec.nhom_pl3 == nhom_pl3)
        count_query = count_query.where(DanhMucSpCongViec.nhom_pl3 == nhom_pl3)

    if search:
        pattern = f"%{search}%"
        cond = or_(
            DanhMucSpCongViec.ten_cong_viec.ilike(pattern),
            DanhMucSpCongViec.cong_viec_chi_tiet.ilike(pattern),
            DanhMucSpCongViec.san_pham_dau_ra.ilike(pattern),
        )
        base_query = base_query.where(cond)
        count_query = count_query.where(cond)

    total = (await db.execute(count_query)).scalar() or 0
    offset = (page - 1) * size
    base_query = (
        base_query
        .order_by(DanhMucSpCongViec.linh_vuc.asc(), DanhMucSpCongViec.ma_danh_muc.asc())
        .offset(offset)
        .limit(size)
    )
    rows = (await db.execute(base_query)).scalars().all()

    data = []
    for dm in rows:
        data.append({
            "id": dm.id,
            "ma_danh_muc": dm.ma_danh_muc,
            "ten_cong_viec": dm.ten_cong_viec,
            "cong_viec_chi_tiet": dm.cong_viec_chi_tiet,
            "san_pham_dau_ra": dm.san_pham_dau_ra,
            "linh_vuc": dm.linh_vuc,
            "ten_linh_vuc": dm.ten_linh_vuc,
            "nhom_pl3": dm.nhom_pl3,
            "khung_diem_toi_da": dm.khung_diem_toi_da,
            "diem_cham": dm.diem_cham,
            "he_so_quy_doi": float(dm.he_so_quy_doi) if dm.he_so_quy_doi is not None else None,
            "nhiem_vu": dm.nhiem_vu,
            "is_active": dm.is_active,
        })

    pagination = Pagination.create(page=page, page_size=size, total_items=total)
    return {
        "success": True,
        "data": data,
        "pagination": pagination.model_dump(),
    }