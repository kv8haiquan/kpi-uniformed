"""
api/endpoints/tai_lieu.py
==========================
Module 3 — Tài liệu họp. 5 endpoints chính + 1 endpoint serve file (gateway).

Spec: §5 HKG_API_SPECS.md (đã cập nhật MVP filesystem + JWT short-lived).
"""

import os
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, UploadFile
from fastapi.responses import FileResponse, Response

from meeting_service.dependencies import (
    DatabaseDep,
    CurrentUserDep,
    require_can_edit_meeting,
    require_can_view_meeting,
)
from meeting_service.services.rate_limit import limiter
from meeting_service.models.cuoc_hop import CuocHop
from meeting_service.schemas.tai_lieu import (
    TaiLieuListItem,
    TaiLieuMetadataUpdate,
    TaiLieuResponse,
)
from meeting_service.services.short_lived_token import (
    PURPOSE_DOWNLOAD_DOC,
    PURPOSE_VIEW_DOC,
    issue_token,
    verify_token,
)
from meeting_service.services.preview_service import (
    ensure_pdf_preview,
    is_office_extension,
)
from meeting_service.services.storage_service import StorageService
from meeting_service.services.tai_lieu_service import TaiLieuService


router = APIRouter(prefix="/tai-lieu", tags=["Tài liệu họp"])
router_cuoc_hop = APIRouter(prefix="/cuoc-hop", tags=["Tài liệu họp"])


# ─── 1. UPLOAD ────────────────────────────────────────────────────────
# Rate-limit: 60/5minutes per user (~12/phút) — cuộc họp công vụ thường có
# 10-30 tài liệu, limit cũ 10/5min đã từng false-positive (sự cố 11/05/2026).
# Override qua env HKG_UPLOAD_RATE_LIMIT khi cần (vd "30/minute").
@router.post("/upload", status_code=201, summary="Upload tài liệu họp")
@limiter.limit(os.getenv("HKG_UPLOAD_RATE_LIMIT", "60/5minutes"))
async def upload_tai_lieu(
    request: Request,
    db: DatabaseDep,
    user: CurrentUserDep,
    cuoc_hop_id: UUID = Form(...),
    file: UploadFile = File(...),
    ten_tai_lieu: Optional[str] = Form(None),
    mo_ta: Optional[str] = Form(None),
    phan_quyen: str = Form("CONG_KHAI"),
    cho_phep_tai: bool = Form(True),
    cho_phep_in: bool = Form(True),
):
    """Upload 1 file vào cuộc họp. Permission: chu_toa | thu_ky | admin."""
    # Tự kiểm tra edit-permission ở đây vì cuoc_hop_id từ Form không phải Path
    from sqlalchemy import select
    from meeting_service.models.cuoc_hop import CuocHop as CuocHopModel
    res = await db.execute(
        select(CuocHopModel).where(
            CuocHopModel.id == cuoc_hop_id, CuocHopModel.is_deleted.is_(False)
        )
    )
    ch = res.scalar_one_or_none()
    if ch is None:
        raise HTTPException(
            status_code=404,
            detail={"success": False, "error": {"code": "MEETING_NOT_FOUND",
                    "message": "Không tìm thấy cuộc họp"}},
        )
    # G4-fix-5: chặn upload cho cuộc họp đã hủy (audit trail)
    if ch.trang_thai == "HUY":
        raise HTTPException(
            status_code=409,
            detail={"success": False, "error": {"code": "MEETING_CANCELLED",
                    "message": "Cuộc họp đã hủy — không thể upload tài liệu"}},
        )
    user_id = UUID(user.sub)
    if not (
        user.is_admin or user.vai_tro in ("SUPER_ADMIN", "ADMIN")
        or "TRUONG_CNTT" in (user.platform_roles or [])
        or ch.chu_toa_id == user_id or ch.thu_ky_id == user_id
        or "THU_KY_HOP" in (user.platform_roles or [])  # role THU_KY_HOP của đơn vị
    ):
        raise HTTPException(
            status_code=403,
            detail={"success": False, "error": {"code": "NO_PERMISSION",
                    "message": "Bạn không có quyền upload tài liệu cho cuộc họp này"}},
        )

    service = TaiLieuService(db)
    tl = await service.upload(
        ch, file, user,
        ten_tai_lieu=ten_tai_lieu,
        mo_ta=mo_ta,
        phan_quyen=phan_quyen,
        cho_phep_tai=cho_phep_tai,
        cho_phep_in=cho_phep_in,
    )
    return {
        "success": True,
        "data": TaiLieuResponse.model_validate(tl).model_dump(mode="json"),
    }


# ─── 2. LIST của 1 cuộc họp ───────────────────────────────────────────
@router_cuoc_hop.get(
    "/{cuoc_hop_id}/tai-lieu",
    summary="Danh sách tài liệu của cuộc họp",
)
async def list_tai_lieu(
    db: DatabaseDep,
    user: CurrentUserDep,
    ch: CuocHop = Depends(require_can_view_meeting),
):
    """Trả về danh sách tài liệu + URL xem (kèm short-lived token)."""
    service = TaiLieuService(db)
    items = await service.list_for_cuoc_hop(ch.id)

    out = []
    for tl in items:
        # Skip nếu phan_quyen=HAN_CHE và user chưa được chỉ định —
        # MVP đơn giản: HAN_CHE vẫn cho người được mời xem (do require_can_view_meeting đã pass)
        token = issue_token(
            purpose=PURPOSE_VIEW_DOC,
            subject=str(tl.id),
            extra_claims={"viewer_id": user.sub},
            ttl_seconds=3600,
        )
        item = TaiLieuListItem.model_validate(tl).model_dump(mode="json")
        item["url_xem"] = f"/api/v1/hop-khong-giay/tai-lieu/{tl.id}/xem-noi-dung?t={token}"
        out.append(item)

    return {"success": True, "data": out}


# ─── 3. ISSUE VIEW URL (302 redirect) ─────────────────────────────────
@router.get("/{tai_lieu_id}/xem", summary="Sinh URL xem tài liệu (1h)")
async def xem_tai_lieu(
    tai_lieu_id: UUID,
    db: DatabaseDep,
    user: CurrentUserDep,
):
    """
    Sinh URL ngắn hạn để client GET /xem-noi-dung. Audit VIEW_DOC.
    """
    service = TaiLieuService(db)
    tl = await service.get(tai_lieu_id)

    # Check user xem được cuộc họp chứa tài liệu không
    from meeting_service.dependencies import _can_view_cuoc_hop
    from sqlalchemy import select
    from meeting_service.models.cuoc_hop import CuocHop as CuocHopModel
    res = await db.execute(
        select(CuocHopModel).where(CuocHopModel.id == tl.cuoc_hop_id)
    )
    ch = res.scalar_one_or_none()
    if ch is None or not await _can_view_cuoc_hop(ch, user, db):
        raise HTTPException(
            status_code=403,
            detail={"success": False, "error": {"code": "NO_PERMISSION",
                    "message": "Không có quyền xem tài liệu này"}},
        )

    await service.audit_view(tl, UUID(user.sub))

    token = issue_token(
        purpose=PURPOSE_VIEW_DOC,
        subject=str(tl.id),
        extra_claims={"viewer_id": user.sub},
        ttl_seconds=3600,
    )
    return {
        "success": True,
        "data": {
            "url": f"/api/v1/hop-khong-giay/tai-lieu/{tl.id}/xem-noi-dung?t={token}",
            "expires_in_seconds": 3600,
        },
    }


# ─── 4. DOWNLOAD URL ──────────────────────────────────────────────────
@router.get("/{tai_lieu_id}/tai", summary="Sinh URL tải tài liệu")
async def tai_tai_lieu(
    tai_lieu_id: UUID,
    db: DatabaseDep,
    user: CurrentUserDep,
):
    service = TaiLieuService(db)
    tl = await service.get(tai_lieu_id)

    if not tl.cho_phep_tai:
        raise HTTPException(
            status_code=403,
            detail={"success": False, "error": {"code": "DOWNLOAD_DISABLED",
                    "message": "Tài liệu không cho phép tải về"}},
        )

    # View permission cũng phải có
    from meeting_service.dependencies import _can_view_cuoc_hop
    from sqlalchemy import select
    from meeting_service.models.cuoc_hop import CuocHop as CuocHopModel
    res = await db.execute(select(CuocHopModel).where(CuocHopModel.id == tl.cuoc_hop_id))
    ch = res.scalar_one_or_none()
    if ch is None or not await _can_view_cuoc_hop(ch, user, db):
        raise HTTPException(
            status_code=403,
            detail={"success": False, "error": {"code": "NO_PERMISSION",
                    "message": "Không có quyền tải tài liệu này"}},
        )

    await service.audit_download(tl, UUID(user.sub))

    token = issue_token(
        purpose=PURPOSE_DOWNLOAD_DOC,
        subject=str(tl.id),
        extra_claims={"viewer_id": user.sub},
        ttl_seconds=3600,
    )
    return {
        "success": True,
        "data": {
            "url": f"/api/v1/hop-khong-giay/tai-lieu/{tl.id}/tai-noi-dung?t={token}",
            "expires_in_seconds": 3600,
        },
    }


# ─── 5. SOFT DELETE ───────────────────────────────────────────────────
@router.delete("/{tai_lieu_id}", summary="Xóa tài liệu (soft delete)")
async def xoa_tai_lieu(
    tai_lieu_id: UUID,
    db: DatabaseDep,
    user: CurrentUserDep,
):
    service = TaiLieuService(db)
    tl = await service.get(tai_lieu_id)

    # Check edit permission via cuoc_hop
    from sqlalchemy import select
    from meeting_service.models.cuoc_hop import CuocHop as CuocHopModel
    res = await db.execute(select(CuocHopModel).where(CuocHopModel.id == tl.cuoc_hop_id))
    ch = res.scalar_one_or_none()
    if ch is None:
        raise HTTPException(404)
    user_id = UUID(user.sub)
    if not (
        user.is_admin or user.vai_tro in ("SUPER_ADMIN", "ADMIN")
        or "TRUONG_CNTT" in (user.platform_roles or [])
        or ch.chu_toa_id == user_id or ch.thu_ky_id == user_id
    ):
        raise HTTPException(
            status_code=403,
            detail={"success": False, "error": {"code": "NO_PERMISSION",
                    "message": "Bạn không có quyền xóa tài liệu này"}},
        )

    await service.soft_delete(tl, user)
    return {"success": True, "data": {"id": str(tl.id), "is_deleted": True}}


# ─── 6. SERVE FILE NỘI DUNG (gateway) ─────────────────────────────────
@router.get(
    "/{tai_lieu_id}/xem-noi-dung",
    summary="Serve file nội dung — yêu cầu short-lived token",
    response_class=FileResponse,
)
async def serve_view(
    tai_lieu_id: UUID,
    db: DatabaseDep,
    t: str = Query(..., description="Short-lived token từ /xem"),
):
    """Serve file để xem inline. KHÔNG audit (audit đã ghi ở /xem)."""
    payload = verify_token(t, expected_purpose=PURPOSE_VIEW_DOC)
    if payload.get("sub") != str(tai_lieu_id):
        raise HTTPException(
            status_code=401,
            detail={"success": False, "error": {"code": "TOKEN_MISMATCH",
                    "message": "Token không đúng tài liệu"}},
        )

    service = TaiLieuService(db)
    tl = await service.get(tai_lieu_id)

    storage = StorageService()
    if not storage.file_exists(tl.minio_key):
        raise HTTPException(
            status_code=404,
            detail={"success": False, "error": {"code": "FILE_NOT_FOUND",
                    "message": "File vật lý không tồn tại"}},
        )

    source_path = storage.resolve_path(tl.minio_key)

    # Browser không render native được Office formats — convert sang PDF rồi
    # serve inline. Cache PDF tại _preview_cache/<id>.pdf.
    if is_office_extension(tl.extension):
        try:
            pdf_path = await ensure_pdf_preview(str(tl.id), source_path)
        except RuntimeError as e:
            raise HTTPException(
                status_code=503,
                detail={"success": False, "error": {
                    "code": "PREVIEW_UNAVAILABLE",
                    "message": f"Không thể chuyển đổi file sang PDF: {e}",
                }},
            )
        return FileResponse(
            path=pdf_path,
            media_type="application/pdf",
            filename=f"{tl.ten_tai_lieu}.pdf",
            content_disposition_type="inline",
        )

    return FileResponse(
        path=source_path,
        media_type=tl.mime_type or "application/octet-stream",
        filename=tl.ten_tai_lieu,
        content_disposition_type="inline",
    )


@router.get(
    "/{tai_lieu_id}/tai-noi-dung",
    summary="Serve file để tải xuống — yêu cầu short-lived token",
    response_class=FileResponse,
)
async def serve_download(
    tai_lieu_id: UUID,
    db: DatabaseDep,
    t: str = Query(...),
):
    payload = verify_token(t, expected_purpose=PURPOSE_DOWNLOAD_DOC)
    if payload.get("sub") != str(tai_lieu_id):
        raise HTTPException(
            status_code=401,
            detail={"success": False, "error": {"code": "TOKEN_MISMATCH",
                    "message": "Token không đúng tài liệu"}},
        )

    service = TaiLieuService(db)
    tl = await service.get(tai_lieu_id)

    if not tl.cho_phep_tai:
        raise HTTPException(
            status_code=403,
            detail={"success": False, "error": {"code": "DOWNLOAD_DISABLED",
                    "message": "Tài liệu không cho phép tải về"}},
        )

    storage = StorageService()
    if not storage.file_exists(tl.minio_key):
        raise HTTPException(
            status_code=404,
            detail={"success": False, "error": {"code": "FILE_NOT_FOUND",
                    "message": "File vật lý không tồn tại"}},
        )

    return FileResponse(
        path=storage.resolve_path(tl.minio_key),
        media_type="application/octet-stream",
        filename=tl.ten_tai_lieu,
    )
