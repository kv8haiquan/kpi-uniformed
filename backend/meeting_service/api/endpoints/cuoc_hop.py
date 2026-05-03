"""
api/endpoints/cuoc_hop.py
==========================
Module 1 — Quản lý cuộc họp. 7 endpoints theo §4 HKG_API_SPECS.md.

Permission được áp qua dependencies (require_can_view/edit_meeting,
require_role, require_platform_role).
"""

from datetime import date as date_type
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from meeting_service.dependencies import (
    DatabaseDep,
    CurrentUserDep,
    require_can_edit_meeting,
    require_can_view_meeting,
)
from meeting_service.models.cuoc_hop import CuocHop
from meeting_service.schemas.cuoc_hop import (
    CuocHopCreate,
    CuocHopHuy,
    CuocHopListItem,
    CuocHopResponse,
    CuocHopUpdate,
    ThanhPhanReplaceList,
    XacNhanThamDu,
)
from meeting_service.services.cuoc_hop_service import CuocHopService


router = APIRouter(prefix="/cuoc-hop", tags=["Cuộc họp"])


# ─── 1. CREATE ────────────────────────────────────────────────────────
@router.post("/", status_code=201, summary="Tạo cuộc họp mới")
async def tao_cuoc_hop(
    data: CuocHopCreate,
    db: DatabaseDep,
    user: CurrentUserDep,
):
    """Tạo cuộc họp mới + thành phần. Audit log + ghi mặc định LEN_KE_HOACH."""
    service = CuocHopService(db)
    ch = await service.tao_moi(data, user)
    return {
        "success": True,
        "data": CuocHopResponse.model_validate(ch).model_dump(mode="json"),
    }


# ─── 2. LIST ──────────────────────────────────────────────────────────
@router.get("/", summary="Danh sách cuộc họp (filter + phân trang)")
async def danh_sach_cuoc_hop(
    db: DatabaseDep,
    user: CurrentUserDep,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    ngay_tu: Optional[date_type] = Query(None, description="Lọc từ ngày (YYYY-MM-DD)"),
    ngay_den: Optional[date_type] = Query(None, description="Lọc đến ngày"),
    don_vi_id: Optional[UUID] = Query(None),
    khoi: Optional[str] = Query(None),
    trang_thai: Optional[str] = Query(None),
):
    """Danh sách cuộc họp user xem được (theo phân quyền 2 lớp)."""
    service = CuocHopService(db)
    result = await service.danh_sach(
        user,
        page=page,
        limit=limit,
        ngay_tu=ngay_tu,
        ngay_den=ngay_den,
        don_vi_id=don_vi_id,
        khoi=khoi,
        trang_thai=trang_thai,
    )

    items = []
    for ch in result["items"]:
        item = CuocHopListItem.model_validate(ch).model_dump(mode="json")
        item["so_thanh_phan"] = result["so_thanh_phan_map"].get(ch.id, 0)
        items.append(item)

    return {
        "success": True,
        "data": items,
        "pagination": result["pagination"],
    }


# ─── 3. GET DETAIL ────────────────────────────────────────────────────
@router.get("/{cuoc_hop_id}", summary="Chi tiết cuộc họp")
async def chi_tiet_cuoc_hop(
    ch: CuocHop = Depends(require_can_view_meeting),
):
    """Chi tiết 1 cuộc họp. Permission qua require_can_view_meeting."""
    return {
        "success": True,
        "data": CuocHopResponse.model_validate(ch).model_dump(mode="json"),
    }


# ─── 4. UPDATE ────────────────────────────────────────────────────────
@router.patch("/{cuoc_hop_id}", summary="Cập nhật cuộc họp")
async def cap_nhat_cuoc_hop(
    data: CuocHopUpdate,
    db: DatabaseDep,
    user: CurrentUserDep,
    ch: CuocHop = Depends(require_can_edit_meeting),
):
    """Cập nhật cuộc họp. Chỉ chu_toa | thu_ky | SUPER_ADMIN | TRUONG_CNTT."""
    service = CuocHopService(db)
    ch = await service.cap_nhat(ch, data, user)
    return {
        "success": True,
        "data": CuocHopResponse.model_validate(ch).model_dump(mode="json"),
    }


# ─── 5. CANCEL ────────────────────────────────────────────────────────
@router.post("/{cuoc_hop_id}/huy", summary="Hủy cuộc họp")
async def huy_cuoc_hop(
    payload: CuocHopHuy,
    db: DatabaseDep,
    user: CurrentUserDep,
    ch: CuocHop = Depends(require_can_edit_meeting),
):
    """Hủy cuộc họp. Notification cho thành phần. Audit CANCEL_MEETING."""
    service = CuocHopService(db)
    ch = await service.huy(ch, payload.ly_do, user)
    return {
        "success": True,
        "data": CuocHopResponse.model_validate(ch).model_dump(mode="json"),
    }


# ─── 6. SEND INVITATION ───────────────────────────────────────────────
@router.post("/{cuoc_hop_id}/gui-giay-moi", summary="Gửi giấy mời")
async def gui_giay_moi(
    db: DatabaseDep,
    user: CurrentUserDep,
    ch: CuocHop = Depends(require_can_edit_meeting),
):
    """Gửi giấy mời + đổi trang_thai = DA_THONG_BAO + N row thong_bao."""
    service = CuocHopService(db)
    so_gui = await service.gui_giay_moi(ch, user)
    return {
        "success": True,
        "data": {"so_giay_moi_da_gui": so_gui},
    }


# ─── 7. CONFIRM ATTENDANCE ────────────────────────────────────────────
@router.post("/{cuoc_hop_id}/xac-nhan", summary="CBCC xác nhận tham dự")
async def xac_nhan_tham_du(
    cuoc_hop_id: UUID,
    payload: XacNhanThamDu,
    db: DatabaseDep,
    user: CurrentUserDep,
):
    """CBCC tự xác nhận tham dự / không / ủy quyền."""
    service = CuocHopService(db)
    tp = await service.xac_nhan_tham_du(cuoc_hop_id, payload, user)
    return {
        "success": True,
        "data": {
            "id": str(tp.id),
            "xac_nhan": tp.xac_nhan,
            "thoi_gian_xac_nhan": tp.thoi_gian_xac_nhan.isoformat() if tp.thoi_gian_xac_nhan else None,
        },
    }


# ─── 8. SỬA THÀNH PHẦN (G4-fix-6) ─────────────────────────────────────
@router.get(
    "/{cuoc_hop_id}/thanh-phan",
    summary="Lấy danh sách thành phần cuộc họp",
)
async def list_thanh_phan(
    db: DatabaseDep,
    user: CurrentUserDep,
    ch: CuocHop = Depends(require_can_view_meeting),
):
    """Trả về list thành phần kèm thông tin CBCC (ho_ten/ma_cc/đơn vị) cho UI."""
    from sqlalchemy import text as _sa_text
    res = await db.execute(_sa_text("""
        SELECT tp.id, tp.cuoc_hop_id, tp.cong_chuc_id, tp.loai_tham_du, tp.xac_nhan,
               cc.ho_ten, cc.ma_cc, cc.don_vi_id, cc.chuc_vu,
               dv.ten_don_vi
          FROM meeting.thanh_phan tp
          LEFT JOIN public.cong_chuc cc ON cc.id = tp.cong_chuc_id
          LEFT JOIN public.don_vi   dv ON dv.id = cc.don_vi_id
         WHERE tp.cuoc_hop_id = :ch_id
         ORDER BY cc.ho_ten
    """), {"ch_id": str(ch.id)})

    items = []
    for row in res.fetchall():
        items.append({
            "id": str(row.id),
            "cuoc_hop_id": str(row.cuoc_hop_id),
            "cong_chuc_id": str(row.cong_chuc_id),
            "loai_tham_du": row.loai_tham_du,
            "xac_nhan": row.xac_nhan,
            "ho_ten": row.ho_ten,
            "ma_cc": row.ma_cc,
            "don_vi_id": str(row.don_vi_id) if row.don_vi_id else None,
            "ten_don_vi": row.ten_don_vi,
            "chuc_vu": row.chuc_vu,
        })

    return {"success": True, "data": items}


@router.put(
    "/{cuoc_hop_id}/thanh-phan",
    summary="Sửa thành phần (replace list, diff add/remove)",
)
async def sua_thanh_phan(
    payload: ThanhPhanReplaceList,
    db: DatabaseDep,
    user: CurrentUserDep,
    ch: CuocHop = Depends(require_can_edit_meeting),
):
    """
    Replace toàn bộ thành phần. Service tự diff:
    - Người mới được thêm: nhận GIAY_MOI_HOP nếu cuộc họp đã DA_THONG_BAO
    - Người bị bỏ: KHÔNG được phép nếu là chu_toa hoặc thu_ky (409)
    """
    service = CuocHopService(db)
    summary = await service.sua_thanh_phan(ch, payload.thanh_phan, user)
    return {"success": True, "data": summary}
