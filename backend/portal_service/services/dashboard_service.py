"""
portal_service/services/dashboard_service.py
==============================================
Business logic cho Dashboard Portal.

Tổng hợp dữ liệu nhanh cho 2 loại dashboard:
  - get_portal_summary()   → Widget trang chủ (tất cả CBCC)
  - get_lanh_dao_summary() → Thống kê lãnh đạo (lãnh đạo + ADMIN)
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from portal_service.models.bai_viet import BaiViet
from portal_service.models.chuyen_muc import ChuyenMuc
from portal_service.models.tai_lieu import TaiLieu
from portal_service.schemas.dashboard import (
    LanhDaoDashboard,
    PortalDashboardSummary,
    TaiLieuStats,
    ThongKeChuyenMuc,
    TinGhimBrief,
    TinTucStats,
)
from portal_service.services.tai_lieu_service import _la_admin_qt
from shared.auth import TokenPayload


def _now() -> datetime:
    """Trả về thời điểm hiện tại (UTC, naive)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


async def get_portal_summary(
    db: AsyncSession,
    user: TokenPayload,
) -> PortalDashboardSummary:
    """Tổng hợp dữ liệu cho widget trang chủ Portal.

    Gồm:
      - bai_viet_moi: số bài XUAT_BAN trong 7 ngày qua
      - tai_lieu_moi: số tài liệu upload trong 7 ngày qua (lọc quyền)
      - tin_ghim:     bài ghim is_ghim=True (tối đa 3, sắp ngay_xuat_ban DESC)
      - tin_moi_nhat: 5 bài mới nhất không ghim (XUAT_BAN, ngay_xuat_ban DESC)
    """
    ngay_7_truoc = _now() - timedelta(days=7)

    # -----------------------------------------------------------------------
    # 1. Đếm bài viết mới trong 7 ngày
    # -----------------------------------------------------------------------
    bv_moi_stmt = select(func.count()).where(
        BaiViet.trang_thai == "XUAT_BAN",
        BaiViet.is_deleted == False,  # noqa: E712
        BaiViet.ngay_xuat_ban >= ngay_7_truoc,
    )
    bv_moi_result = await db.execute(bv_moi_stmt)
    bai_viet_moi = bv_moi_result.scalar() or 0

    # -----------------------------------------------------------------------
    # 2. Đếm tài liệu mới trong 7 ngày
    # -----------------------------------------------------------------------
    tl_moi_stmt = select(func.count()).where(
        TaiLieu.is_deleted == False,  # noqa: E712
        TaiLieu.created_at >= ngay_7_truoc,
    )
    # ADMIN / QT_NOI_DUNG đếm tất cả; user thường chỉ đếm bản quyền TAT_CA
    if not _la_admin_qt(user):
        tl_moi_stmt = tl_moi_stmt.where(TaiLieu.quyen_truy_cap == "TAT_CA")

    tl_moi_result = await db.execute(tl_moi_stmt)
    tai_lieu_moi = tl_moi_result.scalar() or 0

    # -----------------------------------------------------------------------
    # 3. Bài ghim (tối đa 3, chỉ XUAT_BAN)
    # -----------------------------------------------------------------------
    ghim_stmt = (
        select(BaiViet)
        .where(
            BaiViet.is_ghim == True,  # noqa: E712
            BaiViet.trang_thai == "XUAT_BAN",
            BaiViet.is_deleted == False,  # noqa: E712
        )
        .order_by(BaiViet.ngay_xuat_ban.desc())
        .limit(3)
    )
    ghim_result = await db.execute(ghim_stmt)
    tin_ghim = [
        TinGhimBrief.model_validate(bv)
        for bv in ghim_result.scalars().all()
    ]

    # -----------------------------------------------------------------------
    # 4. 5 bài mới nhất (không ghim, XUAT_BAN)
    # -----------------------------------------------------------------------
    moi_nhat_stmt = (
        select(BaiViet)
        .where(
            BaiViet.is_ghim == False,  # noqa: E712
            BaiViet.trang_thai == "XUAT_BAN",
            BaiViet.is_deleted == False,  # noqa: E712
        )
        .order_by(BaiViet.ngay_xuat_ban.desc())
        .limit(5)
    )
    moi_nhat_result = await db.execute(moi_nhat_stmt)
    tin_moi_nhat = [
        TinGhimBrief.model_validate(bv)
        for bv in moi_nhat_result.scalars().all()
    ]

    return PortalDashboardSummary(
        bai_viet_moi=bai_viet_moi,
        tai_lieu_moi=tai_lieu_moi,
        tin_ghim=tin_ghim,
        tin_moi_nhat=tin_moi_nhat,
    )


async def get_lanh_dao_summary(
    db: AsyncSession,
    thang: int,
    nam: int,
) -> LanhDaoDashboard:
    """Thống kê Portal cho Lãnh đạo trong tháng/năm cụ thể.

    Phần Portal gồm:
      - Thống kê bài viết (tổng đã xuất bản + trong tháng + breakdown chuyên mục)
      - Thống kê tài liệu (tổng + trong tháng)
    """
    # Xác định khoảng thời gian tháng
    tu_ngay = datetime(nam, thang, 1)
    if thang == 12:
        den_ngay = datetime(nam + 1, 1, 1)
    else:
        den_ngay = datetime(nam, thang + 1, 1)

    # -----------------------------------------------------------------------
    # Thống kê bài viết
    # -----------------------------------------------------------------------
    # Tổng bài đã xuất bản
    tong_bv_stmt = select(func.count()).where(
        BaiViet.trang_thai == "XUAT_BAN",
        BaiViet.is_deleted == False,  # noqa: E712
    )
    tong_bv_result = await db.execute(tong_bv_stmt)
    tong_bai_xuat_ban = tong_bv_result.scalar() or 0

    # Bài mới trong tháng
    bv_thang_stmt = select(func.count()).where(
        BaiViet.trang_thai == "XUAT_BAN",
        BaiViet.is_deleted == False,  # noqa: E712
        BaiViet.ngay_xuat_ban >= tu_ngay,
        BaiViet.ngay_xuat_ban < den_ngay,
    )
    bv_thang_result = await db.execute(bv_thang_stmt)
    bai_moi_thang_nay = bv_thang_result.scalar() or 0

    # Breakdown theo chuyên mục
    theo_cm_stmt = (
        select(
            ChuyenMuc.ten,
            ChuyenMuc.slug,
            func.count(BaiViet.id).label("so_bai"),
        )
        .outerjoin(BaiViet, BaiViet.chuyen_muc_id == ChuyenMuc.id)
        .where(
            ChuyenMuc.is_active == True,  # noqa: E712
        )
        .filter(
            (BaiViet.trang_thai == "XUAT_BAN") | (BaiViet.id.is_(None)),
            (BaiViet.is_deleted == False) | (BaiViet.id.is_(None)),  # noqa: E712
        )
        .group_by(ChuyenMuc.id, ChuyenMuc.ten, ChuyenMuc.slug)
        .order_by(func.count(BaiViet.id).desc())
    )
    theo_cm_result = await db.execute(theo_cm_stmt)
    theo_chuyen_muc = [
        ThongKeChuyenMuc(ten_chuyen_muc=row.ten, slug=row.slug, so_bai=row.so_bai or 0)
        for row in theo_cm_result.all()
    ]

    # -----------------------------------------------------------------------
    # Thống kê tài liệu
    # -----------------------------------------------------------------------
    tong_tl_stmt = select(func.count()).where(
        TaiLieu.is_deleted == False,  # noqa: E712
    )
    tong_tl_result = await db.execute(tong_tl_stmt)
    tong_tai_lieu = tong_tl_result.scalar() or 0

    tl_thang_stmt = select(func.count()).where(
        TaiLieu.is_deleted == False,  # noqa: E712
        TaiLieu.created_at >= tu_ngay,
        TaiLieu.created_at < den_ngay,
    )
    tl_thang_result = await db.execute(tl_thang_stmt)
    moi_thang_nay = tl_thang_result.scalar() or 0

    return LanhDaoDashboard(
        thang=thang,
        nam=nam,
        tin_tuc=TinTucStats(
            tong_bai_xuat_ban=tong_bai_xuat_ban,
            bai_moi_thang_nay=bai_moi_thang_nay,
            theo_chuyen_muc=theo_chuyen_muc,
        ),
        tai_lieu=TaiLieuStats(
            tong_tai_lieu=tong_tai_lieu,
            moi_thang_nay=moi_thang_nay,
        ),
    )
