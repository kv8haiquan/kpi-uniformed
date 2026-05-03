"""
api/endpoints/ket_luan.py
==========================
Module 10 — Kết luận + Dashboard. 8 endpoints.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from meeting_service.dependencies import (
    CurrentUserDep,
    DatabaseDep,
    require_can_edit_meeting,
    require_can_view_meeting,
)
from meeting_service.models.cuoc_hop import CuocHop
from meeting_service.schemas.ket_luan import (
    DashboardCaNhan,
    DashboardDonVi,
    KetLuanCreate,
    KetLuanResponse,
    KetLuanUpdate,
    TienDoCreate,
    TienDoResponse,
)
from meeting_service.services.ket_luan_service import KetLuanService


router = APIRouter(prefix="/ket-luan", tags=["Kết luận"])
router_cuoc_hop = APIRouter(prefix="/cuoc-hop", tags=["Kết luận"])
router_thong_ke = APIRouter(prefix="/thong-ke", tags=["Thống kê"])


# ─── 1. CREATE (theo cuộc họp) ────────────────────────────────────────
@router_cuoc_hop.post(
    "/{cuoc_hop_id}/ket-luan",
    status_code=201,
    summary="Giao nhiệm vụ (kết luận họp)",
)
async def tao_ket_luan(
    data: KetLuanCreate,
    db: DatabaseDep,
    user: CurrentUserDep,
    ch: CuocHop = Depends(require_can_edit_meeting),
):
    service = KetLuanService(db)
    kl = await service.tao(ch.id, data, user)
    return {
        "success": True,
        "data": KetLuanResponse.model_validate(kl).model_dump(mode="json"),
    }


# ─── 2. LIST (theo cuộc họp) ──────────────────────────────────────────
@router_cuoc_hop.get(
    "/{cuoc_hop_id}/ket-luan",
    summary="Danh sách kết luận của cuộc họp",
)
async def list_ket_luan(
    db: DatabaseDep,
    user: CurrentUserDep,
    ch: CuocHop = Depends(require_can_view_meeting),
):
    service = KetLuanService(db)
    items = await service.list_for_cuoc_hop(ch.id)
    return {
        "success": True,
        "data": [
            KetLuanResponse.model_validate(k).model_dump(mode="json")
            for k in items
        ],
    }


# ─── 3. UPDATE METADATA ───────────────────────────────────────────────
@router.patch("/{kl_id}", summary="Cập nhật metadata kết luận")
async def cap_nhat(
    kl_id: UUID,
    data: KetLuanUpdate,
    db: DatabaseDep,
    user: CurrentUserDep,
):
    service = KetLuanService(db)
    kl = await service.cap_nhat(kl_id, data, user)
    return {
        "success": True,
        "data": KetLuanResponse.model_validate(kl).model_dump(mode="json"),
    }


# ─── 4. CẬP NHẬT TIẾN ĐỘ ──────────────────────────────────────────────
@router.post("/{kl_id}/tien-do", status_code=201, summary="Cập nhật tiến độ")
async def cap_nhat_tien_do(
    kl_id: UUID,
    data: TienDoCreate,
    db: DatabaseDep,
    user: CurrentUserDep,
):
    service = KetLuanService(db)
    td = await service.cap_nhat_tien_do(kl_id, data, user)
    return {
        "success": True,
        "data": TienDoResponse.model_validate(td).model_dump(mode="json"),
    }


# ─── 5. CỦA TÔI ───────────────────────────────────────────────────────
@router.get("/cua-toi", summary="Nhiệm vụ tôi phụ trách")
async def cua_toi(
    db: DatabaseDep,
    user: CurrentUserDep,
    trang_thai: Optional[str] = Query(None),
):
    service = KetLuanService(db)
    items = await service.cua_toi(user, trang_thai=trang_thai)
    return {
        "success": True,
        "data": [
            KetLuanResponse.model_validate(k).model_dump(mode="json")
            for k in items
        ],
    }


# ─── 6. CỦA ĐƠN VỊ ────────────────────────────────────────────────────
@router.get("/cua-don-vi/{don_vi_id}", summary="Nhiệm vụ của đơn vị (LĐ ĐV/CHANH_VP)")
async def cua_don_vi(
    don_vi_id: UUID,
    db: DatabaseDep,
    user: CurrentUserDep,
):
    service = KetLuanService(db)
    items = await service.cua_don_vi(don_vi_id, user)
    return {
        "success": True,
        "data": [
            KetLuanResponse.model_validate(k).model_dump(mode="json")
            for k in items
        ],
    }


# ─── 7. DASHBOARD CÁ NHÂN ─────────────────────────────────────────────
@router_thong_ke.get("/ca-nhan", summary="Dashboard cá nhân")
async def dashboard_ca_nhan(
    db: DatabaseDep,
    user: CurrentUserDep,
):
    service = KetLuanService(db)
    data = await service.dashboard_ca_nhan(user)
    return {"success": True, "data": data}


# ─── 8. DASHBOARD ĐƠN VỊ ──────────────────────────────────────────────
@router_thong_ke.get(
    "/don-vi/{don_vi_id}",
    summary="Dashboard đơn vị (LĐ ĐV/CHANH_VP/TRUONG_CNTT/CCT/PCCT)",
)
async def dashboard_don_vi(
    don_vi_id: UUID,
    db: DatabaseDep,
    user: CurrentUserDep,
):
    service = KetLuanService(db)
    data = await service.dashboard_don_vi(don_vi_id, user)
    return {"success": True, "data": data}
