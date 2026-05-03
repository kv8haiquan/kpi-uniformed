"""
api/endpoints/nhom_thanh_phan.py
=================================
Module "Nhóm thành phần" — danh sách thành viên dùng chung cho nhiều cuộc họp.

10 endpoints:
  GET    /nhom-thanh-phan                       — list (search + filter loai_nhom)
  POST   /nhom-thanh-phan                       — tạo nhóm + danh sách thành viên
  GET    /nhom-thanh-phan/{id}                  — chi tiết nhóm + members
  PATCH  /nhom-thanh-phan/{id}                  — sửa metadata nhóm
  DELETE /nhom-thanh-phan/{id}                  — xoá hẳn (cascade chi_tiet)
  POST   /nhom-thanh-phan/{id}/thanh-vien       — thêm 1 thành viên
  PUT    /nhom-thanh-phan/{id}/thanh-vien/{cc}  — sửa vai_tro / loai_tham_du
  DELETE /nhom-thanh-phan/{id}/thanh-vien/{cc}  — xoá thành viên

Permission: mọi công chức đã đăng nhập đều CRUD được mọi nhóm (yêu cầu user duyệt).
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from meeting_service.dependencies import (
    CurrentUserDep,
    DatabaseDep,
    require_can_edit_meeting,
)
from meeting_service.models.cuoc_hop import CuocHop
from meeting_service.schemas.nhom_thanh_phan import (
    ChiTietCreate,
    ChiTietResponse,
    ChiTietUpdate,
    NhomCreate,
    NhomListItem,
    NhomResponse,
    NhomUpdate,
    ThemTuNhomRequest,
)
from meeting_service.services.nhom_thanh_phan_service import NhomThanhPhanService


router = APIRouter(prefix="/nhom-thanh-phan", tags=["Nhóm thành phần"])

# Router phụ — endpoint "them-tu-nhom" gắn dưới /cuoc-hop/{id}/thanh-phan
router_cuoc_hop = APIRouter(prefix="/cuoc-hop", tags=["Nhóm thành phần"])


# ──────────────────────────────────────────────────────────────────────
# CRUD nhóm
# ──────────────────────────────────────────────────────────────────────

@router.get("/", summary="Danh sách nhóm thành phần")
async def danh_sach(
    db: DatabaseDep,
    _: CurrentUserDep,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    q: Optional[str] = Query(None, max_length=200, description="Search ten_nhom"),
    loai_nhom: Optional[str] = Query(None, max_length=100),
):
    service = NhomThanhPhanService(db)
    result = await service.danh_sach(page=page, limit=limit, q=q, loai_nhom=loai_nhom)
    return {
        "success": True,
        "data": [NhomListItem.model_validate(item).model_dump(mode="json")
                 for item in result["items"]],
        "pagination": result["pagination"],
    }


@router.post("/", status_code=201, summary="Tạo nhóm thành phần")
async def tao_moi(
    data: NhomCreate,
    db: DatabaseDep,
    user: CurrentUserDep,
):
    service = NhomThanhPhanService(db)
    nhom = await service.tao_moi(data, user)
    detail = await service.chi_tiet(nhom.id)
    return {
        "success": True,
        "data": NhomResponse.model_validate(detail).model_dump(mode="json"),
    }


@router.get("/{nhom_id}", summary="Chi tiết nhóm + danh sách thành viên")
async def chi_tiet(
    nhom_id: UUID,
    db: DatabaseDep,
    _: CurrentUserDep,
):
    service = NhomThanhPhanService(db)
    detail = await service.chi_tiet(nhom_id)
    return {
        "success": True,
        "data": NhomResponse.model_validate(detail).model_dump(mode="json"),
    }


@router.patch("/{nhom_id}", summary="Cập nhật metadata nhóm")
async def cap_nhat(
    nhom_id: UUID,
    data: NhomUpdate,
    db: DatabaseDep,
    user: CurrentUserDep,
):
    service = NhomThanhPhanService(db)
    await service.cap_nhat(nhom_id, data, user)
    detail = await service.chi_tiet(nhom_id)
    return {
        "success": True,
        "data": NhomResponse.model_validate(detail).model_dump(mode="json"),
    }


@router.delete("/{nhom_id}", summary="Xoá nhóm (hard delete)")
async def xoa(
    nhom_id: UUID,
    db: DatabaseDep,
    user: CurrentUserDep,
):
    service = NhomThanhPhanService(db)
    await service.xoa(nhom_id, user)
    return {"success": True, "data": {"id": str(nhom_id), "deleted": True}}


# ──────────────────────────────────────────────────────────────────────
# CRUD thành viên trong nhóm
# ──────────────────────────────────────────────────────────────────────

@router.post("/{nhom_id}/thanh-vien", status_code=201, summary="Thêm 1 thành viên vào nhóm")
async def them_thanh_vien(
    nhom_id: UUID,
    data: ChiTietCreate,
    db: DatabaseDep,
    user: CurrentUserDep,
):
    service = NhomThanhPhanService(db)
    ct = await service.them_thanh_vien(nhom_id, data, user)
    return {
        "success": True,
        "data": ChiTietResponse.model_validate(ct).model_dump(mode="json"),
    }


@router.put("/{nhom_id}/thanh-vien/{cong_chuc_id}",
            summary="Sửa vai_tro / loai_tham_du của thành viên")
async def sua_thanh_vien(
    nhom_id: UUID,
    cong_chuc_id: UUID,
    data: ChiTietUpdate,
    db: DatabaseDep,
    user: CurrentUserDep,
):
    service = NhomThanhPhanService(db)
    ct = await service.cap_nhat_thanh_vien(nhom_id, cong_chuc_id, data, user)
    return {
        "success": True,
        "data": ChiTietResponse.model_validate(ct).model_dump(mode="json"),
    }


@router.delete("/{nhom_id}/thanh-vien/{cong_chuc_id}",
               summary="Gỡ 1 thành viên khỏi nhóm")
async def xoa_thanh_vien(
    nhom_id: UUID,
    cong_chuc_id: UUID,
    db: DatabaseDep,
    user: CurrentUserDep,
):
    service = NhomThanhPhanService(db)
    await service.xoa_thanh_vien(nhom_id, cong_chuc_id, user)
    return {"success": True, "data": {"deleted": True}}


# ──────────────────────────────────────────────────────────────────────
# MERGE — POST /cuoc-hop/{id}/thanh-phan/them-tu-nhom
# ──────────────────────────────────────────────────────────────────────

@router_cuoc_hop.post("/{cuoc_hop_id}/thanh-phan/them-tu-nhom",
                       summary="Gộp thành viên từ 1+ nhóm vào cuộc họp")
async def them_tu_nhom(
    data: ThemTuNhomRequest,
    db: DatabaseDep,
    user: CurrentUserDep,
    ch: CuocHop = Depends(require_can_edit_meeting),
):
    """Gộp thành viên từ các nhóm vào cuộc họp.

    Skip người đã có trong cuộc họp (KHÔNG ghi đè loai_tham_du cũ).
    Auto-fill chu_toa_id / thu_ky_id nếu cuộc họp đang để trống.
    Chỉ chu_toa | thu_ky | SUPER_ADMIN | TRUONG_CNTT của cuộc họp được phép gọi.
    """
    service = NhomThanhPhanService(db)
    result = await service.merge_into_cuoc_hop(ch, data.nhom_ids, user)
    return {"success": True, "data": result.model_dump(mode="json")}
