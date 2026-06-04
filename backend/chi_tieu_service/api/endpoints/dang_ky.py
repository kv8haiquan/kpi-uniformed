"""
chi_tieu_service/api/endpoints/dang_ky.py
=========================================
Đăng ký + kết quả tháng (THEO_DOI_CHI_TIEU). Backend kiểm tra phạm vi đơn vị.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from chi_tieu_service.dependencies import get_db, get_current_user, require_platform_role
from chi_tieu_service.schemas.dang_ky import (
    DangKyCreate, DangKyResponse, DangKyUpdate, LichSuResponse,
    NhapKetQuaRequest, YeuCauSuaRequest,
)
from chi_tieu_service.services.dang_ky_service import DangKyService
from chi_tieu_service.services.guards import assert_theo_doi_don_vi
from shared.auth import TokenPayload

router = APIRouter(prefix="/dang-ky", tags=["Chỉ tiêu - Đăng ký & kết quả"])

# Role gate: nguoi theo doi hoac quan tri chi tieu
_RoleDep = require_platform_role("THEO_DOI_CHI_TIEU", "QT_CHI_TIEU")


def _resp(dk) -> dict:
    return {"success": True, "data": DangKyResponse.model_validate(dk).model_dump(mode="json")}


@router.get("")
async def danh_sach_can_dang_ky(
    don_vi_id: UUID = Query(...),
    thang: int = Query(..., ge=1, le=12),
    nam: int = Query(..., ge=2025),
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(_RoleDep),
):
    """Danh sách chỉ tiêu đơn vị CÓ giao năm, kèm trạng thái bản ghi (nếu đã tạo)."""
    await assert_theo_doi_don_vi(db, user, don_vi_id)
    data = await DangKyService(db).danh_sach_can_dang_ky(don_vi_id, thang, nam)
    # serialize gia tri Decimal trong muc_giao + ban ghi dang ky
    out = []
    for row in data:
        dk = row["dang_ky"]
        out.append({
            "chi_tieu_id": str(row["chi_tieu_id"]),
            "muc_giao": [
                {"loai_muc": m["loai_muc"],
                 "gia_tri_giao": str(m["gia_tri_giao"]) if m["gia_tri_giao"] is not None else None,
                 "luy_ke_dau_ky": str(m["luy_ke_dau_ky"]) if m["luy_ke_dau_ky"] is not None else None}
                for m in row["muc_giao"]
            ],
            "dang_ky": DangKyResponse.model_validate(dk).model_dump(mode="json") if dk else None,
        })
    return {"success": True, "data": out}


@router.post("", status_code=201)
async def tao(
    data: DangKyCreate,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(_RoleDep),
):
    await assert_theo_doi_don_vi(db, user, data.don_vi_id)
    dk = await DangKyService(db).tao_moi(data, nguoi_theo_doi_id=UUID(user.sub))
    return _resp(dk) | {"message": "Tạo đăng ký thành công"}


@router.put("/{dk_id}")
async def cap_nhat(
    dk_id: UUID,
    data: DangKyUpdate,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(_RoleDep),
):
    svc = DangKyService(db)
    dk = await svc.chi_tiet(dk_id)
    await assert_theo_doi_don_vi(db, user, dk.don_vi_id)
    dk = await svc.cap_nhat(dk_id, data)
    return _resp(dk) | {"message": "Cập nhật đăng ký thành công"}


@router.post("/{dk_id}/gui-duyet")
async def gui_duyet(
    dk_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(_RoleDep),
):
    svc = DangKyService(db)
    dk = await svc.chi_tiet(dk_id)
    await assert_theo_doi_don_vi(db, user, dk.don_vi_id)
    dk = await svc.gui_duyet(dk_id, UUID(user.sub))
    return _resp(dk) | {"message": "Đã gửi Trưởng đơn vị duyệt đăng ký"}


@router.post("/{dk_id}/yeu-cau-sua")
async def yeu_cau_sua(
    dk_id: UUID,
    data: YeuCauSuaRequest,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(_RoleDep),
):
    svc = DangKyService(db)
    dk = await svc.chi_tiet(dk_id)
    await assert_theo_doi_don_vi(db, user, dk.don_vi_id)
    dk = await svc.yeu_cau_sua(dk_id, data, UUID(user.sub))
    return _resp(dk) | {"message": "Đã gửi yêu cầu sửa đăng ký"}


@router.post("/{dk_id}/nhap-ket-qua")
async def nhap_ket_qua(
    dk_id: UUID,
    data: NhapKetQuaRequest,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(_RoleDep),
):
    svc = DangKyService(db)
    dk = await svc.chi_tiet(dk_id)
    await assert_theo_doi_don_vi(db, user, dk.don_vi_id)
    dk = await svc.nhap_ket_qua(dk_id, data)
    return _resp(dk) | {"message": "Đã lưu kết quả"}


@router.post("/{dk_id}/gui-ket-qua")
async def gui_ket_qua(
    dk_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(_RoleDep),
):
    svc = DangKyService(db)
    dk = await svc.chi_tiet(dk_id)
    await assert_theo_doi_don_vi(db, user, dk.don_vi_id)
    dk = await svc.gui_ket_qua(dk_id, UUID(user.sub))
    return _resp(dk) | {"message": "Đã gửi Trưởng đơn vị duyệt kết quả"}


@router.post("/{dk_id}/mo-khoa")
async def mo_khoa(
    dk_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(require_platform_role("QT_CHI_TIEU")),
):
    """Mở khóa bản ghi đã chốt kết quả — chỉ QT_CHI_TIEU / LĐ Chi cục."""
    from chi_tieu_service.services.duyet_service import DuyetService
    dk = await DuyetService(db).mo_khoa(dk_id, UUID(user.sub))
    return _resp(dk) | {"message": "Đã mở khóa bản ghi"}


@router.get("/{dk_id}/lich-su")
async def lich_su(
    dk_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(_RoleDep),
):
    rows = await DangKyService(db).lich_su(dk_id)
    return {"success": True, "data": [LichSuResponse.model_validate(r).model_dump(mode="json") for r in rows]}
