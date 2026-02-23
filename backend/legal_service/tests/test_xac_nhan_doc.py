"""
legal_service/tests/test_xac_nhan_doc.py
==========================================
Tests xác nhận đọc văn bản.

Business rules:
  - Xác nhận đọc → tạo/cập nhật bản ghi xac_nhan_doc
  - Đã xác nhận rồi → LEGAL_ERR_005 (không xác nhận lại được)
  - Tracking cộng dồn thời gian đọc (không reset)
  - Dashboard trả về 5 metrics
"""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class TestXacNhanDoc:
    """Test xác nhận đã đọc và hiểu văn bản."""

    async def test_xac_nhan_thanh_cong(
        self, client: AsyncClient, cbcc_user, published_van_ban, db_session: AsyncSession
    ):
        """CBCC xác nhận đọc VB thành công."""
        vb_id = published_van_ban["id"]

        resp = await client.post(
            f"/api/legal/v1/van-ban/{vb_id}/xac-nhan",
            json={"ghi_chu": "Đã đọc và hiểu"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["da_xac_nhan"] is True
        assert data["data"]["van_ban_id"] == vb_id

    async def test_xac_nhan_trung_lap_loi(
        self, client: AsyncClient, cbcc_user, published_van_ban, db_session: AsyncSession
    ):
        """Xác nhận 2 lần → lần 2 lỗi LEGAL_ERR_005."""
        vb_id = published_van_ban["id"]

        # Lần 1: thành công
        r1 = await client.post(
            f"/api/legal/v1/van-ban/{vb_id}/xac-nhan",
            json={"ghi_chu": "Đã đọc"},
        )
        assert r1.status_code == 200

        # Lần 2: lỗi trùng lặp
        r2 = await client.post(
            f"/api/legal/v1/van-ban/{vb_id}/xac-nhan",
            json={"ghi_chu": "Đọc lại"},
        )
        assert r2.status_code == 400
        data = r2.json()
        assert data["success"] is False
        assert data["error"]["code"] == "LEGAL_ERR_005"

    async def test_xac_nhan_khong_ton_tai_van_ban(
        self, client: AsyncClient, cbcc_user
    ):
        """Xác nhận VB không tồn tại → 404."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        resp = await client.post(
            f"/api/legal/v1/van-ban/{fake_id}/xac-nhan",
            json={},
        )
        assert resp.status_code == 404

    async def test_xac_nhan_tao_ban_ghi_da_doc(
        self, client: AsyncClient, cbcc_user, published_van_ban, db_session: AsyncSession
    ):
        """Xác nhận → bản ghi xac_nhan_doc có da_doc=True và da_xac_nhan=True."""
        from uuid import UUID
        from legal_service.models.xac_nhan_doc import XacNhanDoc

        vb_id = UUID(published_van_ban["id"])
        cbcc_id = UUID("00327c43-c9a3-44d7-8306-7084e75cb2b5")  # cbcc_user idx=0

        resp = await client.post(
            f"/api/legal/v1/van-ban/{vb_id}/xac-nhan",
            json={"ghi_chu": "Đã hiểu nội dung"},
        )
        assert resp.status_code == 200

        db_session.expire_all()  # sync method, not async
        xnd = (
            await db_session.execute(
                select(XacNhanDoc)
                .where(XacNhanDoc.van_ban_id == vb_id)
                .where(XacNhanDoc.cong_chuc_id == cbcc_id)
            )
        ).scalar_one_or_none()

        assert xnd is not None
        assert xnd.da_doc is True
        assert xnd.da_xac_nhan is True
        assert xnd.ngay_xac_nhan is not None


class TestTrackingDoc:
    """Test ghi nhận thời gian đọc."""

    async def test_tracking_lan_dau(
        self, client: AsyncClient, cbcc_user, published_van_ban
    ):
        """Tracking lần đầu → tạo bản ghi với thời gian = input."""
        vb_id = published_van_ban["id"]

        resp = await client.patch(
            f"/api/legal/v1/van-ban/{vb_id}/tracking",
            json={"thoi_gian_doc_giay": 30},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["thoi_gian_doc_giay"] == 30

    async def test_tracking_cong_don_thoi_gian(
        self, client: AsyncClient, cbcc_user, published_van_ban
    ):
        """Tracking cộng dồn: gọi 2 lần 30s → tổng 60s."""
        vb_id = published_van_ban["id"]

        # Gọi lần 1: 30s
        r1 = await client.patch(
            f"/api/legal/v1/van-ban/{vb_id}/tracking",
            json={"thoi_gian_doc_giay": 30},
        )
        assert r1.status_code == 200

        # Gọi lần 2: 30s → tổng phải là 60s
        r2 = await client.patch(
            f"/api/legal/v1/van-ban/{vb_id}/tracking",
            json={"thoi_gian_doc_giay": 30},
        )
        assert r2.status_code == 200
        data = r2.json()
        assert data["data"]["thoi_gian_doc_giay"] == 60

    async def test_tracking_nhieu_lan(
        self, client: AsyncClient, cbcc_user, published_van_ban
    ):
        """Tracking nhiều lần → tổng cộng dồn chính xác."""
        vb_id = published_van_ban["id"]
        total = 0

        for seconds in [10, 20, 15, 5]:
            total += seconds
            resp = await client.patch(
                f"/api/legal/v1/van-ban/{vb_id}/tracking",
                json={"thoi_gian_doc_giay": seconds},
            )
            assert resp.status_code == 200

        # Lần cuối phải trả về tổng = 50
        assert resp.json()["data"]["thoi_gian_doc_giay"] == total


class TestDashboard:
    """Test dashboard summary metrics."""

    async def test_dashboard_summary_co_du_fields(
        self, client: AsyncClient, cbcc_user
    ):
        """Dashboard trả về đủ 5 metrics."""
        resp = await client.get("/api/legal/v1/dashboard/summary")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True

        metrics = data["data"]
        assert "vb_moi_tuan" in metrics
        assert "vb_chua_doc" in metrics
        assert "vb_khan" in metrics
        assert "vb_sap_het_han" in metrics
        assert "quiz_chua_lam" in metrics

    async def test_dashboard_summary_gia_tri_hop_le(
        self, client: AsyncClient, cbcc_user
    ):
        """Tất cả metrics trong dashboard phải >= 0."""
        resp = await client.get("/api/legal/v1/dashboard/summary")
        assert resp.status_code == 200
        metrics = resp.json()["data"]

        for key, value in metrics.items():
            assert value >= 0, f"Metric '{key}' phải >= 0, got {value}"

    async def test_dashboard_cho_admin(self, client: AsyncClient, admin_user):
        """Admin cũng xem được dashboard."""
        resp = await client.get("/api/legal/v1/dashboard/summary")
        assert resp.status_code == 200
        assert resp.json()["success"] is True


class TestBaoCao:
    """Test báo cáo cá nhân và đơn vị."""

    async def test_bao_cao_ca_nhan_thanh_cong(self, client: AsyncClient, cbcc_user):
        """CBCC xem báo cáo cá nhân tháng này."""
        resp = await client.get("/api/legal/v1/bao-cao/ca-nhan?thang=2&nam=2026")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        bao_cao = data["data"]
        assert bao_cao["thang"] == 2
        assert bao_cao["nam"] == 2026
        assert "vb_da_doc" in bao_cao
        assert "vb_chua_doc" in bao_cao
        assert "vb_qua_han" in bao_cao
        assert "quiz_hoan_thanh" in bao_cao

    async def test_bao_cao_ca_nhan_thang_hop_le(self, client: AsyncClient, cbcc_user):
        """Báo cáo cá nhân tháng 1-12 đều hợp lệ."""
        for thang in [1, 6, 12]:
            resp = await client.get(f"/api/legal/v1/bao-cao/ca-nhan?thang={thang}&nam=2026")
            assert resp.status_code == 200

    async def test_bao_cao_ca_nhan_thang_khong_hop_le(
        self, client: AsyncClient, cbcc_user
    ):
        """Tháng 13 → validation error."""
        resp = await client.get("/api/legal/v1/bao-cao/ca-nhan?thang=13&nam=2026")
        assert resp.status_code == 422  # Validation error

    async def test_bao_cao_doc_van_ban_cbcc_forbidden(
        self, client: AsyncClient, cbcc_user, published_van_ban
    ):
        """CBCC không xem được báo cáo đọc theo VB → 403."""
        vb_id = published_van_ban["id"]
        resp = await client.get(f"/api/legal/v1/van-ban/{vb_id}/bao-cao-doc")
        assert resp.status_code == 403

    async def test_bao_cao_doc_van_ban_qt_noi_dung_ok(
        self, client: AsyncClient, qt_noi_dung_user, published_van_ban
    ):
        """QT_NOI_DUNG xem báo cáo đọc theo VB → OK."""
        vb_id = published_van_ban["id"]
        resp = await client.get(f"/api/legal/v1/van-ban/{vb_id}/bao-cao-doc")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        bao_cao = data["data"]
        assert "van_ban" in bao_cao
        assert "tong_doi_tuong" in bao_cao
        assert "da_doc" in bao_cao
        assert "da_xac_nhan" in bao_cao
