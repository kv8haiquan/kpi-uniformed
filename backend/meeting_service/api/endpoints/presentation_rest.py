"""REST endpoints Phase 4.1 — Page-Sync.

GET /cuoc-hop/{cuoc_hop_id}/presentation/state
- Trả state hiện tại của phiên trình chiếu + WS token cho client kết nối.
- UPSERT row trang_thai_trinh_chieu nếu chưa có (1-1 với cuoc_hop).

Threat model:
- Scope check (v3.1 §3.2): chỉ cấp token khi cuộc họp ở trạng thái
  DA_THONG_BAO/DANG_DIEN_RA — chặn token cấp quá sớm hoặc sau khi đã
  HOAN_THANH/HUY.
- Permission: chu_toa | thu_ky | thanh_phan | admin (qua _can_view_cuoc_hop).
  KHÔNG cấp cho user ngoài cuộc họp (tránh leak state).
- WS token TTL ≤ 6h, scope=meeting:{id} → chống cross-meeting injection.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text as sa_text

from meeting_service.dependencies import (
    CurrentUserDep,
    DatabaseDep,
    _can_view_cuoc_hop,
    _get_thu_ky_pham_vi,
)
from meeting_service.models.cuoc_hop import CuocHop
from meeting_service.schemas.presentation import PresentationStateResponse
from meeting_service.services.ws_token_service import create_ws_token


router = APIRouter(prefix="/cuoc-hop", tags=["Presentation (Phase 4.1)"])


_VALID_STATES_FOR_TOKEN = ("DA_THONG_BAO", "DANG_DIEN_RA")


@router.get(
    "/{cuoc_hop_id}/presentation/state",
    summary="State hiện tại của phiên trình chiếu + WS token",
)
async def get_presentation_state(
    cuoc_hop_id: UUID,
    db: DatabaseDep,
    user: CurrentUserDep,
) -> dict:
    """
    Trả state phiên trình chiếu + cấp WS token để client kết nối WS.

    v3.1 scope check:
    - Cuộc họp phải có trang_thai IN ('DA_THONG_BAO', 'DANG_DIEN_RA')
    - LEN_KE_HOACH / HOAN_THANH / HUY → 403
    - Cho phép DA_THONG_BAO để chu_toa pre-load tài liệu trước giờ họp

    Permissions: chu_toa | thu_ky | thanh_phan | admin | TRUONG_CNTT.
    Response gồm WS token với TTL theo formula v3.1.
    """
    # 1. Load cuộc họp + check tồn tại + chưa bị xóa
    from sqlalchemy import select
    res = await db.execute(
        select(CuocHop).where(
            CuocHop.id == cuoc_hop_id,
            CuocHop.is_deleted.is_(False),
        )
    )
    ch: CuocHop | None = res.scalar_one_or_none()
    if ch is None:
        raise HTTPException(
            status_code=404,
            detail={
                "success": False,
                "error": {"code": "MEETING_NOT_FOUND", "message": "Không tìm thấy cuộc họp"},
            },
        )

    # 2. Scope check (v3.1): chỉ cấp token khi DA_THONG_BAO/DANG_DIEN_RA
    if ch.trang_thai not in _VALID_STATES_FOR_TOKEN:
        raise HTTPException(
            status_code=403,
            detail={
                "success": False,
                "error": {
                    "code": "INVALID_MEETING_STATE",
                    "message": (
                        f"Chỉ cấp WS token khi cuộc họp ở trạng thái "
                        f"DA_THONG_BAO/DANG_DIEN_RA. Hiện tại: {ch.trang_thai}."
                    ),
                },
            },
        )

    # 3. Permission: tái dùng _can_view_cuoc_hop (chu_toa | thu_ky | thanh_phan | admin)
    if not await _can_view_cuoc_hop(ch, user, db):
        raise HTTPException(
            status_code=403,
            detail={
                "success": False,
                "error": {"code": "NO_PERMISSION", "message": "Không có quyền xem cuộc họp này"},
            },
        )

    # 4. UPSERT trang_thai_trinh_chieu (1 row / cuoc_hop). RETURNING để lấy
    # row vừa create/update không cần SELECT thêm.
    user_uuid = UUID(user.sub)
    upsert = await db.execute(sa_text("""
        INSERT INTO meeting.trang_thai_trinh_chieu
            (cuoc_hop_id, cap_nhat_boi_id)
        VALUES (:ch, :uid)
        ON CONFLICT (cuoc_hop_id) DO UPDATE
            SET cap_nhat_luc = NOW(),
                cap_nhat_boi_id = EXCLUDED.cap_nhat_boi_id
        RETURNING id, cuoc_hop_id, tai_lieu_hien_tai_id, trang_hien_tai,
                  zoom_level, is_active, bat_dau_luc, ket_thuc_luc,
                  cap_nhat_luc, cap_nhat_boi_id
    """), {"ch": str(cuoc_hop_id), "uid": str(user_uuid)})
    state = upsert.one()
    await db.flush()

    # 5. Cấp WS token (formula v3.1)
    ws_token, expires_at = create_ws_token(user_uuid, cuoc_hop_id, ch)

    # 6. Flags is_chu_toa / is_thu_ky cho FE quyết định UI
    is_chu_toa = ch.chu_toa_id == user_uuid
    is_thu_ky = ch.thu_ky_id == user_uuid
    if not is_thu_ky and "THU_KY_HOP" in (user.platform_roles or []):
        # Mở rộng: thư ký phòng theo pham_vi
        thu_ky_dvs = await _get_thu_ky_pham_vi(user.sub, db)
        if ch.don_vi_to_chuc_id in thu_ky_dvs:
            is_thu_ky = True

    payload = PresentationStateResponse(
        cuoc_hop_id=state.cuoc_hop_id,
        is_active=state.is_active,
        tai_lieu_hien_tai_id=state.tai_lieu_hien_tai_id,
        trang_hien_tai=state.trang_hien_tai,
        zoom_level=state.zoom_level,
        bat_dau_luc=state.bat_dau_luc,
        ket_thuc_luc=state.ket_thuc_luc,
        cap_nhat_luc=state.cap_nhat_luc,
        cap_nhat_boi_id=state.cap_nhat_boi_id,
        ws_token=ws_token,
        ws_token_expires_at=expires_at,
        is_chu_toa=is_chu_toa,
        is_thu_ky=is_thu_ky,
    )
    return {"success": True, "data": payload.model_dump(mode="json")}
