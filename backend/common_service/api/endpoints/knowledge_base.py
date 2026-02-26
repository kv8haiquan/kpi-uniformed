"""
common_service/api/endpoints/knowledge_base.py
================================================
Public API cho Knowledge Base (SOP/FAQ).
Prefix: /api/common/v1/knowledge-base
Auth: JWT Bearer token

Endpoints:
  GET    /knowledge-base                  — Danh sach + search
  GET    /knowledge-base/{id}             — Chi tiet
  POST   /knowledge-base                  — Tao (CHUYEN_GIA, QT_NOI_DUNG, ADMIN)
  PUT    /knowledge-base/{id}             — Sua (chu so huu, QT_NOI_DUNG, ADMIN)
  DELETE /knowledge-base/{id}             — Xoa (chu so huu, QT_NOI_DUNG, ADMIN)
  PATCH  /knowledge-base/{id}/trang-thai  — Doi trang thai
"""

from __future__ import annotations

import math
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query

from common_service.dependencies import CurrentUserDep, DatabaseDep, require_platform_role
from common_service.schemas.base import PaginatedResponse, PaginationInfo, SuccessResponse
from common_service.schemas.knowledge_base import (
    KBCreate,
    KBDoiTrangThai,
    KBListItem,
    KBResponse,
    KBUpdate,
)
from common_service.services import knowledge_base_service

router = APIRouter(prefix="/knowledge-base", tags=["Knowledge Base"])


def _user_roles(user) -> set[str]:
    """Extract platform roles tu user token."""
    return set(user.platform_roles or [])


def _is_admin(user) -> bool:
    """Check admin status."""
    return user.vai_tro == "SUPER_ADMIN" or user.is_admin


@router.get("", response_model=PaginatedResponse[KBListItem])
async def danh_sach(
    db: DatabaseDep,
    user: CurrentUserDep,
    loai: Optional[str] = Query(default=None, description="SOP hoac FAQ"),
    chuyen_de: Optional[str] = Query(default=None, description="Loc theo chuyen de"),
    tags: Optional[str] = Query(default=None, description="Loc theo tag"),
    trang_thai: Optional[str] = Query(default=None, description="NHAP, CHO_DUYET, DA_XUAT_BAN, CAN_CAP_NHAT"),
    search: Optional[str] = Query(default=None, description="Full-text search"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    """Danh sach Knowledge Base — ho tro full-text search.

    Tat ca CBCC xem bai DA_XUAT_BAN.
    CHUYEN_GIA, QT_NOI_DUNG, ADMIN xem duoc tat ca trang thai.
    """
    items, total = await knowledge_base_service.danh_sach(
        db, user.sub, _user_roles(user),
        is_admin=_is_admin(user),
        loai=loai,
        chuyen_de=chuyen_de,
        tags=tags,
        trang_thai=trang_thai,
        search=search,
        page=page,
        page_size=page_size,
    )

    return PaginatedResponse(
        data=[KBListItem.model_validate(kb) for kb in items],
        pagination=PaginationInfo(
            page=page,
            page_size=page_size,
            total_items=total,
            total_pages=max(1, math.ceil(total / page_size)),
        ),
    )


@router.get("/{kb_id}", response_model=SuccessResponse[KBResponse])
async def chi_tiet(
    kb_id: uuid.UUID,
    db: DatabaseDep,
    user: CurrentUserDep,
):
    """Chi tiet Knowledge Base — bao gom lien ket cheo."""
    kb = await knowledge_base_service.chi_tiet(db, kb_id)
    return SuccessResponse(data=KBResponse.model_validate(kb))


@router.post(
    "",
    response_model=SuccessResponse[KBResponse],
    status_code=201,
)
async def tao(
    data: KBCreate,
    db: DatabaseDep,
    user=Depends(require_platform_role("CHUYEN_GIA", "DIEU_PHOI_FORUM", "QT_NOI_DUNG")),
):
    """Tao Knowledge Base moi.

    Quyen: CHUYEN_GIA, DIEU_PHOI_FORUM, QT_NOI_DUNG, ADMIN.
    Trang thai ban dau: NHAP.
    """
    kb = await knowledge_base_service.tao(db, data, user.sub)
    return SuccessResponse(
        data=KBResponse.model_validate(kb),
        message="Tạo Knowledge Base thành công",
    )


@router.put("/{kb_id}", response_model=SuccessResponse[KBResponse])
async def sua(
    kb_id: uuid.UUID,
    data: KBUpdate,
    db: DatabaseDep,
    user: CurrentUserDep,
):
    """Sua Knowledge Base.

    Quyen: chu so huu, QT_NOI_DUNG, ADMIN.
    Neu sua noi_dung → phien_ban tang 1.
    """
    kb = await knowledge_base_service.sua(
        db, kb_id, data, user.sub,
        is_admin=_is_admin(user),
        user_roles=_user_roles(user),
    )
    return SuccessResponse(
        data=KBResponse.model_validate(kb),
        message="Cập nhật thành công",
    )


@router.delete("/{kb_id}", response_model=SuccessResponse[dict])
async def xoa(
    kb_id: uuid.UUID,
    db: DatabaseDep,
    user: CurrentUserDep,
):
    """Xoa Knowledge Base (soft delete).

    Quyen: chu so huu, QT_NOI_DUNG, ADMIN.
    """
    await knowledge_base_service.xoa(
        db, kb_id, user.sub,
        is_admin=_is_admin(user),
        user_roles=_user_roles(user),
    )
    return SuccessResponse(
        data={"deleted": True},
        message="Đã xóa Knowledge Base",
    )


@router.patch("/{kb_id}/trang-thai", response_model=SuccessResponse[KBResponse])
async def doi_trang_thai(
    kb_id: uuid.UUID,
    body: KBDoiTrangThai,
    db: DatabaseDep,
    user: CurrentUserDep,
):
    """Doi trang thai Knowledge Base.

    Workflow:
      NHAP → CHO_DUYET (chu so huu gui duyet)
      CHO_DUYET → DA_XUAT_BAN (QT_NOI_DUNG duyet)
      CHO_DUYET → NHAP (QT_NOI_DUNG tu choi)
      DA_XUAT_BAN → CAN_CAP_NHAT
      CAN_CAP_NHAT → NHAP
    """
    kb = await knowledge_base_service.doi_trang_thai(
        db, kb_id, body.trang_thai_moi, user.sub,
        is_admin=_is_admin(user),
        user_roles=_user_roles(user),
    )
    return SuccessResponse(
        data=KBResponse.model_validate(kb),
        message=f"Đã chuyển sang {body.trang_thai_moi}",
    )
