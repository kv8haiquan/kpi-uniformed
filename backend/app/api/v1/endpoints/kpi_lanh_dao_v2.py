"""
app/api/v1/endpoints/kpi_lanh_dao_v2.py
=======================================
Endpoints mới cho KPI lãnh đạo công thức MỚI (từ tháng 4/2026).

Spec: docs/Ke_khai_LĐ/Phuong phap tinh KPI cho lanh dao.docx

KHÔNG SỬA endpoint cũ — giữ để dữ liệu tháng < 4/2026 vẫn dùng được.

Endpoints:
- GET /api/v1/kpi-lanh-dao-v2/me?thang=&nam=         # Tự xem KPI mình
- GET /api/v1/kpi-lanh-dao-v2/{cong_chuc_id}?thang=&nam=  # CCT/Admin xem ai đó
- GET /api/v1/kpi-lanh-dao-v2/feature-flag           # Trả từ tháng nào áp dụng

Phiên bản: 1.0 (05/05/2026)
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import ActiveUserDep, DatabaseDep, require_roles
from app.core.kpi_lanh_dao_v2 import (
    KPI_LANH_DAO_V2_FROM_NAM,
    KPI_LANH_DAO_V2_FROM_THANG,
    calc_kpi_lanh_dao_v2,
    is_kpi_lanh_dao_v2_active,
)
from app.models.user_org import CapBacVaiTro, CongChuc
from app.schemas.common import success_response


router = APIRouter()


# =============================================================================
# FEATURE FLAG
# =============================================================================

@router.get(
    "/feature-flag",
    summary="Cấu hình áp dụng công thức KPI lãnh đạo mới",
)
async def feature_flag():
    return success_response(
        data={
            "tu_thang": KPI_LANH_DAO_V2_FROM_THANG,
            "tu_nam": KPI_LANH_DAO_V2_FROM_NAM,
            "mo_ta": (
                f"Áp dụng công thức KPI lãnh đạo mới từ tháng "
                f"{KPI_LANH_DAO_V2_FROM_THANG}/{KPI_LANH_DAO_V2_FROM_NAM}"
            ),
        }
    )


# =============================================================================
# GET KPI MÌNH
# =============================================================================

LANH_DAO_CAP_BAC = {
    CapBacVaiTro.PHO_DON_VI,
    CapBacVaiTro.TRUONG_DON_VI,
    CapBacVaiTro.PHO_CHI_CUC_TRUONG,
    CapBacVaiTro.CHI_CUC_TRUONG,
}


def _check_thang_nam(thang: int, nam: int) -> None:
    if thang < 1 or thang > 12:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "error": {"code": "VAL_THANG", "message": "Tháng phải 1-12"},
            },
        )
    if nam < 2025 or nam > 2099:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "error": {"code": "VAL_NAM", "message": "Năm không hợp lệ"},
            },
        )
    if not is_kpi_lanh_dao_v2_active(thang, nam):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "error": {
                    "code": "KPI_V2_NOT_ACTIVE",
                    "message": (
                        f"Công thức KPI v2 chỉ áp dụng từ "
                        f"{KPI_LANH_DAO_V2_FROM_THANG}/{KPI_LANH_DAO_V2_FROM_NAM}. "
                        f"Tháng {thang}/{nam} dùng công thức cũ."
                    ),
                },
            },
        )


@router.get(
    "/me",
    summary="Tự xem KPI lãnh đạo của mình (công thức mới)",
)
async def get_kpi_v2_cua_toi(
    db: DatabaseDep,
    current_user: ActiveUserDep,
    thang: int = Query(..., ge=1, le=12),
    nam: int = Query(..., ge=2025, le=2099),
):
    _check_thang_nam(thang, nam)

    if not current_user.vai_tro or current_user.vai_tro.cap_bac not in LANH_DAO_CAP_BAC:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "error": {
                    "code": "KPI_V2_NOT_LD",
                    "message": "Chỉ lãnh đạo (PDV/TDV/PCCT/CCT) có KPI v2",
                },
            },
        )

    data = await calc_kpi_lanh_dao_v2(db, current_user.id, thang, nam)
    return success_response(data=data)


# =============================================================================
# GET KPI CỦA NGƯỜI KHÁC (CCT + ADMIN)
# =============================================================================

@router.get(
    "/{cong_chuc_id}",
    summary="Xem KPI lãnh đạo của người khác (CCT + Admin)",
)
async def get_kpi_v2_cua_nguoi_khac(
    cong_chuc_id: UUID,
    db: DatabaseDep,
    thang: int = Query(..., ge=1, le=12),
    nam: int = Query(..., ge=2025, le=2099),
    current_user: CongChuc = Depends(require_roles("CCT")),
):
    _check_thang_nam(thang, nam)

    try:
        data = await calc_kpi_lanh_dao_v2(db, cong_chuc_id, thang, nam)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": {"code": "KPI_V2_NOT_FOUND", "message": str(e)},
            },
        )
    return success_response(data=data)
