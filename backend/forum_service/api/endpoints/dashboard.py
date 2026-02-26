"""
forum_service/api/endpoints/dashboard.py
=========================================
Endpoints Dashboard va Bao cao.

Dashboard: summary cho widget trang chu
Bao cao: thong ke ca nhan, don vi, top contributors
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))

from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from forum_service.dependencies import (
    CurrentUserDep,
    DatabaseDep,
    get_current_user,
    get_db,
)
from forum_service.models import BieuQuyet, ChuDe, TraLoi
from forum_service.models.base import CongChucRef
from forum_service.schemas.dashboard import (
    BaoCaoCaNhan,
    BaoCaoDonVi,
    DashboardSummary,
    TopContributor,
)

dashboard_router = APIRouter(prefix="/dashboard", tags=["Dashboard"])
bao_cao_router = APIRouter(prefix="/bao-cao", tags=["Báo cáo"])


def _now() -> datetime:
    """Lay thoi gian hien tai (UTC)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


@dashboard_router.get("/summary")
async def dashboard_summary(
    db: DatabaseDep,
    current_user: CurrentUserDep,
) -> dict:
    """
    Summary cho widget trang chu.

    Returns:
      - chu_de_moi_tuan: count chu_de created in last 7 days
      - tra_loi_chua_doc: placeholder (TODO: implement notification)
      - upvote_tuan: count bieu_quyet (UP) cho chu_de/tra_loi cua user trong 7 ngay
      - chu_de_cua_toi_chua_tra_loi: count chu_de where tac_gia_id=user and so_tra_loi=0
    """
    user_uuid = UUID(current_user.sub)
    now = _now()
    week_ago = now - timedelta(days=7)

    # 1. chu_de_moi_tuan: count chu_de created in last 7 days
    stmt_chu_de_moi = select(func.count(ChuDe.id)).where(
        ChuDe.is_deleted == False,
        ChuDe.trang_thai.in_(["MO", "DONG"]),
        ChuDe.created_at >= week_ago,
    )
    chu_de_moi_tuan = (await db.execute(stmt_chu_de_moi)).scalar_one()

    # 2. upvote_tuan: count bieu_quyet (UP) cho content cua user trong 7 ngay
    # JOIN chu_de OR tra_loi where tac_gia_id = user
    stmt_upvote_chu_de = (
        select(func.count(BieuQuyet.id))
        .join(ChuDe, and_(BieuQuyet.doi_tuong_type == "CHU_DE", BieuQuyet.doi_tuong_id == ChuDe.id))
        .where(
            ChuDe.tac_gia_id == user_uuid,
            BieuQuyet.loai == "UP",
            BieuQuyet.created_at >= week_ago,
        )
    )
    upvote_chu_de = (await db.execute(stmt_upvote_chu_de)).scalar_one()

    stmt_upvote_tra_loi = (
        select(func.count(BieuQuyet.id))
        .join(TraLoi, and_(BieuQuyet.doi_tuong_type == "TRA_LOI", BieuQuyet.doi_tuong_id == TraLoi.id))
        .where(
            TraLoi.tac_gia_id == user_uuid,
            BieuQuyet.loai == "UP",
            BieuQuyet.created_at >= week_ago,
        )
    )
    upvote_tra_loi = (await db.execute(stmt_upvote_tra_loi)).scalar_one()
    upvote_tuan = upvote_chu_de + upvote_tra_loi

    # 3. chu_de_cua_toi_chua_tra_loi: count chu_de cua user ma so_tra_loi = 0
    stmt_chua_tra_loi = select(func.count(ChuDe.id)).where(
        ChuDe.tac_gia_id == user_uuid,
        ChuDe.is_deleted == False,
        ChuDe.so_tra_loi == 0,
        ChuDe.trang_thai.in_(["MO", "DONG"]),
    )
    chu_de_chua_tra_loi = (await db.execute(stmt_chua_tra_loi)).scalar_one()

    summary = DashboardSummary(
        chu_de_moi_tuan=chu_de_moi_tuan,
        tra_loi_chua_doc=0,  # placeholder
        upvote_tuan=upvote_tuan,
        chu_de_cua_toi_chua_tra_loi=chu_de_chua_tra_loi,
    )

    return {
        "success": True,
        "data": summary.model_dump(),
        "message": "Lay summary thanh cong",
    }


@bao_cao_router.get("/ca-nhan")
async def bao_cao_ca_nhan(
    db: DatabaseDep,
    current_user: CurrentUserDep,
    thang: int = Query(..., ge=1, le=12),
    nam: int = Query(..., ge=2020),
) -> dict:
    """
    Thong ke dong gop ca nhan theo thang.

    Returns:
      - chu_de_da_dang: count chu_de created in month
      - tra_loi_da_dang: count tra_loi created in month
      - upvote_nhan_duoc: count upvote (UP) cho content trong month
      - bai_ghim: count chu_de is_ghim=True
      - dap_an_chuan: count tra_loi is_dap_an_chuan=True
    """
    user_uuid = UUID(current_user.sub)

    # Tinh khoang thoi gian thang
    start_date = datetime(nam, thang, 1)
    if thang == 12:
        end_date = datetime(nam + 1, 1, 1)
    else:
        end_date = datetime(nam, thang + 1, 1)

    # 1. chu_de_da_dang
    stmt_chu_de = select(func.count(ChuDe.id)).where(
        ChuDe.tac_gia_id == user_uuid,
        ChuDe.is_deleted == False,
        ChuDe.created_at >= start_date,
        ChuDe.created_at < end_date,
    )
    chu_de_da_dang = (await db.execute(stmt_chu_de)).scalar_one()

    # 2. tra_loi_da_dang
    stmt_tra_loi = select(func.count(TraLoi.id)).where(
        TraLoi.tac_gia_id == user_uuid,
        TraLoi.is_deleted == False,
        TraLoi.created_at >= start_date,
        TraLoi.created_at < end_date,
    )
    tra_loi_da_dang = (await db.execute(stmt_tra_loi)).scalar_one()

    # 3. upvote_nhan_duoc (chi chu_de/tra_loi trong thang nay)
    stmt_upvote_chu_de = (
        select(func.count(BieuQuyet.id))
        .join(ChuDe, and_(BieuQuyet.doi_tuong_type == "CHU_DE", BieuQuyet.doi_tuong_id == ChuDe.id))
        .where(
            ChuDe.tac_gia_id == user_uuid,
            BieuQuyet.loai == "UP",
            ChuDe.created_at >= start_date,
            ChuDe.created_at < end_date,
        )
    )
    upvote_chu_de = (await db.execute(stmt_upvote_chu_de)).scalar_one()

    stmt_upvote_tra_loi = (
        select(func.count(BieuQuyet.id))
        .join(TraLoi, and_(BieuQuyet.doi_tuong_type == "TRA_LOI", BieuQuyet.doi_tuong_id == TraLoi.id))
        .where(
            TraLoi.tac_gia_id == user_uuid,
            BieuQuyet.loai == "UP",
            TraLoi.created_at >= start_date,
            TraLoi.created_at < end_date,
        )
    )
    upvote_tra_loi = (await db.execute(stmt_upvote_tra_loi)).scalar_one()
    upvote_nhan_duoc = upvote_chu_de + upvote_tra_loi

    # 4. bai_ghim (chu_de is_ghim=True, tac gia = user)
    stmt_bai_ghim = select(func.count(ChuDe.id)).where(
        ChuDe.tac_gia_id == user_uuid,
        ChuDe.is_ghim == True,
        ChuDe.is_deleted == False,
    )
    bai_ghim = (await db.execute(stmt_bai_ghim)).scalar_one()

    # 5. dap_an_chuan (tra_loi is_dap_an_chuan=True, tac gia = user)
    stmt_dap_an = select(func.count(TraLoi.id)).where(
        TraLoi.tac_gia_id == user_uuid,
        TraLoi.is_dap_an_chuan == True,
        TraLoi.is_deleted == False,
    )
    dap_an_chuan = (await db.execute(stmt_dap_an)).scalar_one()

    bao_cao = BaoCaoCaNhan(
        thang=thang,
        nam=nam,
        chu_de_da_dang=chu_de_da_dang,
        tra_loi_da_dang=tra_loi_da_dang,
        upvote_nhan_duoc=upvote_nhan_duoc,
        bai_ghim=bai_ghim,
        dap_an_chuan=dap_an_chuan,
    )

    return {
        "success": True,
        "data": bao_cao.model_dump(),
        "message": "Lay bao cao ca nhan thanh cong",
    }


@bao_cao_router.get("/don-vi/{don_vi_id}")
async def bao_cao_don_vi(
    don_vi_id: UUID,
    db: DatabaseDep,
    current_user: CurrentUserDep,
    thang: int = Query(..., ge=1, le=12),
    nam: int = Query(..., ge=2020),
) -> dict:
    """
    Thong ke dong gop don vi.

    Kiem tra quyen:
      - User phai la thanh vien cua don_vi nay hoac lanh dao

    Returns:
      - tong_chu_de: count chu_de cua don vi
      - tong_tra_loi: count tra_loi cua don vi
      - tong_upvote: sum upvote cho content cua don vi
      - so_nguoi_tham_gia: distinct count user da dang chu_de/tra_loi
    """
    user_uuid = UUID(current_user.sub)

    # Kiem tra quyen: user phai la thanh vien don_vi hoac lanh dao
    # Load user from public.cong_chuc
    stmt_user = select(CongChucRef).where(CongChucRef.id == user_uuid)
    user_obj = (await db.execute(stmt_user)).scalar_one_or_none()

    if not user_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": {"code": "AUTH_001", "message": "User khong ton tai"},
            },
        )

    # Check permission: user thuoc don_vi nay OR is_lanh_dao
    if user_obj.don_vi_id != don_vi_id and not user_obj.is_lanh_dao:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "error": {
                    "code": "PERM_001",
                    "message": "Ban khong co quyen xem bao cao don vi nay",
                },
            },
        )

    # Tinh khoang thoi gian thang
    start_date = datetime(nam, thang, 1)
    if thang == 12:
        end_date = datetime(nam + 1, 1, 1)
    else:
        end_date = datetime(nam, thang + 1, 1)

    # 1. tong_chu_de: JOIN CongChucRef de filter don_vi_id
    stmt_chu_de = (
        select(func.count(ChuDe.id))
        .join(CongChucRef, ChuDe.tac_gia_id == CongChucRef.id)
        .where(
            CongChucRef.don_vi_id == don_vi_id,
            ChuDe.is_deleted == False,
            ChuDe.created_at >= start_date,
            ChuDe.created_at < end_date,
        )
    )
    tong_chu_de = (await db.execute(stmt_chu_de)).scalar_one()

    # 2. tong_tra_loi
    stmt_tra_loi = (
        select(func.count(TraLoi.id))
        .join(CongChucRef, TraLoi.tac_gia_id == CongChucRef.id)
        .where(
            CongChucRef.don_vi_id == don_vi_id,
            TraLoi.is_deleted == False,
            TraLoi.created_at >= start_date,
            TraLoi.created_at < end_date,
        )
    )
    tong_tra_loi = (await db.execute(stmt_tra_loi)).scalar_one()

    # 3. tong_upvote (sum upvote cho content cua don vi)
    # Chu de
    stmt_upvote_chu_de = (
        select(func.coalesce(func.sum(ChuDe.so_upvote), 0))
        .join(CongChucRef, ChuDe.tac_gia_id == CongChucRef.id)
        .where(
            CongChucRef.don_vi_id == don_vi_id,
            ChuDe.is_deleted == False,
            ChuDe.created_at >= start_date,
            ChuDe.created_at < end_date,
        )
    )
    upvote_chu_de = (await db.execute(stmt_upvote_chu_de)).scalar_one()

    # Tra loi
    stmt_upvote_tra_loi = (
        select(func.coalesce(func.sum(TraLoi.so_upvote), 0))
        .join(CongChucRef, TraLoi.tac_gia_id == CongChucRef.id)
        .where(
            CongChucRef.don_vi_id == don_vi_id,
            TraLoi.is_deleted == False,
            TraLoi.created_at >= start_date,
            TraLoi.created_at < end_date,
        )
    )
    upvote_tra_loi = (await db.execute(stmt_upvote_tra_loi)).scalar_one()
    tong_upvote = upvote_chu_de + upvote_tra_loi

    # 4. so_nguoi_tham_gia: distinct user da dang chu_de OR tra_loi
    # UNION chu_de.tac_gia_id va tra_loi.tac_gia_id
    stmt_tham_gia = text(
        """
        SELECT COUNT(DISTINCT user_id) FROM (
            SELECT cd.tac_gia_id AS user_id
            FROM forum.chu_de cd
            JOIN public.cong_chuc cc ON cd.tac_gia_id = cc.id
            WHERE cc.don_vi_id = :don_vi_id
              AND cd.is_deleted = FALSE
              AND cd.created_at >= :start_date
              AND cd.created_at < :end_date
            UNION
            SELECT tl.tac_gia_id AS user_id
            FROM forum.tra_loi tl
            JOIN public.cong_chuc cc ON tl.tac_gia_id = cc.id
            WHERE cc.don_vi_id = :don_vi_id
              AND tl.is_deleted = FALSE
              AND tl.created_at >= :start_date
              AND tl.created_at < :end_date
        ) AS users
        """
    )
    result = await db.execute(
        stmt_tham_gia,
        {
            "don_vi_id": don_vi_id,
            "start_date": start_date,
            "end_date": end_date,
        },
    )
    so_nguoi_tham_gia = result.scalar_one()

    # Get don_vi_ten
    don_vi_ten = user_obj.don_vi.ten_don_vi if user_obj.don_vi_id == don_vi_id else None
    if not don_vi_ten:
        # Query don_vi
        from forum_service.models.base import DonViRef
        stmt_don_vi = select(DonViRef.ten_don_vi).where(DonViRef.id == don_vi_id)
        don_vi_ten = (await db.execute(stmt_don_vi)).scalar_one_or_none()

    bao_cao = BaoCaoDonVi(
        don_vi_id=don_vi_id,
        don_vi_ten=don_vi_ten,
        thang=thang,
        nam=nam,
        tong_chu_de=tong_chu_de,
        tong_tra_loi=tong_tra_loi,
        tong_upvote=tong_upvote,
        so_nguoi_tham_gia=so_nguoi_tham_gia,
    )

    return {
        "success": True,
        "data": bao_cao.model_dump(),
        "message": "Lay bao cao don vi thanh cong",
    }


@bao_cao_router.get("/top")
async def bao_cao_top_contributors(
    db: DatabaseDep,
    current_user: CurrentUserDep,
    thang: Optional[int] = Query(default=None, ge=1, le=12),
    nam: Optional[int] = Query(default=None, ge=2020),
    limit: int = Query(default=10, ge=1, le=100),
) -> dict:
    """
    Bao cao top contributors.

    Diem tinh: chu_de*3 + tra_loi*2 + dap_an_chuan*5 + upvote*1

    Query params:
      - thang, nam: filter theo thang (optional, neu khong co thi lay tat ca)
      - limit: so luong top user (default 10)

    Returns:
      - List TopContributor
    """
    # Build date filter
    date_filter_chu_de = []
    date_filter_tra_loi = []
    if thang and nam:
        start_date = datetime(nam, thang, 1)
        if thang == 12:
            end_date = datetime(nam + 1, 1, 1)
        else:
            end_date = datetime(nam, thang + 1, 1)
        date_filter_chu_de = [ChuDe.created_at >= start_date, ChuDe.created_at < end_date]
        date_filter_tra_loi = [TraLoi.created_at >= start_date, TraLoi.created_at < end_date]

    # Raw SQL query de tinh diem
    # UNION chu_de va tra_loi, GROUP BY user, compute diem
    sql = text(
        """
        WITH user_stats AS (
            SELECT
                tac_gia_id,
                COUNT(CASE WHEN type='CHU_DE' THEN 1 END) AS chu_de,
                COUNT(CASE WHEN type='TRA_LOI' THEN 1 END) AS tra_loi,
                COUNT(CASE WHEN type='DAP_AN' THEN 1 END) AS dap_an_chuan,
                COALESCE(SUM(so_upvote), 0) AS upvote
            FROM (
                SELECT
                    cd.tac_gia_id,
                    'CHU_DE' AS type,
                    cd.so_upvote
                FROM forum.chu_de cd
                WHERE cd.is_deleted = FALSE
                  AND (:thang IS NULL OR EXTRACT(MONTH FROM cd.created_at) = :thang)
                  AND (:nam IS NULL OR EXTRACT(YEAR FROM cd.created_at) = :nam)
                UNION ALL
                SELECT
                    tl.tac_gia_id,
                    'TRA_LOI' AS type,
                    tl.so_upvote
                FROM forum.tra_loi tl
                WHERE tl.is_deleted = FALSE
                  AND (:thang IS NULL OR EXTRACT(MONTH FROM tl.created_at) = :thang)
                  AND (:nam IS NULL OR EXTRACT(YEAR FROM tl.created_at) = :nam)
                UNION ALL
                SELECT
                    tl.tac_gia_id,
                    'DAP_AN' AS type,
                    0 AS so_upvote
                FROM forum.tra_loi tl
                WHERE tl.is_dap_an_chuan = TRUE
                  AND tl.is_deleted = FALSE
            ) AS combined
            GROUP BY tac_gia_id
        )
        SELECT
            us.tac_gia_id,
            us.chu_de,
            us.tra_loi,
            us.upvote,
            us.dap_an_chuan,
            (us.chu_de * 3 + us.tra_loi * 2 + us.dap_an_chuan * 5 + us.upvote) AS diem
        FROM user_stats us
        ORDER BY diem DESC
        LIMIT :limit
        """
    )

    result = await db.execute(sql, {"thang": thang, "nam": nam, "limit": limit})
    rows = result.fetchall()

    # Build TopContributor list
    top_list = []
    for row in rows:
        user_id = row[0]
        chu_de_count = row[1]
        tra_loi_count = row[2]
        upvote_count = row[3]
        dap_an_count = row[4]
        diem = row[5]

        # Load user info
        stmt_user = select(CongChucRef).where(CongChucRef.id == user_id)
        user_obj = (await db.execute(stmt_user)).scalar_one_or_none()

        if user_obj:
            user_brief = {
                "id": user_obj.id,
                "ma_cc": user_obj.ma_cc,
                "ho_ten": user_obj.ho_ten,
                "chuc_vu": user_obj.chuc_vu,
                "don_vi_ten": user_obj.don_vi.ten_don_vi if user_obj.don_vi else None,
            }
            top_list.append(
                TopContributor(
                    user=user_brief,
                    chu_de=chu_de_count,
                    tra_loi=tra_loi_count,
                    upvote=upvote_count,
                    dap_an_chuan=dap_an_count,
                    diem=diem,
                )
            )

    return {
        "success": True,
        "data": [item.model_dump() for item in top_list],
        "message": "Lay top contributors thanh cong",
    }
