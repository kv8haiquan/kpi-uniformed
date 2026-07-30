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
  POST   /ky-thi/{id}/xac-nhan                  Xac nhan ca thi (chot ket qua)
  GET    /ky-thi/{id}/ket-qua                   Ket qua ca nhan
  GET    /ky-thi/{id}/ket-qua/{cong_chuc_id}    Ket qua CBCC cu the
  GET    /ky-thi/{id}/export                     Export Excel
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, Header, HTTPException, Query, Response, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from lms_service.dependencies import get_db, get_current_user, require_platform_role
from lms_service.schemas.thi_sinh import (
    ThiSinhBatchCreate, ThiSinhResponse,
    NopBaiRequest, KetQuaResponse,
    LuuNhapRequest, GiamSatResponse,
    ViPhamCreate, ViPhamLyDoUpdate,
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
    user: TokenPayload = Depends(require_platform_role("QT_DAO_TAO")),
):
    """Danh sach thi sinh + ket qua. Chi admin (QT_DAO_TAO/SUPER_ADMIN)."""
    service = ThiSinhService(db)
    result = await service.danh_sach_thi_sinh(ky_thi_id, user, trang_thai=trang_thai, page=page, page_size=page_size)
    return {
        "success": True,
        "data": [ThiSinhResponse(**item).model_dump(mode="json") for item in result["items"]],
        "pagination": result["pagination"],
    }


@router.get("/{ky_thi_id}/thi-sinh/import/mau")
async def download_mau_import_thi_sinh(
    ky_thi_id: UUID,
    user: TokenPayload = Depends(require_platform_role("QT_DAO_TAO")),
):
    """Tai file Excel mau import thi sinh (chi 1 cot ma_cc)."""
    xlsx_bytes = ThiSinhService.generate_template_import_thi_sinh()
    return Response(
        content=xlsx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=mau_import_thi_sinh.xlsx"},
    )


@router.post("/{ky_thi_id}/thi-sinh/import-excel", status_code=201)
async def import_thi_sinh_excel(
    ky_thi_id: UUID,
    vi_tri_id: UUID = Query(..., description="Vị trí việc làm áp dụng chung cho cả file"),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(require_platform_role("QT_DAO_TAO")),
):
    """Import thi sinh tu file Excel (cot ma_cc). Loi tung dong tra ve loi_chi_tiet."""
    content = await file.read()
    service = ThiSinhService(db)
    result = await service.import_thi_sinh_excel(ky_thi_id, vi_tri_id, content, user)
    return {
        "success": True,
        "data": result,
        "message": f"Import hoàn tất: {result['thanh_cong']}/{result['tong']} thí sinh",
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
    user_agent: Optional[str] = Header(None),
):
    """Bat dau thi — random de thi cho thi sinh. Tra ve danh sach cau hoi (khong co dap an).

    Sinh phien_token moi (1 phien/tai khoan): thiet bi nay so huu phien thi.
    """
    service = ThiSinhService(db)
    result = await service.bat_dau_thi(ky_thi_id, user, thiet_bi=user_agent)
    return {"success": True, "data": result}


@router.post("/{ky_thi_id}/nop-bai")
async def nop_bai(
    ky_thi_id: UUID,
    data: NopBaiRequest,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
    x_phien_thi: Optional[str] = Header(None, alias="X-Phien-Thi"),
):
    """Nop bai thi — cham diem tu dong. Yeu cau token phien dang so huu."""
    service = ThiSinhService(db)
    result = await service.nop_bai(ky_thi_id, data, user, phien_token=x_phien_thi)
    return {
        "success": True,
        "data": result.model_dump(mode="json"),
        "message": f"Nộp bài thành công — {result.ket_qua['xep_loai']}",
    }


@router.post("/{ky_thi_id}/xac-nhan")
async def xac_nhan_ca_thi(
    ky_thi_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    """Xac nhan ca thi — chot ket qua, khong duoc thi lai du con luot. Idempotent."""
    service = ThiSinhService(db)
    result = await service.xac_nhan_ca_thi(ky_thi_id, user)
    return {"success": True, "data": result, "message": "Xác nhận ca thi thành công"}


@router.post("/{ky_thi_id}/luu-nhap")
async def luu_nhap(
    ky_thi_id: UUID,
    data: LuuNhapRequest,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
    x_phien_thi: Optional[str] = Header(None, alias="X-Phien-Thi"),
):
    """Luu bai lam nhap (auto-save). Frontend goi moi 30s. Cung la heartbeat giam sat."""
    service = ThiSinhService(db)
    result = await service.luu_nhap(
        ky_thi_id, data.cau_tra_loi, data.so_lan_vi_pham, user, phien_token=x_phien_thi
    )
    return {"success": True, "data": result}


@router.post("/{ky_thi_id}/vi-pham", status_code=201)
async def ghi_vi_pham(
    ky_thi_id: UUID,
    data: ViPhamCreate,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
    x_phien_thi: Optional[str] = Header(None, alias="X-Phien-Thi"),
):
    """Ghi nhan 1 lan vi pham ngay khi xay ra (kem thoi gian). Tra ve id de nhap ly do."""
    service = ThiSinhService(db)
    result = await service.ghi_vi_pham(ky_thi_id, data.loai_vi_pham, user, phien_token=x_phien_thi)
    return {"success": True, "data": result}


@router.patch("/{ky_thi_id}/vi-pham/{vp_id}/ly-do")
async def cap_nhat_ly_do_vi_pham(
    ky_thi_id: UUID,
    vp_id: UUID,
    data: ViPhamLyDoUpdate,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    """Thi sinh nhap ly do giai trinh cho vi pham cua chinh minh (khong bat buoc)."""
    service = ThiSinhService(db)
    await service.cap_nhat_ly_do_vi_pham(ky_thi_id, vp_id, data.ly_do, user)
    return {"success": True, "message": "Đã lưu lý do giải trình"}


@router.get("/{ky_thi_id}/thi-sinh/{cong_chuc_id}/vi-pham")
async def danh_sach_vi_pham(
    ky_thi_id: UUID,
    cong_chuc_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(require_platform_role("QT_DAO_TAO")),
):
    """Danh sach vi pham chi tiet cua 1 thi sinh (gio + loai + ly do). Chi admin."""
    service = ThiSinhService(db)
    result = await service.danh_sach_vi_pham(ky_thi_id, cong_chuc_id)
    return {"success": True, "data": result}


@router.get("/{ky_thi_id}/giam-sat")
async def giam_sat_ky_thi(
    ky_thi_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(require_platform_role("QT_DAO_TAO")),
):
    """Giam sat truc tiep ky thi — tien do/vi pham/online tung thi sinh.

    Chi admin (QT_DAO_TAO/SUPER_ADMIN). FE poll ~7s.
    """
    service = ThiSinhService(db)
    result = await service.giam_sat(ky_thi_id, user)
    return {
        "success": True,
        "data": GiamSatResponse(**result).model_dump(mode="json"),
    }


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
    user: TokenPayload = Depends(require_platform_role("QT_DAO_TAO")),
):
    """Xem ket qua CBCC cu the — chi admin (QT_DAO_TAO/SUPER_ADMIN)."""
    service = ThiSinhService(db)
    result = await service.ket_qua_cbcc(ky_thi_id, cong_chuc_id, user)
    return {"success": True, "data": result.model_dump(mode="json")}


@router.get("/{ky_thi_id}/thi-sinh/{cong_chuc_id}/ket-qua/{lan}")
async def ket_qua_lan_thi(
    ky_thi_id: UUID,
    cong_chuc_id: UUID,
    lan: int,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(require_platform_role("QT_DAO_TAO")),
):
    """Xem chi tiet bai lam cua 1 lan thi cu the — chi admin (QT_DAO_TAO/SUPER_ADMIN).

    `lan` la so thu tu lan thi (1, 2, 3, ...). Lan moi nhat (= lan_thi_hien_tai)
    duoc tra ve giong nhu /ket-qua/{cong_chuc_id}. Lan cu hon duoc lay tu
    lich_su_thi JSONB.
    """
    service = ThiSinhService(db)
    result = await service.ket_qua_lan_thi(ky_thi_id, cong_chuc_id, lan, user)
    return {"success": True, "data": result.model_dump(mode="json")}


# ================================================================
# EXPORT EXCEL
# ================================================================

@router.get("/{ky_thi_id}/export")
async def export_ket_qua(
    ky_thi_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(require_platform_role("QT_DAO_TAO")),
):
    """Export ket qua ky thi ra file Excel (.xlsx). Chi admin (QT_DAO_TAO/SUPER_ADMIN)."""
    service = ThiSinhService(db)
    xlsx_bytes = await service.export_excel(ky_thi_id, user)
    return Response(
        content=xlsx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=ket_qua_ky_thi_{ky_thi_id}.xlsx"},
    )
