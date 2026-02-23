"""
portal_service/tests/test_dashboard.py
========================================
Tests cho Dashboard API Portal.

Business rules:
  - GET /dashboard/summary — tất cả CBCC xem được
  - Trả về: so_bai_moi_7_ngay, so_tai_lieu_moi_7_ngay, tin_ghim (max 3),
            tin_moi_nhat (max 5 bài không ghim)
  - GET /dashboard/lanh-dao — chỉ is_lanh_dao=True
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


class TestDashboardSummary:
    """Test dashboard tổng hợp cho tất cả CBCC."""

    async def test_cbcc_xem_duoc_summary(
        self, client: AsyncClient, cbcc_user
    ):
        """CBCC xem được dashboard summary."""
        resp = await client.get("/api/v1/dashboard/summary")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        summary = data["data"]
        # Kiểm tra các field bắt buộc
        assert "bai_viet_moi" in summary
        assert "tai_lieu_moi" in summary
        assert "tin_ghim" in summary
        assert "tin_moi_nhat" in summary

    async def test_tin_ghim_toi_da_3(
        self, client: AsyncClient, cbcc_user, db_session: AsyncSession
    ):
        """Danh sách tin ghim tối đa 3 bài."""
        from portal_service.models.bai_viet import BaiViet
        from uuid import UUID
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc).replace(tzinfo=None)
        # Tạo 3 bài ghim
        for i in range(3):
            bv = BaiViet(
                tieu_de=f"Bai ghim so {i + 1}",
                noi_dung="<p>noi dung</p>",
                trang_thai="XUAT_BAN",
                nguoi_soan_id=UUID("01014af6-1505-495b-95ab-8c1503cfa061"),
                is_ghim=True,
                ngay_xuat_ban=now,
                so_luot_xem=0,
                is_deleted=False,
                created_at=now,
                updated_at=now,
            )
            db_session.add(bv)
        await db_session.flush()

        resp = await client.get("/api/v1/dashboard/summary")
        assert resp.status_code == 200
        data = resp.json()
        tin_ghim = data["data"]["tin_ghim"]
        assert isinstance(tin_ghim, list)
        assert len(tin_ghim) <= 3  # tối đa 3

    async def test_tin_moi_nhat_toi_da_5(
        self, client: AsyncClient, cbcc_user, db_session: AsyncSession
    ):
        """Danh sách tin mới nhất tối đa 5 bài (không ghim)."""
        from portal_service.models.bai_viet import BaiViet
        from uuid import UUID
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc).replace(tzinfo=None)
        # Tạo 7 bài xuất bản (không ghim)
        for i in range(7):
            bv = BaiViet(
                tieu_de=f"Bai moi so {i + 1}",
                noi_dung="<p>noi dung</p>",
                trang_thai="XUAT_BAN",
                nguoi_soan_id=UUID("01014af6-1505-495b-95ab-8c1503cfa061"),
                is_ghim=False,
                ngay_xuat_ban=now,
                so_luot_xem=0,
                is_deleted=False,
                created_at=now,
                updated_at=now,
            )
            db_session.add(bv)
        await db_session.flush()

        resp = await client.get("/api/v1/dashboard/summary")
        assert resp.status_code == 200
        data = resp.json()
        tin_moi_nhat = data["data"]["tin_moi_nhat"]
        assert isinstance(tin_moi_nhat, list)
        assert len(tin_moi_nhat) <= 5  # tối đa 5

    async def test_dem_bai_moi_7_ngay(
        self, client: AsyncClient, cbcc_user, db_session: AsyncSession
    ):
        """Đếm bài viết mới trong 7 ngày qua."""
        from portal_service.models.bai_viet import BaiViet
        from uuid import UUID
        from datetime import datetime, timezone, timedelta

        now = datetime.now(timezone.utc).replace(tzinfo=None)
        # Tạo 2 bài mới trong 7 ngày
        for i in range(2):
            bv = BaiViet(
                tieu_de=f"Bai 7 ngay {i}",
                noi_dung="<p>noi dung</p>",
                trang_thai="XUAT_BAN",
                nguoi_soan_id=UUID("01014af6-1505-495b-95ab-8c1503cfa061"),
                is_ghim=False,
                ngay_xuat_ban=now,
                so_luot_xem=0,
                is_deleted=False,
                created_at=now,
                updated_at=now,
            )
            db_session.add(bv)
        await db_session.flush()

        resp = await client.get("/api/v1/dashboard/summary")
        assert resp.status_code == 200
        data = resp.json()
        # bai_viet_moi phải >= 2
        assert data["data"]["bai_viet_moi"] >= 2


class TestDashboardLanhDao:
    """Test dashboard thống kê Lãnh đạo."""

    async def test_lanh_dao_xem_duoc(
        self, client: AsyncClient, lanh_dao_user
    ):
        """Lãnh đạo xem được dashboard lãnh đạo."""
        resp = await client.get("/api/v1/dashboard/lanh-dao")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        # Kiểm tra có field thống kê
        summary = data["data"]
        assert "tong_bai_xuat_ban" in summary or "thong_ke" in summary or len(summary) > 0

    async def test_cbcc_khong_xem_duoc(
        self, client: AsyncClient, cbcc_user
    ):
        """CBCC không có quyền xem dashboard lãnh đạo."""
        resp = await client.get("/api/v1/dashboard/lanh-dao")
        assert resp.status_code == 403
