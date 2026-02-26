"""
forum_service/services/chu_de_service.py
=========================================
Business logic cho quan ly chu de / thread.

DAY LA SERVICE PHUC TAP NHAT cua module Forum:
  - Danh sach phan trang voi filter (tags, search, sap_xep), phan quyen
  - Chi tiet chu de (tang so_luot_xem, nested tra loi, da_upvote, da_theo_doi)
  - Tao chu de (kiem tra quyen chi_doc, auto theo doi, CHO_DUYET/MO)
  - Sua chu de (author trong 24h hoac DIEU_PHOI)
  - Xoa chu de (reject neu co tra loi)
  - Hanh dong dieu phoi (ghim 3, khoa, duyet, an)
  - Chon dap an chuan
"""

import os
import sys
from datetime import datetime, timedelta, timezone
from math import ceil
from typing import Optional
from uuid import UUID

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from fastapi import HTTPException, status
from sqlalchemy import and_, func, or_, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from forum_service.models import BieuQuyet, ChuDe, ChuyenMuc, TheoDoi, TraLoi
from forum_service.models.base import CongChucRef, DonViRef
from shared.auth import TokenPayload


def _now() -> datetime:
    """Lay thoi gian hien tai (UTC)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _is_dieu_phoi(user: TokenPayload) -> bool:
    """Kiem tra user co quyen dieu phoi forum (DIEU_PHOI_FORUM hoac SUPER_ADMIN)."""
    if user.vai_tro == "SUPER_ADMIN" or user.is_admin:
        return True
    return "DIEU_PHOI_FORUM" in (user.platform_roles or [])


def _is_chuyen_gia(user: TokenPayload) -> bool:
    """Kiem tra user co quyen chuyen gia (CHUYEN_GIA hoac SUPER_ADMIN)."""
    if user.vai_tro == "SUPER_ADMIN" or user.is_admin:
        return True
    return "CHUYEN_GIA" in (user.platform_roles or [])


def _build_user_brief(cong_chuc: CongChucRef) -> dict:
    """Build UserBrief tu CongChucRef + DonViRef."""
    if not cong_chuc:
        return None
    return {
        "id": cong_chuc.id,
        "ma_cc": cong_chuc.ma_cc,
        "ho_ten": cong_chuc.ho_ten,
        "chuc_vu": cong_chuc.chuc_vu,
        "don_vi_ten": cong_chuc.don_vi.ten_don_vi if cong_chuc.don_vi else None,
    }


def _compute_noi_dung_tom_tat(noi_dung: str) -> str:
    """Tao tom tat tu noi dung (200 ky tu dau, strip HTML)."""
    # Simple HTML strip (TODO: dung bleach/html2text)
    clean = noi_dung.replace("<br>", " ").replace("<p>", " ").replace("</p>", " ")
    clean = clean.replace("<", " ").replace(">", " ")
    clean = " ".join(clean.split())  # normalize whitespace
    return clean[:200]


async def danh_sach(
    db: AsyncSession,
    user: TokenPayload,
    chuyen_muc_id: Optional[UUID] = None,
    trang_thai: Optional[str] = None,
    tags: Optional[list[str]] = None,
    search: Optional[str] = None,
    sap_xep: str = "moi_nhat",
    page: int = 1,
    page_size: int = 20,
) -> dict:
    """
    Lay danh sach chu de co filter + phan trang + phan quyen.

    Phan quyen:
      - CBCC chi xem chu de trang_thai IN ('MO', 'DONG')
      - DIEU_PHOI xem tat ca ('CHO_DUYET', 'MO', 'DONG', 'AN')

    Filter:
      - chuyen_muc_id: filter theo chuyen muc
      - trang_thai: filter theo trang thai (CBCC bi gioi han)
      - tags: JSONB contains — chu de co tag nay
      - search: full-text search voi tsvector

    Sap xep:
      - is_ghim DESC FIRST (ghim len top)
      - Sau do theo sap_xep:
        * moi_nhat: created_at DESC
        * nhieu_upvote: so_upvote DESC
        * nhieu_tra_loi: so_tra_loi DESC

    Returns:
        Paginated response with items + pagination
    """
    # Base query: chi xem chu de chua bi xoa
    query = select(ChuDe).where(ChuDe.is_deleted == False)

    # Phan quyen: CBCC chi xem MO, DONG
    is_dp = _is_dieu_phoi(user)
    if not is_dp:
        query = query.where(ChuDe.trang_thai.in_(["MO", "DONG"]))
    elif trang_thai:
        query = query.where(ChuDe.trang_thai == trang_thai)

    # Filter chuyen_muc
    if chuyen_muc_id:
        query = query.where(ChuDe.chuyen_muc_id == chuyen_muc_id)

    # Filter tags (JSONB contains)
    if tags:
        for tag in tags:
            query = query.where(ChuDe.tags.contains([tag]))

    # Full-text search
    if search:
        query = query.where(
            text("forum.chu_de.search_vector @@ plainto_tsquery('simple', :q)").bindparams(
                q=search
            )
        )

    # Sap xep: ghim len top first
    query = query.order_by(ChuDe.is_ghim.desc())
    if sap_xep == "nhieu_upvote":
        query = query.order_by(ChuDe.so_upvote.desc())
    elif sap_xep == "nhieu_tra_loi":
        query = query.order_by(ChuDe.so_tra_loi.desc())
    else:  # moi_nhat (default)
        query = query.order_by(ChuDe.created_at.desc())

    # Dem tong
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar_one()

    # Phan trang
    skip = (page - 1) * page_size
    query = query.offset(skip).limit(page_size)
    chu_de_list = list((await db.execute(query)).scalars().all())

    # Build items
    items = []
    for cd in chu_de_list:
        tac_gia = _build_user_brief(cd.tac_gia)
        noi_dung_tom_tat = _compute_noi_dung_tom_tat(cd.noi_dung)
        co_dap_an_chuan = cd.tra_loi_chuan_id is not None

        items.append({
            "id": cd.id,
            "tieu_de": cd.tieu_de,
            "noi_dung_tom_tat": noi_dung_tom_tat,
            "tags": cd.tags or [],
            "tac_gia": tac_gia,
            "trang_thai": cd.trang_thai,
            "is_ghim": cd.is_ghim,
            "is_khoa": cd.is_khoa,
            "so_luot_xem": cd.so_luot_xem,
            "so_tra_loi": cd.so_tra_loi,
            "so_upvote": cd.so_upvote,
            "co_dap_an_chuan": co_dap_an_chuan,
            "created_at": cd.created_at,
            "updated_at": cd.updated_at,
        })

    total_pages = ceil(total / page_size) if page_size > 0 else 0
    return {
        "items": items,
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total_items": total,
            "total_pages": total_pages,
        },
    }


async def chi_tiet(
    db: AsyncSession,
    chu_de_id: UUID,
    user: TokenPayload,
) -> dict:
    """
    Lay chi tiet chu de.

    Side effects:
      - Tang so_luot_xem += 1 (UPDATE truc tiep)

    Build:
      - Nested tra_loi tree (parent → children)
      - da_upvote (user hien tai co vote chu de nay khong)
      - da_theo_doi (user hien tai co theo doi chu de nay khong)
      - da_upvote cho moi tra loi

    Phan quyen:
      - CBCC chi xem CHU_DE o trang thai MO, DONG
      - DIEU_PHOI xem tat ca

    Returns:
        ChuDeDetail
    """
    # Load chu de
    stmt = select(ChuDe).where(ChuDe.id == chu_de_id, ChuDe.is_deleted == False)
    cd = (await db.execute(stmt)).scalar_one_or_none()
    if not cd:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": {
                    "code": "FORUM_ERR_001",
                    "message": "Khong tim thay chu de",
                },
            },
        )

    # Kiem tra quyen xem
    is_dp = _is_dieu_phoi(user)
    if not is_dp and cd.trang_thai not in ("MO", "DONG"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": {
                    "code": "FORUM_ERR_001",
                    "message": "Khong tim thay chu de",
                },
            },
        )

    # Tang so_luot_xem
    await db.execute(
        update(ChuDe)
        .where(ChuDe.id == chu_de_id)
        .values(so_luot_xem=ChuDe.so_luot_xem + 1)
    )
    await db.commit()
    # Refresh de lay so_luot_xem moi
    await db.refresh(cd)

    # Check da_upvote (chu de)
    user_uuid = UUID(user.sub)
    vote_stmt = select(BieuQuyet.loai).where(
        BieuQuyet.cong_chuc_id == user_uuid,
        BieuQuyet.doi_tuong_type == "CHU_DE",
        BieuQuyet.doi_tuong_id == chu_de_id,
    )
    vote_result = (await db.execute(vote_stmt)).scalar_one_or_none()
    da_upvote = vote_result == "UP" if vote_result else None

    # Check da_theo_doi
    theo_doi_stmt = select(TheoDoi.cong_chuc_id).where(
        TheoDoi.cong_chuc_id == user_uuid,
        TheoDoi.chu_de_id == chu_de_id,
    )
    da_theo_doi = (await db.execute(theo_doi_stmt)).scalar_one_or_none() is not None

    # Build nested tra loi tree
    # Lay tat ca tra loi chua bi xoa, chua bi an
    tra_loi_stmt = (
        select(TraLoi)
        .where(TraLoi.chu_de_id == chu_de_id, TraLoi.is_deleted == False, TraLoi.is_an == False)
        .order_by(TraLoi.created_at.asc())
    )
    tra_loi_list = list((await db.execute(tra_loi_stmt)).scalars().all())

    # Load vote cua user cho cac tra loi
    tra_loi_ids = [tl.id for tl in tra_loi_list]
    tra_loi_vote_map = {}
    if tra_loi_ids:
        vote_tra_loi_stmt = select(BieuQuyet).where(
            BieuQuyet.cong_chuc_id == user_uuid,
            BieuQuyet.doi_tuong_type == "TRA_LOI",
            BieuQuyet.doi_tuong_id.in_(tra_loi_ids),
        )
        for vote in (await db.execute(vote_tra_loi_stmt)).scalars():
            tra_loi_vote_map[vote.doi_tuong_id] = vote.loai

    # Build tra loi tree: parent (parent_id IS NULL) -> children
    tra_loi_map = {tl.id: tl for tl in tra_loi_list}
    tra_loi_tree = []
    for tl in tra_loi_list:
        if tl.parent_id is None:
            # Level 1 tra loi
            tl_dict = _build_tra_loi_dict(tl, tra_loi_vote_map)
            # Add children
            children = []
            for child_tl in tra_loi_list:
                if child_tl.parent_id == tl.id:
                    child_dict = _build_tra_loi_dict(child_tl, tra_loi_vote_map)
                    children.append(child_dict)
            tl_dict["children"] = children
            tra_loi_tree.append(tl_dict)

    # Build chu de detail
    tac_gia = _build_user_brief(cd.tac_gia)
    co_dap_an_chuan = cd.tra_loi_chuan_id is not None

    return {
        "id": cd.id,
        "chuyen_muc_id": cd.chuyen_muc_id,
        "tieu_de": cd.tieu_de,
        "noi_dung": cd.noi_dung,
        "tags": cd.tags or [],
        "tac_gia": tac_gia,
        "trang_thai": cd.trang_thai,
        "is_ghim": cd.is_ghim,
        "is_khoa": cd.is_khoa,
        "so_luot_xem": cd.so_luot_xem,
        "so_tra_loi": cd.so_tra_loi,
        "so_upvote": cd.so_upvote,
        "tra_loi_chuan_id": cd.tra_loi_chuan_id,
        "van_ban_lien_quan": cd.van_ban_lien_quan,
        "sop_lien_quan": cd.sop_lien_quan,
        "nguoi_duyet_id": cd.nguoi_duyet_id,
        "ngay_duyet": cd.ngay_duyet,
        "created_at": cd.created_at,
        "updated_at": cd.updated_at,
        "da_upvote": da_upvote,
        "da_theo_doi": da_theo_doi,
        "co_dap_an_chuan": co_dap_an_chuan,
        "tra_loi": tra_loi_tree,
    }


def _build_tra_loi_dict(tl: TraLoi, vote_map: dict) -> dict:
    """Build dict cho TraLoiInChuDe."""
    tac_gia = _build_user_brief(tl.tac_gia)
    vote_loai = vote_map.get(tl.id)
    da_upvote = vote_loai == "UP" if vote_loai else None

    return {
        "id": tl.id,
        "noi_dung": tl.noi_dung,
        "tac_gia": tac_gia,
        "is_dap_an_chuan": tl.is_dap_an_chuan,
        "is_an": tl.is_an,
        "so_upvote": tl.so_upvote,
        "da_upvote": da_upvote,
        "can_cu_phap_ly": tl.can_cu_phap_ly,
        "created_at": tl.created_at,
        "updated_at": tl.updated_at,
        "children": [],  # Will be filled by caller
    }


async def tao(
    db: AsyncSession,
    data: dict,
    user: TokenPayload,
) -> dict:
    """
    Tao chu de moi.

    Quy tac:
      - Validate chuyen_muc exists va is_active
      - Neu chuyen_muc.chi_doc = TRUE → require CHUYEN_GIA/DIEU_PHOI/SUPER_ADMIN
        else 403 FORUM_ERR_004
      - trang_thai: CHO_DUYET neu chuyen_muc.yeu_cau_duyet else MO
      - Auto tao TheoDoi cho author

    Args:
        db: Database session
        data: ChuDeCreate
        user: Current user

    Returns:
        ChuDe vua tao (chi tiet)
    """
    chuyen_muc_id = data["chuyen_muc_id"]

    # Validate chuyen muc
    cm_stmt = select(ChuyenMuc).where(ChuyenMuc.id == chuyen_muc_id)
    cm = (await db.execute(cm_stmt)).scalar_one_or_none()
    if not cm or not cm.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": {
                    "code": "FORUM_ERR_001",
                    "message": "Chuyen muc khong ton tai hoac khong hoat dong",
                },
            },
        )

    # Kiem tra quyen dang bai neu chuyen muc chi_doc
    if cm.chi_doc:
        if not (_is_chuyen_gia(user) or _is_dieu_phoi(user)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "success": False,
                    "error": {
                        "code": "FORUM_ERR_004",
                        "message": "Chuyen muc nay chi cho phep CHUYEN_GIA/DIEU_PHOI dang bai",
                    },
                },
            )

    # Xac dinh trang thai
    trang_thai = "CHO_DUYET" if cm.yeu_cau_duyet else "MO"

    # Tao chu de
    user_uuid = UUID(user.sub)
    cd = ChuDe(
        chuyen_muc_id=chuyen_muc_id,
        tieu_de=data["tieu_de"],
        noi_dung=data["noi_dung"],
        tags=data.get("tags", []),
        tac_gia_id=user_uuid,
        trang_thai=trang_thai,
        is_ghim=False,
        is_khoa=False,
        so_luot_xem=0,
        so_tra_loi=0,
        so_upvote=0,
        van_ban_lien_quan=data.get("van_ban_lien_quan"),
        sop_lien_quan=data.get("sop_lien_quan"),
        created_at=_now(),
        updated_at=_now(),
    )
    db.add(cd)
    await db.flush()

    # Auto tao TheoDoi cho author
    theo_doi = TheoDoi(
        cong_chuc_id=user_uuid,
        chu_de_id=cd.id,
        created_at=_now(),
    )
    db.add(theo_doi)

    await db.commit()
    await db.refresh(cd)

    # Return chi tiet
    return await chi_tiet(db, cd.id, user)


async def sua(
    db: AsyncSession,
    chu_de_id: UUID,
    data: dict,
    user: TokenPayload,
) -> dict:
    """
    Sua chu de.

    Quy tac:
      - Author: chi trong 24h sau khi tao, else 403 FORUM_ERR_005
      - DIEU_PHOI/SUPER_ADMIN: luon duoc sua
      - Otherwise: 403 FORUM_ERR_008

    Args:
        db: Database session
        chu_de_id: ID chu de can sua
        data: ChuDeUpdate (chi cap nhat field khac None)
        user: Current user

    Returns:
        Chu de sau khi update
    """
    # Load chu de
    stmt = select(ChuDe).where(ChuDe.id == chu_de_id, ChuDe.is_deleted == False)
    cd = (await db.execute(stmt)).scalar_one_or_none()
    if not cd:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": {
                    "code": "FORUM_ERR_001",
                    "message": "Khong tim thay chu de",
                },
            },
        )

    user_uuid = UUID(user.sub)
    is_dp = _is_dieu_phoi(user)
    is_author = cd.tac_gia_id == user_uuid

    # Kiem tra quyen sua
    if is_author:
        # Author chi sua trong 24h
        cutoff = _now() - timedelta(hours=24)
        if cd.created_at < cutoff:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "success": False,
                    "error": {
                        "code": "FORUM_ERR_005",
                        "message": "Chi co the sua chu de trong vong 24 gio sau khi tao",
                    },
                },
            )
    elif not is_dp:
        # Khong phai author, khong phai DIEU_PHOI
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "error": {
                    "code": "FORUM_ERR_008",
                    "message": "Ban khong co quyen sua chu de nay",
                },
            },
        )

    # Cap nhat cac field co gia tri
    if data.get("tieu_de") is not None:
        cd.tieu_de = data["tieu_de"]
    if data.get("noi_dung") is not None:
        cd.noi_dung = data["noi_dung"]
    if "tags" in data:
        cd.tags = data["tags"]
    if "van_ban_lien_quan" in data:
        cd.van_ban_lien_quan = data["van_ban_lien_quan"]
    if "sop_lien_quan" in data:
        cd.sop_lien_quan = data["sop_lien_quan"]

    cd.updated_at = _now()
    await db.commit()
    await db.refresh(cd)

    return await chi_tiet(db, chu_de_id, user)


async def xoa(
    db: AsyncSession,
    chu_de_id: UUID,
    user: TokenPayload,
) -> None:
    """
    Xoa chu de (soft delete).

    Quy tac:
      - Author: reject neu so_tra_loi > 0 → 400 FORUM_ERR_007
      - DIEU_PHOI/SUPER_ADMIN: luon duoc xoa

    Args:
        db: Database session
        chu_de_id: ID chu de can xoa
        user: Current user
    """
    # Load chu de
    stmt = select(ChuDe).where(ChuDe.id == chu_de_id, ChuDe.is_deleted == False)
    cd = (await db.execute(stmt)).scalar_one_or_none()
    if not cd:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": {
                    "code": "FORUM_ERR_001",
                    "message": "Khong tim thay chu de",
                },
            },
        )

    user_uuid = UUID(user.sub)
    is_dp = _is_dieu_phoi(user)
    is_author = cd.tac_gia_id == user_uuid

    if is_author and not is_dp:
        # Author: reject neu co tra loi
        if cd.so_tra_loi > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "success": False,
                    "error": {
                        "code": "FORUM_ERR_007",
                        "message": "Khong the xoa chu de da co tra loi. Lien he quan tri vien neu can thiet.",
                    },
                },
            )
    elif not is_dp:
        # Khong phai author, khong phai DIEU_PHOI
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "error": {
                    "code": "FORUM_ERR_008",
                    "message": "Ban khong co quyen xoa chu de nay",
                },
            },
        )

    # Soft delete
    cd.is_deleted = True
    cd.updated_at = _now()
    await db.commit()


async def hanh_dong(
    db: AsyncSession,
    chu_de_id: UUID,
    user: TokenPayload,
    hanh_dong: str,
    ly_do: Optional[str] = None,
) -> dict:
    """
    Hanh dong dieu phoi: GHIM, BO_GHIM, KHOA, MO_KHOA, DUYET, AN.

    Quy tac chung: Require DIEU_PHOI/SUPER_ADMIN

    GHIM:
      - Set is_ghim = True
      - Check toi da 3 chu de ghim trong cung chuyen_muc

    BO_GHIM:
      - Set is_ghim = False

    KHOA:
      - Set is_khoa = True (khong cho tra loi moi)

    MO_KHOA:
      - Set is_khoa = False

    DUYET:
      - Chuyen trang_thai tu CHO_DUYET → MO
      - Set nguoi_duyet_id, ngay_duyet

    AN:
      - Set trang_thai = AN

    Args:
        db: Database session
        chu_de_id: ID chu de
        user: Current user
        hanh_dong: GHIM | BO_GHIM | KHOA | MO_KHOA | DUYET | AN
        ly_do: Ly do (optional, cho AN)

    Returns:
        dict with message
    """
    # Require DIEU_PHOI
    if not _is_dieu_phoi(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "error": {
                    "code": "PERM_001",
                    "message": "Yeu cau vai tro DIEU_PHOI_FORUM hoac SUPER_ADMIN",
                },
            },
        )

    # Load chu de
    stmt = select(ChuDe).where(ChuDe.id == chu_de_id, ChuDe.is_deleted == False)
    cd = (await db.execute(stmt)).scalar_one_or_none()
    if not cd:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": {
                    "code": "FORUM_ERR_001",
                    "message": "Khong tim thay chu de",
                },
            },
        )

    user_uuid = UUID(user.sub)
    message = ""

    if hanh_dong == "GHIM":
        # Check max 3 chu de ghim trong chuyen muc
        count_ghim_stmt = select(func.count(ChuDe.id)).where(
            ChuDe.chuyen_muc_id == cd.chuyen_muc_id,
            ChuDe.is_ghim == True,
            ChuDe.is_deleted == False,
            ChuDe.id != chu_de_id,
        )
        count_ghim = (await db.execute(count_ghim_stmt)).scalar_one()
        if count_ghim >= 3:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "success": False,
                    "error": {
                        "code": "FORUM_ERR_009",
                        "message": "Moi chuyen muc chi duoc ghim toi da 3 chu de. Hay bo ghim chu de khac truoc.",
                    },
                },
            )
        cd.is_ghim = True
        message = "Da ghim chu de"

    elif hanh_dong == "BO_GHIM":
        cd.is_ghim = False
        message = "Da bo ghim chu de"

    elif hanh_dong == "KHOA":
        cd.is_khoa = True
        message = "Da khoa chu de (khong cho tra loi moi)"

    elif hanh_dong == "MO_KHOA":
        cd.is_khoa = False
        message = "Da mo khoa chu de"

    elif hanh_dong == "DUYET":
        if cd.trang_thai != "CHO_DUYET":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "success": False,
                    "error": {
                        "code": "FORUM_ERR_010",
                        "message": f"Chi duyet chu de o trang thai CHO_DUYET. Trang thai hien tai: {cd.trang_thai}",
                    },
                },
            )
        cd.trang_thai = "MO"
        cd.nguoi_duyet_id = user_uuid
        cd.ngay_duyet = _now()
        message = "Da duyet chu de"

    elif hanh_dong == "AN":
        cd.trang_thai = "AN"
        message = f"Da an chu de. Ly do: {ly_do or 'Khong co ly do'}"

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": f"Hanh dong khong hop le: {hanh_dong}",
                },
            },
        )

    cd.updated_at = _now()
    await db.commit()

    return {"message": message}


async def chon_dap_an_chuan(
    db: AsyncSession,
    chu_de_id: UUID,
    tra_loi_id: UUID,
    user: TokenPayload,
) -> dict:
    """
    Chon 1 tra loi lam dap an chuan.

    Quy tac:
      - Author OR CHUYEN_GIA OR DIEU_PHOI OR SUPER_ADMIN
      - Validate tra_loi thuoc chu_de nay
      - Neu da co dap an chuan cu → set is_dap_an_chuan = False
      - Set tra loi moi: is_dap_an_chuan = True
      - Update chu_de.tra_loi_chuan_id

    Args:
        db: Database session
        chu_de_id: ID chu de
        tra_loi_id: ID tra loi chon lam chuan
        user: Current user

    Returns:
        dict with message
    """
    # Load chu de
    cd_stmt = select(ChuDe).where(ChuDe.id == chu_de_id, ChuDe.is_deleted == False)
    cd = (await db.execute(cd_stmt)).scalar_one_or_none()
    if not cd:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": {
                    "code": "FORUM_ERR_001",
                    "message": "Khong tim thay chu de",
                },
            },
        )

    user_uuid = UUID(user.sub)
    is_author = cd.tac_gia_id == user_uuid
    is_cg = _is_chuyen_gia(user)
    is_dp = _is_dieu_phoi(user)

    # Kiem tra quyen
    if not (is_author or is_cg or is_dp):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "error": {
                    "code": "FORUM_ERR_008",
                    "message": "Chi tac gia/chuyen gia/dieu phoi moi chon dap an chuan",
                },
            },
        )

    # Validate tra loi thuoc chu de nay
    tl_stmt = select(TraLoi).where(
        TraLoi.id == tra_loi_id,
        TraLoi.chu_de_id == chu_de_id,
        TraLoi.is_deleted == False
    )
    tl = (await db.execute(tl_stmt)).scalar_one_or_none()
    if not tl:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": {
                    "code": "FORUM_ERR_001",
                    "message": "Tra loi khong ton tai hoac khong thuoc chu de nay",
                },
            },
        )

    # Neu da co dap an chuan cu → unset
    if cd.tra_loi_chuan_id:
        old_tl_stmt = select(TraLoi).where(TraLoi.id == cd.tra_loi_chuan_id)
        old_tl = (await db.execute(old_tl_stmt)).scalar_one_or_none()
        if old_tl:
            old_tl.is_dap_an_chuan = False

    # Set tra loi moi lam chuan
    tl.is_dap_an_chuan = True
    cd.tra_loi_chuan_id = tra_loi_id
    cd.updated_at = _now()

    await db.commit()

    return {"message": "Da chon dap an chuan"}
