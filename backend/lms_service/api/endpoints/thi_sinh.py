"""
lms_service/api/endpoints/thi_sinh.py
======================================
API endpoints thi sinh DGNL: giao, danh sach, xoa, bat dau, nop bai, ket qua, export.

8 endpoints:
  POST   /ky-thi/{id}/thi-sinh                  Giao thi sinh (batch)
  GET    /ky-thi/{id}/thi-sinh                  Danh sach thi sinh + ket qua
  DELETE /ky-thi/{id}/thi-sinh/{cong_chuc_id}   Xoa thi sinh
  POST   /ky-thi/{id}/bat-dau                   Bat dau thi -> random de
  POST   /ky-thi/{id}/nop-bai                   Nop bai -> cham diem
  GET    /ky-thi/{id}/ket-qua                   Ket qua ca nhan
  GET    /ky-thi/{id}/ket-qua/{cong_chuc_id}    Ket qua CBCC cu the
  GET    /ky-thi/{id}/export                     Export Excel
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from lms_service.dependencies import get_db, get_current_user, require_platform_role
from lms_service.schemas.thi_sinh import (
    ThiSinhBatchCreate, ThiSinhResponse,
    NopBaiRequest, KetQuaResponse,
    LuuNhapRequest,
)
from lms_service.services.thi_sinh_service import ThiSinhService
from shared.auth import TokenPayload

router = APIRouter(prefix="/ky-thi", tags=["ĐGNL - Thí sinh & Làm thi"])


# ================================================================
# GIAO THI SINH
# ================================================================

@router.post("/{ky_thi_id}/thi-sinh", status_code=201)
async def giao_thi_sinh(
    ky_thi_id: UUID,
    data: ThiSinhBatchCreate,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(require_platform_role("QT_DAO_TAO")),
):
    """Giao thi sinh (batch). Theo danh sach hoac theo don vi."""
    service = ThiSinhService(db)
    result = await service.giao_thi_sinh(ky_thi_id, data, user)
    return {
        "success": True,
        "data": result,
        "message": f"Giao thí sinh thành công: {result['thanh_cong']}/{result['tong']}",
    }


@router.get("/{ky_thi_id}/thi-sinh")
async def danh_sach_thi_sinh(
    ky_thi_id: UUID,
    trang_thai: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    """Danh sach thi sinh + ket qua. QT xem tat ca, LD xem don vi minh."""
    service = ThiSinhService(db)
    if not service._is_manager(user) and not service._is_lanh_dao(user):
        raise HTTPException(
            status_code=403,
            detail={"success": False, "error": {"code": "PERM_001", "message": "Yêu cầu vai trò QT_DAO_TAO hoặc Lãnh đạo"}},
        )
    result = await service.danh_sach_thi_sinh(ky_thi_id, user, trang_thai=trang_thai, page=page, page_size=page_size)
    return {
        "success": True,
        "data": [ThiSinhResponse(**item).model_dump(mode="json") for item in result["items"]],
        "pagination": result["pagination"],
    }


@router.delete("/{ky_thi_id}/thi-sinh/{cong_chuc_id}")
async def xoa_thi_sinh(
    ky_thi_id: UUID,
    cong_chuc_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(require_platform_role("QT_DAO_TAO")),
):
    """Xoa thi sinh — chi khi chua thi."""
    service = ThiSinhService(db)
    await service.xoa_thi_sinh(ky_thi_id, cong_chuc_id, user)
    return {"success": True, "message": "Xóa thí sinh thành công"}


# ================================================================
# LAM THI
# ================================================================

@router.post("/{ky_thi_id}/bat-dau")
async def bat_dau_thi(
    ky_thi_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    """Bat dau thi — random de thi cho thi sinh. Tra ve danh sach cau hoi (khong co dap an)."""
    service = ThiSinhService(db)
    result = await service.bat_dau_thi(ky_thi_id, user)
    return {"success": True, "data": result}


@router.post("/{ky_thi_id}/nop-bai")
async def nop_bai(
    ky_thi_id: UUID,
    data: NopBaiRequest,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    """Nop bai thi — cham diem tu dong."""
    service = ThiSinhService(db)
    result = await service.nop_bai(ky_thi_id, data, user)
    return {
        "success": True,
        "data": result.model_dump(mode="json"),
        "message": f"Nộp bài thành công — {result.ket_qua['xep_loai']}",
    }


@router.post("/{ky_thi_id}/luu-nhap")
async def luu_nhap(
    ky_thi_id: UUID,
    data: LuuNhapRequest,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    """Luu bai lam nhap (auto-save). Frontend goi moi 30s."""
    service = ThiSinhService(db)
    result = await service.luu_nhap(
        ky_thi_id, data.cau_tra_loi, data.so_lan_vi_pham, user
    )
    return {"success": True, "data": result}


# ================================================================
# KET QUA
# ================================================================

@router.get("/{ky_thi_id}/ket-qua")
async def ket_qua_ca_nhan(
    ky_thi_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    """Xem ket qua ca nhan."""
    service = ThiSinhService(db)
    result = await service.ket_qua_ca_nhan(ky_thi_id, user)
    return {"success": True, "data": result.model_dump(mode="json")}


@router.get("/{ky_thi_id}/ket-qua/{cong_chuc_id}")
async def ket_qua_cbcc(
    ky_thi_id: UUID,
    cong_chuc_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    """Xem ket qua CBCC cu the — QT_DAO_TAO hoac Lanh dao."""
    service = ThiSinhService(db)
    if not service._is_manager(user) and not service._is_lanh_dao(user):
        raise HTTPException(
            status_code=403,
            detail={"success": False, "error": {"code": "PERM_001", "message": "Yêu cầu vai trò QT_DAO_TAO hoặc Lãnh đạo"}},
        )
    result = await service.ket_qua_cbcc(ky_thi_id, cong_chuc_id, user)
    return {"success": True, "data": result.model_dump(mode="json")}


@router.get("/{ky_thi_id}/thi-sinh/{cong_chuc_id}/ket-qua/{lan}")
async def ket_qua_lan_thi(
    ky_thi_id: UUID,
    cong_chuc_id: UUID,
    lan: int,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    """Xem chi tiet bai lam cua 1 lan thi cu the — QT_DAO_TAO hoac Lanh dao.

    `lan` la so thu tu lan thi (1, 2, 3, ...). Lan moi nhat (= lan_thi_hien_tai)
    duoc tra ve giong nhu /ket-qua/{cong_chuc_id}. Lan cu hon duoc lay tu
    lich_su_thi JSONB.
    """
    service = ThiSinhService(db)
    if not service._is_manager(user) and not service._is_lanh_dao(user):
        raise HTTPException(
            status_code=403,
            detail={"success": False, "error": {"code": "PERM_001", "message": "Yêu cầu vai trò QT_DAO_TAO hoặc Lãnh đạo"}},
        )
    result = await service.ket_qua_lan_thi(ky_thi_id, cong_chuc_id, lan, user)
    return {"success": True, "data": result.model_dump(mode="json")}


# ================================================================
# EXPORT EXCEL
# ================================================================

@router.get("/{ky_thi_id}/export")
async def export_ket_qua(
    ky_thi_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    """Export ket qua ky thi ra file Excel (.xlsx). QT xem tat ca, LD xem don vi minh."""
    service = ThiSinhService(db)
    if not service._is_manager(user) and not service._is_lanh_dao(user):
        raise HTTPException(
            status_code=403,
            detail={"success": False, "error": {"code": "PERM_001", "message": "Yêu cầu vai trò QT_DAO_TAO hoặc Lãnh đạo"}},
        )
    xlsx_bytes = await service.export_excel(ky_thi_id, user)
    return Response(
        content=xlsx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=ket_qua_ky_thi_{ky_thi_id}.xlsx"},
    )
