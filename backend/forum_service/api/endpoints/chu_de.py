"""
forum_service/api/endpoints/chu_de.py
======================================
Endpoints CRUD Chu de / Thread.

DAY LA ENDPOINT PHUC TAP NHAT cua Forum module.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from forum_service.dependencies import (
    CurrentUserDep,
    DatabaseDep,
    get_current_user,
    get_db,
    require_platform_role,
)
from forum_service.schemas.chu_de import (
    ChonDapAnChuan,
    ChuDeCreate,
    ChuDeDetail,
    ChuDeListItem,
    ChuDeUpdate,
    HanhDongChuDe,
)
from forum_service.schemas.tra_loi import TraLoiCreate, TraLoiResponse
from forum_service.services import chu_de_service, theo_doi_service, tra_loi_service
from shared.auth import TokenPayload

router = APIRouter(prefix="/chu-de", tags=["Chủ đề"])


@router.get("")
async def danh_sach_chu_de(
    db: DatabaseDep,
    current_user: CurrentUserDep,
    chuyen_muc_id: Optional[UUID] = Query(default=None),
    trang_thai: Optional[str] = Query(default=None),
    tags: Optional[str] = Query(default=None),
    search: Optional[str] = Query(default=None),
    sap_xep: str = Query(default="moi_nhat"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> dict:
    """
    Lay danh sach chu de voi filter + phan trang.

    Phan quyen:
      - CBCC: chi xem chu de trang_thai IN ('MO', 'DONG')
      - DIEU_PHOI: xem tat ca ('CHO_DUYET', 'MO', 'DONG', 'AN')

    Query params:
      - chuyen_muc_id: filter theo chuyen muc
      - trang_thai: filter theo trang thai
      - tags: comma-separated tags (VD: "haiquan,thue")
      - search: full-text search
      - sap_xep: moi_nhat | nhieu_upvote | nhieu_tra_loi
    """
    # Parse tags from comma-separated string
    tags_list = None
    if tags:
        tags_list = [t.strip() for t in tags.split(",") if t.strip()]

    result = await chu_de_service.danh_sach(
        db=db,
        user=current_user,
        chuyen_muc_id=chuyen_muc_id,
        trang_thai=trang_thai,
        tags=tags_list,
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


@router.get("/{chu_de_id}")
async def chi_tiet_chu_de(
    chu_de_id: UUID,
    db: DatabaseDep,
    current_user: CurrentUserDep,
) -> dict:
    """
    Lay chi tiet chu de.
    Side effect: tang so_luot_xem += 1.
    Build nested tra loi tree, da_upvote, da_theo_doi.
    """
    data = await chu_de_service.chi_tiet(
        db=db,
        chu_de_id=chu_de_id,
        user=current_user,
    )
    return {
        "success": True,
        "data": data,
        "message": "Lay chi tiet chu de thanh cong",
    }


@router.post("", status_code=status.HTTP_201_CREATED)
async def tao_chu_de(
    data: ChuDeCreate,
    db: DatabaseDep,
    current_user: CurrentUserDep,
) -> dict:
    """
    Tao chu de moi.

    Quy tac:
      - Validate chuyen_muc exists
      - Neu chuyen_muc.chi_doc = TRUE → require CHUYEN_GIA/DIEU_PHOI
      - trang_thai: CHO_DUYET neu chuyen_muc.yeu_cau_duyet else MO
      - Auto tao TheoDoi cho author
    """
    result = await chu_de_service.tao(
        db=db,
        data=data.model_dump(),
        user=current_user,
    )
    return {
        "success": True,
        "data": result,
        "message": "Tao chu de thanh cong",
    }


@router.put("/{chu_de_id}")
async def sua_chu_de(
    chu_de_id: UUID,
    data: ChuDeUpdate,
    db: DatabaseDep,
    current_user: CurrentUserDep,
) -> dict:
    """
    Cap nhat chu de.

    Quy tac:
      - Author: chi trong 24h sau khi tao
      - DIEU_PHOI/SUPER_ADMIN: luon duoc sua
    """
    result = await chu_de_service.sua(
        db=db,
        chu_de_id=chu_de_id,
        data=data.model_dump(exclude_unset=True),
        user=current_user,
    )
    return {
        "success": True,
        "data": result,
        "message": "Cap nhat chu de thanh cong",
    }


@router.delete("/{chu_de_id}")
async def xoa_chu_de(
    chu_de_id: UUID,
    db: DatabaseDep,
    current_user: CurrentUserDep,
) -> dict:
    """
    Xoa chu de (soft delete).

    Quy tac:
      - Author: reject neu so_tra_loi > 0
      - DIEU_PHOI/SUPER_ADMIN: luon duoc xoa
    """
    await chu_de_service.xoa(
        db=db,
        chu_de_id=chu_de_id,
        user=current_user,
    )
    return {
        "success": True,
        "data": None,
        "message": "Xoa chu de thanh cong",
    }


@router.patch("/{chu_de_id}/hanh-dong")
async def hanh_dong_chu_de(
    chu_de_id: UUID,
    data: HanhDongChuDe,
    db: DatabaseDep,
    current_user: TokenPayload = Depends(require_platform_role("DIEU_PHOI_FORUM")),
) -> dict:
    """
    Hanh dong dieu phoi: GHIM, BO_GHIM, KHOA, MO_KHOA, DUYET, AN.
    Yeu cau: DIEU_PHOI_FORUM hoac SUPER_ADMIN.

    GHIM: Set is_ghim = True (max 3 chu de ghim/chuyen_muc)
    BO_GHIM: Set is_ghim = False
    KHOA: Set is_khoa = True (khong cho tra loi moi)
    MO_KHOA: Set is_khoa = False
    DUYET: Chuyen CHO_DUYET → MO
    AN: Set trang_thai = AN
    """
    result = await chu_de_service.hanh_dong(
        db=db,
        chu_de_id=chu_de_id,
        user=current_user,
        hanh_dong=data.hanh_dong,
        ly_do=data.ly_do,
    )
    return {
        "success": True,
        "data": result,
        "message": result["message"],
    }


@router.patch("/{chu_de_id}/dap-an-chuan")
async def chon_dap_an_chuan(
    chu_de_id: UUID,
    data: ChonDapAnChuan,
    db: DatabaseDep,
    current_user: CurrentUserDep,
) -> dict:
    """
    Chon 1 tra loi lam dap an chuan.

    Quy tac:
      - Author OR CHUYEN_GIA OR DIEU_PHOI OR SUPER_ADMIN
      - Validate tra_loi thuoc chu_de nay
      - Neu da co dap an chuan cu → unset cu, set moi
    """
    result = await chu_de_service.chon_dap_an_chuan(
        db=db,
        chu_de_id=chu_de_id,
        tra_loi_id=data.tra_loi_id,
        user=current_user,
    )
    return {
        "success": True,
        "data": result,
        "message": result["message"],
    }


@router.post("/{chu_de_id}/tra-loi", status_code=status.HTTP_201_CREATED)
async def tao_tra_loi(
    chu_de_id: UUID,
    data: TraLoiCreate,
    db: DatabaseDep,
    current_user: CurrentUserDep,
) -> dict:
    """
    Tao tra loi moi cho chu de.

    Quy tac:
      - Validate chu_de exists, not locked (is_khoa)
      - Handle nested reply: neu parent_id la level-2 → flatten to level-1
      - Tang chu_de.so_tra_loi += 1
      - Auto tao TheoDoi cho responder
    """
    result = await tra_loi_service.tao(
        db=db,
        chu_de_id=chu_de_id,
        data=data.model_dump(),
        user=current_user,
    )
    return {
        "success": True,
        "data": result,
        "message": "Tao tra loi thanh cong",
    }


@router.post("/{chu_de_id}/theo-doi")
async def theo_doi_chu_de(
    chu_de_id: UUID,
    db: DatabaseDep,
    current_user: CurrentUserDep,
) -> dict:
    """Theo doi chu de (idempotent)."""
    result = await theo_doi_service.theo_doi(
        db=db,
        chu_de_id=chu_de_id,
        user=current_user,
    )
    return {
        "success": True,
        "data": result,
        "message": result["message"],
    }


@router.delete("/{chu_de_id}/theo-doi")
async def bo_theo_doi_chu_de(
    chu_de_id: UUID,
    db: DatabaseDep,
    current_user: CurrentUserDep,
) -> dict:
    """Bo theo doi chu de."""
    result = await theo_doi_service.bo_theo_doi(
        db=db,
        chu_de_id=chu_de_id,
        user=current_user,
    )
    return {
        "success": True,
        "data": result,
        "message": result["message"],
    }
