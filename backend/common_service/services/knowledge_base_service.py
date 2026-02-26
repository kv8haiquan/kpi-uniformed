"""
common_service/services/knowledge_base_service.py
==================================================
Business logic cho Knowledge Base (SOP/FAQ).

Public methods:
  - danh_sach: tim kiem + phan trang
  - chi_tiet: lay 1 KB
  - tao: tao KB moi
  - sua: cap nhat KB
  - doi_trang_thai: chuyen trang thai workflow
  - xoa: soft delete

Internal methods:
  - danh_dau_can_cap_nhat: Legal goi khi VB thay doi
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from common_service.models.knowledge_base import KnowledgeBase
from common_service.schemas.knowledge_base import (
    KB_WORKFLOW,
    KBCreate,
    KBUpdate,
    LOAI_KB,
    TRANG_THAI_KB,
)

# Roles co quyen tao/quan ly KB
KB_MANAGER_ROLES = {"CHUYEN_GIA", "DIEU_PHOI_FORUM", "QT_NOI_DUNG"}
# Roles co quyen duyet KB
KB_APPROVER_ROLES = {"QT_NOI_DUNG"}
# Roles co quyen xem tat ca trang thai
KB_VIEW_ALL_ROLES = {"CHUYEN_GIA", "QT_NOI_DUNG"}


# ---------------------------------------------------------------------------
# Public methods
# ---------------------------------------------------------------------------


async def danh_sach(
    db: AsyncSession,
    user_id: str,
    user_roles: set[str],
    *,
    is_admin: bool = False,
    loai: Optional[str] = None,
    chuyen_de: Optional[str] = None,
    tags: Optional[str] = None,
    trang_thai: Optional[str] = None,
    search: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[KnowledgeBase], int]:
    """Tim kiem va phan trang Knowledge Base.

    - Tat ca CBCC xem duoc bai DA_XUAT_BAN
    - CHUYEN_GIA, QT_NOI_DUNG, ADMIN xem duoc tat ca trang thai
    - Sap xep: ts_rank (neu search) hoac updated_at DESC
    """
    conditions = [KnowledgeBase.is_deleted == False]  # noqa: E712

    # Phan quyen xem
    can_view_all = is_admin or bool(user_roles.intersection(KB_VIEW_ALL_ROLES))
    if not can_view_all:
        if trang_thai:
            # User thuong chi xem DA_XUAT_BAN hoac bai cua minh
            conditions.append(
                (KnowledgeBase.trang_thai == trang_thai)
                & (
                    (KnowledgeBase.trang_thai == "DA_XUAT_BAN")
                    | (KnowledgeBase.chu_so_huu_id == uuid.UUID(user_id))
                )
            )
        else:
            conditions.append(
                (KnowledgeBase.trang_thai == "DA_XUAT_BAN")
                | (KnowledgeBase.chu_so_huu_id == uuid.UUID(user_id))
            )
    else:
        if trang_thai:
            conditions.append(KnowledgeBase.trang_thai == trang_thai)

    # Loc theo loai
    if loai:
        conditions.append(KnowledgeBase.loai == loai)

    # Loc theo chuyen_de (JSONB contains)
    if chuyen_de:
        conditions.append(
            KnowledgeBase.chuyen_de.op("@>")(f'["{chuyen_de}"]')
        )

    # Loc theo tags (JSONB contains)
    if tags:
        conditions.append(
            KnowledgeBase.tags.op("@>")(f'["{tags}"]')
        )

    # Full-text search
    rank_col = None
    if search:
        ts_query = func.plainto_tsquery("simple", search)
        conditions.append(
            KnowledgeBase.search_vector.op("@@")(ts_query)
        )
        rank_col = func.ts_rank(KnowledgeBase.search_vector, ts_query).label("rank")

    # Dem tong
    count_q = select(func.count()).select_from(KnowledgeBase).where(*conditions)
    total = (await db.execute(count_q)).scalar() or 0

    # Query phan trang
    offset = (page - 1) * page_size
    if rank_col is not None:
        items_q = (
            select(KnowledgeBase)
            .where(*conditions)
            .order_by(rank_col.desc(), KnowledgeBase.updated_at.desc())
            .offset(offset)
            .limit(page_size)
        )
    else:
        items_q = (
            select(KnowledgeBase)
            .where(*conditions)
            .order_by(KnowledgeBase.updated_at.desc())
            .offset(offset)
            .limit(page_size)
        )

    result = await db.execute(items_q)
    items = list(result.scalars().all())
    return items, total


async def chi_tiet(
    db: AsyncSession,
    kb_id: uuid.UUID,
) -> KnowledgeBase:
    """Lay chi tiet 1 Knowledge Base.

    - 404 neu khong tim thay hoac da xoa
    """
    q = select(KnowledgeBase).where(
        KnowledgeBase.id == kb_id,
        KnowledgeBase.is_deleted == False,  # noqa: E712
    )
    result = await db.execute(q)
    kb = result.scalar_one_or_none()

    if kb is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": {
                    "code": "CMN_ERR_003",
                    "message": "Knowledge Base không tồn tại",
                },
            },
        )
    return kb


async def tao(
    db: AsyncSession,
    data: KBCreate,
    user_id: str,
) -> KnowledgeBase:
    """Tao Knowledge Base moi.

    - Validate loai (SOP/FAQ)
    - Gan chu_so_huu_id = user.id
    - trang_thai = NHAP
    """
    if data.loai not in LOAI_KB:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "error": {
                    "code": "CMN_ERR_004",
                    "message": f"Loại không hợp lệ: {data.loai}. Chấp nhận: {', '.join(sorted(LOAI_KB))}",
                },
            },
        )

    # Serialize UUID lists to strings for JSONB
    vb_lien_quan = [str(x) for x in data.van_ban_lien_quan] if data.van_ban_lien_quan else None
    cd_lien_quan = [str(x) for x in data.chu_de_forum_lien_quan] if data.chu_de_forum_lien_quan else None

    kb = KnowledgeBase(
        loai=data.loai,
        tieu_de=data.tieu_de,
        noi_dung=data.noi_dung,
        chuyen_de=data.chuyen_de,
        tags=data.tags,
        van_ban_lien_quan=vb_lien_quan,
        chu_de_forum_lien_quan=cd_lien_quan,
        chu_so_huu_id=uuid.UUID(user_id),
        trang_thai="NHAP",
    )
    db.add(kb)
    await db.flush()
    await db.refresh(kb)
    return kb


async def sua(
    db: AsyncSession,
    kb_id: uuid.UUID,
    data: KBUpdate,
    user_id: str,
    *,
    is_admin: bool = False,
    user_roles: set[str] = frozenset(),
) -> KnowledgeBase:
    """Cap nhat Knowledge Base.

    Quyen: chu so huu, QT_NOI_DUNG, ADMIN.
    Neu sua noi_dung → phien_ban += 1.
    """
    kb = await chi_tiet(db, kb_id)

    # Kiem tra quyen
    is_owner = str(kb.chu_so_huu_id) == user_id
    is_manager = is_admin or bool(user_roles.intersection(KB_APPROVER_ROLES))
    if not is_owner and not is_manager:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "error": {
                    "code": "PERM_001",
                    "message": "Bạn không có quyền sửa Knowledge Base này",
                },
            },
        )

    # Cap nhat cac field co gia tri
    update_data = data.model_dump(exclude_unset=True)
    noi_dung_changed = False

    for field, value in update_data.items():
        if field == "noi_dung" and value is not None:
            noi_dung_changed = True
        if field in ("van_ban_lien_quan", "chu_de_forum_lien_quan") and value is not None:
            # Serialize UUID lists to strings for JSONB
            value = [str(x) for x in value]
        setattr(kb, field, value)

    # Neu sua noi_dung → tang phien_ban
    if noi_dung_changed:
        kb.phien_ban += 1

    kb.ngay_cap_nhat_cuoi = datetime.utcnow()
    kb.updated_at = datetime.utcnow()
    await db.flush()
    await db.refresh(kb)
    return kb


async def doi_trang_thai(
    db: AsyncSession,
    kb_id: uuid.UUID,
    trang_thai_moi: str,
    user_id: str,
    *,
    is_admin: bool = False,
    user_roles: set[str] = frozenset(),
) -> KnowledgeBase:
    """Doi trang thai Knowledge Base theo workflow.

    Workflow:
      NHAP → CHO_DUYET          (chu so huu gui duyet)
      CHO_DUYET → DA_XUAT_BAN   (QT_NOI_DUNG duyet)
      CHO_DUYET → NHAP           (QT_NOI_DUNG tu choi)
      DA_XUAT_BAN → CAN_CAP_NHAT (tu dong hoac thu cong)
      CAN_CAP_NHAT → NHAP        (chu so huu sua lai)
    """
    kb = await chi_tiet(db, kb_id)

    # Validate trang_thai_moi
    if trang_thai_moi not in TRANG_THAI_KB:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "error": {
                    "code": "CMN_ERR_004",
                    "message": f"Trạng thái không hợp lệ: {trang_thai_moi}",
                },
            },
        )

    # Validate workflow transition
    allowed = KB_WORKFLOW.get(kb.trang_thai, set())
    if trang_thai_moi not in allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "error": {
                    "code": "CMN_ERR_004",
                    "message": f"Không thể chuyển từ {kb.trang_thai} sang {trang_thai_moi}. "
                    f"Cho phép: {', '.join(sorted(allowed)) if allowed else 'không có'}",
                },
            },
        )

    is_owner = str(kb.chu_so_huu_id) == user_id
    is_approver = is_admin or bool(user_roles.intersection(KB_APPROVER_ROLES))

    # Kiem tra quyen theo transition
    if trang_thai_moi == "CHO_DUYET":
        # Chi chu so huu gui duyet
        if not is_owner and not is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "success": False,
                    "error": {"code": "PERM_001", "message": "Chỉ chủ sở hữu mới có thể gửi duyệt"},
                },
            )
    elif trang_thai_moi in ("DA_XUAT_BAN", "NHAP") and kb.trang_thai == "CHO_DUYET":
        # Chi approver duyet/tu choi
        if not is_approver:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "success": False,
                    "error": {"code": "PERM_001", "message": "Chỉ QT_NOI_DUNG/ADMIN mới có thể duyệt"},
                },
            )

    kb.trang_thai = trang_thai_moi
    kb.updated_at = datetime.utcnow()
    await db.flush()
    await db.refresh(kb)
    return kb


async def xoa(
    db: AsyncSession,
    kb_id: uuid.UUID,
    user_id: str,
    *,
    is_admin: bool = False,
    user_roles: set[str] = frozenset(),
) -> KnowledgeBase:
    """Soft delete Knowledge Base.

    Quyen: chu so huu, QT_NOI_DUNG, ADMIN.
    """
    kb = await chi_tiet(db, kb_id)

    is_owner = str(kb.chu_so_huu_id) == user_id
    is_manager = is_admin or bool(user_roles.intersection(KB_APPROVER_ROLES))
    if not is_owner and not is_manager:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "error": {
                    "code": "PERM_001",
                    "message": "Bạn không có quyền xóa Knowledge Base này",
                },
            },
        )

    kb.is_deleted = True
    kb.updated_at = datetime.utcnow()
    await db.flush()
    return kb


# ---------------------------------------------------------------------------
# Internal methods
# ---------------------------------------------------------------------------


async def danh_dau_can_cap_nhat(
    db: AsyncSession,
    van_ban_id: uuid.UUID,
) -> int:
    """Khi VB phap luat thay doi → tat ca KB lien ket VB do → CAN_CAP_NHAT.

    Tim toan bo KB co van_ban_lien_quan chua van_ban_id,
    trang_thai = DA_XUAT_BAN → chuyen sang CAN_CAP_NHAT.

    Returns:
        So luong KB da cap nhat.
    """
    van_ban_str = str(van_ban_id)

    # Tim cac KB co van_ban_lien_quan chua van_ban_id va dang DA_XUAT_BAN
    q = select(KnowledgeBase).where(
        KnowledgeBase.is_deleted == False,  # noqa: E712
        KnowledgeBase.trang_thai == "DA_XUAT_BAN",
        KnowledgeBase.van_ban_lien_quan.op("@>")(f'["{van_ban_str}"]'),
    )
    result = await db.execute(q)
    kbs = list(result.scalars().all())

    count = 0
    now = datetime.utcnow()
    for kb in kbs:
        kb.trang_thai = "CAN_CAP_NHAT"
        kb.updated_at = now
        count += 1

    if count > 0:
        await db.flush()

    return count
