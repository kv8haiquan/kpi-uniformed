"""
legal_service/services/van_ban_service.py
==========================================
Business logic cho Van Ban phap luat — phan phuc tap nhat.

Workflow duyet:
  NHAP → CHO_DUYET → DA_DUYET → DA_XUAT_BAN
  DA_XUAT_BAN → NHAP (thu hoi)
  CHO_DUYET → NHAP (tu choi)

Quy tac phan quyen:
  BIEN_TAP: tao/sua VB cua minh, gui duyet
  QT_NOI_DUNG: quan ly tat ca VB, duyet, xuat ban
  Lanh dao: duyet xuat ban
  CBCC: chi xem DA_XUAT_BAN
"""

import os
import sys
from datetime import date, datetime, timedelta, timezone
from math import ceil
from typing import Optional
from uuid import UUID

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from fastapi import HTTPException, status
from sqlalchemy import and_, delete, func, or_, select, text, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from legal_service.models.base import CongChucRef, DonViRef
from legal_service.models.loai_van_ban import LoaiVanBan
from legal_service.models.quiz_van_ban import QuizVanBan
from legal_service.models.van_ban import VanBan
from legal_service.models.van_ban_lien_ket import VanBanLienKet
from legal_service.models.xac_nhan_doc import XacNhanDoc
from legal_service.schemas.van_ban import (
    LoaiVanBanBrief,
    QuizBrief,
    TrangThaiDuyetUpdate,
    VanBanCreate,
    VanBanDetail,
    VanBanLienKetDetail,
    VanBanListItem,
    VanBanUpdate,
    XacNhanInfo,
)
from shared.auth import TokenPayload

# Cac buoc chuyen trang thai hop le
WORKFLOW_TRANSITIONS = {
    "NHAP": ["CHO_DUYET"],
    "CHO_DUYET": ["DA_DUYET", "NHAP"],
    "DA_DUYET": ["DA_XUAT_BAN"],
    "DA_XUAT_BAN": ["NHAP"],
}


def _now() -> datetime:
    """Lay thoi gian hien tai (UTC)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _today() -> date:
    """Lay ngay hom nay."""
    return date.today()


def _is_quan_ly(user: TokenPayload) -> bool:
    """Kiem tra user co quyen quan ly (QT_NOI_DUNG hoac SUPER_ADMIN) khong."""
    if user.vai_tro == "SUPER_ADMIN" or user.is_admin:
        return True
    return "QT_NOI_DUNG" in (user.platform_roles or [])


def _is_bien_tap(user: TokenPayload) -> bool:
    """Kiem tra user co quyen bien tap khong."""
    return "BIEN_TAP" in (user.platform_roles or [])


def _build_van_ban_list_item(
    vb: VanBan,
    da_doc: bool = False,
    da_xac_nhan: bool = False,
) -> dict:
    """Chuyen VanBan model sang dict cho VanBanListItem."""
    loai_vb = None
    if vb.loai_van_ban:
        loai_vb = {
            "id": vb.loai_van_ban.id,
            "ma": vb.loai_van_ban.ma,
            "ten": vb.loai_van_ban.ten,
        }

    return {
        "id": vb.id,
        "so_hieu": vb.so_hieu,
        "trich_yeu": vb.trich_yeu,
        "loai_van_ban": loai_vb,
        "co_quan_ban_hanh": vb.co_quan_ban_hanh,
        "ngay_ban_hanh": vb.ngay_ban_hanh,
        "ngay_hieu_luc": vb.ngay_hieu_luc,
        "trang_thai_hieu_luc": vb.trang_thai_hieu_luc,
        "trang_thai_duyet": vb.trang_thai_duyet,
        "muc_do": vb.muc_do,
        "bat_buoc_doc": vb.bat_buoc_doc,
        "han_xac_nhan": vb.han_xac_nhan,
        "ngay_xuat_ban": vb.ngay_xuat_ban,
        "tom_tat": vb.tom_tat,
        "diem_moi": vb.diem_moi,
        "da_doc": da_doc,
        "da_xac_nhan": da_xac_nhan,
        "co_diem_moi": bool(vb.diem_moi),
        "phien_ban": vb.phien_ban or 1,
    }


def _build_van_ban_detail(
    vb: VanBan,
    xac_nhan: Optional[XacNhanDoc] = None,
) -> dict:
    """Chuyen VanBan model sang dict cho VanBanDetail."""
    # Thong tin loai van ban
    loai_vb = None
    if vb.loai_van_ban:
        loai_vb = {
            "id": vb.loai_van_ban.id,
            "ma": vb.loai_van_ban.ma,
            "ten": vb.loai_van_ban.ten,
        }

    # Thong tin nguoi nhap/duyet
    nguoi_nhap = None
    if vb.nguoi_nhap:
        nguoi_nhap = {
            "id": vb.nguoi_nhap.id,
            "ho_ten": vb.nguoi_nhap.ho_ten,
            "don_vi": vb.nguoi_nhap.don_vi.ten_don_vi if vb.nguoi_nhap.don_vi else None,
        }

    nguoi_duyet = None
    if vb.nguoi_duyet:
        nguoi_duyet = {
            "id": vb.nguoi_duyet.id,
            "ho_ten": vb.nguoi_duyet.ho_ten,
        }

    # Danh sach lien ket
    lien_kets = []
    for lk in vb.lien_kets or []:
        vb_lq = lk.van_ban_lien_quan
        if vb_lq:
            lien_kets.append(
                {
                    "van_ban_lien_quan_id": vb_lq.id,
                    "so_hieu": vb_lq.so_hieu,
                    "trich_yeu": vb_lq.trich_yeu,
                    "loai_lien_ket": lk.loai_lien_ket,
                }
            )

    # Thong tin xac nhan cua user hien tai
    xac_nhan_info = None
    if xac_nhan is not None:
        xac_nhan_info = {
            "da_doc": xac_nhan.da_doc,
            "ngay_doc": xac_nhan.ngay_doc,
            "da_xac_nhan": xac_nhan.da_xac_nhan,
            "ngay_xac_nhan": xac_nhan.ngay_xac_nhan,
        }

    # Danh sach quiz
    quizzes = []
    for q in vb.quizzes or []:
        if q.is_active:
            quizzes.append(
                {
                    "id": q.id,
                    "tieu_de": q.tieu_de,
                    "so_cau_hoi": q.so_cau_hoi,
                    "thoi_gian_phut": q.thoi_gian_phut,
                    "diem_dat": float(q.diem_dat),
                    "is_active": q.is_active,
                }
            )

    return {
        "id": vb.id,
        "so_hieu": vb.so_hieu,
        "trich_yeu": vb.trich_yeu,
        "loai_van_ban": loai_vb,
        "co_quan_ban_hanh": vb.co_quan_ban_hanh,
        "ngay_ban_hanh": vb.ngay_ban_hanh,
        "ngay_hieu_luc": vb.ngay_hieu_luc,
        "ngay_het_hieu_luc": vb.ngay_het_hieu_luc,
        "trang_thai_hieu_luc": vb.trang_thai_hieu_luc,
        "van_ban_thay_the_id": vb.van_ban_thay_the_id,
        "tom_tat": vb.tom_tat,
        "noi_dung_html": vb.noi_dung_html,
        "file_goc_url": vb.file_goc_url,
        "chuyen_de": vb.chuyen_de or [],
        "doi_tuong_ap_dung": vb.doi_tuong_ap_dung or [],
        "tags": vb.tags or [],
        "diem_moi": vb.diem_moi,
        "viec_can_lam": vb.viec_can_lam,
        "muc_do": vb.muc_do,
        "bat_buoc_doc": vb.bat_buoc_doc,
        "han_xac_nhan": vb.han_xac_nhan,
        "trang_thai_duyet": vb.trang_thai_duyet,
        "ngay_xuat_ban": vb.ngay_xuat_ban,
        "phien_ban": vb.phien_ban,
        "nguoi_nhap": nguoi_nhap,
        "nguoi_duyet": nguoi_duyet,
        "van_ban_lien_ket": lien_kets,
        "xac_nhan": xac_nhan_info,
        "quizzes": quizzes,
        "created_at": vb.created_at,
        "updated_at": vb.updated_at,
    }


async def _load_van_ban(
    db: AsyncSession,
    van_ban_id: UUID,
    check_deleted: bool = True,
) -> VanBan:
    """Utility: load VanBan theo id, 404 neu khong tim thay."""
    result = await db.execute(select(VanBan).where(VanBan.id == van_ban_id))
    vb = result.scalar_one_or_none()
    if not vb or (check_deleted and vb.is_deleted):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": {
                    "code": "LEGAL_ERR_001",
                    "message": "Khong tim thay van ban",
                },
            },
        )
    return vb


async def danh_sach(
    db: AsyncSession,
    user_id: str,
    loai_van_ban_id: Optional[UUID] = None,
    trang_thai_hieu_luc: Optional[str] = None,
    muc_do: Optional[str] = None,
    bat_buoc_doc: Optional[bool] = None,
    chuyen_de: Optional[str] = None,
    search: Optional[str] = None,
    sap_xep: str = "moi_nhat",
    page: int = 1,
    page_size: int = 20,
) -> dict:
    """
    Lay danh sach van ban da xuat ban (DA_XUAT_BAN) cho CBCC.
    Bao gom trang thai da_doc, da_xac_nhan cua user hien tai.
    """
    # Base query: chi xem VB da xuat ban, chua bi xoa
    query = (
        select(VanBan)
        .where(VanBan.trang_thai_duyet == "DA_XUAT_BAN")
        .where(VanBan.is_deleted == False)
    )

    # Ap dung cac filter
    if loai_van_ban_id:
        query = query.where(VanBan.loai_van_ban_id == loai_van_ban_id)
    if trang_thai_hieu_luc:
        query = query.where(VanBan.trang_thai_hieu_luc == trang_thai_hieu_luc)
    if muc_do:
        query = query.where(VanBan.muc_do == muc_do)
    if bat_buoc_doc is not None:
        query = query.where(VanBan.bat_buoc_doc == bat_buoc_doc)
    if chuyen_de:
        # JSONB contains — tim van ban co chuyen_de chua gia tri nay
        query = query.where(VanBan.chuyen_de.contains([chuyen_de]))
    if search:
        # Full-text search voi tsvector
        query = query.where(
            text("legal.van_ban.search_vector @@ plainto_tsquery('simple', :q)").bindparams(
                q=search
            )
        )

    # Sap xep
    if sap_xep == "quan_trong":
        # KHAN first, roi QUAN_TRONG, roi BINH_THUONG
        query = query.order_by(
            text("CASE muc_do " "WHEN 'KHAN' THEN 1 " "WHEN 'QUAN_TRONG' THEN 2 " "ELSE 3 END"),
            VanBan.ngay_xuat_ban.desc().nullslast(),
        )
    else:
        # mac dinh: moi nhat truoc
        query = query.order_by(VanBan.ngay_xuat_ban.desc().nullslast())

    # Dem tong
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar_one()

    # Phan trang
    skip = (page - 1) * page_size
    query = query.offset(skip).limit(page_size)
    vb_list = list((await db.execute(query)).scalars().all())

    # Lay trang thai doc cua user hien tai cho cac VB nay
    user_uuid = UUID(user_id)
    vb_ids = [vb.id for vb in vb_list]
    xac_nhan_map = {}
    if vb_ids:
        xnd_result = await db.execute(
            select(XacNhanDoc)
            .where(XacNhanDoc.cong_chuc_id == user_uuid)
            .where(XacNhanDoc.van_ban_id.in_(vb_ids))
        )
        for xnd in xnd_result.scalars():
            xac_nhan_map[xnd.van_ban_id] = xnd

    # Build items
    items = []
    for vb in vb_list:
        xnd = xac_nhan_map.get(vb.id)
        items.append(
            _build_van_ban_list_item(
                vb,
                da_doc=xnd.da_doc if xnd else False,
                da_xac_nhan=xnd.da_xac_nhan if xnd else False,
            )
        )

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


async def danh_sach_quan_ly(
    db: AsyncSession,
    user: TokenPayload,
    trang_thai_duyet: Optional[str] = None,
    loai_van_ban_id: Optional[UUID] = None,
    search: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    """
    Lay danh sach van ban cho quan ly (BIEN_TAP, QT_NOI_DUNG).
    BIEN_TAP chi xem VB cua minh.
    QT_NOI_DUNG va SUPER_ADMIN xem tat ca.
    """
    query = select(VanBan).where(VanBan.is_deleted == False)

    # BIEN_TAP chi xem VB cua minh
    if _is_bien_tap(user) and not _is_quan_ly(user):
        query = query.where(VanBan.nguoi_nhap_id == UUID(user.sub))

    # Filters
    if trang_thai_duyet:
        query = query.where(VanBan.trang_thai_duyet == trang_thai_duyet)
    if loai_van_ban_id:
        query = query.where(VanBan.loai_van_ban_id == loai_van_ban_id)
    if search:
        query = query.where(
            text("legal.van_ban.search_vector @@ plainto_tsquery('simple', :q)").bindparams(
                q=search
            )
        )

    query = query.order_by(VanBan.updated_at.desc().nullslast())

    # Dem tong
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar_one()

    skip = (page - 1) * page_size
    query = query.offset(skip).limit(page_size)
    vb_list = list((await db.execute(query)).scalars().all())

    items = [_build_van_ban_list_item(vb) for vb in vb_list]
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


async def danh_sach_chua_doc(
    db: AsyncSession,
    user_id: str,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    """
    Lay danh sach van ban bat_buoc_doc ma user chua xac nhan.
    Sap xep: KHAN first → QUAN_TRONG → BINH_THUONG → han_xac_nhan ASC NULLS LAST.
    """
    user_uuid = UUID(user_id)

    # Tim cac van ban bat buoc da xuat ban
    # Nhung chua co xac nhan hoac da_xac_nhan=FALSE
    query = (
        select(VanBan)
        .outerjoin(
            XacNhanDoc,
            and_(
                XacNhanDoc.van_ban_id == VanBan.id,
                XacNhanDoc.cong_chuc_id == user_uuid,
            ),
        )
        .where(VanBan.bat_buoc_doc == True)
        .where(VanBan.trang_thai_duyet == "DA_XUAT_BAN")
        .where(VanBan.is_deleted == False)
        .where(
            or_(
                XacNhanDoc.id == None,  # Chua co ban ghi xac nhan
                XacNhanDoc.da_xac_nhan == False,  # Da co nhung chua xac nhan
            )
        )
        .order_by(
            text(
                "CASE legal.van_ban.muc_do "
                "WHEN 'KHAN' THEN 1 "
                "WHEN 'QUAN_TRONG' THEN 2 "
                "ELSE 3 END"
            ),
            VanBan.han_xac_nhan.asc().nullslast(),
        )
    )

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar_one()

    skip = (page - 1) * page_size
    query = query.offset(skip).limit(page_size)
    vb_list = list((await db.execute(query)).scalars().all())

    # Lay xac nhan cho cac vb nay
    vb_ids = [vb.id for vb in vb_list]
    xac_nhan_map = {}
    if vb_ids:
        xnd_result = await db.execute(
            select(XacNhanDoc)
            .where(XacNhanDoc.cong_chuc_id == user_uuid)
            .where(XacNhanDoc.van_ban_id.in_(vb_ids))
        )
        for xnd in xnd_result.scalars():
            xac_nhan_map[xnd.van_ban_id] = xnd

    items = []
    for vb in vb_list:
        xnd = xac_nhan_map.get(vb.id)
        items.append(
            _build_van_ban_list_item(
                vb,
                da_doc=xnd.da_doc if xnd else False,
                da_xac_nhan=False,
            )
        )

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
    user: TokenPayload,
    van_ban_id: UUID,
) -> dict:
    """
    Lay chi tiet van ban.
    CBCC: chi xem DA_XUAT_BAN.
    BIEN_TAP/QT_NOI_DUNG: xem tat ca.
    Side effect: upsert xac_nhan_doc (da_doc=TRUE).
    """
    vb = await _load_van_ban(db, van_ban_id)

    # Kiem tra quyen xem
    co_quyen_quan_ly = _is_quan_ly(user) or _is_bien_tap(user)
    if not co_quyen_quan_ly and vb.trang_thai_duyet != "DA_XUAT_BAN":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": {
                    "code": "LEGAL_ERR_001",
                    "message": "Khong tim thay van ban",
                },
            },
        )

    user_uuid = UUID(user.sub)

    # Upsert xac_nhan_doc: ghi nhan CBCC da mo doc
    xnd_result = await db.execute(
        select(XacNhanDoc)
        .where(XacNhanDoc.van_ban_id == van_ban_id)
        .where(XacNhanDoc.cong_chuc_id == user_uuid)
    )
    xac_nhan = xnd_result.scalar_one_or_none()

    if xac_nhan is None:
        # Tao ban ghi moi
        xac_nhan = XacNhanDoc(
            van_ban_id=van_ban_id,
            cong_chuc_id=user_uuid,
            da_doc=True,
            ngay_doc=_now(),
            da_xac_nhan=False,
        )
        db.add(xac_nhan)
        await db.commit()
        await db.refresh(xac_nhan)
    elif not xac_nhan.da_doc:
        # Cap nhat neu chua doc
        xac_nhan.da_doc = True
        xac_nhan.ngay_doc = _now()
        await db.commit()
        await db.refresh(xac_nhan)

    return _build_van_ban_detail(vb, xac_nhan)


async def tao_van_ban(
    db: AsyncSession,
    user: TokenPayload,
    data: VanBanCreate,
) -> dict:
    """
    Tao van ban moi.
    - Check trung so_hieu
    - trang_thai_duyet = NHAP
    - Tao van_ban_lien_ket neu co
    - Neu loai THAY_THE → cap nhat VB cu
    """
    # Kiem tra trung so_hieu
    existing = await db.execute(
        select(VanBan.id).where(VanBan.so_hieu == data.so_hieu).where(VanBan.is_deleted == False)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "error": {
                    "code": "LEGAL_ERR_002",
                    "message": f"So hieu van ban '{data.so_hieu}' da ton tai",
                },
            },
        )

    # Tao van ban moi
    vb = VanBan(
        so_hieu=data.so_hieu,
        trich_yeu=data.trich_yeu,
        loai_van_ban_id=data.loai_van_ban_id,
        co_quan_ban_hanh=data.co_quan_ban_hanh,
        ngay_ban_hanh=data.ngay_ban_hanh,
        ngay_hieu_luc=data.ngay_hieu_luc,
        ngay_het_hieu_luc=data.ngay_het_hieu_luc,
        trang_thai_hieu_luc=data.trang_thai_hieu_luc,
        van_ban_thay_the_id=data.van_ban_thay_the_id,
        tom_tat=data.tom_tat,
        noi_dung_html=data.noi_dung_html,
        file_goc_url=data.file_goc_url,
        chuyen_de=data.chuyen_de,
        doi_tuong_ap_dung=data.doi_tuong_ap_dung,
        tags=data.tags,
        diem_moi=data.diem_moi,
        viec_can_lam=data.viec_can_lam,
        muc_do=data.muc_do,
        bat_buoc_doc=data.bat_buoc_doc,
        han_xac_nhan=data.han_xac_nhan,
        trang_thai_duyet="NHAP",
        nguoi_nhap_id=UUID(user.sub),
        phien_ban=1,
        created_at=_now(),
        updated_at=_now(),
    )
    db.add(vb)
    await db.flush()  # De lay vb.id truoc khi commit

    # Tao cac lien ket van ban
    for lk_input in data.van_ban_lien_ket:
        lk = VanBanLienKet(
            van_ban_id=vb.id,
            van_ban_lien_quan_id=lk_input.van_ban_lien_quan_id,
            loai_lien_ket=lk_input.loai_lien_ket,
        )
        db.add(lk)

        # Neu loai THAY_THE → cap nhat VB cu: trang_thai_hieu_luc = BI_THAY_THE
        if lk_input.loai_lien_ket == "THAY_THE":
            await db.execute(
                update(VanBan)
                .where(VanBan.id == lk_input.van_ban_lien_quan_id)
                .values(
                    trang_thai_hieu_luc="BI_THAY_THE",
                    van_ban_thay_the_id=vb.id,
                    updated_at=_now(),
                )
            )

    await db.commit()

    # Load lai de tra ve day du thong tin
    vb_fresh = await _load_van_ban(db, vb.id)
    return _build_van_ban_detail(vb_fresh)


async def sua_van_ban(
    db: AsyncSession,
    user: TokenPayload,
    van_ban_id: UUID,
    data: VanBanUpdate,
) -> dict:
    """
    Cap nhat van ban.
    BIEN_TAP: chi sua VB cua minh va chi o trang thai NHAP/CHO_DUYET.
    QT_NOI_DUNG: sua tat ca.
    Neu VB DA_XUAT_BAN → phien_ban += 1.
    """
    vb = await _load_van_ban(db, van_ban_id)

    # Kiem tra quyen sua
    if _is_bien_tap(user) and not _is_quan_ly(user):
        # BIEN_TAP chi sua VB cua minh
        if vb.nguoi_nhap_id != UUID(user.sub):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "success": False,
                    "error": {
                        "code": "PERM_003",
                        "message": "Ban chi co the sua van ban do chinh minh tao",
                    },
                },
            )
        # BIEN_TAP chi sua o trang thai NHAP hoac CHO_DUYET
        if vb.trang_thai_duyet not in ("NHAP", "CHO_DUYET"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "success": False,
                    "error": {
                        "code": "PERM_004",
                        "message": "Chi co the sua van ban o trang thai NHAP hoac CHO_DUYET",
                    },
                },
            )

    # Neu VB da xuat ban → tang phien ban
    if vb.trang_thai_duyet == "DA_XUAT_BAN":
        vb.phien_ban = (vb.phien_ban or 1) + 1

    # Cap nhat cac truong co gia tri
    if data.so_hieu is not None:
        vb.so_hieu = data.so_hieu
    if data.trich_yeu is not None:
        vb.trich_yeu = data.trich_yeu
    if data.loai_van_ban_id is not None:
        vb.loai_van_ban_id = data.loai_van_ban_id
    if data.co_quan_ban_hanh is not None:
        vb.co_quan_ban_hanh = data.co_quan_ban_hanh
    if data.ngay_ban_hanh is not None:
        vb.ngay_ban_hanh = data.ngay_ban_hanh
    if data.ngay_hieu_luc is not None:
        vb.ngay_hieu_luc = data.ngay_hieu_luc
    if data.ngay_het_hieu_luc is not None:
        vb.ngay_het_hieu_luc = data.ngay_het_hieu_luc
    if data.trang_thai_hieu_luc is not None:
        vb.trang_thai_hieu_luc = data.trang_thai_hieu_luc
    if data.van_ban_thay_the_id is not None:
        vb.van_ban_thay_the_id = data.van_ban_thay_the_id
    if data.tom_tat is not None:
        vb.tom_tat = data.tom_tat
    if data.noi_dung_html is not None:
        vb.noi_dung_html = data.noi_dung_html
    if data.file_goc_url is not None:
        vb.file_goc_url = data.file_goc_url
    if data.chuyen_de is not None:
        vb.chuyen_de = data.chuyen_de
    if data.doi_tuong_ap_dung is not None:
        vb.doi_tuong_ap_dung = data.doi_tuong_ap_dung
    if data.tags is not None:
        vb.tags = data.tags
    if data.diem_moi is not None:
        vb.diem_moi = data.diem_moi
    if data.viec_can_lam is not None:
        vb.viec_can_lam = data.viec_can_lam
    if data.muc_do is not None:
        vb.muc_do = data.muc_do
    if data.bat_buoc_doc is not None:
        vb.bat_buoc_doc = data.bat_buoc_doc
    if data.han_xac_nhan is not None:
        vb.han_xac_nhan = data.han_xac_nhan
    vb.updated_at = _now()

    # Cap nhat lien ket neu co
    if data.van_ban_lien_ket is not None:
        # Xoa het lien ket cu
        await db.execute(delete(VanBanLienKet).where(VanBanLienKet.van_ban_id == van_ban_id))
        # Them lai lien ket moi
        for lk_input in data.van_ban_lien_ket:
            lk = VanBanLienKet(
                van_ban_id=van_ban_id,
                van_ban_lien_quan_id=lk_input.van_ban_lien_quan_id,
                loai_lien_ket=lk_input.loai_lien_ket,
            )
            db.add(lk)

    await db.commit()

    vb_fresh = await _load_van_ban(db, van_ban_id)
    return _build_van_ban_detail(vb_fresh)


async def cap_nhat_trang_thai(
    db: AsyncSession,
    user: TokenPayload,
    van_ban_id: UUID,
    data: TrangThaiDuyetUpdate,
) -> dict:
    """
    Cap nhat trang thai duyet van ban theo workflow.

    Quy tac chuyen trang thai:
      NHAP → CHO_DUYET: BIEN_TAP (VB cua minh) hoac QT_NOI_DUNG
      CHO_DUYET → DA_DUYET: QT_NOI_DUNG
      CHO_DUYET → NHAP: QT_NOI_DUNG (tu choi)
      DA_DUYET → DA_XUAT_BAN: QT_NOI_DUNG hoac is_lanh_dao
      DA_XUAT_BAN → NHAP: QT_NOI_DUNG (thu hoi)

    Dieu kien xuat ban:
      - so_hieu, trich_yeu, loai_van_ban_id, ngay_ban_hanh
      - noi_dung_html HOAC file_goc_url
    """
    vb = await _load_van_ban(db, van_ban_id)
    current_status = vb.trang_thai_duyet
    new_status = data.trang_thai_duyet

    # Kiem tra buoc chuyen hop le
    allowed_next = WORKFLOW_TRANSITIONS.get(current_status, [])
    if new_status not in allowed_next:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "error": {
                    "code": "LEGAL_ERR_003",
                    "message": (
                        f"Khong the chuyen tu '{current_status}' sang '{new_status}'. "
                        f"Cac buoc hop le: {allowed_next}"
                    ),
                },
            },
        )

    # Kiem tra quyen theo tung buoc chuyen
    user_uuid = UUID(user.sub)
    is_qt = _is_quan_ly(user)
    is_bt = _is_bien_tap(user)
    is_ld = user.is_lanh_dao

    if current_status == "NHAP" and new_status == "CHO_DUYET":
        # BIEN_TAP chi gui duyet VB cua minh; QT_NOI_DUNG gui bat ky VB
        if is_bt and not is_qt:
            if vb.nguoi_nhap_id != user_uuid:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "success": False,
                        "error": {
                            "code": "PERM_005",
                            "message": "BIEN_TAP chi co the gui duyet van ban cua minh",
                        },
                    },
                )
        elif not is_qt:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "success": False,
                    "error": {
                        "code": "PERM_001",
                        "message": "Khong co quyen gui duyet van ban",
                    },
                },
            )

    elif current_status == "CHO_DUYET" and new_status in ("DA_DUYET", "NHAP"):
        # Chi QT_NOI_DUNG moi duyet hoac tu choi
        if not is_qt:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "success": False,
                    "error": {
                        "code": "PERM_001",
                        "message": "Yeu cau vai tro QT_NOI_DUNG de duyet van ban",
                    },
                },
            )

    elif current_status == "DA_DUYET" and new_status == "DA_XUAT_BAN":
        # QT_NOI_DUNG hoac Lanh dao
        if not is_qt and not is_ld:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "success": False,
                    "error": {
                        "code": "PERM_001",
                        "message": "Yeu cau QT_NOI_DUNG hoac lanh dao de xuat ban van ban",
                    },
                },
            )
        # Kiem tra dieu kien xuat ban
        if not vb.so_hieu or not vb.trich_yeu or not vb.loai_van_ban_id or not vb.ngay_ban_hanh:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "success": False,
                    "error": {
                        "code": "LEGAL_ERR_004",
                        "message": (
                            "Van ban phai co day du: so_hieu, trich_yeu, "
                            "loai_van_ban_id, ngay_ban_hanh"
                        ),
                    },
                },
            )
        if not vb.noi_dung_html and not vb.file_goc_url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "success": False,
                    "error": {
                        "code": "LEGAL_ERR_004",
                        "message": "Van ban phai co noi_dung_html hoac file_goc_url truoc khi xuat ban",
                    },
                },
            )

    elif current_status == "DA_XUAT_BAN" and new_status == "NHAP":
        # Thu hoi: chi QT_NOI_DUNG
        if not is_qt:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "success": False,
                    "error": {
                        "code": "PERM_001",
                        "message": "Yeu cau QT_NOI_DUNG de thu hoi van ban",
                    },
                },
            )

    # Thuc hien chuyen trang thai
    vb.trang_thai_duyet = new_status
    vb.updated_at = _now()

    # Khi xuat ban: ghi ngay_xuat_ban va nguoi_duyet
    if new_status == "DA_XUAT_BAN":
        vb.ngay_xuat_ban = _now()
        vb.nguoi_duyet_id = user_uuid

        # Neu bat_buoc_doc → tao xac_nhan_doc hang loat cho doi tuong ap dung
        if vb.bat_buoc_doc:
            await _tao_xac_nhan_doc_hang_loat(db, vb)

    await db.commit()

    return {
        "trang_thai_duyet": new_status,
        "message": f"Da chuyen trang thai sang {new_status}",
    }


def _is_uuid_str(s: str) -> bool:
    """Kiem tra xem chuoi co phai UUID hop le khong."""
    try:
        UUID(s)
        return True
    except (ValueError, AttributeError):
        return False


async def _tao_xac_nhan_doc_hang_loat(
    db: AsyncSession,
    vb: VanBan,
) -> None:
    """
    Tao ban ghi xac_nhan_doc cho tat ca CBCC thuoc doi tuong ap dung.

    doi_tuong_ap_dung:
      [] hoac ["TAT_CA"] → tat ca CBCC active
      ["uuid-don-vi-1", "uuid-don-vi-2"] → CBCC thuoc cac don vi (UUID, format moi)
      ["Doi thu tuc", "Doi KTSTQ"] → CBCC thuoc don vi (ten_don_vi, format cu — backward compat)

    Dung INSERT ... ON CONFLICT DO NOTHING de tranh duplicate va tranh N+1 query.
    """
    doi_tuong = vb.doi_tuong_ap_dung or []

    # Xac dinh danh sach CBCC can tao xac nhan
    if not doi_tuong or "TAT_CA" in doi_tuong:
        # Tat ca CBCC active
        result = await db.execute(
            select(CongChucRef.id).where(CongChucRef.is_active.is_(True))
        )
    else:
        non_tat_ca = [x for x in doi_tuong if x != "TAT_CA"]
        # Format "cc:<uuid>" — danh sach cong chuc cu the
        cc_items = [x for x in non_tat_ca if isinstance(x, str) and x.startswith("cc:")]
        if cc_items:
            cc_ids = [UUID(x[3:]) for x in cc_items if _is_uuid_str(x[3:])]
            result = await db.execute(
                select(CongChucRef.id)
                .where(CongChucRef.id.in_(cc_ids))
                .where(CongChucRef.is_active.is_(True))
            )
        elif non_tat_ca and all(_is_uuid_str(x) for x in non_tat_ca):
            # Format moi: UUID don vi — loc theo don_vi_id (chinh xac hon)
            don_vi_ids = [UUID(x) for x in non_tat_ca]
            result = await db.execute(
                select(CongChucRef.id)
                .where(CongChucRef.don_vi_id.in_(don_vi_ids))
                .where(CongChucRef.is_active.is_(True))
            )
        else:
            # Format cu (backward compat): loc theo ten_don_vi
            result = await db.execute(
                select(CongChucRef.id)
                .join(DonViRef, CongChucRef.don_vi_id == DonViRef.id)
                .where(DonViRef.ten_don_vi.in_(non_tat_ca))
                .where(CongChucRef.is_active.is_(True))
            )

    cbcc_ids = [row[0] for row in result.all()]
    if not cbcc_ids:
        return

    # Dung INSERT ... ON CONFLICT DO NOTHING thay vi N SELECT + INSERT rieng le
    # Tranh N+1 query khi co 549 CBCC
    now = _now()
    rows_to_insert = [
        {
            "van_ban_id": vb.id,
            "cong_chuc_id": cbcc_id,
            "da_doc": False,
            "da_xac_nhan": False,
            "created_at": now,
        }
        for cbcc_id in cbcc_ids
    ]

    # PostgreSQL INSERT ... ON CONFLICT (van_ban_id, cong_chuc_id) DO NOTHING
    stmt = pg_insert(XacNhanDoc).values(rows_to_insert)
    stmt = stmt.on_conflict_do_nothing(index_elements=["van_ban_id", "cong_chuc_id"])
    await db.execute(stmt)

    # Commit duoc thuc hien boi ham goi (cap_nhat_trang_thai)


async def xoa_van_ban(
    db: AsyncSession,
    user: TokenPayload,
    van_ban_id: UUID,
) -> None:
    """
    Soft delete van ban.
    Chi xoa duoc VB o trang thai NHAP.
    Chi QT_NOI_DUNG hoac SUPER_ADMIN moi xoa duoc.
    """
    if not _is_quan_ly(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "error": {
                    "code": "PERM_001",
                    "message": "Yeu cau quyen QT_NOI_DUNG de xoa van ban",
                },
            },
        )

    vb = await _load_van_ban(db, van_ban_id)

    # Chi xoa duoc VB o trang thai NHAP
    if vb.trang_thai_duyet != "NHAP":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "error": {
                    # LEGAL_ERR_003: Trang thai khong hop le (LEGAL_ERR_006 danh cho Quiz)
                    "code": "LEGAL_ERR_003",
                    "message": "Chi co the xoa van ban o trang thai NHAP",
                },
            },
        )

    vb.is_deleted = True
    vb.updated_at = _now()
    await db.commit()


async def get_summary(db: AsyncSession, van_ban_id: UUID) -> dict:
    """
    Lay thong tin tom tat van ban cho Internal API.
    Tra ve dict de cac service khac su dung.
    """
    result = await db.execute(
        select(VanBan).where(VanBan.id == van_ban_id).where(VanBan.is_deleted == False)
    )
    vb = result.scalar_one_or_none()
    if not vb:
        return None

    return {
        "id": str(vb.id),
        "so_hieu": vb.so_hieu,
        "trich_yeu": vb.trich_yeu,
        "trang_thai_duyet": vb.trang_thai_duyet,
        "trang_thai_hieu_luc": vb.trang_thai_hieu_luc,
        "ngay_xuat_ban": vb.ngay_xuat_ban.isoformat() if vb.ngay_xuat_ban else None,
        "file_goc_url": vb.file_goc_url,
    }


async def search_van_ban(
    db: AsyncSession,
    q: str,
    limit: int = 10,
) -> list[dict]:
    """
    Tim kiem van ban theo tu khoa cho Internal API autocomplete.
    Chi tra ve VB DA_XUAT_BAN.
    """
    result = await db.execute(
        select(VanBan)
        .where(VanBan.trang_thai_duyet == "DA_XUAT_BAN")
        .where(VanBan.is_deleted == False)
        .where(
            or_(
                VanBan.so_hieu.ilike(f"%{q}%"),
                VanBan.trich_yeu.ilike(f"%{q}%"),
            )
        )
        .order_by(VanBan.ngay_xuat_ban.desc().nullslast())
        .limit(limit)
    )
    vb_list = result.scalars().all()
    return [
        {
            "id": str(vb.id),
            "so_hieu": vb.so_hieu,
            "trich_yeu": vb.trich_yeu,
            "ngay_ban_hanh": vb.ngay_ban_hanh.isoformat() if vb.ngay_ban_hanh else None,
        }
        for vb in vb_list
    ]
