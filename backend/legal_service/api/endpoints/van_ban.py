"""
legal_service/api/endpoints/van_ban.py
========================================
Endpoints Van Ban phap luat.

QUAN TRONG: Cac route co static path (/chua-doc, /quan-ly) phai duoc
dang ky TRUOC route co path parameter (/{id}) de tranh conflict.

GET    /van-ban                  — danh sach VB xuat ban (login required)
GET    /van-ban/chua-doc         — VB bat_buoc_doc chua xac nhan (login)
GET    /van-ban/quan-ly          — danh sach quan ly (BIEN_TAP, QT_NOI_DUNG)
GET    /van-ban/{id}             — chi tiet VB (login)
POST   /van-ban                  — tao VB moi (BIEN_TAP, QT_NOI_DUNG)
PUT    /van-ban/{id}             — sua VB (BIEN_TAP, QT_NOI_DUNG)
PATCH  /van-ban/{id}/trang-thai  — cap nhat trang thai duyet
DELETE /van-ban/{id}             — xoa VB (QT_NOI_DUNG)
GET    /van-ban/{id}/download    — redirect file_goc_url (login)
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from legal_service.dependencies import (
    CurrentUserDep,
    DatabaseDep,
    get_current_user,
    get_db,
    require_platform_role,
)
from legal_service.models.van_ban import VanBan
from legal_service.schemas.van_ban import (
    TrangThaiDuyetUpdate,
    VanBanCreate,
    VanBanUpdate,
)
from legal_service.services import van_ban_service
from legal_service.services.file_service import LegalFileService
from shared.auth import TokenPayload

router = APIRouter(tags=["Van Ban"])


@router.get("/van-ban/chua-doc")
async def lay_van_ban_chua_doc(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user),
) -> dict:
    """
    Lay danh sach van ban bat_buoc_doc ma user chua xac nhan.
    Sap xep: KHAN → QUAN_TRONG → BINH_THUONG → han_xac_nhan ASC.
    """
    result = await van_ban_service.danh_sach_chua_doc(
        db=db,
        user_id=current_user.sub,
        page=page,
        page_size=page_size,
    )
    return {
        "success": True,
        "data": result["items"],
        "pagination": result["pagination"],
    }


@router.get("/van-ban/quan-ly")
async def lay_danh_sach_quan_ly(
    trang_thai_duyet: Optional[str] = Query(default=None),
    loai_van_ban_id: Optional[UUID] = Query(default=None),
    search: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_platform_role("BIEN_TAP", "QT_NOI_DUNG")),
) -> dict:
    """
    Lay danh sach van ban cho quan ly.
    BIEN_TAP: chi xem VB cua minh.
    QT_NOI_DUNG: xem tat ca.
    """
    result = await van_ban_service.danh_sach_quan_ly(
        db=db,
        user=current_user,
        trang_thai_duyet=trang_thai_duyet,
        loai_van_ban_id=loai_van_ban_id,
        search=search,
        page=page,
        page_size=page_size,
    )
    return {
        "success": True,
        "data": result["items"],
        "pagination": result["pagination"],
    }


@router.get("/van-ban")
async def lay_danh_sach_van_ban(
    loai_van_ban_id: Optional[UUID] = Query(default=None),
    trang_thai_hieu_luc: Optional[str] = Query(default=None),
    muc_do: Optional[str] = Query(default=None),
    bat_buoc_doc: Optional[bool] = Query(default=None),
    chuyen_de: Optional[str] = Query(default=None),
    search: Optional[str] = Query(default=None),
    sap_xep: str = Query(default="moi_nhat"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user),
) -> dict:
    """Lay danh sach van ban da xuat ban voi filters."""
    result = await van_ban_service.danh_sach(
        db=db,
        user_id=current_user.sub,
        loai_van_ban_id=loai_van_ban_id,
        trang_thai_hieu_luc=trang_thai_hieu_luc,
        muc_do=muc_do,
        bat_buoc_doc=bat_buoc_doc,
        chuyen_de=chuyen_de,
        search=search,
        sap_xep=sap_xep,
        page=page,
        page_size=page_size,
    )
    return {
        "success": True,
        "data": result["items"],
        "pagination": result["pagination"],
    }


@router.get("/van-ban/{van_ban_id}")
async def lay_chi_tiet_van_ban(
    van_ban_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user),
) -> dict:
    """
    Lay chi tiet van ban.
    Side effect: ghi nhan da_doc=TRUE khi CBCC mo xem.
    """
    data = await van_ban_service.chi_tiet(db=db, user=current_user, van_ban_id=van_ban_id)
    return {
        "success": True,
        "data": data,
        "message": "Lay chi tiet van ban thanh cong",
    }


@router.post("/van-ban")
async def tao_van_ban(
    data: VanBanCreate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_platform_role("BIEN_TAP", "QT_NOI_DUNG")),
) -> dict:
    """Tao van ban moi. Yeu cau: BIEN_TAP hoac QT_NOI_DUNG."""
    result = await van_ban_service.tao_van_ban(db=db, user=current_user, data=data)
    return {
        "success": True,
        "data": result,
        "message": "Tao van ban thanh cong",
    }


@router.put("/van-ban/{van_ban_id}")
async def sua_van_ban(
    van_ban_id: UUID,
    data: VanBanUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_platform_role("BIEN_TAP", "QT_NOI_DUNG")),
) -> dict:
    """Cap nhat van ban. BIEN_TAP chi sua VB cua minh."""
    result = await van_ban_service.sua_van_ban(
        db=db,
        user=current_user,
        van_ban_id=van_ban_id,
        data=data,
    )
    return {
        "success": True,
        "data": result,
        "message": "Cap nhat van ban thanh cong",
    }


@router.patch("/van-ban/{van_ban_id}/trang-thai")
async def cap_nhat_trang_thai_van_ban(
    van_ban_id: UUID,
    data: TrangThaiDuyetUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user),
) -> dict:
    """
    Cap nhat trang thai duyet van ban theo workflow.
    - BIEN_TAP: gui duyet (NHAP → CHO_DUYET)
    - QT_NOI_DUNG: duyet, tu choi, xuat ban, thu hoi
    - Lanh dao: xuat ban (DA_DUYET → DA_XUAT_BAN)
    """
    result = await van_ban_service.cap_nhat_trang_thai(
        db=db,
        user=current_user,
        van_ban_id=van_ban_id,
        data=data,
    )
    return {
        "success": True,
        "data": result,
        "message": "Cap nhat trang thai thanh cong",
    }


@router.delete("/van-ban/{van_ban_id}")
async def xoa_van_ban(
    van_ban_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_platform_role("QT_NOI_DUNG")),
) -> dict:
    """Xoa van ban (soft delete). Chi xoa duoc VB o trang thai NHAP."""
    await van_ban_service.xoa_van_ban(db=db, user=current_user, van_ban_id=van_ban_id)
    return {
        "success": True,
        "data": None,
        "message": "Xoa van ban thanh cong",
    }


@router.post("/van-ban/{van_ban_id}/upload-file")
async def upload_file_van_ban(
    van_ban_id: UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_platform_role("BIEN_TAP", "QT_NOI_DUNG")),
) -> dict:
    """
    Upload file PDF/DOCX dinh kem cho van ban.
    - BIEN_TAP: chi upload VB cua minh (trang thai NHAP hoac CHO_DUYET)
    - QT_NOI_DUNG: upload bat ky VB nao
    File cu se bi xoa truoc khi luu file moi.
    """
    # Lay van ban tu DB
    result = await db.execute(
        select(VanBan).where(VanBan.id == van_ban_id, VanBan.is_deleted.is_(False))
    )
    vb = result.scalar_one_or_none()
    if not vb:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": {"code": "LEGAL_ERR_001", "message": "Khong tim thay van ban"},
            },
        )

    # Kiem tra quyen: BIEN_TAP chi upload VB cua minh
    is_qt_noi_dung = "QT_NOI_DUNG" in (current_user.platform_roles or [])
    is_admin = current_user.vai_tro == "SUPER_ADMIN"
    if not is_qt_noi_dung and not is_admin:
        if str(vb.nguoi_nhap_id) != current_user.sub:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "success": False,
                    "error": {
                        "code": "AUTH_002",
                        "message": "Ban khong co quyen upload file cho van ban nay",
                    },
                },
            )

    # Luu file moi (service tu validate ext va size)
    svc = LegalFileService()
    old_url = vb.file_goc_url
    file_info = await svc.save_file(file)

    # Xoa file cu neu co
    if old_url:
        await svc.delete_file(old_url)

    # Cap nhat DB
    vb.file_goc_url = file_info["file_url"]
    await db.commit()

    return {
        "success": True,
        "data": {
            "file_url": file_info["file_url"],
            "file_name": file_info["file_name"],
            "file_size": file_info["file_size"],
        },
        "message": "Upload file thanh cong",
    }


@router.get("/van-ban/{van_ban_id}/download")
async def tai_van_ban(
    van_ban_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user),
):
    """Redirect den file goc cua van ban (PDF/Word tren MinIO)."""
    # Lay chi tiet VB (co side effect ghi nhan da_doc)
    detail = await van_ban_service.chi_tiet(db=db, user=current_user, van_ban_id=van_ban_id)
    file_url = detail.get("file_goc_url")

    if not file_url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": {
                    "code": "LEGAL_ERR_010",
                    "message": "Van ban nay khong co file dinh kem",
                },
            },
        )

    return RedirectResponse(url=file_url, status_code=302)
