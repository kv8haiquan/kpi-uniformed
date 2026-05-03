"""
api/endpoints/bien_ban.py
==========================
Module 9 — Biên bản + Mock CKS.

Routes:
- GET   /cuoc-hop/{id}/bien-ban
- PUT   /cuoc-hop/{id}/bien-ban
- POST  /bien-ban/{id}/trinh-ky
- POST  /bien-ban/{id}/ky
- POST  /bien-ban/{id}/xuat?dinh-dang={docx|pdf}
- GET   /bien-ban/{id}/file?dinh-dang={docx|pdf}  (gateway)
"""

from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse

from meeting_service.config import settings
from meeting_service.dependencies import (
    CurrentUserDep,
    DatabaseDep,
    require_can_view_meeting,
)
from meeting_service.models.cuoc_hop import CuocHop
from meeting_service.schemas.bien_ban import (
    BienBanResponse,
    BienBanUpdate,
    XuatBienBanResponse,
)
from meeting_service.services.bien_ban_service import BienBanService


router = APIRouter(prefix="/bien-ban", tags=["Biên bản"])
router_cuoc_hop = APIRouter(prefix="/cuoc-hop", tags=["Biên bản"])


# ─── GET / PUT theo cuoc_hop ──────────────────────────────────────────
@router_cuoc_hop.get(
    "/{cuoc_hop_id}/bien-ban",
    summary="Đọc biên bản (auto-fill nếu chưa có)",
)
async def get_bien_ban(
    db: DatabaseDep,
    user: CurrentUserDep,
    ch: CuocHop = Depends(require_can_view_meeting),
):
    service = BienBanService(db)
    bb = await service.get_or_init(ch.id, user)
    return {
        "success": True,
        "data": BienBanResponse.model_validate(bb).model_dump(mode="json"),
    }


@router_cuoc_hop.put(
    "/{cuoc_hop_id}/bien-ban",
    summary="Lưu nội dung biên bản (Thư ký)",
)
async def update_bien_ban(
    payload: BienBanUpdate,
    db: DatabaseDep,
    user: CurrentUserDep,
    ch: CuocHop = Depends(require_can_view_meeting),  # tạm — service tự check soạn-permission
):
    # Verify thư ký
    user_id = UUID(user.sub)
    if not (
        user.is_admin or user.vai_tro in ("SUPER_ADMIN", "ADMIN")
        or ch.thu_ky_id == user_id or ch.chu_toa_id == user_id
    ):
        raise HTTPException(
            status_code=403,
            detail={"success": False, "error": {"code": "NO_PERMISSION",
                    "message": "Chỉ thư ký/chủ tọa được sửa biên bản"}},
        )

    service = BienBanService(db)
    bb = await service.update(ch.id, payload.noi_dung_json, payload.noi_dung_html, user)
    return {
        "success": True,
        "data": BienBanResponse.model_validate(bb).model_dump(mode="json"),
    }


# ─── ACTIONS theo bien_ban ────────────────────────────────────────────
@router.post("/{bien_ban_id}/trinh-ky", summary="Thư ký trình biên bản chờ ký")
async def trinh_ky(
    bien_ban_id: UUID,
    db: DatabaseDep,
    user: CurrentUserDep,
):
    service = BienBanService(db)
    bb = await service.trinh_ky(bien_ban_id, user)
    return {
        "success": True,
        "data": BienBanResponse.model_validate(bb).model_dump(mode="json"),
    }


@router.post(
    "/{bien_ban_id}/ky",
    summary="Chủ tọa ký biên bản (Mock CKS)",
)
async def ky(
    bien_ban_id: UUID,
    db: DatabaseDep,
    user: CurrentUserDep,
):
    service = BienBanService(db)
    bb = await service.ky_mock(bien_ban_id, user)
    return {
        "success": True,
        "data": BienBanResponse.model_validate(bb).model_dump(mode="json"),
    }


# ─── EXPORT ───────────────────────────────────────────────────────────
@router.post(
    "/{bien_ban_id}/xuat",
    summary="Xuất biên bản DOCX/PDF",
)
async def xuat(
    bien_ban_id: UUID,
    db: DatabaseDep,
    user: CurrentUserDep,
    dinh_dang: str = Query(..., regex="^(docx|pdf)$", alias="dinh-dang"),
):
    service = BienBanService(db)
    if dinh_dang == "docx":
        result = await service.xuat_docx(bien_ban_id, user)
    else:
        result = await service.xuat_pdf(bien_ban_id, user)
    return {"success": True, "data": result}


@router.get(
    "/{bien_ban_id}/file",
    summary="Tải file biên bản đã xuất",
    response_class=FileResponse,
)
async def tai_file(
    bien_ban_id: UUID,
    db: DatabaseDep,
    user: CurrentUserDep,
    dinh_dang: str = Query(..., regex="^(docx|pdf)$", alias="dinh-dang"),
):
    """Stream file đã xuất. Permission qua require_can_view_meeting (tự check)."""
    service = BienBanService(db)
    bb = await service._get(bien_ban_id)

    # View permission
    from sqlalchemy import select
    from meeting_service.dependencies import _can_view_cuoc_hop
    from meeting_service.models.cuoc_hop import CuocHop as CuocHopModel
    res = await db.execute(select(CuocHopModel).where(CuocHopModel.id == bb.cuoc_hop_id))
    ch = res.scalar_one_or_none()
    if ch is None or not await _can_view_cuoc_hop(ch, user, db):
        raise HTTPException(
            status_code=403,
            detail={"success": False, "error": {"code": "NO_PERMISSION",
                    "message": "Không có quyền xem biên bản này"}},
        )

    key = bb.file_pdf_minio_key if dinh_dang == "pdf" else bb.file_docx_minio_key
    if not key:
        raise HTTPException(
            status_code=404,
            detail={"success": False, "error": {"code": "FILE_NOT_EXPORTED",
                    "message": f"Chưa xuất file {dinh_dang}"}},
        )
    full_path = Path(settings.upload_dir) / key
    if not full_path.is_file():
        raise HTTPException(
            status_code=404,
            detail={"success": False, "error": {"code": "FILE_NOT_FOUND",
                    "message": "File vật lý không tồn tại"}},
        )
    return FileResponse(
        path=full_path,
        media_type="application/pdf" if dinh_dang == "pdf" else "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=f"bien_ban_{bb.cuoc_hop_id}.{dinh_dang}",
    )
