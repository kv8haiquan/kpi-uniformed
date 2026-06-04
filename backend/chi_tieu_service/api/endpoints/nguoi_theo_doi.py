"""
chi_tieu_service/api/endpoints/nguoi_theo_doi.py
================================================
Quan ly nguoi theo doi chi tieu (gan platform_role). Quyen: QT_CHI_TIEU / admin.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from chi_tieu_service.dependencies import get_db, require_platform_role
from chi_tieu_service.schemas.nguoi_theo_doi import (
    CapNhatPhamViRequest, CongChucSearchItem, GanNguoiTheoDoiRequest,
    NguoiTheoDoiItem, RoleChiTieu,
)
from chi_tieu_service.services.nguoi_theo_doi_service import NguoiTheoDoiService
from shared.auth import TokenPayload

router = APIRouter(prefix="/nguoi-theo-doi", tags=["Chỉ tiêu - Người theo dõi"])

_QtDep = require_platform_role("QT_CHI_TIEU")


@router.get("")
async def danh_sach(
    role: RoleChiTieu = Query("THEO_DOI_CHI_TIEU"),
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(_QtDep),
):
    """Danh sách công chức đang giữ role + phạm vi đơn vị."""
    data = await NguoiTheoDoiService(db).danh_sach(role)
    return {"success": True, "data": [NguoiTheoDoiItem.model_validate(i).model_dump(mode="json") for i in data]}


@router.get("/cong-chuc")
async def tim_cong_chuc(
    search: Optional[str] = Query(None, min_length=1, max_length=100),
    don_vi_id: Optional[UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(_QtDep),
):
    """Tìm công chức để gán (READONLY public.cong_chuc)."""
    data = await NguoiTheoDoiService(db).tim_cong_chuc(search, don_vi_id)
    return {"success": True, "data": [CongChucSearchItem.model_validate(i).model_dump(mode="json") for i in data]}


@router.post("", status_code=201)
async def gan(
    body: GanNguoiTheoDoiRequest,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(_QtDep),
):
    """Gán / cập nhật role + phạm vi đơn vị cho công chức."""
    data = await NguoiTheoDoiService(db).gan(body.cong_chuc_id, body.don_vi_ids, body.role, UUID(user.sub))
    return {"success": True, "data": data, "message": "Đã gán người theo dõi"}


@router.put("/{cong_chuc_id}")
async def cap_nhat(
    cong_chuc_id: UUID,
    body: CapNhatPhamViRequest,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(_QtDep),
):
    """Cập nhật phạm vi đơn vị của 1 người theo dõi."""
    data = await NguoiTheoDoiService(db).gan(cong_chuc_id, body.don_vi_ids, body.role, UUID(user.sub))
    return {"success": True, "data": data, "message": "Đã cập nhật phạm vi"}


@router.delete("/{cong_chuc_id}")
async def go(
    cong_chuc_id: UUID,
    role: RoleChiTieu = Query("THEO_DOI_CHI_TIEU"),
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(_QtDep),
):
    """Gỡ role khỏi công chức (is_active=false)."""
    await NguoiTheoDoiService(db).go(cong_chuc_id, role)
    return {"success": True, "message": "Đã gỡ người theo dõi"}
