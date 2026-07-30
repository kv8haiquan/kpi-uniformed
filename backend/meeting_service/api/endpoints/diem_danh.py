"""
api/endpoints/diem_danh.py
============================
Module 4 — Điểm danh. 4 endpoints theo §6 HKG_API_SPECS.md.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from meeting_service.dependencies import (
    DatabaseDep,
    CurrentUserDep,
    require_can_edit_meeting,
    require_can_view_meeting,
)
from meeting_service.models.cuoc_hop import CuocHop
from meeting_service.schemas.diem_danh import (
    BamTayBulk,
    DiemDanhResponse,
    DiemDanhSummary,
    QRSubmit,
    QRTokenResponse,
)
from meeting_service.services.diem_danh_service import DiemDanhService


router = APIRouter(prefix="/diem-danh", tags=["Điểm danh"])
router_cuoc_hop = APIRouter(prefix="/cuoc-hop", tags=["Điểm danh"])


# ─── 1. Sinh QR token ─────────────────────────────────────────────────
@router.post(
    "/qr-token/{cuoc_hop_id}",
    response_model=None,
    summary="Sinh QR token cho cuộc họp (chu_toa/thu_ky)",
)
async def qr_token(
    db: DatabaseDep,
    user: CurrentUserDep,
    ch: CuocHop = Depends(require_can_edit_meeting),
):
    service = DiemDanhService(db)
    data = service.issue_qr_token(ch.id, ttl_seconds=3600)
    return {"success": True, "data": data}


# ─── 2. CBCC quét QR submit ───────────────────────────────────────────
@router.post("/quet", summary="CBCC quét QR submit token")
async def quet_qr(
    payload: QRSubmit,
    db: DatabaseDep,
    user: CurrentUserDep,
):
    service = DiemDanhService(db)
    dd = await service.submit_qr(payload.token, user)
    return {
        "success": True,
        "data": DiemDanhResponse.model_validate(dd).model_dump(mode="json"),
    }


# ─── 3. Bấm tay ───────────────────────────────────────────────────────
@router.post("/bam-tay", summary="Thư ký bấm tay điểm danh nhiều CBCC")
async def bam_tay(
    payload: BamTayBulk,
    db: DatabaseDep,
    user: CurrentUserDep,
):
    # Verify edit permission cho cuộc họp
    from sqlalchemy import select
    from meeting_service.models.cuoc_hop import CuocHop as CuocHopModel
    res = await db.execute(
        select(CuocHopModel).where(
            CuocHopModel.id == payload.cuoc_hop_id, CuocHopModel.is_deleted.is_(False)
        )
    )
    ch = res.scalar_one_or_none()
    if ch is None:
        raise HTTPException(
            status_code=404,
            detail={"success": False, "error": {"code": "MEETING_NOT_FOUND",
                    "message": "Không tìm thấy cuộc họp"}},
        )
    # G4-fix-5: chặn điểm danh tay cho cuộc họp đã hủy
    if ch.trang_thai == "HUY":
        raise HTTPException(
            status_code=409,
            detail={"success": False, "error": {"code": "MEETING_CANCELLED",
                    "message": "Cuộc họp đã hủy — không thể điểm danh"}},
        )
    user_id = UUID(user.sub)
    if not (
        user.is_admin or user.vai_tro in ("SUPER_ADMIN", "ADMIN")
        or ch.chu_toa_id == user_id or ch.thu_ky_id == user_id
        or "TRUONG_CNTT" in (user.platform_roles or [])
    ):
        raise HTTPException(
            status_code=403,
            detail={"success": False, "error": {"code": "NO_PERMISSION",
                    "message": "Chỉ chu_toa/thu_ky/admin mới được bấm tay"}},
        )

    service = DiemDanhService(db)
    results = await service.bam_tay(payload, user)
    return {
        "success": True,
        "data": {
            "so_diem_danh": len(results),
            "chi_tiet": [
                DiemDanhResponse.model_validate(r).model_dump(mode="json")
                for r in results
            ],
        },
    }


# ─── G4-fix-6.2: SELF CHECKIN (CBCC tự click trong app) ───────────────
@router_cuoc_hop.post(
    "/{cuoc_hop_id}/tu-diem-danh",
    summary="CBCC tự điểm danh (không cần QR)",
)
async def tu_diem_danh(
    cuoc_hop_id: UUID,
    db: DatabaseDep,
    user: CurrentUserDep,
):
    """CBCC click "Tôi có mặt" trong app trên máy tính."""
    service = DiemDanhService(db)
    dd = await service.tu_diem_danh(cuoc_hop_id, user)
    return {
        "success": True,
        "data": DiemDanhResponse.model_validate(dd).model_dump(mode="json"),
    }


@router_cuoc_hop.get(
    "/{cuoc_hop_id}/diem-danh-cua-toi",
    summary="Trạng thái điểm danh của user hiện tại",
)
async def diem_danh_cua_toi(
    cuoc_hop_id: UUID,
    db: DatabaseDep,
    user: CurrentUserDep,
    ch: CuocHop = Depends(require_can_view_meeting),
):
    """FE dùng để biết hiển thị nút 'Tôi có mặt' hay 'Đã điểm danh'.

    Fix 30/07/2026: bổ sung require_can_view_meeting — trước đây endpoint này
    không kiểm tra quyền nên user không thuộc cuộc họp vẫn gọi được (trả 200
    trong khi các endpoint cùng trang trả 403, gây log khó đọc).
    """
    service = DiemDanhService(db)
    return {"success": True, "data": await service.my_status(cuoc_hop_id, user)}


# ─── 4. Tổng hợp điểm danh ────────────────────────────────────────────
@router_cuoc_hop.get(
    "/{cuoc_hop_id}/diem-danh",
    summary="Tổng hợp điểm danh cuộc họp",
)
async def summary_diem_danh(
    db: DatabaseDep,
    user: CurrentUserDep,
    ch: CuocHop = Depends(require_can_view_meeting),
):
    service = DiemDanhService(db)
    data = await service.summary(ch.id)
    return {
        "success": True,
        "data": {
            **{k: v for k, v in data.items() if k != "chi_tiet"},
            "chi_tiet": [
                DiemDanhResponse.model_validate(d).model_dump(mode="json")
                for d in data["chi_tiet"]
            ],
        },
    }
