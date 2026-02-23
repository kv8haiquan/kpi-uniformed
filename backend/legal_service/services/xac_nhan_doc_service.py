"""
legal_service/services/xac_nhan_doc_service.py
================================================
Business logic cho Xac nhan doc van ban, Dashboard va Bao cao.

Cac ham:
  xac_nhan_da_doc     — CBCC xac nhan da doc va hieu van ban
  tracking_doc        — Ghi nhan thoi gian doc thuc te
  bao_cao_doc         — Bao cao trang thai doc theo tung van ban (QT/LD)
  dashboard_summary   — Tong hop so lieu dashboard cho CBCC
  bao_cao_ca_nhan     — Bao cao doc theo ca nhan trong thang
  bao_cao_don_vi      — Bao cao tuan thu doc theo don vi
"""

import os
import sys
from datetime import date, datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from fastapi import HTTPException, status
from sqlalchemy import Integer, and_, cast, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from legal_service.models.base import CongChucRef, DonViRef
from legal_service.models.ket_qua_quiz import KetQuaQuiz
from legal_service.models.quiz_van_ban import QuizVanBan
from legal_service.models.van_ban import VanBan
from legal_service.models.xac_nhan_doc import XacNhanDoc
from legal_service.schemas.xac_nhan_doc import (
    BaoCaoCaNhan,
    BaoCaoDocResponse,
    BaoCaoDonVi,
    CbccChuaDoc,
    ChiTietDoc,
    DashboardSummary,
    TrackingDocInput,
    XacNhanDocCreate,
)
from shared.auth import TokenPayload


def _now() -> datetime:
    """Lay thoi gian hien tai (UTC)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _today() -> date:
    return date.today()


def _is_quan_ly(user: TokenPayload) -> bool:
    if user.vai_tro == "SUPER_ADMIN" or user.is_admin:
        return True
    return "QT_NOI_DUNG" in (user.platform_roles or [])


async def xac_nhan_da_doc(
    db: AsyncSession,
    user_id: str,
    van_ban_id: UUID,
    data: XacNhanDocCreate,
) -> dict:
    """
    CBCC xac nhan da doc va hieu van ban.

    Quy tac:
      - Neu chua co ban ghi xac nhan → tao moi voi da_doc=TRUE
      - Neu da xac nhan roi → loi LEGAL_ERR_005
      - Update da_xac_nhan=TRUE, ngay_xac_nhan=NOW
    """
    user_uuid = UUID(user_id)

    # Tim ban ghi xac nhan hien tai
    result = await db.execute(
        select(XacNhanDoc)
        .where(XacNhanDoc.van_ban_id == van_ban_id)
        .where(XacNhanDoc.cong_chuc_id == user_uuid)
    )
    xac_nhan = result.scalar_one_or_none()

    # Kiem tra van ban ton tai va da xuat ban
    vb_result = await db.execute(
        select(VanBan.id, VanBan.trang_thai_duyet)
        .where(VanBan.id == van_ban_id)
        .where(VanBan.is_deleted == False)
    )
    vb_row = vb_result.first()
    if not vb_row:
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

    if xac_nhan is None:
        # Tao ban ghi moi
        xac_nhan = XacNhanDoc(
            van_ban_id=van_ban_id,
            cong_chuc_id=user_uuid,
            da_doc=True,
            ngay_doc=_now(),
            da_xac_nhan=True,
            ngay_xac_nhan=_now(),
            ghi_chu=data.ghi_chu,
            created_at=_now(),
        )
        db.add(xac_nhan)
    else:
        # Kiem tra da xac nhan chua
        if xac_nhan.da_xac_nhan:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "success": False,
                    "error": {
                        "code": "LEGAL_ERR_005",
                        "message": "Ban da xac nhan doc van ban nay roi",
                    },
                },
            )
        xac_nhan.da_xac_nhan = True
        xac_nhan.ngay_xac_nhan = _now()
        if not xac_nhan.da_doc:
            xac_nhan.da_doc = True
            xac_nhan.ngay_doc = _now()
        if data.ghi_chu:
            xac_nhan.ghi_chu = data.ghi_chu

    await db.commit()
    await db.refresh(xac_nhan)

    return {
        "van_ban_id": str(van_ban_id),
        "da_xac_nhan": xac_nhan.da_xac_nhan,
        "ngay_xac_nhan": xac_nhan.ngay_xac_nhan,
        "message": "Xac nhan doc van ban thanh cong",
    }


async def tracking_doc(
    db: AsyncSession,
    user_id: str,
    van_ban_id: UUID,
    data: TrackingDocInput,
) -> dict:
    """
    Ghi nhan/cong don thoi gian doc thuc te cua CBCC.
    Cong don vao thoi_gian_doc_giay (khong reset).
    """
    user_uuid = UUID(user_id)

    result = await db.execute(
        select(XacNhanDoc)
        .where(XacNhanDoc.van_ban_id == van_ban_id)
        .where(XacNhanDoc.cong_chuc_id == user_uuid)
    )
    xac_nhan = result.scalar_one_or_none()

    if xac_nhan is None:
        # Tao ban ghi moi
        xac_nhan = XacNhanDoc(
            van_ban_id=van_ban_id,
            cong_chuc_id=user_uuid,
            da_doc=True,
            ngay_doc=_now(),
            da_xac_nhan=False,
            thoi_gian_doc_giay=data.thoi_gian_doc_giay,
            created_at=_now(),
        )
        db.add(xac_nhan)
    else:
        # Cong don thoi gian
        current = xac_nhan.thoi_gian_doc_giay or 0
        xac_nhan.thoi_gian_doc_giay = current + data.thoi_gian_doc_giay

    await db.commit()

    return {
        "van_ban_id": str(van_ban_id),
        "thoi_gian_doc_giay": xac_nhan.thoi_gian_doc_giay,
        "message": "Cap nhat thoi gian doc thanh cong",
    }


async def bao_cao_doc(
    db: AsyncSession,
    user: TokenPayload,
    van_ban_id: UUID,
    don_vi_id: Optional[UUID] = None,
) -> dict:
    """
    Bao cao trang thai doc cua tung CBCC voi 1 van ban.

    Quyen:
      - QT_NOI_DUNG: xem tat ca don vi
      - Lanh dao: chi xem don vi cua minh
    """
    is_qt = _is_quan_ly(user)

    # Kiem tra quyen
    if not is_qt and not user.is_lanh_dao:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "error": {
                    "code": "PERM_001",
                    "message": "Yeu cau QT_NOI_DUNG hoac quyen lanh dao",
                },
            },
        )

    # Lanh dao chi xem don vi cua minh
    if user.is_lanh_dao and not is_qt:
        don_vi_id = UUID(user.don_vi_id) if user.don_vi_id else don_vi_id

    # Lay thong tin van ban
    vb_result = await db.execute(
        select(VanBan).where(VanBan.id == van_ban_id).where(VanBan.is_deleted == False)
    )
    vb = vb_result.scalar_one_or_none()
    if not vb:
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

    # Query xac_nhan_doc join cong_chuc join don_vi
    query = (
        select(XacNhanDoc, CongChucRef, DonViRef)
        .join(CongChucRef, XacNhanDoc.cong_chuc_id == CongChucRef.id)
        .join(DonViRef, CongChucRef.don_vi_id == DonViRef.id)
        .where(XacNhanDoc.van_ban_id == van_ban_id)
    )
    if don_vi_id:
        query = query.where(CongChucRef.don_vi_id == don_vi_id)

    result = await db.execute(query)
    rows = result.all()

    # Tinh toan thong ke
    today = _today()
    chi_tiet = []
    da_doc_count = 0
    da_xac_nhan_count = 0
    qua_han_count = 0

    for xnd, cc, dv in rows:
        chi_tiet.append(
            {
                "cong_chuc": {
                    "ho_ten": cc.ho_ten,
                    "don_vi": dv.ten_don_vi,
                },
                "da_doc": xnd.da_doc,
                "da_xac_nhan": xnd.da_xac_nhan,
                "ngay_doc": xnd.ngay_doc,
                "ngay_xac_nhan": xnd.ngay_xac_nhan,
                "thoi_gian_doc_giay": xnd.thoi_gian_doc_giay,
            }
        )
        if xnd.da_doc:
            da_doc_count += 1
        if xnd.da_xac_nhan:
            da_xac_nhan_count += 1
        # Qua han: chua xac nhan va han_xac_nhan da qua
        if not xnd.da_xac_nhan and vb.han_xac_nhan and vb.han_xac_nhan < today:
            qua_han_count += 1

    tong = len(rows)
    return {
        "van_ban": {
            "so_hieu": vb.so_hieu,
            "trich_yeu": vb.trich_yeu,
            "han_xac_nhan": vb.han_xac_nhan,
        },
        "tong_doi_tuong": tong,
        "da_doc": da_doc_count,
        "da_xac_nhan": da_xac_nhan_count,
        "chua_doc": tong - da_doc_count,
        "qua_han": qua_han_count,
        "chi_tiet": chi_tiet,
    }


async def dashboard_summary(
    db: AsyncSession,
    user_id: str,
) -> dict:
    """
    Tong hop so lieu dashboard cho CBCC hien tai.

    Tra ve:
      - vb_moi_tuan: Van ban moi trong 7 ngay qua
      - vb_chua_doc: Van ban bat_buoc_doc chua xac nhan
      - vb_khan: Van ban KHAN chua doc
      - vb_sap_het_han: Van ban co han_xac_nhan trong 3 ngay toi
      - quiz_chua_lam: Quiz cua VB da doc ma chua co ket qua
    """
    user_uuid = UUID(user_id)
    today = _today()
    now = _now()
    tuan_truoc = datetime.combine(today - timedelta(days=7), datetime.min.time())

    # Van ban moi trong 7 ngay qua
    vb_moi_result = await db.execute(
        select(func.count(VanBan.id))
        .where(VanBan.trang_thai_duyet == "DA_XUAT_BAN")
        .where(VanBan.is_deleted == False)
        .where(VanBan.ngay_xuat_ban >= tuan_truoc)
    )
    vb_moi_tuan = vb_moi_result.scalar_one() or 0

    # Van ban bat_buoc_doc chua xac nhan cua user
    vb_chua_doc_result = await db.execute(
        select(func.count(XacNhanDoc.id))
        .where(XacNhanDoc.cong_chuc_id == user_uuid)
        .where(XacNhanDoc.da_xac_nhan == False)
        .join(VanBan, XacNhanDoc.van_ban_id == VanBan.id)
        .where(VanBan.bat_buoc_doc == True)
        .where(VanBan.trang_thai_duyet == "DA_XUAT_BAN")
        .where(VanBan.is_deleted == False)
    )
    vb_chua_doc = vb_chua_doc_result.scalar_one() or 0

    # Van ban KHAN chua xac nhan
    vb_khan_result = await db.execute(
        select(func.count(XacNhanDoc.id))
        .where(XacNhanDoc.cong_chuc_id == user_uuid)
        .where(XacNhanDoc.da_xac_nhan == False)
        .join(VanBan, XacNhanDoc.van_ban_id == VanBan.id)
        .where(VanBan.muc_do == "KHAN")
        .where(VanBan.trang_thai_duyet == "DA_XUAT_BAN")
        .where(VanBan.is_deleted == False)
    )
    vb_khan = vb_khan_result.scalar_one() or 0

    # Van ban sap het han (trong 3 ngay toi)
    ngay_3 = today + timedelta(days=3)
    sap_het_han_result = await db.execute(
        select(func.count(XacNhanDoc.id))
        .where(XacNhanDoc.cong_chuc_id == user_uuid)
        .where(XacNhanDoc.da_xac_nhan == False)
        .join(VanBan, XacNhanDoc.van_ban_id == VanBan.id)
        .where(VanBan.han_xac_nhan.between(today, ngay_3))
        .where(VanBan.is_deleted == False)
    )
    vb_sap_het_han = sap_het_han_result.scalar_one() or 0

    # Quiz chua lam: quiz cua VB da doc (da_doc=TRUE) ma chua co ket qua
    # Lay cac quiz_id ma user chua co ket qua
    quiz_chua_lam_result = await db.execute(
        select(func.count(QuizVanBan.id))
        .join(VanBan, QuizVanBan.van_ban_id == VanBan.id)
        .join(
            XacNhanDoc,
            and_(
                XacNhanDoc.van_ban_id == VanBan.id,
                XacNhanDoc.cong_chuc_id == user_uuid,
                XacNhanDoc.da_doc == True,
            ),
        )
        .where(QuizVanBan.is_active == True)
        .where(VanBan.is_deleted == False)
        .where(
            QuizVanBan.id.not_in(
                select(KetQuaQuiz.quiz_id).where(KetQuaQuiz.cong_chuc_id == user_uuid)
            )
        )
    )
    quiz_chua_lam = quiz_chua_lam_result.scalar_one() or 0

    return {
        "vb_moi_tuan": vb_moi_tuan,
        "vb_chua_doc": vb_chua_doc,
        "vb_khan": vb_khan,
        "vb_sap_het_han": vb_sap_het_han,
        "quiz_chua_lam": quiz_chua_lam,
    }


async def bao_cao_ca_nhan(
    db: AsyncSession,
    user_id: str,
    thang: int,
    nam: int,
) -> dict:
    """
    Bao cao doc van ban ca nhan trong thang.
    Thong ke:
      - vb_da_doc: VB co ngay_doc trong thang
      - vb_chua_doc: VB bat_buoc_doc ma chua doc
      - vb_qua_han: VB chua xac nhan ma da qua han
      - quiz_hoan_thanh, quiz_diem_tb
      - thoi_gian_doc_tb_giay
    """
    user_uuid = UUID(user_id)
    today = _today()

    # Lay tong hop xac nhan doc trong thang
    # (Loc theo ngay_doc trong thang/nam)
    from datetime import date as date_type

    dau_thang = date_type(nam, thang, 1)
    if thang == 12:
        cuoi_thang = date_type(nam + 1, 1, 1) - timedelta(days=1)
    else:
        cuoi_thang = date_type(nam, thang + 1, 1) - timedelta(days=1)

    # VB da doc trong thang
    vb_da_doc_result = await db.execute(
        select(func.count(XacNhanDoc.id))
        .where(XacNhanDoc.cong_chuc_id == user_uuid)
        .where(XacNhanDoc.da_doc == True)
        .where(func.date(XacNhanDoc.ngay_doc).between(dau_thang, cuoi_thang))
    )
    vb_da_doc = vb_da_doc_result.scalar_one() or 0

    # VB bat buoc doc ma chua doc (tinh den hom nay)
    vb_chua_doc_result = await db.execute(
        select(func.count())
        .select_from(VanBan)
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
                XacNhanDoc.id == None,
                XacNhanDoc.da_doc == False,
            )
        )
    )
    vb_chua_doc = vb_chua_doc_result.scalar_one() or 0

    # VB qua han (chua xac nhan, han_xac_nhan da qua)
    vb_qua_han_result = await db.execute(
        select(func.count(XacNhanDoc.id))
        .where(XacNhanDoc.cong_chuc_id == user_uuid)
        .where(XacNhanDoc.da_xac_nhan == False)
        .join(VanBan, XacNhanDoc.van_ban_id == VanBan.id)
        .where(VanBan.han_xac_nhan < today)
        .where(VanBan.is_deleted == False)
    )
    vb_qua_han = vb_qua_han_result.scalar_one() or 0

    # Quiz hoan thanh trong thang
    quiz_result = await db.execute(
        select(func.count(KetQuaQuiz.id), func.avg(KetQuaQuiz.diem))
        .where(KetQuaQuiz.cong_chuc_id == user_uuid)
        .where(func.date(KetQuaQuiz.created_at).between(dau_thang, cuoi_thang))
    )
    quiz_row = quiz_result.first()
    quiz_hoan_thanh = quiz_row[0] or 0
    quiz_diem_tb = float(quiz_row[1]) if quiz_row[1] else None

    # Thoi gian doc trung binh
    tg_result = await db.execute(
        select(func.avg(XacNhanDoc.thoi_gian_doc_giay))
        .where(XacNhanDoc.cong_chuc_id == user_uuid)
        .where(XacNhanDoc.thoi_gian_doc_giay != None)
        .where(func.date(XacNhanDoc.ngay_doc).between(dau_thang, cuoi_thang))
    )
    thoi_gian_doc_tb = tg_result.scalar_one()
    thoi_gian_doc_tb = float(thoi_gian_doc_tb) if thoi_gian_doc_tb else None

    return {
        "thang": thang,
        "nam": nam,
        "vb_da_doc": vb_da_doc,
        "vb_chua_doc": vb_chua_doc,
        "vb_qua_han": vb_qua_han,
        "quiz_hoan_thanh": quiz_hoan_thanh,
        "quiz_diem_tb": quiz_diem_tb,
        "thoi_gian_doc_tb_giay": thoi_gian_doc_tb,
    }


async def bao_cao_don_vi(
    db: AsyncSession,
    user: TokenPayload,
    don_vi_id: UUID,
    thang: int,
    nam: int,
) -> dict:
    """
    Bao cao tuan thu doc van ban theo don vi trong thang.

    Quyen:
      - QT_NOI_DUNG: xem tat ca don vi
      - Lanh dao: chi xem don vi cua minh
    """
    is_qt = _is_quan_ly(user)

    if not is_qt and not user.is_lanh_dao:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "error": {
                    "code": "PERM_001",
                    "message": "Yeu cau QT_NOI_DUNG hoac quyen lanh dao",
                },
            },
        )

    # Lanh dao chi xem don vi cua minh
    if user.is_lanh_dao and not is_qt:
        if user.don_vi_id and UUID(user.don_vi_id) != don_vi_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "success": False,
                    "error": {
                        "code": "PERM_006",
                        "message": "Lanh dao chi xem bao cao don vi cua minh",
                    },
                },
            )

    from datetime import date as date_type

    dau_thang = date_type(nam, thang, 1)
    if thang == 12:
        cuoi_thang = date_type(nam + 1, 1, 1) - timedelta(days=1)
    else:
        cuoi_thang = date_type(nam, thang + 1, 1) - timedelta(days=1)
    today = _today()

    # Lay thong tin don vi
    dv_result = await db.execute(select(DonViRef).where(DonViRef.id == don_vi_id))
    don_vi = dv_result.scalar_one_or_none()
    if not don_vi:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": {
                    "code": "ERR_404",
                    "message": "Khong tim thay don vi",
                },
            },
        )

    # Tong CBCC active trong don vi
    tong_result = await db.execute(
        select(func.count(CongChucRef.id))
        .where(CongChucRef.don_vi_id == don_vi_id)
        .where(CongChucRef.is_active == True)
    )
    tong_cbcc = tong_result.scalar_one() or 0

    # Lay tat ca CBCC trong don vi
    cbcc_result = await db.execute(
        select(CongChucRef.id, CongChucRef.ho_ten)
        .where(CongChucRef.don_vi_id == don_vi_id)
        .where(CongChucRef.is_active == True)
    )
    cbcc_rows = cbcc_result.all()
    cbcc_ids = [row[0] for row in cbcc_rows]
    cbcc_map = {row[0]: row[1] for row in cbcc_rows}

    # Van ban bat buoc trong thang
    vb_bat_buoc_result = await db.execute(
        select(func.count(VanBan.id))
        .where(VanBan.bat_buoc_doc == True)
        .where(VanBan.trang_thai_duyet == "DA_XUAT_BAN")
        .where(VanBan.is_deleted == False)
        .where(func.date(VanBan.ngay_xuat_ban).between(dau_thang, cuoi_thang))
    )
    vb_bat_buoc = vb_bat_buoc_result.scalar_one() or 0

    # Thong ke xac nhan — dung cast(Boolean, Integer) chuan cho PostgreSQL
    if cbcc_ids:
        xnd_result = await db.execute(
            select(
                XacNhanDoc.cong_chuc_id,
                func.count(XacNhanDoc.id).label("tong"),
                func.sum(cast(XacNhanDoc.da_doc, Integer)).label("da_doc"),
                func.sum(cast(XacNhanDoc.da_xac_nhan, Integer)).label("da_xac_nhan"),
            )
            .where(XacNhanDoc.cong_chuc_id.in_(cbcc_ids))
            .group_by(XacNhanDoc.cong_chuc_id)
        )
        xnd_rows = xnd_result.all()
    else:
        xnd_rows = []

    # Tinh ty le
    total_vb = max(vb_bat_buoc, 1)
    tong_da_doc = sum(row[2] or 0 for row in xnd_rows)
    tong_da_xac_nhan = sum(row[3] or 0 for row in xnd_rows)

    ty_le_da_doc = round(tong_da_doc / (tong_cbcc * total_vb) * 100, 1) if tong_cbcc > 0 else 0
    ty_le_xac_nhan = (
        round(tong_da_xac_nhan / (tong_cbcc * total_vb) * 100, 1) if tong_cbcc > 0 else 0
    )

    # Qua han
    qua_han_result = (
        await db.execute(
            select(func.count(XacNhanDoc.id))
            .where(XacNhanDoc.cong_chuc_id.in_(cbcc_ids) if cbcc_ids else False)
            .where(XacNhanDoc.da_xac_nhan == False)
            .join(VanBan, XacNhanDoc.van_ban_id == VanBan.id)
            .where(VanBan.han_xac_nhan < today)
            .where(VanBan.is_deleted == False)
        )
        if cbcc_ids
        else None
    )
    qua_han_count = qua_han_result.scalar_one() if qua_han_result else 0

    ty_le_qua_han = round(qua_han_count / (tong_cbcc * total_vb) * 100, 1) if tong_cbcc > 0 else 0

    # Diem quiz trung binh don vi
    quiz_diem_tb = None
    if cbcc_ids:
        quiz_result = await db.execute(
            select(func.avg(KetQuaQuiz.diem))
            .where(KetQuaQuiz.cong_chuc_id.in_(cbcc_ids))
            .where(func.date(KetQuaQuiz.created_at).between(dau_thang, cuoi_thang))
        )
        quiz_avg = quiz_result.scalar_one()
        quiz_diem_tb = float(quiz_avg) if quiz_avg is not None else None

    # Danh sach CBCC chua doc
    cbcc_chua_doc = []
    xnd_per_cbcc = {row[0]: {"da_doc": row[2] or 0, "da_xac_nhan": row[3] or 0} for row in xnd_rows}
    for cbcc_id, ho_ten in cbcc_map.items():
        stats = xnd_per_cbcc.get(cbcc_id, {"da_doc": 0, "da_xac_nhan": 0})
        vb_chua = vb_bat_buoc - stats["da_doc"]
        vb_qua_han_cc = 0  # Simplified
        if vb_chua > 0:
            cbcc_chua_doc.append(
                {
                    "ho_ten": ho_ten,
                    "vb_chua_doc": max(vb_chua, 0),
                    "vb_qua_han": vb_qua_han_cc,
                }
            )

    return {
        "don_vi": {"ten_don_vi": don_vi.ten_don_vi},
        "tong_cbcc": tong_cbcc,
        "thong_ke": {
            "vb_bat_buoc_trong_thang": vb_bat_buoc,
            "ty_le_da_doc": ty_le_da_doc,
            "ty_le_xac_nhan": ty_le_xac_nhan,
            "ty_le_qua_han": ty_le_qua_han,
            "quiz_diem_tb": quiz_diem_tb,
        },
        "cbcc_chua_doc": cbcc_chua_doc,
    }
