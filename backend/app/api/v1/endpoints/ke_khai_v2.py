"""
app/api/v1/endpoints/ke_khai_v2.py
==================================
API Endpoints cho Kê khai công việc V2_PL3 (28/04/2026).

Khác V1:
- Không có cap_do_id, không có he_so_thuc_te (LOCKED 14).
- Hệ số quy đổi đọc thẳng từ danh_muc_sp_cong_viec.he_so_quy_doi.
- Snapshot 3 fields lúc tạo (LOCKED 13 — immutable).
- 1 tháng = 1 version (LOCKED 12) — reject nếu tháng đã có V1.

Endpoints:
- GET    /me                  : Danh sách kê khai V2 của bản thân
- GET    /thong-ke/thang      : Tổng SP tháng (mẫu số V2 dự kiến) cho banner UI
- POST   /                    : Tạo mới
- POST   /nhieu-ngay          : Tạo nhiều ngày
- PUT    /{id}                : Sửa NHAP/TU_CHOI
- DELETE /{id}                : Xoá NHAP/TU_CHOI
- GET    /{id}                : Chi tiết
"""

from decimal import Decimal
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import ActiveUserDep, DatabaseDep, is_qldv
from app.core.kpi_calculator_v2 import (
    calculate_so_sp_goc_quy_doi_v2,
    calculate_sp_dat_v2,
)
from app.models.cong_viec_yeu_thich import CongViecYeuThich
from app.models.kpi_submission import KeKhaiCongViec, TrangThaiKeKhai
from app.models.task_catalog import DanhMucSpCongViec
from app.models.user_org import CongChuc
from app.schemas.common import (
    DataResponse,
    Pagination,
    PaginatedResponse,
    success_response,
)
from app.schemas.kpi_submission_v2 import (
    CongViecYeuThichCreate,
    CongViecYeuThichResponse,
    KeKhaiV2Create,
    KeKhaiV2NhieuNgayCreate,
    KeKhaiV2NhieuNgayResponse,
    KeKhaiV2Response,
    KeKhaiV2Update,
    RecentDanhMucResponse,
    ThongKeKeKhaiV2Response,
)


router = APIRouter()


# =============================================================================
# HELPERS
# =============================================================================

VERSION_V2 = "V2_PL3"
VERSION_V1 = "V1"


async def _load_pl3_danh_muc(db: AsyncSession, danh_muc_sp_id: UUID) -> DanhMucSpCongViec:
    """Load 1 mục PL3 + validate nguon_du_lieu='PL3' + còn active.

    Raises:
        HTTPException 400 — nếu mục không tồn tại / không phải PL3 / inactive.
    """
    stmt = (
        select(DanhMucSpCongViec)
        .where(DanhMucSpCongViec.id == danh_muc_sp_id)
        .where(DanhMucSpCongViec.is_deleted == False)  # noqa: E712
    )
    result = await db.execute(stmt)
    dm = result.scalar_one_or_none()

    if not dm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "error": {"code": "INVALID_DANH_MUC", "message": "Không tìm thấy mục công việc"},
            },
        )

    if dm.nguon_du_lieu != "PL3":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "error": {
                    "code": "INVALID_CATALOG_VERSION",
                    "message": f"Mục '{dm.ma_danh_muc}' là V1, không thể dùng cho kê khai V2_PL3",
                },
            },
        )

    if not dm.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "error": {"code": "INACTIVE_DANH_MUC", "message": "Mục công việc đã ngừng sử dụng"},
            },
        )

    if dm.he_so_quy_doi is None or dm.he_so_quy_doi <= Decimal("0"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "error": {"code": "MISSING_HE_SO", "message": "Mục PL3 thiếu he_so_quy_doi"},
            },
        )

    return dm


async def _check_no_v1_in_month(
    db: AsyncSession, cong_chuc_id: UUID, thang: int, nam: int
) -> None:
    """Đảm bảo (CC, tháng, năm) chưa có kê khai V1 nào.

    LOCKED 12: 1 tháng = 1 version.
    """
    stmt = (
        select(KeKhaiCongViec.version_kekhai)
        .where(KeKhaiCongViec.cong_chuc_id == cong_chuc_id)
        .where(KeKhaiCongViec.thang == thang)
        .where(KeKhaiCongViec.nam == nam)
        .where(KeKhaiCongViec.is_deleted == False)  # noqa: E712
        .limit(1)
    )
    res = await db.execute(stmt)
    existing_version = res.scalar_one_or_none()

    if existing_version is not None and existing_version != VERSION_V2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "error": {
                    "code": "MIXED_VERSION_NOT_ALLOWED",
                    "message": (
                        f"Tháng {thang}/{nam} đã có kê khai phiên bản '{existing_version}'. "
                        "Không thể thêm kê khai V2_PL3 vào tháng này."
                    ),
                },
            },
        )


async def _validate_phe_duyet(db: AsyncSession, nguoi_phe_duyet_id: UUID) -> CongChuc:
    """Verify người phê duyệt còn active."""
    stmt = (
        select(CongChuc)
        .where(CongChuc.id == nguoi_phe_duyet_id)
        .where(CongChuc.is_deleted == False)  # noqa: E712
        .where(CongChuc.is_active == True)  # noqa: E712
    )
    res = await db.execute(stmt)
    npd = res.scalar_one_or_none()
    if not npd:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "error": {
                    "code": "INVALID_APPROVER",
                    "message": "Người phê duyệt không tồn tại hoặc không hoạt động",
                },
            },
        )
    return npd


def _kk_v2_to_response(kk: KeKhaiCongViec) -> dict:
    """Convert model V2 sang dict response."""
    response = {
        "id": kk.id,
        "cong_chuc_id": kk.cong_chuc_id,
        "thang": kk.thang,
        "nam": kk.nam,
        "ngay_thuc_hien": kk.ngay_thuc_hien,
        "version_kekhai": kk.version_kekhai,
        "he_so_quy_doi_snapshot": float(kk.he_so_quy_doi_snapshot) if kk.he_so_quy_doi_snapshot is not None else None,
        "nhom_pl3_snapshot": kk.nhom_pl3_snapshot,
        "linh_vuc_snapshot": kk.linh_vuc_snapshot,
        "danh_muc_sp": None,
        "so_luong": kk.so_luong,
        "nguoi_phe_duyet_id": kk.nguoi_phe_duyet_id,
        "mo_ta_cong_viec": kk.mo_ta_cong_viec,
        "is_doi_moi_sang_tao": kk.is_doi_moi_sang_tao,
        "ngay_deadline": kk.ngay_deadline,
        "ngay_hoan_thanh": kk.ngay_hoan_thanh,
        "trang_thai": kk.trang_thai.value if kk.trang_thai else "NHAP",
        "tu_danh_gia_chat_luong": kk.tu_danh_gia_chat_luong or 0,
        "tu_danh_gia_tien_do": kk.tu_danh_gia_tien_do or 0,
        "ghi_chu_tu_danh_gia": kk.ghi_chu_tu_danh_gia,
        "ghi_chu_tu_dg_chat_luong": kk.ghi_chu_tu_dg_chat_luong,
        "ghi_chu_tu_dg_tien_do": kk.ghi_chu_tu_dg_tien_do,
        "so_loi_chat_luong": kk.so_loi_chat_luong or 0,
        "so_loi_tien_do": kk.so_loi_tien_do or 0,
        "y_kien_lanh_dao": kk.y_kien_lanh_dao,
        "ghi_chu_loi_chat_luong": kk.ghi_chu_loi_chat_luong,
        "ghi_chu_loi_tien_do": kk.ghi_chu_loi_tien_do,
        "so_sp_goc_quy_doi": float(kk.so_sp_goc_quy_doi) if kk.so_sp_goc_quy_doi is not None else None,
        "so_sp_chat_luong": float(kk.so_sp_chat_luong) if kk.so_sp_chat_luong is not None else None,
        "so_sp_tien_do": float(kk.so_sp_tien_do) if kk.so_sp_tien_do is not None else None,
        "is_khoa": kk.is_khoa,
        "created_at": kk.created_at,
        "updated_at": kk.updated_at,
    }

    if kk.danh_muc_sp:
        dm = kk.danh_muc_sp
        response["danh_muc_sp"] = {
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
        }

    response["nguoi_phe_duyet"] = None
    if kk.nguoi_phe_duyet:
        npd = kk.nguoi_phe_duyet
        response["nguoi_phe_duyet"] = {
            "id": npd.id,
            "ho_ten": npd.ho_ten,
            "chuc_vu": npd.chuc_vu,
        }
    return response


def _check_owner_or_403(kk: KeKhaiCongViec, current_user: CongChuc) -> None:
    """Chỉ chủ sở hữu được sửa/xoá."""
    if kk.cong_chuc_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "error": {"code": "NOT_OWNER", "message": "Bạn không phải chủ kê khai này"},
            },
        )


def _check_editable_or_400(kk: KeKhaiCongViec) -> None:
    """Chỉ NHAP/TU_CHOI mới sửa/xoá được."""
    if kk.trang_thai not in (TrangThaiKeKhai.NHAP, TrangThaiKeKhai.TU_CHOI):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "error": {
                    "code": "NOT_EDITABLE",
                    "message": f"Kê khai ở trạng thái {kk.trang_thai.value} không sửa/xoá được",
                },
            },
        )


def _check_v2_or_400(kk: KeKhaiCongViec) -> None:
    """Reject nếu kk không phải V2 (V1 dùng endpoint /ke-khai cũ)."""
    if kk.version_kekhai != VERSION_V2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "error": {
                    "code": "WRONG_VERSION",
                    "message": "Bản kê khai này là V1, vui lòng dùng /api/v1/ke-khai",
                },
            },
        )


def _reject_leader_v2(current_user: CongChuc) -> None:
    """LOCKED 4: V2_PL3 chỉ áp cho công chức.
    Phase 3 (29/04/2026): HD_111 cũng dùng form lãnh đạo, không kê khai V2."""
    if current_user.is_lanh_dao:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "error": {
                    "code": "LEADER_NOT_ALLOWED_V2",
                    "message": "Lãnh đạo kê khai theo V1, vui lòng dùng /ke-khai",
                },
            },
        )
    if current_user.is_hd_111:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "error": {
                    "code": "HD_111_NOT_ALLOWED_V2",
                    "message": "HĐ 111 kê khai theo form công việc, vui lòng dùng /ke-khai",
                },
            },
        )


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.get(
    "/me",
    summary="Danh sách kê khai V2 của bản thân",
    response_model=PaginatedResponse[KeKhaiV2Response],
)
async def list_my_kekhai_v2(
    db: DatabaseDep,
    current_user: ActiveUserDep,
    thang: Optional[int] = Query(default=None, ge=1, le=12),
    nam: Optional[int] = Query(default=None, ge=2025),
    trang_thai: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
) -> dict:
    """Lấy danh sách kê khai V2 của user hiện tại, có filter."""
    base_query = (
        select(KeKhaiCongViec)
        .options(
            selectinload(KeKhaiCongViec.danh_muc_sp),
            selectinload(KeKhaiCongViec.nguoi_phe_duyet),
        )
        .where(KeKhaiCongViec.cong_chuc_id == current_user.id)
        .where(KeKhaiCongViec.version_kekhai == VERSION_V2)
        .where(KeKhaiCongViec.is_deleted == False)  # noqa: E712
    )
    count_query = (
        select(func.count(KeKhaiCongViec.id))
        .where(KeKhaiCongViec.cong_chuc_id == current_user.id)
        .where(KeKhaiCongViec.version_kekhai == VERSION_V2)
        .where(KeKhaiCongViec.is_deleted == False)  # noqa: E712
    )

    if thang:
        base_query = base_query.where(KeKhaiCongViec.thang == thang)
        count_query = count_query.where(KeKhaiCongViec.thang == thang)
    if nam:
        base_query = base_query.where(KeKhaiCongViec.nam == nam)
        count_query = count_query.where(KeKhaiCongViec.nam == nam)
    if trang_thai:
        try:
            tt_enum = TrangThaiKeKhai(trang_thai)
            base_query = base_query.where(KeKhaiCongViec.trang_thai == tt_enum)
            count_query = count_query.where(KeKhaiCongViec.trang_thai == tt_enum)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "success": False,
                    "error": {"code": "INVALID_TRANG_THAI", "message": f"Trạng thái không hợp lệ: {trang_thai}"},
                },
            )

    total = (await db.execute(count_query)).scalar() or 0
    offset = (page - 1) * page_size
    base_query = base_query.order_by(
        KeKhaiCongViec.thang.desc(),
        KeKhaiCongViec.ngay_thuc_hien.desc().nulls_last(),
        KeKhaiCongViec.created_at.desc(),
    ).offset(offset).limit(page_size)

    result = await db.execute(base_query)
    items = result.scalars().all()

    pagination = Pagination.create(page=page, page_size=page_size, total_items=total)

    return {
        "success": True,
        "data": [_kk_v2_to_response(kk) for kk in items],
        "pagination": pagination.model_dump(),
    }


@router.get(
    "/thong-ke/thang",
    summary="Thống kê tổng SP V2 trong tháng (banner UI)",
    response_model=DataResponse[ThongKeKeKhaiV2Response],
)
async def thong_ke_thang_v2(
    db: DatabaseDep,
    current_user: ActiveUserDep,
    thang: int = Query(..., ge=1, le=12),
    nam: int = Query(..., ge=2025),
) -> dict:
    """Thống kê tổng SP V2 đã duyệt + chờ duyệt + dự kiến cho 1 tháng.

    Trả thêm tổng SP đạt CL/TĐ chính thức (DA_PHE_DUYET) và tạm tính
    (NHAP + CHO + DA) để trang /danh-gia-v2 dùng tính 3 chỉ số a, b, c.
    """
    rows = (
        await db.execute(
            select(
                KeKhaiCongViec.trang_thai,
                func.count(KeKhaiCongViec.id),
                func.coalesce(func.sum(KeKhaiCongViec.so_sp_goc_quy_doi), 0),
                func.coalesce(func.sum(KeKhaiCongViec.so_sp_chat_luong), 0),
                func.coalesce(func.sum(KeKhaiCongViec.so_sp_tien_do), 0),
            )
            .where(KeKhaiCongViec.cong_chuc_id == current_user.id)
            .where(KeKhaiCongViec.thang == thang)
            .where(KeKhaiCongViec.nam == nam)
            .where(KeKhaiCongViec.version_kekhai == VERSION_V2)
            .where(KeKhaiCongViec.is_deleted == False)  # noqa: E712
            .group_by(KeKhaiCongViec.trang_thai)
        )
    ).all()

    tong_da_duyet = Decimal("0")
    tong_cho_duyet = Decimal("0")
    tong_nhap = Decimal("0")
    tong_cl_da_duyet = Decimal("0")
    tong_td_da_duyet = Decimal("0")
    tong_cl_tam_tinh = Decimal("0")
    tong_td_tam_tinh = Decimal("0")
    so_da_duyet = 0
    so_cho_duyet = 0
    so_nhap = 0

    for trang_thai, count, sum_sp, sum_cl, sum_td in rows:
        sum_sp = Decimal(str(sum_sp or 0))
        sum_cl = Decimal(str(sum_cl or 0))
        sum_td = Decimal(str(sum_td or 0))
        if trang_thai == TrangThaiKeKhai.DA_PHE_DUYET:
            tong_da_duyet = sum_sp
            tong_cl_da_duyet = sum_cl
            tong_td_da_duyet = sum_td
            so_da_duyet = count
        elif trang_thai == TrangThaiKeKhai.CHO_PHE_DUYET:
            tong_cho_duyet = sum_sp
            so_cho_duyet = count
        elif trang_thai == TrangThaiKeKhai.NHAP:
            tong_nhap = sum_sp
            so_nhap = count
        # Tạm tính cộng dồn 3 trạng thái (NHAP + CHO + DA) — bỏ TU_CHOI/HUY
        if trang_thai in (
            TrangThaiKeKhai.NHAP,
            TrangThaiKeKhai.CHO_PHE_DUYET,
            TrangThaiKeKhai.DA_PHE_DUYET,
        ):
            tong_cl_tam_tinh += sum_cl
            tong_td_tam_tinh += sum_td

    tong_du_kien = tong_da_duyet + tong_cho_duyet + tong_nhap

    return success_response(data={
        "thang": thang,
        "nam": nam,
        "version_kekhai": VERSION_V2,
        "tong_sp_da_duyet": float(tong_da_duyet),
        "tong_sp_cho_duyet": float(tong_cho_duyet),
        "tong_sp_du_kien": float(tong_du_kien),
        "tong_sp_chat_luong_da_duyet": float(tong_cl_da_duyet),
        "tong_sp_tien_do_da_duyet": float(tong_td_da_duyet),
        "tong_sp_chat_luong_tam_tinh": float(tong_cl_tam_tinh),
        "tong_sp_tien_do_tam_tinh": float(tong_td_tam_tinh),
        "so_kekhai_da_duyet": so_da_duyet,
        "so_kekhai_cho_duyet": so_cho_duyet,
        "so_kekhai_nhap": so_nhap,
    })


@router.post(
    "",
    summary="Tạo kê khai V2",
    status_code=status.HTTP_201_CREATED,
    response_model=DataResponse[KeKhaiV2Response],
)
async def create_kekhai_v2(
    payload: KeKhaiV2Create,
    db: DatabaseDep,
    current_user: ActiveUserDep,
) -> dict:
    """Tạo bản kê khai V2 mới."""
    if is_qldv(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"success": False, "error": {"code": "PERM_QLDV", "message": "QLDV không có quyền kê khai"}},
        )
    _reject_leader_v2(current_user)

    # Validate danh mục PL3
    dm = await _load_pl3_danh_muc(db, payload.danh_muc_sp_id)

    # LOCKED 12: 1 tháng = 1 version
    await _check_no_v1_in_month(db, current_user.id, payload.thang, payload.nam)

    # Người phê duyệt
    await _validate_phe_duyet(db, payload.nguoi_phe_duyet_id)

    # Tính SP gốc quy đổi + SP đạt CL/TĐ (theo tự đánh giá CC)
    so_sp_goc = calculate_so_sp_goc_quy_doi_v2(payload.so_luong, dm.he_so_quy_doi)
    so_sp_cl = calculate_sp_dat_v2(
        payload.so_luong, dm.he_so_quy_doi, payload.tu_danh_gia_chat_luong
    )
    so_sp_td = calculate_sp_dat_v2(
        payload.so_luong, dm.he_so_quy_doi, payload.tu_danh_gia_tien_do
    )

    kk = KeKhaiCongViec(
        cong_chuc_id=current_user.id,
        don_vi_id_snapshot=current_user.don_vi_id,
        thang=payload.thang,
        nam=payload.nam,
        ngay_thuc_hien=payload.ngay_thuc_hien,
        danh_muc_sp_id=dm.id,
        cap_do_id=None,  # V2 không dùng C1-C5
        so_luong=payload.so_luong,
        he_so_thuc_te=None,  # LOCKED 14: không cho override
        nguoi_phe_duyet_id=payload.nguoi_phe_duyet_id,
        mo_ta_cong_viec=payload.mo_ta_cong_viec,
        is_doi_moi_sang_tao=payload.is_doi_moi_sang_tao,
        ngay_deadline=payload.ngay_deadline,
        ngay_hoan_thanh=payload.ngay_hoan_thanh,
        tu_danh_gia_chat_luong=payload.tu_danh_gia_chat_luong,
        tu_danh_gia_tien_do=payload.tu_danh_gia_tien_do,
        ghi_chu_tu_danh_gia=payload.ghi_chu_tu_danh_gia,
        ghi_chu_tu_dg_chat_luong=payload.ghi_chu_tu_dg_chat_luong,
        ghi_chu_tu_dg_tien_do=payload.ghi_chu_tu_dg_tien_do,
        trang_thai=TrangThaiKeKhai.NHAP,
        so_sp_goc_quy_doi=so_sp_goc,
        so_sp_chat_luong=so_sp_cl,
        so_sp_tien_do=so_sp_td,
        # Snapshot V2 (LOCKED 13 — immutable)
        version_kekhai=VERSION_V2,
        he_so_quy_doi_snapshot=dm.he_so_quy_doi,
        nhom_pl3_snapshot=dm.nhom_pl3,
        linh_vuc_snapshot=dm.linh_vuc,
    )
    db.add(kk)
    await db.flush()
    await db.refresh(kk, attribute_names=["danh_muc_sp", "nguoi_phe_duyet"])
    await db.commit()

    return success_response(
        data=_kk_v2_to_response(kk),
        message="Tạo kê khai V2 thành công",
    )


@router.post(
    "/nhieu-ngay",
    summary="Tạo kê khai V2 cho nhiều ngày",
    status_code=status.HTTP_201_CREATED,
    response_model=DataResponse[KeKhaiV2NhieuNgayResponse],
)
async def create_kekhai_v2_multi_day(
    payload: KeKhaiV2NhieuNgayCreate,
    db: DatabaseDep,
    current_user: ActiveUserDep,
) -> dict:
    """Tạo nhiều bản kê khai V2 cùng công việc cho nhiều ngày."""
    if is_qldv(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"success": False, "error": {"code": "PERM_QLDV", "message": "QLDV không có quyền kê khai"}},
        )
    _reject_leader_v2(current_user)

    dm = await _load_pl3_danh_muc(db, payload.danh_muc_sp_id)

    first_date = payload.ngay_thuc_hien_list[0]
    thang = first_date.month
    nam = first_date.year

    await _check_no_v1_in_month(db, current_user.id, thang, nam)
    await _validate_phe_duyet(db, payload.nguoi_phe_duyet_id)

    so_sp_goc = calculate_so_sp_goc_quy_doi_v2(payload.so_luong, dm.he_so_quy_doi)
    so_sp_cl = calculate_sp_dat_v2(
        payload.so_luong, dm.he_so_quy_doi, payload.tu_danh_gia_chat_luong
    )
    so_sp_td = calculate_sp_dat_v2(
        payload.so_luong, dm.he_so_quy_doi, payload.tu_danh_gia_tien_do
    )

    created = []
    for ngay in payload.ngay_thuc_hien_list:
        kk = KeKhaiCongViec(
            cong_chuc_id=current_user.id,
            don_vi_id_snapshot=current_user.don_vi_id,
            thang=thang,
            nam=nam,
            ngay_thuc_hien=ngay,
            danh_muc_sp_id=dm.id,
            cap_do_id=None,
            so_luong=payload.so_luong,
            he_so_thuc_te=None,
            nguoi_phe_duyet_id=payload.nguoi_phe_duyet_id,
            mo_ta_cong_viec=payload.mo_ta_cong_viec,
            is_doi_moi_sang_tao=payload.is_doi_moi_sang_tao,
            tu_danh_gia_chat_luong=payload.tu_danh_gia_chat_luong,
            tu_danh_gia_tien_do=payload.tu_danh_gia_tien_do,
            ghi_chu_tu_danh_gia=payload.ghi_chu_tu_danh_gia,
            ghi_chu_tu_dg_chat_luong=payload.ghi_chu_tu_dg_chat_luong,
            ghi_chu_tu_dg_tien_do=payload.ghi_chu_tu_dg_tien_do,
            trang_thai=TrangThaiKeKhai.NHAP,
            so_sp_goc_quy_doi=so_sp_goc,
            so_sp_chat_luong=so_sp_cl,
            so_sp_tien_do=so_sp_td,
            version_kekhai=VERSION_V2,
            he_so_quy_doi_snapshot=dm.he_so_quy_doi,
            nhom_pl3_snapshot=dm.nhom_pl3,
            linh_vuc_snapshot=dm.linh_vuc,
        )
        db.add(kk)
        created.append(kk)

    await db.flush()
    ids = [k.id for k in created]
    await db.commit()

    return success_response(
        data={
            "total_created": len(ids),
            "ke_khai_ids": ids,
            "thang": thang,
            "nam": nam,
        },
        message=f"Đã tạo {len(ids)} bản kê khai V2 cho tháng {thang}/{nam}",
    )


# =============================================================================
# FAVORITES + RECENT (30/04/2026) — chỉ V2_PL3
# Đặt TRƯỚC GET /{ke_khai_id} để FastAPI match path cụ thể trước path biến.
# =============================================================================


def _dm_to_brief(dm: DanhMucSpCongViec) -> dict:
    """Brief response của 1 mục PL3 (giống DanhMucPL3BriefResponse)."""
    return {
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
    }


@router.get(
    "/favorites",
    summary="Danh sách công việc yêu thích của bản thân",
    response_model=DataResponse[list[CongViecYeuThichResponse]],
)
async def list_my_favorites(
    db: DatabaseDep,
    current_user: ActiveUserDep,
) -> dict:
    """Trả về list favorites của user, mới nhất trước.

    LĐ và HĐ 111 không dùng V2 → trả [] để FE đơn giản hoá.
    Tự động loại bỏ favorites trỏ đến danh mục đã soft-delete /
    không còn nguon_du_lieu='PL3' / inactive.
    """
    if current_user.is_lanh_dao or current_user.is_hd_111:
        return success_response(data=[])

    stmt = (
        select(CongViecYeuThich)
        .options(selectinload(CongViecYeuThich.danh_muc_sp))
        .join(DanhMucSpCongViec, DanhMucSpCongViec.id == CongViecYeuThich.danh_muc_sp_id)
        .where(CongViecYeuThich.cong_chuc_id == current_user.id)
        .where(DanhMucSpCongViec.is_deleted == False)  # noqa: E712
        .where(DanhMucSpCongViec.is_active == True)  # noqa: E712
        .where(DanhMucSpCongViec.nguon_du_lieu == "PL3")
        .order_by(CongViecYeuThich.created_at.desc())
    )
    rows = (await db.execute(stmt)).scalars().all()

    return success_response(
        data=[
            {
                "id": fav.id,
                "danh_muc_sp_id": fav.danh_muc_sp_id,
                "danh_muc_sp": _dm_to_brief(fav.danh_muc_sp),
                "created_at": fav.created_at,
            }
            for fav in rows
        ]
    )


@router.post(
    "/favorites",
    summary="Đánh dấu 1 mục PL3 là yêu thích (idempotent)",
    status_code=status.HTTP_201_CREATED,
    response_model=DataResponse[CongViecYeuThichResponse],
)
async def add_favorite(
    payload: CongViecYeuThichCreate,
    db: DatabaseDep,
    current_user: ActiveUserDep,
) -> dict:
    """Thêm 1 favorite. Idempotent: nếu đã tồn tại trả về bản ghi cũ."""
    _reject_leader_v2(current_user)

    # Validate danh mục là PL3, active, còn sống
    dm = await _load_pl3_danh_muc(db, payload.danh_muc_sp_id)

    # Idempotent: tìm bản ghi cũ trước
    existing_stmt = (
        select(CongViecYeuThich)
        .where(CongViecYeuThich.cong_chuc_id == current_user.id)
        .where(CongViecYeuThich.danh_muc_sp_id == dm.id)
    )
    fav = (await db.execute(existing_stmt)).scalar_one_or_none()

    if fav is None:
        fav = CongViecYeuThich(
            cong_chuc_id=current_user.id,
            danh_muc_sp_id=dm.id,
        )
        db.add(fav)
        await db.flush()
        await db.commit()

    return success_response(
        data={
            "id": fav.id,
            "danh_muc_sp_id": fav.danh_muc_sp_id,
            "danh_muc_sp": _dm_to_brief(dm),
            "created_at": fav.created_at,
        },
        message="Đã thêm vào danh sách yêu thích",
    )


@router.delete(
    "/favorites/{danh_muc_sp_id}",
    summary="Bỏ yêu thích 1 mục PL3",
    response_model=DataResponse[dict],
)
async def remove_favorite(
    danh_muc_sp_id: UUID,
    db: DatabaseDep,
    current_user: ActiveUserDep,
) -> dict:
    """Xoá favorite (idempotent: nếu chưa có thì trả OK rỗng)."""
    stmt = (
        select(CongViecYeuThich)
        .where(CongViecYeuThich.cong_chuc_id == current_user.id)
        .where(CongViecYeuThich.danh_muc_sp_id == danh_muc_sp_id)
    )
    fav = (await db.execute(stmt)).scalar_one_or_none()

    if fav is not None:
        await db.delete(fav)
        await db.commit()

    return success_response(
        data={"danh_muc_sp_id": danh_muc_sp_id, "removed": fav is not None},
        message="Đã bỏ yêu thích" if fav else "Mục này không có trong danh sách yêu thích",
    )


@router.get(
    "/recent",
    summary="Danh sách công việc đã dùng gần đây (look-back tối đa 3 tháng)",
    response_model=DataResponse[list[RecentDanhMucResponse]],
)
async def list_recent_danh_muc(
    db: DatabaseDep,
    current_user: ActiveUserDep,
    thang: int = Query(..., ge=1, le=12, description="Tháng đang kê khai (FE truyền)"),
    nam: int = Query(..., ge=2025),
) -> dict:
    """Trả về các mục PL3 user đã dùng trong 3 tháng gần nhất CÓ DỮ LIỆU
    trước (thang, nam).

    Logic look-back:
    - Bắt đầu từ tháng (thang-1, nam), lùi dần.
    - Bỏ qua tháng không có data (vd: nghỉ thai sản).
    - Tối đa 3 tháng có data.

    LĐ / HĐ 111 / QLDV → trả [] (V2 không áp dụng).
    """
    if current_user.is_lanh_dao or current_user.is_hd_111 or is_qldv(current_user):
        return success_response(data=[])

    # Tìm tối đa 3 (thang, nam) có ke_khai_v2 trước (thang, nam) hiện tại.
    cur_yyyymm = nam * 100 + thang
    stmt_months = (
        select(KeKhaiCongViec.thang, KeKhaiCongViec.nam)
        .where(KeKhaiCongViec.cong_chuc_id == current_user.id)
        .where(KeKhaiCongViec.version_kekhai == VERSION_V2)
        .where(KeKhaiCongViec.is_deleted == False)  # noqa: E712
        .where((KeKhaiCongViec.nam * 100 + KeKhaiCongViec.thang) < cur_yyyymm)
        .group_by(KeKhaiCongViec.thang, KeKhaiCongViec.nam)
        .order_by(KeKhaiCongViec.nam.desc(), KeKhaiCongViec.thang.desc())
        .limit(3)
    )
    months_rows = (await db.execute(stmt_months)).all()
    if not months_rows:
        return success_response(data=[])

    yyyymm_set = [n * 100 + t for (t, n) in months_rows]

    yyyymm_expr = KeKhaiCongViec.nam * 100 + KeKhaiCongViec.thang
    stmt_recent = (
        select(
            KeKhaiCongViec.danh_muc_sp_id,
            func.max(yyyymm_expr).label("last_yyyymm"),
            func.count(KeKhaiCongViec.id).label("used_count"),
        )
        .where(KeKhaiCongViec.cong_chuc_id == current_user.id)
        .where(KeKhaiCongViec.version_kekhai == VERSION_V2)
        .where(KeKhaiCongViec.is_deleted == False)  # noqa: E712
        .where(yyyymm_expr.in_(yyyymm_set))
        .where(KeKhaiCongViec.danh_muc_sp_id.is_not(None))
        .group_by(KeKhaiCongViec.danh_muc_sp_id)
        .order_by(func.max(yyyymm_expr).desc(), func.count(KeKhaiCongViec.id).desc())
    )
    rows = (await db.execute(stmt_recent)).all()
    if not rows:
        return success_response(data=[])

    dm_ids = [r[0] for r in rows]
    dm_stmt = (
        select(DanhMucSpCongViec)
        .where(DanhMucSpCongViec.id.in_(dm_ids))
        .where(DanhMucSpCongViec.is_deleted == False)  # noqa: E712
        .where(DanhMucSpCongViec.is_active == True)  # noqa: E712
        .where(DanhMucSpCongViec.nguon_du_lieu == "PL3")
    )
    dms = (await db.execute(dm_stmt)).scalars().all()
    dm_map = {dm.id: dm for dm in dms}

    items = []
    for dm_id, last_yyyymm, used_count in rows:
        dm = dm_map.get(dm_id)
        if dm is None:
            continue
        last_nam = int(last_yyyymm) // 100
        last_thang = int(last_yyyymm) % 100
        items.append({
            "danh_muc_sp_id": dm_id,
            "danh_muc_sp": _dm_to_brief(dm),
            "last_used_thang": last_thang,
            "last_used_nam": last_nam,
            "used_count_3m": int(used_count),
        })

    return success_response(data=items)


@router.get(
    "/{ke_khai_id}",
    summary="Chi tiết kê khai V2",
    response_model=DataResponse[KeKhaiV2Response],
)
async def get_kekhai_v2_detail(
    ke_khai_id: UUID,
    db: DatabaseDep,
    current_user: ActiveUserDep,
) -> dict:
    """Chi tiết 1 bản kê khai V2 (chỉ chủ sở hữu hoặc người phê duyệt xem được)."""
    stmt = (
        select(KeKhaiCongViec)
        .options(
            selectinload(KeKhaiCongViec.danh_muc_sp),
            selectinload(KeKhaiCongViec.nguoi_phe_duyet),
        )
        .where(KeKhaiCongViec.id == ke_khai_id)
        .where(KeKhaiCongViec.is_deleted == False)  # noqa: E712
    )
    res = await db.execute(stmt)
    kk = res.scalar_one_or_none()
    if not kk:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"success": False, "error": {"code": "NOT_FOUND", "message": "Không tìm thấy"}},
        )
    _check_v2_or_400(kk)

    # Chủ sở hữu hoặc người phê duyệt mới xem được
    if kk.cong_chuc_id != current_user.id and kk.nguoi_phe_duyet_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"success": False, "error": {"code": "FORBIDDEN", "message": "Không có quyền xem"}},
        )

    return success_response(data=_kk_v2_to_response(kk))


@router.put(
    "/{ke_khai_id}",
    summary="Sửa kê khai V2 (NHAP/TU_CHOI)",
    response_model=DataResponse[KeKhaiV2Response],
)
async def update_kekhai_v2(
    ke_khai_id: UUID,
    payload: KeKhaiV2Update,
    db: DatabaseDep,
    current_user: ActiveUserDep,
) -> dict:
    """Sửa bản kê khai V2 ở trạng thái NHAP hoặc TU_CHOI."""
    stmt = (
        select(KeKhaiCongViec)
        .options(
            selectinload(KeKhaiCongViec.danh_muc_sp),
            selectinload(KeKhaiCongViec.nguoi_phe_duyet),
        )
        .where(KeKhaiCongViec.id == ke_khai_id)
        .where(KeKhaiCongViec.is_deleted == False)  # noqa: E712
    )
    kk = (await db.execute(stmt)).scalar_one_or_none()
    if not kk:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"success": False, "error": {"code": "NOT_FOUND", "message": "Không tìm thấy"}},
        )
    _check_v2_or_400(kk)
    _check_owner_or_403(kk, current_user)
    _check_editable_or_400(kk)

    # Nếu đổi danh mục → re-validate + re-snapshot
    new_dm = None
    if payload.danh_muc_sp_id is not None and payload.danh_muc_sp_id != kk.danh_muc_sp_id:
        new_dm = await _load_pl3_danh_muc(db, payload.danh_muc_sp_id)
        kk.danh_muc_sp_id = new_dm.id
        kk.he_so_quy_doi_snapshot = new_dm.he_so_quy_doi
        kk.nhom_pl3_snapshot = new_dm.nhom_pl3
        kk.linh_vuc_snapshot = new_dm.linh_vuc

    # Sửa các field
    update_data = payload.model_dump(exclude_unset=True, exclude={"danh_muc_sp_id"})
    for field, value in update_data.items():
        setattr(kk, field, value)

    # Re-validate phe duyet
    if payload.nguoi_phe_duyet_id is not None:
        await _validate_phe_duyet(db, payload.nguoi_phe_duyet_id)

    # Tính lại so_sp_goc_quy_doi + SP CL/TĐ nếu đổi so_luong / danh mục / tự đánh giá
    needs_recalc = (
        payload.so_luong is not None
        or new_dm is not None
        or payload.tu_danh_gia_chat_luong is not None
        or payload.tu_danh_gia_tien_do is not None
    )
    if needs_recalc:
        kk.so_sp_goc_quy_doi = calculate_so_sp_goc_quy_doi_v2(
            kk.so_luong, kk.he_so_quy_doi_snapshot
        )
        kk.so_sp_chat_luong = calculate_sp_dat_v2(
            kk.so_luong, kk.he_so_quy_doi_snapshot, kk.tu_danh_gia_chat_luong or 0
        )
        kk.so_sp_tien_do = calculate_sp_dat_v2(
            kk.so_luong, kk.he_so_quy_doi_snapshot, kk.tu_danh_gia_tien_do or 0
        )

    # Reset trạng thái về NHAP nếu đang TU_CHOI (để CC có thể gửi lại)
    if kk.trang_thai == TrangThaiKeKhai.TU_CHOI:
        kk.trang_thai = TrangThaiKeKhai.NHAP

    await db.commit()
    await db.refresh(kk, attribute_names=["danh_muc_sp", "nguoi_phe_duyet"])
    return success_response(data=_kk_v2_to_response(kk), message="Cập nhật thành công")


@router.delete(
    "/{ke_khai_id}",
    summary="Xoá kê khai V2 (soft delete, NHAP/TU_CHOI)",
    response_model=DataResponse[dict],
)
async def delete_kekhai_v2(
    ke_khai_id: UUID,
    db: DatabaseDep,
    current_user: ActiveUserDep,
) -> dict:
    """Soft-delete bản kê khai V2 ở trạng thái NHAP hoặc TU_CHOI."""
    stmt = (
        select(KeKhaiCongViec)
        .where(KeKhaiCongViec.id == ke_khai_id)
        .where(KeKhaiCongViec.is_deleted == False)  # noqa: E712
    )
    kk = (await db.execute(stmt)).scalar_one_or_none()
    if not kk:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"success": False, "error": {"code": "NOT_FOUND", "message": "Không tìm thấy"}},
        )
    _check_v2_or_400(kk)
    _check_owner_or_403(kk, current_user)
    _check_editable_or_400(kk)

    kk.is_deleted = True
    await db.commit()

    return success_response(data={"id": ke_khai_id}, message="Đã xoá")
